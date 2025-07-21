import discord
from discord.ext import commands, tasks
from datetime import datetime, timedelta
import json
import os

with open("config.json") as f:
    config = json.load(f)

ROSTER_PATH = "data/roster_data.json"

def load_roster():
    if os.path.exists(ROSTER_PATH):
        with open(ROSTER_PATH, "r") as f:
            return json.load(f)
    return {}

def save_roster(data):
    with open(ROSTER_PATH, "w") as f:
        json.dump(data, f, indent=2)

class Scheduler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.update_day_channels.start()
        self.send_shift_reminders.start()

    def get_rolling_dates(self):
        today = datetime.utcnow().date()
        return [(today + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(7)]

    @tasks.loop(minutes=10)
    async def update_day_channels(self):
        guild = self.bot.guilds[0]
        category = discord.utils.get(guild.categories, id=config["scheduler_category_id"])
        if not category:
            return

        existing = {ch.name: ch for ch in category.text_channels}
        needed = self.get_rolling_dates()

        # Delete expired channels
        for name in existing:
            if name not in needed:
                await existing[name].delete()

        # Create missing ones
        for name in needed:
            if name not in existing:
                channel = await category.create_text_channel(name)
                await self.initialize_roster_message(channel, name)

    async def initialize_roster_message(self, channel, date_str):
        embed = discord.Embed(
            title=f"Roster for {date_str}",
            description="Use the buttons below to manage your shift availability.",
            color=discord.Color.teal()
        )
        embed.add_field(name="Availability", value="(Not implemented: shift slots UI)", inline=False)
        view = discord.ui.View()
        view.add_item(discord.ui.Button(label="Add Availability", style=discord.ButtonStyle.primary))
        await channel.send(embed=embed, view=view)

    @tasks.loop(minutes=1)
    async def send_shift_reminders(self):
        now = datetime.utcnow()
        if now.minute != 55:
            return
        roster = load_roster()
        today = now.date().isoformat()
        hour = now.hour
        if today not in roster:
            return
        entries = roster[today].get(str(hour + 1), [])  # Notify 5 min before shift
        if entries:
            channel = self.bot.get_channel(config["notification_channel_id"])
            mentions = " ".join([f"<@{user_id}>" for user_id in entries])
            await channel.send(f"⏰ Upcoming shift at {hour+1:02}:00 UTC for: {mentions}")

async def setup(bot):
    await bot.add_cog(Scheduler(bot))