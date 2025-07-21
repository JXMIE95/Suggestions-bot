import discord
from discord.ext import commands, tasks
from discord.ui import View, Button
from datetime import datetime, timedelta
import json

with open("config.json") as f:
    config = json.load(f)

class Scheduler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.channel_check_loop.start()
        self.shift_check_loop.start()
        self.rosters = {}

    @tasks.loop(hours=1)
    async def channel_check_loop(self):
        """Ensure 7 rolling daily roster channels exist."""
        category = self.bot.get_channel(config["schedule_category_id"])
        if not category:
            return

        today = datetime.utcnow().date()
        existing = {c.name: c for c in category.text_channels}

        # Remove channels older than today
        for name, chan in existing.items():
            try:
                day = datetime.strptime(name, "%Y-%m-%d").date()
                if day < today:
                    await chan.delete()
            except:
                pass

        # Create missing channels
        for i in range(7):
            day_str = (today + timedelta(days=i)).isoformat()
            if day_str not in existing:
                channel = await category.create_text_channel(day_str)
                await self.initialize_roster(channel)

    async def initialize_roster(self, channel):
        embed = discord.Embed(title=f"Shift Roster for {channel.name}")
        embed.description = "\n".join([f"**{h:02d}:00** — _(empty)_" for h in range(24)])
        view = RosterButtonView()
        msg = await channel.send(embed=embed, view=view)
        self.rosters[channel.id] = {"message_id": msg.id, "entries": {}}

    @tasks.loop(minutes=1)
    async def shift_check_loop(self):
        now = datetime.utcnow()
        notification_time = now + timedelta(minutes=5)

        hour = notification_time.hour
        day_str = notification_time.date().isoformat()
        category = self.bot.get_channel(config["schedule_category_id"])
        if not category:
            return

        channel = discord.utils.get(category.text_channels, name=day_str)
        if not channel:
            return

        async for msg in channel.history(limit=10):
            if msg.author != self.bot.user or not msg.embeds:
                continue

            embed = msg.embeds[0]
            lines = embed.description.split("\n")
            people = [l for l in lines if l.startswith(f"**{hour:02d}:00**")]

            if people and "empty" not in people[0]:
                notif_channel = self.bot.get_channel(config["notification_channel"])
                king_role = f"<@&{config['king_role']}>"
                buff_role = f"<@&{config['buff_role']}>"
                await notif_channel.send(f"⏰ Upcoming shift at {hour:02d}:00 UTC!\n{king_role} {buff_role}")
                return

async def setup(bot):
    await bot.add_cog(Scheduler(bot))

class RosterButtonView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(AddButton())
        self.add_item(CancelButton())
        self.add_item(EditButton())

class AddButton(Button):
    def __init__(self):
        super().__init__(label="Add Availability", style=discord.ButtonStyle.success)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_message("Add availability functionality coming soon!", ephemeral=True)

class CancelButton(Button):
    def __init__(self):
        super().__init__(label="Cancel Availability", style=discord.ButtonStyle.danger)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_message("Cancel functionality coming soon!", ephemeral=True)

class EditButton(Button):
    def __init__(self):
        super().__init__(label="Edit Availability", style=discord.ButtonStyle.primary)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_message("Edit functionality coming soon!", ephemeral=True)
