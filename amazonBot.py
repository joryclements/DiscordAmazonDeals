import os
import discord

from dotenv import load_dotenv

load_dotenv(dotenv_path="settings.env")
DISCORD_API_KEY = os.getenv("DISCORD_API_KEY")
print(DISCORD_API_KEY)

bot = discord.Bot()

ALLOWED_GUILDS = [971268468148166697]

class Commands (discord.Cog, name = "Commands"):
    def __init__ (self, bot):
        super().__init__()
        self.bot = bot

    @discord.Cog.listener()
    async def on_ready(self):
        print(f"Logged in as {self.bot.user}!")

#    @discord.Cog.listener()
#    async def on_message(self, message: discord.Message):
    
    @discord.slash_comand(
        name = "ping",
        description = "Pong!",
        guild_ids = ALLOWED_GUILDS
    )
    async def ping (self, ctx: discord.ApplicationContext):
        await ctx.defer()
        await ctx.respond("Pong!")
        return

bot.add_cog(Commands(bot))
bot.run(DISCORD_API_KEY)
