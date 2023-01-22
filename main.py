import os
import discord
from cogs.amazon_cog import Amazon
from dotenv import load_dotenv

load_dotenv(dotenv_path="settings.env")
DISCORD_API_KEY = os.getenv("DISCORD_API_KEY")

if __name__ == "__main__":
    bot = discord.Bot(intents=discord.Intents.all())
    bot.add_cog(Amazon(bot))
    bot.run(DISCORD_API_KEY)
