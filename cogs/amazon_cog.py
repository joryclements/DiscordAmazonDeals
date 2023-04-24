import asyncio
import datetime
import discord
import os
import re as regex
import bs4
import requests
from dotenv import load_dotenv
import sqlite3
from discord.ext import pages

load_dotenv(dotenv_path="settings.env")
ALLOWED_GUILDS = [int(os.getenv("ALLOWED_GUILDS"))]
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:66.0) Gecko/20100101 Firefox/66.0",
           "Accept-Encoding": "gzip, deflate",
           "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,/;q=0.8", "DNT": "1", "Connection": "close",
           "Upgrade-Insecure-Requests": "1"}


# Job Class
# This class is used to create a job object for each product being tracked
class Job:
    def __init__(self, title, current_price, interval, url, last_checked=None, user_id=None, message=False):
        self.title = title
        self.current_price = current_price
        self.previous_prices = []
        self.refresh_interval = interval
        self.url = url
        self.last_checked = last_checked
        self.user_id = user_id
        self.message = message

    def update_price(self):
        webpage = requests.get(self.url, headers=HEADERS)
        soup = bs4.BeautifulSoup(webpage.content, "lxml")
        self.last_checked = datetime.datetime.now().isoformat()
        try:
            self.previous_prices.append(self.current_price)
            self.current_price = get_price(soup=soup)
        except AttributeError as e:
            print(e)
        try:
            # update the database
            conn = sqlite3.connect(os.getenv("SQLITE_DATABASE"))
            cursor = conn.cursor()
            cursor.execute("UPDATE products SET price = ?, date_updated = ? WHERE url = ?",
                           (self.current_price, datetime.datetime.now().isoformat(), self.url))
            conn.commit()
            conn.close()
        except sqlite3.Error as e:
            print(e)

    async def send_notification(self, user: discord.User):
        embed = discord.Embed(title=self.title, url=self.url, color=0x00ff00)
        embed.add_field(name="Current Price", value=self.current_price, inline=True)
        embed.add_field(name="Previous Price", value=self.previous_prices[-1], inline=True)
        embed.add_field(name="Percent Change", value=self.percent_change, inline=True)
        embed.set_footer(text="Last Checked: " + str(self.last_checked))
        await user.send(embed=embed)

    def check_price_change(self):
        if self.previous_prices[-1] != self.current_price:
            return True
        return False


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


async def get_products(author_id: int):
    conn = sqlite3.connect(os.getenv("SQLITE_DATABASE"))
    cursor = conn.cursor()
    # Select the url and price for all products associated with the user
    cursor.execute("SELECT title, price, date_updated, url FROM products WHERE user_id = ?", (author_id,))
    products = cursor.fetchall()
    print(products)
    conn.close()
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
def generate_user_url(url: str, user_id: int):
    return url + "<" + str(user_id)


def get_original_url(url: str):
    print('URL SPLIT: ' + url.split("<")[0])
    return url.split("<")[0]


def get_title(soup: bs4.BeautifulSoup):
    try:
        print(soup)
        title = soup.find("span", attrs={"id": 'productTitle'}).string.strip()
        print(title)
    except AttributeError as e:
        title = e
    return title


def get_price(soup: bs4.BeautifulSoup = None, url: str = None):
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
        user_id TEXT,
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


class Amazon(discord.Cog, name="az"):
    def __init__(self, bot):
        super().__init__()
        self.bot = bot
        self.queue = asyncio.Queue()
        asyncio.ensure_future(self.process_queue())
        setup_db()

    # Job Scheduler
    async def process_queue(self):
        # This function will run forever, checking the queue for jobs
        while True:
            if self.queue.empty():
                await asyncio.sleep(1)
                continue

            # Get the next job from the queue
            job = await self.queue.get()
            if datetime.datetime.fromisoformat(job.last_checked) + datetime.timedelta(
                    seconds=job.refresh_interval) < datetime.datetime.now():
                job.update_price()
                # Notify the user if the price has changed
                if job.check_price_change():
                    user = await self.bot.fetch_user(job.user_id)
                    await job.send_notification(user=user)
            # Put the job back in the queue
            await self.queue.put(job)
            self.queue.task_done()

    az = discord.SlashCommandGroup(name="amzn",
                                   description="Discord bot to track Amazon products and notify you when the price "
                                               "changes!",
                                   guild_ids=ALLOWED_GUILDS)

    @discord.Cog.listener()
    async def on_ready(self):
        print(f"COG READY: Amazon - NEW")

    @az.command(
        name="view",
        description="View all of your tracked Amazon products",
        guild_ids=ALLOWED_GUILDS)
    async def view_products(self, ctx: discord.ApplicationContext):
        products = await get_products(ctx.author.id)
        if products is None:
            await ctx.send("You have no tracked products!")
            return

        # Split the list of products into chunks of 5 products if there are more than 5 products
        product_pages = []
        for i in range(0, len(products), 5):
            product_pages.append(products[i:i + 5])
        # Create embeds for each page
        embed_pages = []
        for page in product_pages:
            embed = discord.Embed(title=f"{ctx.author}'s Tracked Amazon Products", color=0xFFA500)
            for product in page:
                # Get the time difference between now and the last time the price was updated
                difference = (datetime.datetime.now() - datetime.datetime.fromisoformat(product[2])).total_seconds()

                embed.add_field(name=product[0],
                                value=f"[{product[1]}]({get_original_url(product[3])}) as of {divmod(difference, 3600)[0]} hours, {divmod(difference, 60)[0]} min ago.",
                                inline=False)
            embed_pages.append(embed)

        paginator = pages.Paginator(
            pages=embed_pages,
            timeout=None,
            author_check=False,
        )
        await paginator.respond(ctx.interaction)

    @az.command(
        name="get",
        description="get the product to your tracked products",
        guild_ids=ALLOWED_GUILDS)
    @discord.option(name="url", description="URL of the Amazon product", required=True)
    async def get_all_prodct(self, ctx: discord.ApplicationContext, url: str = "None"):
        await get_products(ctx.author.id)

    @az.command(
        name="track",
        description="Save the product to your tracked products",
        guild_ids=ALLOWED_GUILDS)
    @discord.option(name="url", description="URL of the Amazon product", required=True)
    async def save_product(self, ctx: discord.ApplicationContext, url):
        await ctx.defer()
        # Check if the user is in the database
        user = get_user(ctx)
        if user is None:
            # Add the user to the database
            await new_user(ctx)
        # Get the details of the product
        webpage = requests.get(url, headers=HEADERS)
        soup = bs4.BeautifulSoup(webpage.content, "lxml")
        title = get_title(soup=soup)
        price = get_price(soup=soup)
        user_url = generate_user_url(url=url, user_id=ctx.author.id)
        print((user_url, ctx.author.id, title, price, datetime.datetime.now().isoformat(),
               datetime.datetime.now().isoformat(), "", ""))

        # Add the product to the database
        try:
            conn = sqlite3.connect(os.getenv("SQLITE_DATABASE"))
            cursor = conn.cursor()
            cursor.execute("INSERT INTO products VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                           (user_url, ctx.author.id, title, price, datetime.datetime.now().isoformat(),
                            datetime.datetime.now().isoformat(), "", ""))

            conn.commit()
            conn.close()
            job = Job(title=title, current_price=price, url=url, interval=30,
                      last_checked=datetime.datetime.now().isoformat(), user_id=ctx.author.id)
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
