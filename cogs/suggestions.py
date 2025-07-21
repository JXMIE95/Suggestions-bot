import discord
from discord.ext import commands, tasks
from discord.ui import Button, View, Modal, TextInput
import json
import asyncio

with open("config.json") as f:
    config = json.load(f)

class Suggestions(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.active_suggestions = {}  # message_id -> upvote count
        self.vote_check_loop.start()

    @commands.command()
    async def setup_suggestions(self, ctx):
        """Send a button to start the suggestion modal."""
        button = Button(label="Submit Suggestion", style=discord.ButtonStyle.primary)

        async def button_callback(interaction):
            await interaction.response.send_modal(SuggestionModal())

        button.callback = button_callback
        view = View()
        view.add_item(button)
        await ctx.send("Click the button to submit a suggestion:", view=view)

    @tasks.loop(seconds=30)
    async def vote_check_loop(self):
        for message_id, data in list(self.active_suggestions.items()):
            channel = self.bot.get_channel(data['channel_id'])
            try:
                msg = await channel.fetch_message(message_id)
            except discord.NotFound:
                continue

            upvotes = discord.utils.get(msg.reactions, emoji="👍")
            count = upvotes.count if upvotes else 0

            if count >= config["vote_threshold"]:
                del self.active_suggestions[message_id]
                await self.send_to_staff(msg)

    async def send_to_staff(self, msg):
        staff_channel = self.bot.get_channel(config["staff_channel"])
        embed = discord.Embed(title="Staff Poll", description=msg.embeds[0].description)
        poll_msg = await staff_channel.send(embed=embed)
        await poll_msg.add_reaction("✅")
        await poll_msg.add_reaction("❌")

        await asyncio.sleep(config["vote_timer_minutes"] * 60)

        poll_msg = await staff_channel.fetch_message(poll_msg.id)
        yes = discord.utils.get(poll_msg.reactions, emoji="✅")
        no = discord.utils.get(poll_msg.reactions, emoji="❌")

        yes_count = yes.count - 1 if yes else 0
        no_count = no.count - 1 if no else 0

        result = "✅ Accepted!" if yes_count > no_count else "❌ Rejected."
        result_embed = discord.Embed(title="Suggestion Result", description=msg.embeds[0].description)
        result_embed.add_field(name="Outcome", value=result)

        announce_channel = self.bot.get_channel(config["announcement_channel"])
        role_mention = f"<@&{config['notify_role']}>" if config["notify_role"] else ""
        await announce_channel.send(role_mention, embed=result_embed)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author != self.bot.user and message.embeds:
            self.active_suggestions[message.id] = {
                'channel_id': message.channel.id
            }

class SuggestionModal(Modal, title="Submit a Suggestion"):
    suggestion = TextInput(label="Suggestion", style=discord.TextStyle.paragraph)

    async def on_submit(self, interaction: discord.Interaction):
        embed = discord.Embed(description=self.suggestion.value, color=discord.Color.blue())
        suggestion_channel = interaction.guild.get_channel(config["main_suggestion_channel"])
        role_mention = f"<@&{config['notify_role']}>" if config["notify_role"] else ""
        msg = await suggestion_channel.send(role_mention, embed=embed)
        await msg.add_reaction("👍")
        await msg.add_reaction("👎")
        await interaction.response.send_message("✅ Suggestion submitted!", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Suggestions(bot))
