import discord
from discord.ext import commands
from discord import app_commands

class Suggestion(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="setup_buttons", description="Post the suggestion panel")
    async def setup_buttons(self, interaction: discord.Interaction):
        embed = discord.Embed(title="📬 Suggestion Panel", description="Use the buttons below to submit or view your suggestions.")
        view = discord.ui.View()
        view.add_item(discord.ui.Button(label="💡 Make a Suggestion", style=discord.ButtonStyle.green, custom_id="make_suggestion"))
        view.add_item(discord.ui.Button(label="📂 View My Suggestions", style=discord.ButtonStyle.blurple, custom_id="view_suggestions"))
        await interaction.response.send_message(embed=embed, view=view)

async def setup(bot):
    await bot.add_cog(Suggestion(bot))
