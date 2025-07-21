import discord
from discord.ext import commands, tasks
from discord import app_commands
from datetime import datetime, timedelta
import json
import os
import asyncio

CONFIG_FILE = "buff_config.json"
DATA_FILE = "buff_schedule.json"

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    return {"king_role_id": None, "buff_role_id": None, "category_id": None, "shift_role_id": None}

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
        options = []
        self.schedule = schedule_dict
        self.shift_date = shift_date
        for hour in range(0, 24):
            start = f"{hour:02d}:00"
            end = f"{(hour+1)%24:02d}:00"
            label = f"{start} - {end}"
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

class ShiftView(discord.ui.View):
    def __init__(self, shift_date: datetime, schedule_dict):
        super().__init__(timeout=None)
        self.add_item(TimeRangeSelect(shift_date, schedule_dict))

class BuffScheduler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = load_config()
        self.schedule = load_schedule()
        self.reminder_loop.start()
        self.shift_role_assignment_loop.start()

    def cog_unload(self):
        self.reminder_loop.cancel()
        self.shift_role_assignment_loop.cancel()

    
    @tasks.loop(seconds=60)
    async def shift_role_assignment_loop(self):
        now = datetime.utcnow().replace(second=0, microsecond=0)
        shift_key = now.strftime("%Y-%m-%d %H:00")
        if shift_key in self.schedule:
            for guild in self.bot.guilds:
                shift_role_id = self.config.get("shift_role_id")
                shift_role = guild.get_role(shift_role_id) if shift_role_id else None
                if not shift_role:
                    continue
                for user_id in self.schedule[shift_key]:
                    member = guild.get_member(user_id)
                    if member and shift_role not in member.roles:
                        try:
                            await member.add_roles(shift_role, reason="Buff shift started")
                        except Exception as e:
                            print(f"â Couldn't assign role to {user_id}: {e}")
        # Remove expired roles
        past_key = (now - timedelta(hours=1)).strftime("%Y-%m-%d %H:00")
        if past_key in self.schedule:
            for guild in self.bot.guilds:
                shift_role_id = self.config.get("shift_role_id")
                shift_role = guild.get_role(shift_role_id) if shift_role_id else None
                if not shift_role:
                    continue
                for user_id in self.schedule[past_key]:
                    member = guild.get_member(user_id)
                    if member and shift_role in member.roles:
                        try:
                            await member.remove_roles(shift_role, reason="Buff shift ended")
                        except Exception as e:
                            print(f"â Couldn't remove role from {user_id}: {e}")


    @tasks.loop(seconds=60)
    async def reminder_loop(self):
        now = datetime.utcnow().replace(second=0, microsecond=0)
        reminder_time = now + timedelta(minutes=5)
        shift_key = reminder_time.strftime("%Y-%m-%d %H:00")
        if shift_key in self.schedule:
            for guild in self.bot.guilds:
                for user_id in self.schedule[shift_key]:
                    member = guild.get_member(user_id)
                    if member:
                        try:
                            await member.send(f"â° Reminder: You are scheduled as a Buff Giver in 5 minutes at {shift_key} (UTC).")
        for guild in self.bot.guilds:
            king_role_id = self.config.get("king_role_id")
            shift_role_id = self.config.get("shift_role_id")
            king_role = guild.get_role(king_role_id) if king_role_id else None
            shift_role = guild.get_role(shift_role_id) if shift_role_id else None
            target_channel = discord.utils.get(guild.text_channels, name="buff-reminders")
            if target_channel and (king_role or buff_role):
                mentions = " ".join(role.mention for role in [king_role, buff_role] if role)
                await target_channel.send(f"{mentions} â â° Upcoming buff shift in 5 minutes at {shift_key} UTC")
                        except discord.Forbidden:
                            print(f"â Cannot DM user {user_id}")

    
    @app_commands.command(name="set_shift_role", description="Set the role to auto-assign and remove for shifts")
    async def set_shift_role(self, interaction: discord.Interaction, role: discord.Role):
        self.config["shift_role_id"] = role.id
        save_config(self.config)
        await interaction.response.send_message(f"â Shift role set to {role.mention}", ephemeral=True)


    @app_commands.command(name="generate_week_schedule", description="Auto-create schedule for the next 7 days")
    async def generate_week_schedule(self, interaction: discord.Interaction):
        category_id = self.config.get("category_id")
        if not category_id:
            await interaction.response.send_message("â ï¸ Category not set. Use `/set_schedule_category` first.", ephemeral=True)
            return

        category = discord.utils.get(interaction.guild.categories, id=category_id)
        if not category:
            await interaction.response.send_message("â Invalid category ID.", ephemeral=True)
            return

        today = datetime.utcnow().date()
        for i in range(7):
            day = today + timedelta(days=i)
            channel_name = day.strftime("buffs-%A").lower()
            existing = discord.utils.get(category.channels, name=channel_name)
            if not existing:
                new_channel = await interaction.guild.create_text_channel(channel_name, category=category)
                view = ShiftView(datetime.combine(day, datetime.min.time()), self.schedule)
                embed = discord.Embed(
                    title=f"ð Buff Giver Shifts â {day}",
                    description="Select your available shifts below (UTC time).",
                    color=discord.Color.green()
                )
                await new_channel.send(embed=embed, view=view)

        await interaction.response.send_message("â Weekly schedule generated.", ephemeral=True)

    @app_commands.command(name="set_schedule_category", description="Set the schedule category ID")
    async def set_schedule_category(self, interaction: discord.Interaction, category_id: str):
        self.config["category_id"] = int(category_id)
        save_config(self.config)
        await interaction.response.send_message(f"ð Schedule category set to ID {category_id}", ephemeral=True)

async def setup(bot):
    await bot.add_cog(BuffScheduler(bot))
