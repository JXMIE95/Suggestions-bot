import discord
from discord.ext import commands
import logging
from datetime import datetime
from bot.utils import create_approved_embed

logger = logging.getLogger(__name__)

def setup_handlers(bot):
    """Setup event handlers for the bot"""
    
    @bot.event
    async def on_reaction_add(reaction, user):
        """Handle reaction additions to suggestion messages"""
        # Ignore bot reactions
        if user.bot:
            return
        
        # Check if reaction is on a suggestion message
        if (reaction.message.channel.id == bot.config.SUGGESTION_CHANNEL_ID and 
            reaction.message.author == bot.user and 
            len(reaction.message.embeds) > 0):
            
            # Only allow thumbs up/down reactions
            if reaction.emoji not in ["👍", "👎"]:
                try:
                    await reaction.remove(user)
                except discord.NotFound:
                    pass
                return
            
            # Remove opposite reaction if user already voted
            opposite_emoji = "👎" if reaction.emoji == "👍" else "👍"
            for existing_reaction in reaction.message.reactions:
                if existing_reaction.emoji == opposite_emoji:
                    async for reaction_user in existing_reaction.users():
                        if reaction_user == user:
                            try:
                                await existing_reaction.remove(user)
                            except discord.NotFound:
                                pass
                            break
            
            logger.info(f"User {user} voted {reaction.emoji} on suggestion")
            
            # Check if suggestion reached 10 upvotes for auto-approval
            if reaction.emoji == "👍":
                await check_suggestion_approval(bot, reaction.message)
        
        # Handle poll voting
        elif hasattr(bot, 'active_polls') and reaction.message.id in bot.active_polls:
            await handle_poll_vote(bot, reaction, user)
    
    @bot.event
    async def on_reaction_remove(reaction, user):
        """Handle reaction removals"""
        # Log reaction removal for suggestions
        if (reaction.message.channel.id == bot.config.SUGGESTION_CHANNEL_ID and 
            reaction.message.author == bot.user and 
            not user.bot):
            logger.info(f"User {user} removed {reaction.emoji} vote on suggestion")
    
    @bot.event
    async def on_command_error(ctx, error):
        """Handle command errors"""
        if isinstance(error, commands.CommandNotFound):
            return
        
        logger.error(f"Command error: {error}")
        
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("❌ You don't have permission to use this command.")
        elif isinstance(error, commands.BotMissingPermissions):
            await ctx.send("❌ I don't have the required permissions to execute this command.")
        else:
            await ctx.send("❌ An error occurred while processing the command.")
    
    @bot.event
    async def on_guild_join(guild):
        """Handle bot joining a guild"""
        logger.info(f"Joined guild: {guild.name} (ID: {guild.id})")
        
        # Try to send a welcome message to the system channel
        if guild.system_channel:
            embed = discord.Embed(
                title="👋 Thanks for adding me!",
                description="I'm a suggestion bot that helps manage community suggestions and voting.",
                color=discord.Color.green()
            )
            
            embed.add_field(
                name="🚀 Getting Started",
                value="Use `/suggestion` to submit suggestions!\nMake sure to configure the suggestion and staff channels.",
                inline=False
            )
            
            embed.add_field(
                name="⚙️ Configuration",
                value="Set `SUGGESTION_CHANNEL_ID` and `STAFF_CHANNEL_ID` in your environment variables.",
                inline=False
            )
            
            try:
                await guild.system_channel.send(embed=embed)
            except discord.Forbidden:
                logger.warning(f"Could not send welcome message to {guild.name}")
    
    @bot.event
    async def on_guild_remove(guild):
        """Handle bot leaving a guild"""
        logger.info(f"Left guild: {guild.name} (ID: {guild.id})")
    
    @bot.event
    async def on_message(message):
        """Handle messages (for future features if needed)"""
        # Ignore bot messages
        if message.author.bot:
            return
        
        # Process commands
        await bot.process_commands(message)

async def check_suggestion_approval(bot, message):
    """Check if a suggestion has reached the approval threshold and post to approved channel"""
    try:
        # Get upvote count (subtract 1 for bot's initial reaction)
        upvotes = 0
        for reaction in message.reactions:
            if reaction.emoji == "👍":
                upvotes = reaction.count - 1
                break
        
        # Check if reached threshold and not already approved
        if upvotes >= 10:
            # Check if already approved (look for specific reaction or flag)
            already_approved = False
            for reaction in message.reactions:
                if reaction.emoji == "✅" and reaction.me:
                    already_approved = True
                    break
            
            if not already_approved:
                # Get approved channel and role
                approved_channel = bot.get_channel(bot.config.APPROVED_CHANNEL_ID)
                approved_role = None
                
                if bot.config.APPROVED_ROLE_ID:
                    approved_role = message.guild.get_role(bot.config.APPROVED_ROLE_ID)
                
                if approved_channel and message.embeds:
                    # Create approved embed
                    approved_embed = create_approved_embed(
                        message.embeds[0], 
                        upvotes, 
                        message
                    )
                    
                    # Create message content with role mention
                    content = ""
                    if approved_role:
                        content = f"{approved_role.mention} A suggestion has been approved by the community!"
                    
                    # Post to approved channel
                    await approved_channel.send(content=content, embed=approved_embed)
                    
                    # Add checkmark reaction to original message
                    await message.add_reaction("✅")
                    
                    logger.info(f"Suggestion approved and posted to approved channel: {upvotes} upvotes")
                    
                else:
                    logger.warning("Approved channel not configured or not found")
                    
    except Exception as e:
        logger.error(f"Error checking suggestion approval: {e}", exc_info=True)

async def handle_poll_vote(bot, reaction, user):
    """Handle poll voting with role restrictions"""
    try:
        poll_data = bot.active_polls[reaction.message.id]
        
        # Check if poll has expired
        if datetime.utcnow().timestamp() > poll_data['end_time']:
            await reaction.remove(user)
            return
        
        # Check role restrictions
        if poll_data['allowed_roles']:
            user_roles = [role.id for role in user.roles]
            if not any(role_id in user_roles for role_id in poll_data['allowed_roles']):
                await reaction.remove(user)
                try:
                    await user.send(f"❌ You don't have permission to vote in this poll. Only users with specific roles can vote.")
                except:
                    pass  # User has DMs disabled
                return
        
        # Check if reaction is a valid poll option
        poll_emojis = poll_data.get('emojis', ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣', '🔟'])
        if reaction.emoji not in poll_emojis[:len(poll_data['options'])]:
            await reaction.remove(user)
            return
        
        # Remove other votes from this user (single choice poll)
        for other_reaction in reaction.message.reactions:
            if other_reaction.emoji != reaction.emoji and other_reaction.emoji in poll_emojis:
                async for reaction_user in other_reaction.users():
                    if reaction_user == user:
                        try:
                            await other_reaction.remove(user)
                        except discord.NotFound:
                            pass
                        break
        
        logger.info(f"User {user} voted {reaction.emoji} in poll")
        
    except Exception as e:
        logger.error(f"Error handling poll vote: {e}", exc_info=True)
