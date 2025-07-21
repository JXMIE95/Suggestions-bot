import discord
from discord.ext import commands, tasks
from discord import app_commands
import json
import os
from datetime import datetime, timedelta
from discord.utils import get

CONFIG_FILE = "buff_config.json"
SCHEDULE_FILE = "buff_schedule.json"

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    return {}

def save_config(config):
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=4)

def load_schedule():
    if os.path.exists(SCHEDULE_FILE):
        with open(SCHEDULE_FILE, "r") as f:
            return json.load(f)
    return {}

def save_schedule(schedule):
    with open(SCHEDULE_FILE, "w") as f:
        json.dump(schedule, f, indent=4)

class BuffScheduler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = load_config()
        self.schedule = load_schedule()
        self.reminder_loop.start()

    def cog_unload(self):
        self.reminder_loop.cancel()

    @app_commands.command(name="scheduler_config", description="Configure scheduler settings.")
    @app_commands.describe(
        king_role="King role (manager)",
        buff_giver_role="Buff giver role (assigned during shifts)",
        notification_channel="Channel to send shift alerts",
        schedule_category="Category to create schedule channels"
    )
    async def scheduler_config(self, interaction: discord.Interaction,
        king_role: discord.Role,
        buff_giver_role: discord.Role,
        notification_channel: discord.TextChannel,
        schedule_category: discord.CategoryChannel
    ):
        guild_id = str(interaction.guild.id)
        self.config[guild_id] = {
            "king_role": king_role.id,
            "buff_giver_role": buff_giver_role.id,
            "notification_channel": notification_channel.id,
            "schedule_category": schedule_category.id
        }
        save_config(self.config)
        await interaction.response.send_message("â Scheduler configuration saved.", ephemeral=True)

    async def run_generate_schedule(self, guild):
        guild_id = str(guild.id)
        if guild_id not in self.config:
            return

        config = self.config[guild_id]
        category = get(guild.categories, id=config["schedule_category"])
        if not category:
            return

        for ch in category.channels:
            await ch.delete()

        now = datetime.utcnow().replace(minute=0, second=0, microsecond=0)
        schedule = {}

        for day in range(7):
            date = now + timedelta(days=day)
            date_str = date.strftime("%Y-%m-%d")
            channel = await guild.create_text_channel(name=date_str, category=category)

            schedule[date_str] = {
                "notes": {},
                **{f"{hour:02d}:00": [] for hour in range(24)}
            }

            await self.send_schedule_message(channel, schedule[date_str], guild_id)

        self.schedule[guild_id] = schedule
        save_schedule(self.schedule)

    async def send_schedule_message(self, channel, day_schedule, guild_id):
        embed = discord.Embed(title=f"ð Schedule for {channel.name}", description="", color=discord.Color.blue())
        for hour in range(24):
            hour_str = f"{hour:02d}:00"
            users = day_schedule.get(hour_str, [])
            if not users:
                embed.add_field(name=hour_str, value="Available", inline=False)
            else:
                formatted = []
                for uid in users:
                    note = day_schedule["notes"].get(str(uid), "")
                    formatted.append(f"<@{uid}>" + (f" ({note})" if note else ""))
                embed.add_field(name=hour_str, value="\n".join(formatted), inline=False)

        view = ScheduleView(channel.guild, channel.name)
        await channel.send(embed=embed, view=view)

    @tasks.loop(minutes=1)
    async def reminder_loop(self):
        now = datetime.utcnow().replace(second=0, microsecond=0)
        for guild in self.bot.guilds:
            guild_id = str(guild.id)
            config = self.config.get(guild_id)
            schedule = self.schedule.get(guild_id)
            if not config or not schedule:
                continue

            notification_channel = get(guild.text_channels, id=config["notification_channel"])
            buff_role = get(guild.roles, id=config["buff_giver_role"])
            king_role = get(guild.roles, id=config["king_role"])

            for date, data in schedule.items():
                for hour, users in data.items():
                    if hour == "notes":
                        continue
                    time_obj = datetime.strptime(f"{date} {hour}", "%Y-%m-%d %H:%M")
                    if time_obj - timedelta(minutes=5) == now:
                        mentions = f"{king_role.mention} {buff_role.mention}" if king_role and buff_role else ""
                        if notification_channel and users:
                            await notification_channel.send(f"{mentions} â° Shift at {hour} starting soon for: {', '.join(f'<@{u}>' for u in users)}")

    async def update_message(self, channel, day_schedule, guild_id):
        async for msg in channel.history(limit=10):
            if msg.author == self.bot.user and msg.embeds:
                embed = discord.Embed(title=f"ð Schedule for {channel.name}", description="", color=discord.Color.blue())
                for hour in range(24):
                    hour_str = f"{hour:02d}:00"
                    users = day_schedule.get(hour_str, [])
                    if not users:
                        embed.add_field(name=hour_str, value="Available", inline=False)
                    else:
                        formatted = []
                        for uid in users:
                            note = day_schedule["notes"].get(str(uid), "")
                            formatted.append(f"<@{uid}>" + (f" ({note})" if note else ""))
                        embed.add_field(name=hour_str, value="\n".join(formatted), inline=False)
                await msg.edit(embed=embed)
                return

class ScheduleView(discord.ui.View):
    def __init__(self, guild, date_str):
        super().__init__(timeout=None)
        self.guild = guild
        self.date_str = date_str
        self.add_item(EditShiftButton())

class EditShiftButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="Edit My Shifts", style=discord.ButtonStyle.primary)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(ShiftModal(user=interaction.user, channel=interaction.channel))

class ShiftModal(discord.ui.Modal, title="Edit Your Shifts"):
    def __init__(self, user, channel):
        super().__init__()
        self.user = user
        self.channel = channel
        self.hours = discord.ui.TextInput(label="Hours (comma-separated, e.g. 14:00,15:00)", required=True)
        self.note = discord.ui.TextInput(label="Optional Note", style=discord.TextStyle.short, required=False)
        self.add_item(self.hours)
        self.add_item(self.note)

    async def on_submit(self, interaction: discord.Interaction):
        guild_id = str(interaction.guild.id)
        date_str = self.channel.name
        schedule = load_schedule()
        if guild_id not in schedule or date_str not in schedule[guild_id]:
            await interaction.response.send_message("â Schedule not found.", ephemeral=True)
            return

        selected = [h.strip() for h in self.hours.value.split(",") if h.strip()]
        for hour in schedule[guild_id][date_str]:
            if hour == "notes":
                continue
            if interaction.user.id in schedule[guild_id][date_str][hour]:
                schedule[guild_id][date_str][hour].remove(interaction.user.id)

        for hour in selected:
            if hour in schedule[guild_id][date_str]:
                schedule[guild_id][date_str][hour].append(interaction.user.id)

        if self.note.value:
            schedule[guild_id][date_str]["notes"][str(interaction.user.id)] = self.note.value
        elif str(interaction.user.id) in schedule[guild_id][date_str]["notes"]:
            del schedule[guild_id][date_str]["notes"][str(interaction.user.id)]

        save_schedule(schedule)
        cog = interaction.client.get_cog("BuffScheduler")
        await cog.update_message(self.channel, schedule[guild_id][date_str], guild_id)
        await interaction.response.send_message("â Shifts updated!", ephemeral=True)

async def setup(bot):
    await bot.add_cog(BuffScheduler(bot))