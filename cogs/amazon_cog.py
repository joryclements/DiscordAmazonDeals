import discord
import os
import bs4
import requests
from dotenv import load_dotenv
load_dotenv(dotenv_path="settings.env")
ALLOWED_GUILDS = [(os.getenv("ALLOWED_GUILDS"))]
HEADERS = ({'User-Agent':
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/44.0.2403.157 Safari/537.36',
            'Accept-Language': 'en-US, en;q=0.5'})

class Amazon(discord.Cog, name="az"):
    def __init__(self, bot):
        super().__init__()
        self.bot = bot
    def get_title(self, soup: bs4.BeautifulSoup):
        try:
            # Outer Tag Object
            title = soup.find("span", attrs={"id": 'productTitle'}).string.strip()

        except AttributeError as e:
            title = e

        return title

    def get_price(self, soup: bs4.BeautifulSoup):
        try:
            price = soup.find("span", attrs={'class': 'a-offscreen'}).string.strip()

        except AttributeError as e:
            price = e

        return price

    @discord.Cog.listener()
    async def on_ready(self):
        print(f"COG READY: Amazon")

    @discord.option(
        name="url",
        description="Amazon URL",
        required=True,
    )
    @discord.slash_command(
        name="az",
        description="Amazon",
        guild_ids=ALLOWED_GUILDS
    )
    async def az(self, ctx: discord.ApplicationContext, url: str):
        await ctx.defer()
        webpage = requests.get(url, headers=HEADERS)
        soup = bs4.BeautifulSoup(webpage.content, "lxml")
        soup.prettify()
        title = self.get_title(soup)
        price = self.get_price(soup)
        await ctx.respond(f"{title}\n{price}")
        return