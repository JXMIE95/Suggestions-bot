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

class AvailabilityModal(discord.ui.Modal, title="Add Availability"):
    hour = discord.ui.TextInput(label="Hour (0–23 UTC)", placeholder="e.g. 14")

    def __init__(self, user_id, date_str):
        super().__init__()
        self.user_id = user_id
        self.date_str = date_str

    async def on_submit(self, interaction: discord.Interaction):
        roster = load_roster()
        date = roster.setdefault(self.date_str, {})
        hour = self.hour.value.strip()
        if not hour.isdigit() or not (0 <= int(hour) <= 23):
            await interaction.response.send_message("❌ Invalid hour.", ephemeral=True)
            return
        hour_key = str(int(hour))
        if hour_key not in date:
            date[hour_key] = []
        if self.user_id in date[hour_key]:
            await interaction.response.send_message("❌ You're already in that slot.", ephemeral=True)
            return
        if len(date[hour_key]) >= 2:
            await interaction.response.send_message("❌ That hour is full.", ephemeral=True)
            return
        date[hour_key].append(self.user_id)
        save_roster(roster)
        await interaction.response.send_message(f"✅ Added for {hour}:00 UTC on {self.date_str}", ephemeral=True)

class Scheduler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.update_channels.start()
        self.shift_reminders.start()

    def get_dates(self):
        today = datetime.utcnow().date()
        return [(today + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(7)]

    @tasks.loop(minutes=10)
    async def update_channels(self):
        guild = self.bot.guilds[0]
        category = discord.utils.get(guild.categories, id=config["scheduler_category_id"])
        if not category:
            return
        existing = {ch.name: ch for ch in category.channels}
        expected = self.get_dates()

        for ch_name in list(existing):
            if ch_name not in expected:
                await existing[ch_name].delete()

        for ch_name in expected:
            if ch_name not in existing:
                channel = await category.create_text_channel(ch_name)
                await self.init_roster_msg(channel, ch_name)

    async def init_roster_msg(self, channel, date_str):
        embed = discord.Embed(title=f"Roster for {date_str}", description="Use the button to add yourself.", color=discord.Color.green())
        view = discord.ui.View()
        view.add_item(discord.ui.Button(label="Add Availability", custom_id=f"add_avail_{date_str}", style=discord.ButtonStyle.primary))
        await channel.send(embed=embed, view=view)

    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction):
        if interaction.type == discord.InteractionType.component:
            cid = interaction.data["custom_id"]
            if cid.startswith("add_avail_"):
                date_str = cid.split("_", 2)[2]
                await interaction.response.send_modal(AvailabilityModal(interaction.user.id, date_str))

    @tasks.loop(minutes=1)
    async def shift_reminders(self):
        now = datetime.utcnow()
        if now.minute != 55:
            return
        roster = load_roster()
        date_str = now.date().isoformat()
        next_hour = str((now.hour + 1) % 24)
        if date_str not in roster:
            return
        people = roster[date_str].get(next_hour, [])
        if not people:
            return
        mentions = " ".join(f"<@{uid}>" for uid in people)
        channel = self.bot.get_channel(config["notification_channel_id"])
        await channel.send(f"⏰ Reminder: Shift at {next_hour}:00 UTC for {mentions}")

async def setup(bot):
    await bot.add_cog(Scheduler(bot))