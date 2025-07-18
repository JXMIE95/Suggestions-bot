import discord
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

def create_suggestion_embed(title: str, description: str, author: discord.User) -> discord.Embed:
    """Create an embed for a suggestion"""
    embed = discord.Embed(
        title=f"💡 {title}",
        description=description,
        color=discord.Color.blue(),
        timestamp=datetime.utcnow()
    )
    
    embed.set_author(
        name=f"Suggestion by {author.display_name}",
        icon_url=author.display_avatar.url
    )
    
    embed.add_field(
        name="📊 Voting",
        value="React with 👍 or 👎 to vote on this suggestion!",
        inline=False
    )
    
    embed.set_footer(text="Use /suggestion to submit your own ideas!")
    
    return embed

def create_approved_embed(original_embed: discord.Embed, vote_count: int, original_message: discord.Message) -> discord.Embed:
    """Create an embed for an approved suggestion"""
    # Extract title and description from original embed
    title = original_embed.title.replace("💡 ", "") if original_embed.title else "Approved Suggestion"
    description = original_embed.description or "No description provided"
    
    embed = discord.Embed(
        title=f"✅ {title}",
        description=description,
        color=discord.Color.green(),
        timestamp=datetime.utcnow()
    )
    
    # Copy author info from original embed
    if original_embed.author:
        embed.set_author(
            name=original_embed.author.name,
            icon_url=original_embed.author.icon_url
        )
    
    embed.add_field(
        name="📊 Community Approval",
        value=f"This suggestion received **{vote_count} positive votes** and has been approved by the community!",
        inline=False
    )
    
    embed.add_field(
        name="🔗 Original Suggestion",
        value=f"[Jump to original]({original_message.jump_url})",
        inline=True
    )
    
    embed.add_field(
        name="📅 Approved",
        value=f"<t:{int(datetime.utcnow().timestamp())}:R>",
        inline=True
    )
    
    embed.set_footer(text="🎉 This suggestion has been approved by the community!")
    
    return embed

def create_poll_embed(question: str, options: list, author: discord.User, allowed_roles: list = None, duration: int = 1, emojis: list = None) -> discord.Embed:
    """Create an embed for a poll"""
    embed = discord.Embed(
        title=f"📊 {question}",
        color=discord.Color.blue(),
        timestamp=datetime.utcnow()
    )
    
    embed.set_author(
        name=f"Poll by {author.display_name}",
        icon_url=author.display_avatar.url
    )
    
    # Add options with emojis
    if emojis is None:
        if len(options) == 2:
            emojis = ['✅', '❌']
        else:
            emojis = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣', '🔟'][:len(options)]
    
    options_text = ""
    for i, option in enumerate(options):
        if i < len(emojis):
            options_text += f"{emojis[i]} {option}\n"
    
    embed.add_field(
        name="Options",
        value=options_text,
        inline=False
    )
    
    # Add role restrictions if any
    if allowed_roles and len(allowed_roles) > 0:
        roles_text = ", ".join([role.mention for role in allowed_roles if role])
        embed.add_field(
            name="🔒 Who can vote",
            value=roles_text,
            inline=False
        )
    else:
        embed.add_field(
            name="🔓 Who can vote",
            value="Everyone",
            inline=False
        )
    
    # Add duration info
    end_time = datetime.utcnow().timestamp() + (duration * 3600)  # Convert hours to seconds
    embed.add_field(
        name="⏰ Duration",
        value=f"Ends <t:{int(end_time)}:R>",
        inline=True
    )
    
    embed.add_field(
        name="📋 How to vote",
        value="React with the number emoji of your choice",
        inline=True
    )
    
    embed.set_footer(text="Poll results will be shown when voting ends")
    
    return embed

def create_ticket_embed(title: str, description: str, author: discord.User, suggestion_message: discord.Message) -> discord.Embed:
    """Create an embed for a staff ticket"""
    embed = discord.Embed(
        title=f"🎫 New Suggestion Ticket",
        color=discord.Color.orange(),
        timestamp=datetime.utcnow()
    )
    
    embed.add_field(
        name="📝 Title",
        value=title,
        inline=False
    )
    
    embed.add_field(
        name="📄 Description",
        value=description[:1000] + ("..." if len(description) > 1000 else ""),
        inline=False
    )
    
    embed.add_field(
        name="👤 Submitted by",
        value=f"{author.mention} ({author.display_name})",
        inline=True
    )
    
    embed.add_field(
        name="🔗 Link",
        value=f"[Jump to suggestion]({suggestion_message.jump_url})",
        inline=True
    )
    
    embed.add_field(
        name="📊 Current Status",
        value="⏳ Pending review",
        inline=True
    )
    
    embed.set_thumbnail(url=author.display_avatar.url)
    embed.set_footer(text="Staff: Review this suggestion and take appropriate action")
    
    return embed

def get_vote_counts(message: discord.Message) -> dict:
    """Get vote counts from a message"""
    votes = {"upvotes": 0, "downvotes": 0}
    
    for reaction in message.reactions:
        if reaction.emoji == "👍":
            votes["upvotes"] = reaction.count - 1  # Subtract bot's reaction
        elif reaction.emoji == "👎":
            votes["downvotes"] = reaction.count - 1  # Subtract bot's reaction
    
    return votes

def format_vote_results(votes: dict) -> str:
    """Format vote results into a readable string"""
    upvotes = votes["upvotes"]
    downvotes = votes["downvotes"]
    total = upvotes + downvotes
    
    if total == 0:
        return "No votes yet"
    
    upvote_percentage = (upvotes / total) * 100
    downvote_percentage = (downvotes / total) * 100
    
    return f"👍 {upvotes} ({upvote_percentage:.1f}%) | 👎 {downvotes} ({downvote_percentage:.1f}%)"

def validate_suggestion_input(title: str, description: str) -> tuple[bool, str]:
    """Validate suggestion input and return (is_valid, error_message)"""
    if not title or not title.strip():
        return False, "Title cannot be empty"
    
    if not description or not description.strip():
        return False, "Description cannot be empty"
    
    if len(title) > 100:
        return False, "Title must be 100 characters or less"
    
    if len(description) > 1000:
        return False, "Description must be 1000 characters or less"
    
    # Check for inappropriate content (basic filter)
    prohibited_words = ["spam", "test123", "asdf"]  # Add more as needed
    content_lower = (title + " " + description).lower()
    
    for word in prohibited_words:
        if word in content_lower:
            return False, f"Content contains prohibited word: {word}"
    
    return True, ""

def create_status_embed(bot) -> discord.Embed:
    """Create a status embed for the bot"""
    embed = discord.Embed(
        title="🤖 Bot Status",
        color=discord.Color.green(),
        timestamp=datetime.utcnow()
    )
    
    embed.add_field(
        name="📊 Statistics",
        value=f"Servers: {len(bot.guilds)}\nLatency: {round(bot.latency * 1000)}ms",
        inline=True
    )
    
    embed.add_field(
        name="⚙️ Version",
        value="1.0.0",
        inline=True
    )
    
    embed.add_field(
        name="🔧 Commands",
        value="/suggestion, /help",
        inline=True
    )
    
    return embed
