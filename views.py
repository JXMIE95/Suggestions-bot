import discord
from config import channel_config

class SuggestionButtons(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="💡 Make a Suggestion", style=discord.ButtonStyle.green, custom_id="make_suggestion")
    async def make_suggestion(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(SuggestionModal())

class SuggestionModal(discord.ui.Modal, title="Submit Your Suggestion"):
    title = discord.ui.TextInput(label="Title", placeholder="Short title", max_length=100)
    description = discord.ui.TextInput(label="Description", placeholder="Explain your suggestion...", style=discord.TextStyle.paragraph)

    async def on_submit(self, interaction: discord.Interaction):
        main_channel_id = channel_config.get("main_chat_id")
        channel = interaction.client.get_channel(main_channel_id)

        if not channel:
            await interaction.response.send_message("⚠️ Suggestion channel not set or accessible. Run `/setchannels` first.", ephemeral=True)
            return

        embed = discord.Embed(
            title=self.title.value,
            description=self.description.value,
            color=discord.Color.green()
        )
        embed.set_footer(text=f"Suggested by {interaction.user}", icon_url=interaction.user.avatar.url)

        try:
            msg = await channel.send("@everyone", embed=embed)
            await msg.add_reaction("👍")
            await interaction.response.send_message("✅ Suggestion submitted!", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ Failed to post suggestion.\nError: {str(e)}", ephemeral=True)

class StaffReviewButtons(discord.ui.View):
    def __init__(self, embed):
        super().__init__(timeout=None)
        self.embed = embed

    @discord.ui.button(label="✅ Approve", style=discord.ButtonStyle.success)
    async def approve(self, interaction: discord.Interaction, button: discord.ui.Button):
        announcement_channel_id = channel_config.get("announcement_channel_id")
        announcement_channel = interaction.client.get_channel(announcement_channel_id)

        if not announcement_channel:
            await interaction.response.send_message("⚠️ Announcement channel not set or accessible.", ephemeral=True)
            return

        await announcement_channel.send("📢 Approved Suggestion:", embed=self.embed)
        await interaction.response.send_message("✅ Suggestion approved and announced.", ephemeral=True)
        await interaction.message.edit(view=None)
