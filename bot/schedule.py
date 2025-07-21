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
    return {"king_role_id": None, "buff_role_id": None, "category_id": None}

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

class CancelShiftView(discord.ui.View):
    def __init__(self, schedule_dict):
        super().__init__(timeout=60)
        self.schedule = schedule_dict

    @discord.ui.button(label="Cancel My Shifts", style=discord.ButtonStyle.danger)
    async def cancel_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        user = interaction.user
        removed = 0
        for slot in list(self.schedule.keys()):
            if user.id in self.schedule[slot]:
                self.schedule[slot].remove(user.id)
                removed += 1
        save_schedule(self.schedule)
        await interaction.response.send_message(f"â {removed} shift(s) cancelled.", ephemeral=True)

class ShiftView(discord.ui.View):
    def __init__(self, shift_date: datetime, schedule_dict):
        super().__init__(timeout=None)
        self.add_item(TimeRangeSelect(shift_date, schedule_dict))
        self.add_item(discord.ui.Button(label="Cancel My Shifts", style=discord.ButtonStyle.danger, custom_id="cancel_button"))

class BuffScheduler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = load_config()
        self.schedule = load_schedule()
        self.reminder_loop.start()

    def cog_unload(self):
        self.reminder_loop.cancel()

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
                    description="Select your available shifts below (UTC time). Use the button to cancel if needed.",
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
