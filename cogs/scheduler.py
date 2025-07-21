import discord
from discord.ext import commands, tasks
from discord import app_commands
from discord.ui import View, Button
from datetime import datetime, timedelta
import json

with open("config.json") as f:
    config = json.load(f)

class Scheduler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.rosters = {}
        self.channel_loop.start()
        self.shift_loop.start()

    @tasks.loop(hours=1)
    async def channel_loop(self):
        cat = self.bot.get_channel(config["schedule_category_id"])
        if not cat: return
        today = datetime.utcnow().date()
        existing = {c.name:c for c in cat.text_channels}
        for name,ch in existing.items():
            try:
                d = datetime.fromisoformat(name).date()
                if d < today:
                    await ch.delete()
            except: pass
        for i in range(7):
            day = (today+timedelta(days=i)).isoformat()
            if day not in existing:
                c = await cat.create_text_channel(day)
                await self.init_roster(c)

    async def init_roster(self, channel):
        em = discord.Embed(title=f"Roster {channel.name}")
        em.description = "\n".join([f"**{h:02d}:00** — _(empty)_" for h in range(24)])
        view = RosterView(channel.id)
        msg = await channel.send(embed=em, view=view)
        self.rosters[channel.id] = {"msg": msg.id, "entries": {}}

    @tasks.loop(minutes=1)
    async def shift_loop(self):
        now = datetime.utcnow()
        target = now + timedelta(minutes=5)
        day = target.date().isoformat()
        h = target.hour
        cat = self.bot.get_channel(config["schedule_category_id"])
        if not cat: return
        ch = discord.utils.get(cat.text_channels, name=day)
        if not ch: return
        msg = await ch.fetch_message(self.rosters.get(ch.id,{}).get("msg",0))
        em = msg.embeds[0]
        line = em.description.split("\n")[h]
        if "empty" not in line:
            notify = self.bot.get_channel(config["notification_channel"])
            kr = f"<@&{config['king_role']}>"
            br = f"<@&{config['buff_role']}>"
            await notify.send(f"⏰ Shift at {h:02d}:00 UTC!\n{kr} {br}")
        # Further signup notifications can be added here

    @app_commands.command(description="Print today's roster")
    async def roster(self, interaction: discord.Interaction):
        today = datetime.utcnow().date().isoformat()
        cat = self.bot.get_channel(config["schedule_category_id"])
        ch = discord.utils.get(cat.text_channels, name=today)
        if not ch:
            return await interaction.response.send_message("No roster channel today.")
        msg = await ch.fetch_message(self.rosters[ch.id]["msg"])
        await interaction.response.send_message(embed=msg.embeds[0], ephemeral=True)

async def setup(bot):
    await bot.add_cog(Scheduler(bot))

class RosterView(View):
    def __init__(self, chan_id):
        super().__init__(timeout=None)
        self.chan = chan_id
        self.add_item(AddButton(chan_id))
        self.add_item(CancelButton(chan_id))

class AddButton(Button):
    def __init__(self, c): super().__init__(label="Add Availability", style=discord.ButtonStyle.success); self.chan=c
    async def callback(self, i):
        await i.response.send_message("Add feature coming soon!", ephemeral=True)

class CancelButton(Button):
    def __init__(self, c): super().__init__(label="Cancel Availability", style=discord.ButtonStyle.danger); self.chan=c
    async def callback(self, i):
        await i.response.send_message("Cancel coming soon!", ephemeral=True)