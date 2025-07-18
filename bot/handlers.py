from discord import RawReactionActionEvent

SUGGESTION_CHANNEL_ID = 123456789012345678  # replace this
STAFF_CHANNEL_ID = 987654321098765432      # replace this
LIKE_THRESHOLD = 2
LIKE_EMOJI = "👍"
posted_messages = set()

def setup_handlers(bot):
    @bot.event
    async def on_raw_reaction_add(payload: RawReactionActionEvent):
        if payload.channel_id != SUGGESTION_CHANNEL_ID:
            return
        if str(payload.emoji.name) != LIKE_EMOJI:
            return

        channel = bot.get_channel(payload.channel_id)
        if not channel:
            return

        message = await channel.fetch_message(payload.message_id)
        if not message or message.id in posted_messages:
            return

        for reaction in message.reactions:
            if str(reaction.emoji) == LIKE_EMOJI:
                if reaction.count >= LIKE_THRESHOLD:
                    staff_channel = bot.get_channel(STAFF_CHANNEL_ID)
                    if staff_channel:
                        await staff_channel.send(
                            f"🔔 Suggestion reached {LIKE_THRESHOLD} likes: {message.jump_url}"
                        )
                        posted_messages.add(message.id)
                break