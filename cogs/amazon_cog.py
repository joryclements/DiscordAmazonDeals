import json
import discord
import os
import re as regex
import bs4
import requests
from dotenv import load_dotenv
from pycord.multicog import add_to_group

load_dotenv(dotenv_path="settings.env")
ALLOWED_GUILDS = [int(os.getenv("ALLOWED_GUILDS"))]
HEADERS = ({'User-Agent':
                'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/44.0.2403.157 Safari/537.36',
            'Accept-Language': 'en-US, en;q=0.5'})


## User Functions
## These functions are used to create and manage user files
async def new_user(ctx: discord.ApplicationContext):
    try:
        with open(f"data/{ctx.author.id}.json", "r") as f:
            await ctx.respond("User already exists")
    except FileNotFoundError:
        with open(f"data/{ctx.author.id}.json", "w") as f:
            json.dump({}, f)
            await ctx.respond(f"Created user file {ctx.author.id}.json")
    f.close()
    return


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
    pattern = regex.compile("http(s)*://www.amazon.c(a|om)/([\\w-]+/)?(dp|gp/product)/(\\w+/)?(\\w{10})")
    m = pattern.match(url)
    print(m.groups())


    if m:
        return m[4]
    else:
        return None

class Amazon(discord.Cog, name="az"):
    def __init__(self, bot):
        super().__init__()
        self.bot = bot

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
        if asin is None:
            await ctx.respond("Invalid URL")
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
            with open(f"data/{ctx.author.id}.json", "r") as f:
                data = json.load(f)
            f.close()
            data[asin] = {"title": title, "price": price}
            with open(f"data/{ctx.author.id}.json", "w") as f:
                json.dump(data, f)
            f.close()
            await ctx.respond(f"Saved {title} to your tracked products")
            return

