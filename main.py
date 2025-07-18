import discord
from discord.ext import commands
from views import SuggestionButtons
from handlers import setup_handlers
import os

intents = discord.Intents.default()
intents.message_content = True

class SuggestionBot(commands.Bot):
    async def setup_hook(self):
        self.add_view(SuggestionButtons())
        await self.load_extension("commands")
        await setup_handlers(self)
        await self.tree.sync()

bot = SuggestionBot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")

bot.run(os.getenv("DISCORD_TOKEN"))