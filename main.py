import os

from discord.ext import commands
from discord import app_commands
import discord
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("DISCORD_BOT_TOKEN")

class MyClient(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=discord.Intents.all(), help_command=None)

    async def setup_hook(self) -> None:
        await self.load_extension("cogs.letter")
        pass

    async def on_ready(self):
        print("Logged in as", self.user)
        pass


bot = MyClient()
bot.run("Putbottokenhere")
