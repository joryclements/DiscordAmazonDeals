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


## User Functions
## These functions are used to create and manage user files
async def new_user(ctx: discord.ApplicationContext):
    # Add user to database
    conn = sqlite3.connect(os.getenv("SQLITE_DATABASE"))
    cursor = conn.cursor()
    cursor.execute("INSERT INTO users (user_id) VALUES (?)", (ctx.author.id,))
    conn.commit()
    conn.close()
    return
async def get_products(ctx: discord.ApplicationContext):
    conn = sqlite3.connect(os.getenv("SQLITE_DATABASE"))
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM products WHERE user_id = ?", (ctx.author.id,))
    products = cursor.fetchall()
    conn.close()
    return products

## Parsing Functions
## These functions are used to parse the HTML of the Amazon Canada website
def get_title(soup: bs4.BeautifulSoup):
    try:
        # Outer Tag Object
        title = soup.find("span", attrs={"id": 'productTitle'}).string.strip()

    except AttributeError as e:
        title = e

    return title


def get_price(soup: bs4.BeautifulSoup):
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
    # Create a table
    cursor.execute("""CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY)
    """)
    # Create another table, with a foreign key to the users table
    cursor.execute("""CREATE TABLE IF NOT EXISTS products (
        asin TEXT PRIMARY KEY,
        user_id INTEGER,
        url TEXT,
        title TEXT,
        price TEXT,
        date_added TEXT,
        date_updated TEXT,
        FOREIGN KEY (user_id) REFERENCES users (user_id))
    """)
    # Save (commit) the changes
    conn.commit()
    # Close the connection
    conn.close()

class Amazon(discord.Cog, name="az"):
    def __init__(self, bot):
        super().__init__()
        self.bot = bot
        setup_db()
        # Create a MySQL connection
        # self.conn = mysql.connector.connect(
        #     host=os.getenv("MYSQL_HOST"),
        #     user=os.getenv("MYSQL_USER"),
        #     password=os.getenv("MYSQL_PASSWORD"),
        #     database=os.getenv("MYSQL_DATABASE")
        # )

    az = discord.SlashCommandGroup(name="az",
                                   description="AMAZON CANADA",
                                   guild_ids=ALLOWED_GUILDS)

    @discord.Cog.listener()
    async def on_ready(self):
        print(f"COG READY: Amazon - NEW")

    @az.command(
        name="new_user",
        description="Create a new user file",
        guild_ids=ALLOWED_GUILDS)

    async def new_user(self, ctx: discord.ApplicationContext):
        await new_user(ctx)
        return
    @az.command(
        name="view_products",
        description="Get a list of saved products",
        guild_ids=ALLOWED_GUILDS)
    async def view_products(self, ctx: discord.ApplicationContext):
        products = await get_products(ctx)
        await ctx.respond(products)
        return
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
        price = get_price(soup)
        await ctx.respond(f"{title}\n{price}")
        return

    @az.command(
        name="get_asin",
        description="Get the ASIN of an Amazon product",
        guild_ids=ALLOWED_GUILDS)
    @discord.option(name="url", description="URL of the Amazon product", required=True)
    async def get_product(self, ctx: discord.ApplicationContext, url: str = "None"):
        await ctx.defer()
        asin = get_asin(url)
        if asin == "NAURL":
            await ctx.respond("Invalid URL. Please use Amazon.ca or Amazon.com")
            return
        elif asin == "NASIN":
            await ctx.respond("I couldn't find that products unique identifier")
            return
        else:
            await ctx.respond(f"ASIN: {asin}")
            return

    @az.command(
        name="save_product",
        description="Save the product to your tracked products",
        guild_ids=ALLOWED_GUILDS)
    @discord.option(name="url", description="URL of the Amazon product", required=True)
    async def get_product(self, ctx: discord.ApplicationContext, url: str = "None"):
        await ctx.defer()
        webpage = requests.get(url, headers=HEADERS)
        soup = bs4.BeautifulSoup(webpage.content, "lxml")
        asin = get_asin(url)
        if asin is None:
            await ctx.respond("Invalid URL")
            return
        else:
            title = get_title(soup)
            price = get_price(soup)
            conn = sqlite3.connect(os.getenv("SQLITE_DATABASE"))
            cursor = conn.cursor()
            cursor.execute("INSERT INTO products (asin, user_id, url, title, price, date_added, date_updated) VALUES "
                           "(?, ?, ?, ?, ?, ?, ?)", (asin, ctx.author.id, url, title, price, datetime.datetime.now().isoformat(),
                                                     datetime.datetime.now().isoformat()))
            conn.commit()
            conn.close()
            await ctx.respond(f"Product saved: {title}")
            return
