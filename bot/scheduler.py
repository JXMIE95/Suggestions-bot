import discord
from discord.ext import commands, tasks
from discord import app_commands
import json
from datetime import datetime, timedelta

class BuffScheduler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.schedule_loop.start()

    def cog_unload(self):
        self.schedule_loop.cancel()

    @app_commands.command(name="schedule_configure", description="Configure scheduler settings.")
    @app_commands.describe(
        king_role="King role to notify",
        buff_giver_role="Buff Giver role to assign",
        category="Category where schedules will be created",
        shift_role="Role assigned to users during their shift"
    )
    async def schedule_configure(self, interaction: discord.Interaction,
        king_role: discord.Role,
        buff_giver_role: discord.Role,
        category: discord.CategoryChannel,
        shift_role: discord.Role
    ):
        await interaction.response.defer(thinking=True)
        config = {
            "king_role_id": king_role.id,
            "buff_role_id": buff_giver_role.id,
            "category_id": category.id,
            "shift_role_id": shift_role.id
        }
        with open("buff_config.json", "w") as f:
            json.dump(config, f)
        await interaction.followup.send("â Scheduler configuration updated.")

    @tasks.loop(hours=168)  # Once per week
    async def schedule_loop(self):
        await self.bot.wait_until_ready()
        for guild in self.bot.guilds:
            cog = self.bot.get_cog("BuffScheduler")
            if cog:
                await cog.generate_week_schedule(guild)

    async def generate_week_schedule(self, guild: discord.Guild):
        with open("buff_config.json", "r") as f:
            config = json.load(f)

        category = guild.get_channel(config["category_id"])
        if not category:
            return

        # Clear old channels
        for ch in category.channels:
            await ch.delete()

        now = datetime.utcnow()
        for day in range(7):
            date = now + timedelta(days=day)
            date_str = date.strftime("%Y-%m-%d")
            channel = await guild.create_text_channel(date_str, category=category)

            embed = discord.Embed(title=f"Buff Giver Roster for {date_str}", description="", color=discord.Color.blue())
            for hour in range(24):
                hour_str = f"{hour:02d}:00 - {hour+1:02d}:00"
                embed.add_field(name=hour_str, value="Open", inline=False)

            await channel.send(embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(BuffScheduler(bot))