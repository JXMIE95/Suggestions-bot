import discord

class SuggestionButtons(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="💡 Make a Suggestion", style=discord.ButtonStyle.green, custom_id="make_suggestion")
    async def make_suggestion(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(SuggestionModal())

    @discord.ui.button(label="📂 View My Suggestions", style=discord.ButtonStyle.blurple, custom_id="view_suggestions")
    async def view_suggestions(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("🛠 Feature coming soon!", ephemeral=True)

class SuggestionModal(discord.ui.Modal, title="Submit Your Suggestion"):
    suggestion = discord.ui.TextInput(label="Your Suggestion", style=discord.TextStyle.paragraph, required=True)

    async def on_submit(self, interaction: discord.Interaction):
        from config import channel_config
        target_id = channel_config.get("main_chat_id")
        channel = interaction.client.get_channel(target_id)

        embed = discord.Embed(
            title="New Suggestion",
            description=self.suggestion.value,
            color=discord.Color.green()
        )
        embed.set_footer(text=f"Suggested by {interaction.user}", icon_url=interaction.user.avatar.url)

        if channel:
            msg = await channel.send("@everyone", embed=embed)
            await msg.add_reaction("👍")
            await interaction.response.send_message("✅ Suggestion submitted!", ephemeral=True)
        else:
            await interaction.response.send_message("⚠️ No main suggestion channel set yet.", ephemeral=True)
