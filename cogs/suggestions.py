import discord
from discord.ext import commands, tasks
from discord import app_commands
from discord.ui import Button, View, Modal, TextInput
import json
import asyncio
import os

with open("config.json") as f:
    config = json.load(f)

class Suggestions(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.active = {}  # message_id → posted channel & time
        self.check_loop.start()

    @app_commands.command(description="Setup the suggestion button")
    async def setup_suggestions(self, interaction: discord.Interaction):
        button = Button(label="Submit Suggestion", style=discord.ButtonStyle.primary)
        async def cb(i):
            await i.response.send_modal(SuggestionModal())
        button.callback = cb
        view = View()
        view.add_item(button)
        await interaction.response.send_message("Click to submit a suggestion:", view=view, ephemeral=True)

    @tasks.loop(seconds=30)
    async def check_loop(self):
        for mid, data in list(self.active.items()):
            ch = self.bot.get_channel(data["channel"])
            try:
                msg = await ch.fetch_message(mid)
            except discord.NotFound:
                self.active.pop(mid, None)
                continue
            up = next((r.count for r in msg.reactions if r.emoji == "👍"), 0)
            if up >= config["vote_threshold"]:
                self.active.pop(mid, None)
                await self.to_staff(msg)

    async def to_staff(self, msg):
        sch = self.bot.get_channel(config["staff_channel"])
        em = discord.Embed(title="Staff Poll", description=msg.embeds[0].description)
        poll = await sch.send(embed=em)
        await poll.add_reaction("✅")
        await poll.add_reaction("❌")
        await asyncio.sleep(config["vote_timer_minutes"] * 60)
        poll = await sch.fetch_message(poll.id)
        yes = next((r.count - 1 for r in poll.reactions if r.emoji == "✅"), 0)
        no = next((r.count - 1 for r in poll.reactions if r.emoji == "❌"), 0)
        result = "✅ Accepted" if yes > no else "❌ Rejected"
        ann = self.bot.get_channel(config["announcement_channel"])
        mention = f"<@&{config['notify_role']}>" if config["notify_role"] else ""
        em2 = discord.Embed(title="Suggestion Result", description=msg.embeds[0].description)
        em2.add_field(name="Outcome", value=result)
        await ann.send(content=mention, embed=em2)

    @commands.Cog.listener()
    async def on_message(self, msg):
        if msg.author.bot or not msg.embeds: return
        self.active[msg.id] = {"channel": msg.channel.id}

class SuggestionModal(Modal, title="Submit Suggestion"):
    suggestion = TextInput(label="Suggestion", style=discord.TextStyle.paragraph)
    async def on_submit(self, interaction: discord.Interaction):
        guild = interaction.guild
        ch = guild.get_channel(config["main_suggestion_channel"])
        mention = f"<@&{config['notify_role']}>" if config["notify_role"] else ""
        em = discord.Embed(description=self.suggestion.value, color=discord.Color.blue())
        msg = await ch.send(content=mention, embed=em)
        await msg.add_reaction("👍")
        await msg.add_reaction("👎")
        await interaction.response.send_message("✅ Suggestion submitted!", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Suggestions(bot))