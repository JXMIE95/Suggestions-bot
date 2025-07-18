import discord
from discord import app_commands
from discord.ext import commands
from config import channel_config

class ChannelConfig(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="setchannels", description="Set the bot's target channels.")
    @app_commands.describe(
        main="Channel for posting public suggestions",
        staff="Channel for staff review",
        announce="Channel for approved suggestions"
    )
    async def setchannels(self, interaction: discord.Interaction,
                          main: discord.TextChannel,
                          staff: discord.TextChannel,
                          announce: discord.TextChannel):
        channel_config["main_chat_id"] = main.id
        channel_config["staff_channel_id"] = staff.id
        channel_config["announcement_channel_id"] = announce.id

        await interaction.response.send_message(
            f"✅ Channels set:\nMain: {main.mention}\nStaff: {staff.mention}\nAnnouncement: {announce.mention}",
            ephemeral=True
        )

async def setup(bot):
    await bot.add_cog(ChannelConfig(bot))
