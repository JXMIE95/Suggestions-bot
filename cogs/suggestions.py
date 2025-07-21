import discord
from discord.ext import commands, tasks
import json
import asyncio

with open("config.json") as f:
    config = json.load(f)

class SuggestionModal(discord.ui.Modal, title="Submit a Suggestion"):
    suggestion = discord.ui.TextInput(label="Your Suggestion", style=discord.TextStyle.paragraph)

    async def on_submit(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="New Suggestion",
            description=self.suggestion.value,
            color=discord.Color.blue()
        )
        embed.set_footer(text=f"Suggested by {interaction.user.display_name}")
        msg = await interaction.client.get_channel(config["main_channel_id"]).send(embed=embed)
        await msg.add_reaction("👍")
        await msg.add_reaction("👎")
        await interaction.response.send_message("✅ Suggestion submitted!", ephemeral=True)

class Suggestions(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.checked_messages = set()
        self.check_votes.start()

    @commands.command(name="suggestbutton")
    async def suggest_button(self, ctx):
        view = discord.ui.View()
        view.add_item(discord.ui.Button(label="Submit Suggestion", style=discord.ButtonStyle.green, custom_id="submit_suggestion"))
        await ctx.send("Click the button below to submit a suggestion:", view=view)

    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction):
        if interaction.type == discord.InteractionType.component:
            if interaction.data["custom_id"] == "submit_suggestion":
                await interaction.response.send_modal(SuggestionModal())

    @tasks.loop(seconds=30)
    async def check_votes(self):
        channel = self.bot.get_channel(config["main_channel_id"])
        async for message in channel.history(limit=100):
            if not message.embeds:
                continue
            if message.id in self.checked_messages:
                continue
            upvotes = 0
            for reaction in message.reactions:
                if str(reaction.emoji) == "👍":
                    upvotes = reaction.count - 1  # Subtract bot's own reaction
            if upvotes >= config["suggestion_threshold"]:
                embed = message.embeds[0]
                staff_channel = self.bot.get_channel(config["staff_channel_id"])
                staff_msg = await staff_channel.send(
                    content=f"<@&{config['staff_role_id']}> A suggestion reached the threshold!",
                    embed=embed
                )
                await staff_msg.add_reaction("✅")
                await staff_msg.add_reaction("❌")
                self.checked_messages.add(message.id)

    # Optional: Implement finalize_votes logic for timing staff decision & announcement

async def setup(bot):
    await bot.add_cog(Suggestions(bot))