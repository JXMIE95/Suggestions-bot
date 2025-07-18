import discord
from config import channel_config, LIKE_THRESHOLD, posted_messages
from views import StaffReviewButtons

async def setup_handlers(bot):
    @bot.event
    async def on_raw_reaction_add(payload: discord.RawReactionActionEvent):
        if str(payload.emoji.name) != "👍":
            return

        channel = bot.get_channel(payload.channel_id)
        if not channel:
            return

        try:
            message = await channel.fetch_message(payload.message_id)
        except Exception:
            return

        if message.id in posted_messages:
            return

        for reaction in message.reactions:
            if str(reaction.emoji) == "👍" and reaction.count >= LIKE_THRESHOLD:
                staff_channel_id = channel_config.get("staff_channel_id")
                staff_channel = bot.get_channel(staff_channel_id)
                if staff_channel:
                    embed = message.embeds[0] if message.embeds else None
                    await staff_channel.send("📝 Staff Review", embed=embed, view=StaffReviewButtons(embed))
                    posted_messages.add(message.id)
                break
