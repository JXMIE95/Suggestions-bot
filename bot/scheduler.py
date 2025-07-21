import discord
from discord.ext import commands, tasks
from discord import app_commands
from datetime import datetime, timedelta
import json
import os

CONFIG_FILE = "buff_config.json"
DATA_FILE = "buff_schedule.json"

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    return {
        "king_role_id": None,
        "buff_role_id": None,
        "category_id": None,
        "shift_role_id": None
    }

def save_config(config):
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=4)

def load_schedule():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {}

def save_schedule(schedule):
    with open(DATA_FILE, "w") as f:
        json.dump(schedule, f, indent=4)

class TimeRangeSelect(discord.ui.Select):
    def __init__(self, shift_date: datetime, schedule_dict):
        self.schedule = schedule_dict
        self.shift_date = shift_date
        options = []
        for hour in range(0, 24):
            label = f"{hour:02d}:00 - {(hour+1)%24:02d}:00"
            options.append(discord.SelectOption(label=label, value=str(hour)))
        super().__init__(placeholder="Select your available shift(s)", min_values=1, max_values=6, options=options)

    async def callback(self, interaction: discord.Interaction):
        user = interaction.user
        selected_hours = self.values
        for hour_str in selected_hours:
            hour = int(hour_str)
            shift_time = self.shift_date.replace(hour=hour, minute=0, second=0, microsecond=0)
            shift_key = shift_time.strftime("%Y-%m-%d %H:00")
            if shift_key not in self.schedule:
                self.schedule[shift_key] = []
            if user.id not in self.schedule[shift_key]:
                self.schedule[shift_key].append(user.id)
        save_schedule(self.schedule)
        await interaction.response.send_message(f"â {user.mention}, you signed up for {len(selected_hours)} shift(s)!", ephemeral=True)
        await self.view.cog.log_action(interaction.guild, f"â {user.name} signed up for {len(selected_hours)} shift(s) on {self.shift_date.date()}")

class CancelHourSelect(discord.ui.Select):
    def __init__(self, shift_date: datetime, schedule_dict, user_id):
        self.shift_date = shift_date
        self.schedule = schedule_dict
        self.user_id = user_id

        user_shifts = []
        for hour in range(24):
            shift_time = shift_date.replace(hour=hour, minute=0, second=0, microsecond=0)
            shift_key = shift_time.strftime("%Y-%m-%d %H:00")
            if shift_key in schedule_dict and user_id in schedule_dict[shift_key]:
                user_shifts.append((shift_key, hour))

        options = [
            discord.SelectOption(label=f"{hour:02d}:00 - {(hour+1)%24:02d}:00", value=str(hour))
            for shift_key, hour in user_shifts
        ]

        super().__init__(
            placeholder="Select shifts to cancel",
            min_values=1,
            max_values=len(options),
            options=options,
            custom_id="cancel_hour_select"
        )

    async def callback(self, interaction: discord.Interaction):
        removed = 0
        for hour_str in self.values:
            hour = int(hour_str)
            shift_time = self.shift_date.replace(hour=hour, minute=0, second=0, microsecond=0)
            shift_key = shift_time.strftime("%Y-%m-%d %H:00")
            if shift_key in self.schedule and self.user_id in self.schedule[shift_key]:
                self.schedule[shift_key].remove(self.user_id)
                removed += 1

        save_schedule(self.schedule)
        await interaction.response.send_message(f"ð Cancelled {removed} shift(s) for {self.shift_date.date()}", ephemeral=True)
        await self.view.cog.log_action(interaction.guild, f"ð {interaction.user.name} cancelled {removed} shift(s) for {self.shift_date.date()}")

class CancelShiftView(discord.ui.View):
    def __init__(self, shift_date, schedule_dict, user_id, cog):
        super().__init__(timeout=60)
        self.cog = cog
        self.add_item(CancelHourSelect(shift_date, schedule_dict, user_id))

class CancelShiftButton(discord.ui.Button):
    def __init__(self, shift_date, schedule_dict, cog):
        super().__init__(label="â Cancel My Shift(s)", style=discord.ButtonStyle.danger)
        self.shift_date = shift_date
        self.schedule = schedule_dict
        self.cog = cog

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_message(
            f"Select which shifts to cancel for {self.shift_date.date()}:",
            view=CancelShiftView(self.shift_date, self.schedule, interaction.user.id, self.cog),
            ephemeral=True
        )

class ShiftView(discord.ui.View):
    def __init__(self, shift_date: datetime, schedule_dict, cog):
        super().__init__(timeout=None)
        self.cog = cog
        self.add_item(TimeRangeSelect(shift_date, schedule_dict))
        self.add_item(CancelShiftButton(shift_date, schedule_dict, cog))

class BuffScheduler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = load_config()
        self.schedule = load_schedule()
        self.reminder_loop.start()
        self.shift_role_assignment_loop.start()

    async def log_action(self, guild: discord.Guild, message: str):
        log_channel = discord.utils.get(guild.text_channels, name="buff-log")
        if log_channel:
            await log_channel.send(message)

    def cog_unload(self):
        self.reminder_loop.cancel()
        self.shift_role_assignment_loop.cancel()

    @tasks.loop(seconds=60)
    async def reminder_loop(self):
        now = datetime.utcnow().replace(second=0, microsecond=0)
        reminder_time = now + timedelta(minutes=5)
        shift_key = reminder_time.strftime("%Y-%m-%d %H:00")
        if shift_key in self.schedule:
            for guild in self.bot.guilds:
                king_role = guild.get_role(self.config.get("king_role_id"))
                buff_role = guild.get_role(self.config.get("buff_role_id"))
                target_channel = discord.utils.get(guild.text_channels, name="buff-reminders")
                for user_id in self.schedule[shift_key]:
                    member = guild.get_member(user_id)
                    if member:
                        try:
                            await member.send(f"â° Reminder: Your buff giver shift starts in 5 minutes at {shift_key} UTC.")
                        except discord.Forbidden:
                            print(f"â Could not DM user {user_id}")
                if target_channel and (king_role or buff_role):
                    mentions = " ".join(role.mention for role in [king_role, buff_role] if role)
                    await target_channel.send(f"{mentions} â â° Buff shift starts in 5 minutes at {shift_key} UTC.")

    @tasks.loop(seconds=60)
    async def shift_role_assignment_loop(self):
        now = datetime.utcnow().replace(second=0, microsecond=0)
        shift_key = now.strftime("%Y-%m-%d %H:00")
        role_id = self.config.get("shift_role_id")

        if role_id and shift_key in self.schedule:
            for guild in self.bot.guilds:
                role = guild.get_role(role_id)
                if not role:
                    continue
                for user_id in self.schedule[shift_key]:
                    member = guild.get_member(user_id)
                    if member and role not in member.roles:
                        try:
                            await member.add_roles(role, reason="Shift started")
                        except Exception as e:
                            print(f"â Failed to assign role to {user_id}: {e}")

        past_key = (now - timedelta(hours=1)).strftime("%Y-%m-%d %H:00")
        if role_id and past_key in self.schedule:
            for guild in self.bot.guilds:
                role = guild.get_role(role_id)
                if not role:
                    continue
                for user_id in self.schedule[past_key]:
                    member = guild.get_member(user_id)
                    if member and role in member.roles:
                        try:
                            await member.remove_roles(role, reason="Shift ended")
                        except Exception as e:
                            print(f"â Failed to remove role from {user_id}: {e}")

    @app_commands.command(name="set_schedule_category", description="Set the schedule category ID")
    async def set_schedule_category(self, interaction: discord.Interaction, category_id: str):
        self.config["category_id"] = int(category_id)
        save_config(self.config)
        await interaction.response.send_message(f"ð Schedule category set to ID {category_id}", ephemeral=True)

    @app_commands.command(name="set_shift_role", description="Set the role to auto-assign and remove for shifts")
    async def set_shift_role(self, interaction: discord.Interaction, role: discord.Role):
        self.config["shift_role_id"] = role.id
        save_config(self.config)
        await interaction.response.send_message(f"â Shift role set to {role.mention}", ephemeral=True)

    @app_commands.command(name="generate_week_schedule", description="Auto-create schedule for the next 7 days")
    async def generate_week_schedule(self, interaction: discord.Interaction):
        category_id = self.config.get("category_id")
        if not category_id:
            await interaction.response.send_message("â ï¸ Please set the category first with `/set_schedule_category`", ephemeral=True)
            return

        category = discord.utils.get(interaction.guild.categories, id=category_id)
        if not category:
            await interaction.response.send_message("â Invalid category ID.", ephemeral=True)
            return

        # Delete existing channels
        for channel in category.channels:
            try:
                await channel.delete(reason="Resetting weekly buff schedule")
            except Exception as e:
                print(f"Failed to delete channel: {e}")

        today = datetime.utcnow().date()
        for i in range(7):
            date = today + timedelta(days=i)
            channel_name = date.strftime("buffs-%A").lower()
            channel = await interaction.guild.create_text_channel(channel_name, category=category)
            embed = discord.Embed(
                title=f"ð Buff Giver Shifts â {date}",
                description="Select your available shifts below (UTC time).",
                color=discord.Color.blue()
            )
            await channel.send(embed=embed, view=ShiftView(datetime.combine(date, datetime.min.time()), self.schedule, self))

        await interaction.response.send_message("â Weekly schedule created.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(BuffScheduler(bot))