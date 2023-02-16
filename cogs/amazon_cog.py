import asyncio
import datetime
import discord
import os
import re as regex
import bs4
import requests
from dotenv import load_dotenv
import sqlite3


load_dotenv(dotenv_path="settings.env")
ALLOWED_GUILDS = [int(os.getenv("ALLOWED_GUILDS"))]
HEADERS = ({'User-Agent':
                'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/44.0.2403.157 Safari/537.36',
            'Accept-Language': 'en-US, en;q=0.5'})

class Job:
    def __init__(self, title, current_price, interval, url, last_checked=None, user_id=None):
        self.title = title
        self.current_price = current_price
        self.previous_prices = []
        self.refresh_interval = interval
        self.url = url
        self.last_checked = last_checked
        self.user_id = user_id

    def update_price(self):
        print("Updating price at " + str(datetime.datetime.now()))
        webpage = requests.get(self.url, headers=HEADERS)
        soup = bs4.BeautifulSoup(webpage.content, "lxml")
        self.last_checked = datetime.datetime.now()
        try:
            self.previous_prices.append(self.current_price)
            self.current_price = get_price(soup=soup)
        except AttributeError as e:
            print(e)
        try:
            #update the database
            conn = sqlite3.connect(os.getenv("SQLITE_DATABASE"))
            cursor = conn.cursor()
            cursor.execute("UPDATE products SET price = ?, date_updated = ? WHERE url = ?", (self.current_price, datetime.datetime.now().isoformat(), self.url))
            conn.commit()
            conn.close()
        except sqlite3.Error as e:
            print(e)

## User Functions
## These functions are used to create and manage user files
async def new_user(ctx: discord.ApplicationContext):
    # Add user to database
    conn = sqlite3.connect(os.getenv("SQLITE_DATABASE"))
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO users VALUES (?)", (ctx.author.id,))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        conn.close()
        return False
async def get_products(ctx: discord.ApplicationContext):
    conn = sqlite3.connect(os.getenv("SQLITE_DATABASE"))
    cursor = conn.cursor()
    # Select the url and price for all products associated with the user
    cursor.execute("SELECT title, price, date_updated, url FROM products WHERE user_id = ?", (ctx.author.id,))
    products = cursor.fetchall()
    conn.close()
    print(products)
    return products
def get_user(ctx: discord.ApplicationContext):
    conn = sqlite3.connect(os.getenv("SQLITE_DATABASE"))
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE user_id = ?", (ctx.author.id,))
    user = cursor.fetchone()
    conn.close()
    return user
## Parsing Functions
## These functions are used to parse the HTML of the Amazon Canada website
def get_title(soup: bs4.BeautifulSoup):
    try:
        # Outer Tag Object
        title = soup.find("span", attrs={"id": 'productTitle'}).string.strip()

    except AttributeError as e:
        title = e

    return title


def get_price(soup: bs4.BeautifulSoup=None, url: str=None):
    if soup is None:
        print("Soup is None")
    if url is None:
        print("URL is None")
    print("Getting price at " + str(datetime.datetime.now()))
    if soup is None:
        page = requests.get(url, headers=HEADERS)
        soup = bs4.BeautifulSoup(page.content, "lxml")
    try:
        price = soup.find("span", attrs={'class': 'a-offscreen'}).string.strip()
    except AttributeError as e:
        price = e

    return price

def get_asin(url: str):
    # Split the URL by the forward slash
    url = url.split("/")
    # Verify the URL is for Amazon.ca or Amazon.com
    if url[2] != "www.amazon.ca" or url[2] != "www.amazon.com":
        return "NAURL"
    # Get the ASIN from the URL
    for section in url:
        if regex.match(r"/([a-zA-Z0-9]{10})(?:[/?]|$)", section):
            return section
    return "NASIN"


## Database Functions
def setup_db():
    # Create a SQLite connection
    conn = sqlite3.connect(os.getenv("SQLITE_DATABASE"))
    cursor = conn.cursor()
    # Create a users table
    cursor.execute("CREATE TABLE IF NOT EXISTS users (\n"
                   "        user_id INTEGER PRIMARY KEY)\n"
                   "    ")
    # Create a products table, with a foreign key to the users table
    cursor.execute("""CREATE TABLE IF NOT EXISTS products (
        url TEXT PRIMARY KEY,
        user_id INTEGER,
        title TEXT,
        price TEXT,
        date_added TEXT,
        date_updated TEXT,
        previous_prices TEXT,
        percent_change TEXT,
        FOREIGN KEY (user_id) REFERENCES users (user_id))
    """)
    conn.commit()
    conn.close()

## Scheduler Functions

class Amazon(discord.Cog, name="az"):
    def __init__(self, bot):
        super().__init__()
        self.bot = bot
        setup_db()
        self.queue = asyncio.Queue()
        asyncio.ensure_future(self.process_queue())

    async def process_queue(self):
        while True:
            if self.queue.empty():
                await asyncio.sleep(1)
                continue

            job = await self.queue.get()
            if datetime.datetime.fromisoformat(job.last_checked) + datetime.timedelta(seconds=job.refresh_interval) < datetime.datetime.now():
                job.update_price()
                user = await self.bot.fetch_user(job.user_id)
                await user.send(f"I just checked the price for {job.title} has changed to {job.current_price} (was {job.previous_prices})")
            else:
                # Re-add the job to the queue
                await self.queue.put(job)
            self.queue.task_done()


    az = discord.SlashCommandGroup(name="az",
                                   description="AMAZON CANADA",
                                   guild_ids=ALLOWED_GUILDS)

    @discord.Cog.listener()
    async def on_ready(self):
        print(f"COG READY: Amazon - NEW")

    @az.command(
        name="view_products",
        description="Get a list of saved products",
        guild_ids=ALLOWED_GUILDS)
    async def view_products(self, ctx: discord.ApplicationContext):
        products = await get_products(ctx)
        embed = discord.Embed(
            title="Amazon Tracked Products",
            color=discord.Color.orange()
        )
        for product in products:
            embed.add_field(name=product[0], value=f"[{product[1]}]({product[3]}) as of {product[2]}", inline=False)
        await ctx.send(embed=embed)
    @az.command(
        name="get_product",
        description="Get the title and price of an Amazon product",
        guild_ids=ALLOWED_GUILDS)
    @discord.option(name="url", description="URL of the Amazon product", required=True)
    async def get_product(self, ctx: discord.ApplicationContext, url: str = "None"):
        await ctx.defer()
        webpage = requests.get(url, headers=HEADERS)
        soup = bs4.BeautifulSoup(webpage.content, "lxml")
        title = get_title(soup)
        price = get_price(soup=soup)
        await ctx.respond(f"{title}\n{price}")
        return

    @az.command(
        name="save_product",
        description="Save the product to your tracked products",
        guild_ids=ALLOWED_GUILDS)
    @discord.option(name="url", description="URL of the Amazon product", required=True)
    async def save_product(self, ctx: discord.ApplicationContext, url: str = "None"):
        await ctx.defer()
        # Check if the user is in the database
        user = get_user(ctx)
        if user is None:
            # Add the user to the database
            await new_user(ctx)
        # Get the details of the product
        webpage = requests.get(url, headers=HEADERS)
        soup = bs4.BeautifulSoup(webpage.content, "lxml")
        title = get_title(soup)
        price = get_price(soup=soup)
        # Add the product to the database

        try:
            conn = sqlite3.connect(os.getenv("SQLITE_DATABASE"))
            cursor = conn.cursor()
            cursor.execute("INSERT INTO products VALUES (?, ?, ?, ?, ?, ?, ?, ?)", (url, ctx.author.id, title, price, datetime.datetime.now().isoformat(), datetime.datetime.now().isoformat(), price, 0))
            conn.commit()
            conn.close()
            job = Job(title=title, current_price=price, url=url, interval=30, last_checked=datetime.datetime.now().isoformat(), user_id=ctx.author.id)
            await self.queue.put(job)
        except sqlite3.IntegrityError as e:
            conn.close()
            await ctx.respond("Error adding product to database")
            print(e)
            return
        if user is None:
            await ctx.respond(f"{ctx.author.mention} added {title} to your tracked products ({price}). This is your "
                              f"first product, so I have added you to the database!")
        else:
            await ctx.respond(f"{ctx.author.mention} added {title} to your tracked products ({price}).")
        return
