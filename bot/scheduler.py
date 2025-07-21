import discord
from discord.ext import commands, tasks
from discord import app_commands, Interaction
from datetime import datetime, timedelta
import json
import os

CONFIG_PATH = "buff_config.json"

class BuffScheduler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = self.load_config()
        self.reminder_loop.start()

    def load_config(self):
        if os.path.exists(CONFIG_PATH):
            with open(CONFIG_PATH, "r") as f:
                return json.load(f)
        return {}

    def save_config(self):
        with open(CONFIG_PATH, "w") as f:
            json.dump(self.config, f, indent=2)

    @app_commands.command(name="buff_configure", description="Configure buff scheduler settings.")
    @app_commands.describe(
        king_role="Role of the King",
        buff_givers_role="Role of the Buff Givers",
        schedule_category="Category for the schedule",
        notification_channel="Channel for reminders and logs",
        active_buff_role="Role to assign when active on shift"
    )
    async def buff_configure(self, interaction: Interaction,
                             king_role: discord.Role,
                             buff_givers_role: discord.Role,
                             schedule_category: discord.CategoryChannel,
                             notification_channel: discord.TextChannel,
                             active_buff_role: discord.Role):
        self.config["king_role_id"] = king_role.id
        self.config["buff_givers_role_id"] = buff_givers_role.id
        self.config["schedule_category_id"] = schedule_category.id
        self.config["notification_channel_id"] = notification_channel.id
        self.config["active_buff_role_id"] = active_buff_role.id
        self.save_config()
        await interaction.response.send_message("â Scheduler configured successfully.", ephemeral=True)

    @tasks.loop(minutes=1)
    async def reminder_loop(self):
        now = datetime.utcnow()
        # Check for reminders here...
        # (logic can be expanded with shift data structure and JSON read)
        pass

async def setup(bot):
    await bot.add_cog(BuffScheduler(bot))
