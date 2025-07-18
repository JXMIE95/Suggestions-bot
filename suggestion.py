import discord
from discord import ui
from discord.ext import tasks
import asyncio

class SuggestionModal(ui.Modal, title="Submit a Suggestion"):
    title_input = ui.TextInput(label="Title", max_length=100)
    description_input = ui.TextInput(label="Description", style=discord.TextStyle.paragraph, max_length=1000)

    async def on_submit(self, interaction: discord.Interaction):
        embed = discord.Embed(title=self.title_input.value, description=self.description_input.value, color=discord.Color.blue())
        embed.set_author(name=interaction.user.display_name, icon_url=interaction.user.avatar.url if interaction.user.avatar else None)
        message = await interaction.channel.send(content="@everyone New suggestion!", embed=embed)
        await message.add_reaction("👍")

        await interaction.response.send_message("✅ Suggestion submitted!", ephemeral=True)

        # Monitor reactions
        await monitor_votes(message, interaction)

async def monitor_votes(message, interaction):
    await asyncio.sleep(10)  # Allow some time for votes
    while True:
        msg = await message.channel.fetch_message(message.id)
        thumbs_up = next((reaction.count for reaction in msg.reactions if str(reaction.emoji) == "👍"), 0)
        if thumbs_up >= 10:
            await post_to_staff_channel(interaction.client, msg)
            break
        await asyncio.sleep(30)

async def post_to_staff_channel(client, suggestion_msg):
    guild = suggestion_msg.guild
    staff_channel_id = int(os.getenv("STAFF_CHANNEL_ID"))
    staff_role_id = int(os.getenv("STAFF_ROLE_ID"))
    staff_channel = guild.get_channel(staff_channel_id)

    poll_msg = await staff_channel.send(
        content=f"<@&{staff_role_id}> Vote on the suggestion below (24h):",
        embed=suggestion_msg.embeds[0]
    )
    await poll_msg.add_reaction("✅")
    await poll_msg.add_reaction("❌")
    await asyncio.sleep(86400)  # 24 hours

    final_msg = await staff_channel.fetch_message(poll_msg.id)
    up_votes = next((r.count for r in final_msg.reactions if str(r.emoji) == "✅"), 0)
    down_votes = next((r.count for r in final_msg.reactions if str(r.emoji) == "❌"), 0)
    result = "Approved ✅" if up_votes > down_votes else "Rejected ❌"

    announcement_channel = guild.get_channel(int(os.getenv("ANNOUNCEMENT_CHANNEL_ID")))
    mention_role = int(os.getenv("ANNOUNCE_ROLE_ID"))
    await announcement_channel.send(
        content=f"<@&{mention_role}> Suggestion result: **{result}**",
        embed=final_msg.embeds[0]
    )

class SuggestionView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(ui.Button(label="Make a Suggestion", style=discord.ButtonStyle.primary, custom_id="make_suggestion"))

    @ui.button(label="Make a Suggestion", style=discord.ButtonStyle.primary, custom_id="make_suggestion")
    async def make_suggestion_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(SuggestionModal())
