import discord
from discord.ext import commands
from discord import app_commands
import logging
from datetime import datetime
from bot.utils import create_suggestion_embed, create_ticket_embed, create_poll_embed

logger = logging.getLogger(__name__)

async def setup_commands(bot):
    """Setup slash commands for the bot"""
    
    @bot.tree.command(name="suggestion", description="Submit a suggestion for the server")
    @app_commands.describe(
        title="Title of your suggestion",
        description="Detailed description of your suggestion"
    )
    async def suggestion(interaction: discord.Interaction, title: str, description: str):
        """Handle suggestion submission"""
        logger.info(f"Suggestion command invoked by {interaction.user} with title: {title}")
        try:
            # Validate input
            if len(title) > 100:
                await interaction.response.send_message(
                    "❌ Title must be 100 characters or less.", 
                    ephemeral=True
                )
                return
            
            if len(description) > 1000:
                await interaction.response.send_message(
                    "❌ Description must be 1000 characters or less.", 
                    ephemeral=True
                )
                return
            
            # Get suggestion channel
            suggestion_channel = bot.get_channel(bot.config.SUGGESTION_CHANNEL_ID)
            if not suggestion_channel:
                await interaction.response.send_message(
                    "❌ Suggestion channel not found. Please contact an administrator.", 
                    ephemeral=True
                )
                return
            
            # Create suggestion embed
            suggestion_embed = create_suggestion_embed(
                title=title,
                description=description,
                author=interaction.user
            )
            
            # Post suggestion to channel
            suggestion_message = await suggestion_channel.send(embed=suggestion_embed)
            
            # Add voting reactions
            await suggestion_message.add_reaction("👍")
            await suggestion_message.add_reaction("👎")
            
            # Create ticket in staff channel
            staff_channel = bot.get_channel(bot.config.STAFF_CHANNEL_ID)
            if staff_channel:
                ticket_embed = create_ticket_embed(
                    title=title,
                    description=description,
                    author=interaction.user,
                    suggestion_message=suggestion_message
                )
                await staff_channel.send(embed=ticket_embed)
            
            # Respond to user
            await interaction.response.send_message(
                f"✅ Your suggestion has been submitted! Check {suggestion_channel.mention} to see it.",
                ephemeral=True
            )
            
            logger.info(f"Suggestion submitted by {interaction.user} (ID: {interaction.user.id})")
            
        except discord.Forbidden:
            await interaction.response.send_message(
                "❌ I don't have permission to post in the suggestion channel.", 
                ephemeral=True
            )
            logger.error("Missing permissions to post in suggestion channel")
            
        except Exception as e:
            logger.error(f"Error processing suggestion: {e}", exc_info=True)
            try:
                await interaction.response.send_message(
                    "❌ An error occurred while processing your suggestion. Please try again later.", 
                    ephemeral=True
                )
            except:
                logger.error("Failed to send error response to user")
    
    @bot.tree.command(name="help", description="Show help information about the bot")
    async def help_command(interaction: discord.Interaction):
        """Display help information"""
        embed = discord.Embed(
            title="🤖 Suggestion Bot Help",
            description="Here's how to use the suggestion bot:",
            color=discord.Color.blue()
        )
        
        embed.add_field(
            name="📝 /suggestion",
            value="Submit a new suggestion with a title and description",
            inline=False
        )
        
        embed.add_field(
            name="🗳️ Voting",
            value="React with 👍 or 👎 on suggestions to vote",
            inline=False
        )
        
        embed.add_field(
            name="📋 Process",
            value="1. Submit suggestion\n2. Community votes\n3. Staff reviews ticket",
            inline=False
        )
        
        embed.set_footer(text="Need help? Contact a staff member")
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @bot.tree.command(name="config", description="Configure bot settings (Admin only)")
    @app_commands.describe(
        setting="The setting to configure",
        value="The new value for the setting"
    )
    @app_commands.choices(setting=[
        app_commands.Choice(name="Suggestion Channel", value="suggestion_channel"),
        app_commands.Choice(name="Staff Channel", value="staff_channel"),
        app_commands.Choice(name="Approved Channel", value="approved_channel"),
        app_commands.Choice(name="Approved Role", value="approved_role")
    ])
    async def config_command(interaction: discord.Interaction, setting: str, value: str):
        """Configure bot settings"""
        # Check if user has administrator permissions
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message(
                "❌ You need administrator permissions to use this command.",
                ephemeral=True
            )
            return
        
        try:
            if setting == "suggestion_channel":
                # Extract channel ID from mention or use direct ID
                channel_id = value.strip("<>#")
                try:
                    channel_id = int(channel_id)
                except ValueError:
                    await interaction.response.send_message(
                        "❌ Invalid channel ID. Please provide a valid channel ID or mention.",
                        ephemeral=True
                    )
                    return
                
                # Verify channel exists
                channel = bot.get_channel(channel_id)
                if not channel:
                    await interaction.response.send_message(
                        "❌ Channel not found. Make sure the bot has access to this channel.",
                        ephemeral=True
                    )
                    return
                
                # Update config
                bot.config.SUGGESTION_CHANNEL_ID = channel_id
                await interaction.response.send_message(
                    f"✅ Suggestion channel updated to {channel.mention}",
                    ephemeral=True
                )
                logger.info(f"Suggestion channel updated to {channel_id} by {interaction.user}")
                
            elif setting == "staff_channel":
                # Extract channel ID from mention or use direct ID
                channel_id = value.strip("<>#")
                try:
                    channel_id = int(channel_id)
                except ValueError:
                    await interaction.response.send_message(
                        "❌ Invalid channel ID. Please provide a valid channel ID or mention.",
                        ephemeral=True
                    )
                    return
                
                # Verify channel exists
                channel = bot.get_channel(channel_id)
                if not channel:
                    await interaction.response.send_message(
                        "❌ Channel not found. Make sure the bot has access to this channel.",
                        ephemeral=True
                    )
                    return
                
                # Update config
                bot.config.STAFF_CHANNEL_ID = channel_id
                await interaction.response.send_message(
                    f"✅ Staff channel updated to {channel.mention}",
                    ephemeral=True
                )
                logger.info(f"Staff channel updated to {channel_id} by {interaction.user}")
                
            elif setting == "approved_channel":
                # Extract channel ID from mention or use direct ID
                channel_id = value.strip("<>#")
                try:
                    channel_id = int(channel_id)
                except ValueError:
                    await interaction.response.send_message(
                        "❌ Invalid channel ID. Please provide a valid channel ID or mention.",
                        ephemeral=True
                    )
                    return
                
                # Verify channel exists
                channel = bot.get_channel(channel_id)
                if not channel:
                    await interaction.response.send_message(
                        "❌ Channel not found. Make sure the bot has access to this channel.",
                        ephemeral=True
                    )
                    return
                
                # Update config
                bot.config.APPROVED_CHANNEL_ID = channel_id
                await interaction.response.send_message(
                    f"✅ Approved channel updated to {channel.mention}",
                    ephemeral=True
                )
                logger.info(f"Approved channel updated to {channel_id} by {interaction.user}")
                
            elif setting == "approved_role":
                # Extract role ID from mention or use direct ID
                role_id = value.strip("<>@&")
                try:
                    role_id = int(role_id)
                except ValueError:
                    await interaction.response.send_message(
                        "❌ Invalid role ID. Please provide a valid role ID or mention.",
                        ephemeral=True
                    )
                    return
                
                # Verify role exists
                role = interaction.guild.get_role(role_id)
                if not role:
                    await interaction.response.send_message(
                        "❌ Role not found. Make sure the role exists in this server.",
                        ephemeral=True
                    )
                    return
                
                # Update config
                bot.config.APPROVED_ROLE_ID = role_id
                await interaction.response.send_message(
                    f"✅ Approved role updated to {role.mention}",
                    ephemeral=True
                )
                logger.info(f"Approved role updated to {role_id} by {interaction.user}")
                
        except Exception as e:
            logger.error(f"Error updating config: {e}", exc_info=True)
            await interaction.response.send_message(
                "❌ An error occurred while updating the configuration.",
                ephemeral=True
            )
    
    @bot.tree.command(name="status", description="Show current bot configuration")
    async def status_command(interaction: discord.Interaction):
        """Show current bot status and configuration"""
        embed = discord.Embed(
            title="🤖 Bot Status & Configuration",
            color=discord.Color.blue(),
            timestamp=datetime.utcnow()
        )
        
        # Get channel and role info
        suggestion_channel = bot.get_channel(bot.config.SUGGESTION_CHANNEL_ID) if bot.config.SUGGESTION_CHANNEL_ID else None
        staff_channel = bot.get_channel(bot.config.STAFF_CHANNEL_ID) if bot.config.STAFF_CHANNEL_ID else None
        approved_channel = bot.get_channel(bot.config.APPROVED_CHANNEL_ID) if bot.config.APPROVED_CHANNEL_ID else None
        approved_role = interaction.guild.get_role(bot.config.APPROVED_ROLE_ID) if bot.config.APPROVED_ROLE_ID else None
        
        embed.add_field(
            name="📝 Suggestion Channel",
            value=suggestion_channel.mention if suggestion_channel else "❌ Not configured",
            inline=True
        )
        
        embed.add_field(
            name="🎫 Staff Channel", 
            value=staff_channel.mention if staff_channel else "❌ Not configured",
            inline=True
        )
        
        embed.add_field(
            name="✅ Approved Channel",
            value=approved_channel.mention if approved_channel else "❌ Not configured",
            inline=True
        )
        
        embed.add_field(
            name="👥 Approved Role",
            value=approved_role.mention if approved_role else "❌ Not configured",
            inline=True
        )
        
        embed.add_field(
            name="📊 Bot Info",
            value=f"Servers: {len(bot.guilds)}\nPing: {round(bot.latency * 1000)}ms",
            inline=True
        )
        
        embed.add_field(
            name="⚙️ Available Commands",
            value="• `/suggestion` - Submit a suggestion\n• `/poll` - Create a role-restricted poll\n• `/pollresults` - Show poll results\n• `/editpoll` - Edit an active poll\n• `/config` - Configure channels (Admin)\n• `/status` - Show this status\n• `/help` - Show help",
            inline=False
        )
        
        embed.add_field(
            name="🎯 Auto-Approval",
            value="Suggestions with **10+ upvotes** are automatically posted to the approved channel!",
            inline=False
        )
        
        if interaction.user.guild_permissions.administrator:
            embed.add_field(
                name="🔧 Admin Note",
                value="Use `/config` to change channel settings",
                inline=False
            )
        
        embed.set_footer(text="Bot is running and ready!")
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @bot.tree.command(name="poll", description="Create a poll with role restrictions")
    @app_commands.describe(
        question="The poll question",
        duration="Poll duration in hours (default: 1, max: 168)",
        allowed_roles="Roles that can vote (mention or ID, separated by commas)",
        options="Poll options separated by commas (defaults to 'Yes, No' if not provided)",
        emojis="Custom emojis separated by commas (optional, auto-selected if not provided)"
    )
    async def poll_command(interaction: discord.Interaction, question: str, duration: int = 1, allowed_roles: str = None, options: str = None, emojis: str = None):
        """Create a poll with optional role restrictions"""
        if not interaction.user.guild_permissions.manage_messages:
            await interaction.response.send_message(
                "❌ You need 'Manage Messages' permission to create polls.",
                ephemeral=True
            )
            return
        
        try:
            # Parse options or use default "Yes, No"
            logger.info(f"Poll command called with options: {options}")
            if options:
                option_list = [opt.strip() for opt in options.split(',') if opt.strip()]
                if len(option_list) < 2:
                    await interaction.response.send_message(
                        "❌ Please provide at least 2 options separated by commas.",
                        ephemeral=True
                    )
                    return
            else:
                option_list = ["Yes", "No"]
                logger.info("Using default options: Yes, No")
            
            if len(option_list) > 10:
                await interaction.response.send_message(
                    "❌ Maximum 10 options allowed.",
                    ephemeral=True
                )
                return
            
            # Validate duration
            if duration < 1 or duration > 168:
                await interaction.response.send_message(
                    "❌ Duration must be between 1 and 168 hours (7 days).",
                    ephemeral=True
                )
                return
            
            # Parse allowed roles
            allowed_role_ids = []
            if allowed_roles:
                for role_str in allowed_roles.split(','):
                    role_str = role_str.strip().strip('<>@&')
                    try:
                        role_id = int(role_str)
                        role = interaction.guild.get_role(role_id)
                        if role:
                            allowed_role_ids.append(role_id)
                        else:
                            await interaction.response.send_message(
                                f"❌ Role with ID {role_id} not found.",
                                ephemeral=True
                            )
                            return
                    except ValueError:
                        await interaction.response.send_message(
                            f"❌ Invalid role format: {role_str}",
                            ephemeral=True
                        )
                        return
            
            # Parse custom emojis
            custom_emojis = []
            if emojis:
                custom_emojis = [emoji.strip() for emoji in emojis.split(',') if emoji.strip()]
                if len(custom_emojis) < len(option_list):
                    await interaction.response.send_message(
                        f"❌ You provided {len(custom_emojis)} emojis but have {len(option_list)} options. Please provide the same number of emojis as options.",
                        ephemeral=True
                    )
                    return
            
            # Auto-select emojis if not provided
            if not custom_emojis:
                if len(option_list) == 2:
                    # Use ✅ and ❌ for 2-option polls
                    poll_emojis = ['✅', '❌']
                else:
                    # Use numbered emojis for 3+ options
                    poll_emojis = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣', '🔟'][:len(option_list)]
            else:
                poll_emojis = custom_emojis[:len(option_list)]
            
            # Create poll embed
            poll_embed = create_poll_embed(
                question=question,
                options=option_list,
                author=interaction.user,
                allowed_roles=[interaction.guild.get_role(rid) for rid in allowed_role_ids],
                duration=duration,
                emojis=poll_emojis
            )
            
            # Send poll
            await interaction.response.send_message(embed=poll_embed)
            poll_message = await interaction.original_response()
            
            # Add reaction emojis
            for emoji in poll_emojis:
                await poll_message.add_reaction(emoji)
            
            # Store poll data
            if not hasattr(bot, 'active_polls'):
                bot.active_polls = {}
            
            bot.active_polls[poll_message.id] = {
                'question': question,
                'options': option_list,
                'allowed_roles': allowed_role_ids,
                'creator': interaction.user.id,
                'channel': interaction.channel.id,
                'end_time': datetime.utcnow().timestamp() + (duration * 3600),  # Convert hours to seconds
                'emojis': poll_emojis
            }
            
            logger.info(f"Poll created by {interaction.user} with {len(option_list)} options")
            
        except Exception as e:
            logger.error(f"Error creating poll: {e}", exc_info=True)
            await interaction.response.send_message(
                "❌ An error occurred while creating the poll.",
                ephemeral=True
            )
    
    @bot.tree.command(name="pollresults", description="Show results of an active poll")
    @app_commands.describe(
        message_id="The ID of the poll message (right-click message and copy ID)"
    )
    async def poll_results_command(interaction: discord.Interaction, message_id: str):
        """Show results of an active poll"""
        try:
            poll_message_id = int(message_id)
            
            if not hasattr(bot, 'active_polls') or poll_message_id not in bot.active_polls:
                await interaction.response.send_message(
                    "❌ Poll not found or poll has already ended.",
                    ephemeral=True
                )
                return
            
            poll_data = bot.active_polls[poll_message_id]
            
            # Get the poll message
            try:
                poll_message = await interaction.channel.fetch_message(poll_message_id)
            except discord.NotFound:
                await interaction.response.send_message(
                    "❌ Poll message not found.",
                    ephemeral=True
                )
                return
            
            # Calculate results
            poll_emojis = poll_data.get('emojis', ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣', '🔟'])
            results = []
            total_votes = 0
            
            for i, option in enumerate(poll_data['options']):
                if i < len(poll_emojis):
                    emoji = poll_emojis[i]
                    votes = 0
                    
                    for reaction in poll_message.reactions:
                        if reaction.emoji == emoji:
                            votes = reaction.count - 1  # Subtract bot's reaction
                            break
                    
                    results.append((option, votes, emoji))
                    total_votes += votes
            
            # Create results embed
            embed = discord.Embed(
                title=f"📊 Poll Results: {poll_data['question']}",
                color=discord.Color.green(),
                timestamp=datetime.utcnow()
            )
            
            # Add results with voter information
            results_text = ""
            for option, votes, emoji in results:
                percentage = (votes / total_votes * 100) if total_votes > 0 else 0
                bar_length = int(percentage / 5)  # 20 chars max
                bar = "█" * bar_length + "░" * (20 - bar_length)
                
                # Get voters for this option
                voters = []
                for reaction in poll_message.reactions:
                    if reaction.emoji == emoji:
                        users = await reaction.users().flatten()
                        for user in users:
                            if not user.bot:
                                voters.append(user.display_name)
                        break
                
                voter_text = ""
                if voters:
                    voter_text = f"\n└ {', '.join(voters[:5])}"
                    if len(voters) > 5:
                        voter_text += f" and {len(voters) - 5} more"
                
                results_text += f"{emoji} **{option}**\n{bar} {votes} votes ({percentage:.1f}%){voter_text}\n\n"
            
            embed.add_field(
                name="Results",
                value=results_text,
                inline=False
            )
            
            embed.add_field(
                name="📊 Total Votes",
                value=str(total_votes),
                inline=True
            )
            
            # Check if poll has ended
            if datetime.utcnow().timestamp() > poll_data['end_time']:
                embed.add_field(
                    name="⏰ Status",
                    value="Poll has ended",
                    inline=True
                )
            else:
                embed.add_field(
                    name="⏰ Status",
                    value=f"Ends <t:{int(poll_data['end_time'])}:R>",
                    inline=True
                )
            
            embed.set_footer(text="Use /pollresults to see updated results")
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except ValueError:
            await interaction.response.send_message(
                "❌ Invalid message ID format.",
                ephemeral=True
            )
        except Exception as e:
            logger.error(f"Error showing poll results: {e}", exc_info=True)
            await interaction.response.send_message(
                "❌ An error occurred while showing poll results.",
                ephemeral=True
            )
    
    @bot.tree.command(name="editpoll", description="Edit an active poll (creator only)")
    @app_commands.describe(
        message_id="The ID of the poll message to edit",
        question="New poll question (optional)",
        options="New poll options separated by commas (optional)",
        duration="New duration in hours (optional, max: 168)",
        emojis="New emojis separated by commas (optional)"
    )
    async def edit_poll_command(interaction: discord.Interaction, message_id: str, question: str = None, options: str = None, duration: int = None, emojis: str = None):
        """Edit an active poll (creator only)"""
        try:
            poll_message_id = int(message_id)
            
            if not hasattr(bot, 'active_polls') or poll_message_id not in bot.active_polls:
                await interaction.response.send_message(
                    "❌ Poll not found or poll has already ended.",
                    ephemeral=True
                )
                return
            
            poll_data = bot.active_polls[poll_message_id]
            
            # Check if user is the creator or has manage messages permission
            if poll_data['creator'] != interaction.user.id and not interaction.user.guild_permissions.manage_messages:
                await interaction.response.send_message(
                    "❌ Only the poll creator or users with 'Manage Messages' permission can edit polls.",
                    ephemeral=True
                )
                return
            
            # Check if poll has ended
            if datetime.utcnow().timestamp() > poll_data['end_time']:
                await interaction.response.send_message(
                    "❌ Cannot edit an expired poll.",
                    ephemeral=True
                )
                return
            
            # Get the poll message
            try:
                poll_message = await interaction.channel.fetch_message(poll_message_id)
            except discord.NotFound:
                await interaction.response.send_message(
                    "❌ Poll message not found.",
                    ephemeral=True
                )
                return
            
            # Update poll data with new values
            updated_question = question if question else poll_data['question']
            updated_options = [opt.strip() for opt in options.split(',') if opt.strip()] if options else poll_data['options']
            updated_duration = duration if duration else (poll_data['end_time'] - datetime.utcnow().timestamp()) / 3600
            
            # Validate new options
            if options and (len(updated_options) < 2 or len(updated_options) > 10):
                await interaction.response.send_message(
                    "❌ Please provide between 2 and 10 options.",
                    ephemeral=True
                )
                return
            
            # Validate new duration
            if duration and (duration < 1 or duration > 168):
                await interaction.response.send_message(
                    "❌ Duration must be between 1 and 168 hours (7 days).",
                    ephemeral=True
                )
                return
            
            # Parse new emojis
            updated_emojis = poll_data.get('emojis', ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣', '🔟'])
            if emojis:
                custom_emojis = [emoji.strip() for emoji in emojis.split(',') if emoji.strip()]
                if len(custom_emojis) < len(updated_options):
                    await interaction.response.send_message(
                        f"❌ You provided {len(custom_emojis)} emojis but have {len(updated_options)} options.",
                        ephemeral=True
                    )
                    return
                updated_emojis = custom_emojis[:len(updated_options)]
            elif options:
                # Auto-select emojis for new options
                if len(updated_options) == 2:
                    updated_emojis = ['✅', '❌']
                else:
                    updated_emojis = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣', '🔟'][:len(updated_options)]
            
            # Update poll data
            poll_data['question'] = updated_question
            poll_data['options'] = updated_options
            poll_data['emojis'] = updated_emojis
            if duration:
                poll_data['end_time'] = datetime.utcnow().timestamp() + (duration * 3600)
            
            # Create updated embed
            updated_embed = create_poll_embed(
                question=updated_question,
                options=updated_options,
                author=interaction.guild.get_member(poll_data['creator']),
                allowed_roles=[interaction.guild.get_role(rid) for rid in poll_data['allowed_roles']],
                duration=updated_duration,
                emojis=updated_emojis
            )
            
            # Add edit note
            updated_embed.add_field(
                name="📝 Last Edit",
                value=f"Edited by {interaction.user.mention} <t:{int(datetime.utcnow().timestamp())}:R>",
                inline=False
            )
            
            # Update the message
            await poll_message.edit(embed=updated_embed)
            
            # Clear old reactions if options changed
            if options or emojis:
                await poll_message.clear_reactions()
                # Add new reactions
                for emoji in updated_emojis:
                    await poll_message.add_reaction(emoji)
            
            await interaction.response.send_message(
                "✅ Poll updated successfully!",
                ephemeral=True
            )
            
            logger.info(f"Poll edited by {interaction.user}")
            
        except ValueError:
            await interaction.response.send_message(
                "❌ Invalid message ID format.",
                ephemeral=True
            )
        except Exception as e:
            logger.error(f"Error editing poll: {e}", exc_info=True)
            await interaction.response.send_message(
                "❌ An error occurred while editing the poll.",
                ephemeral=True
            )
