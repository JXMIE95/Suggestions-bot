const { EmbedBuilder, ActionRowBuilder, ButtonBuilder, ButtonStyle, ModalBuilder, TextInputBuilder, TextInputStyle } = require('discord.js');
const fs = require('fs');
const path = require('path');
const db = require('../database/init').getDatabase;
const logger = require('../utils/logger');

const configPath = path.join(__dirname, '..', 'config.json');

async function handleSubmitButton(interaction) {
    const modal = new ModalBuilder()
        .setCustomId('suggestion_modal')
        .setTitle('Submit Your Suggestion');

    const suggestionInput = new TextInputBuilder()
        .setCustomId('suggestion_text')
        .setLabel('Your Suggestion')
        .setStyle(TextInputStyle.Paragraph)
        .setPlaceholder('Describe your suggestion in detail...')
        .setRequired(true)
        .setMaxLength(2000);

    const firstActionRow = new ActionRowBuilder().addComponents(suggestionInput);
    modal.addComponents(firstActionRow);

    await interaction.showModal(modal);
}

async function handleSuggestionSubmit(interaction) {
    try {
        const config = JSON.parse(fs.readFileSync(configPath, 'utf8'));
        const suggestionText = interaction.fields.getTextInputValue('suggestion_text');

        if (!config.suggestions.mainChannelId) {
            await interaction.reply({ content: 'Suggestions system is not properly configured.', ephemeral: true });
            return;
        }

        const mainChannel = await interaction.client.channels.fetch(config.suggestions.mainChannelId);
        if (!mainChannel) {
            await interaction.reply({ content: 'Main channel not found.', ephemeral: true });
            return;
        }

        // Create suggestion embed
        const embed = new EmbedBuilder()
            .setTitle('💡 New Suggestion')
            .setDescription(suggestionText)
            .setAuthor({ 
                name: interaction.user.username, 
                iconURL: interaction.user.displayAvatarURL() 
            })
            .setColor(0x00AE86)
            .addFields(
                { name: '👍🏻 Upvotes', value: '0', inline: true },
                { name: '👎 Downvotes', value: '0', inline: true },
                { name: 'Status', value: 'Voting in progress', inline: true }
            )
            .setTimestamp()
            .setFooter({ text: `Suggestion by ${interaction.user.tag}` });

        // Send to main channel
        let content = '';
        if (config.suggestions.mainRoleId) {
            content = `<@&${config.suggestions.mainRoleId}> New suggestion submitted!`;
        }

        const message = await mainChannel.send({
            content,
            embeds: [embed]
        });

        // Add reactions
        await message.react('👍🏻');
        await message.react('👎');

        // Save to database
        const votingEndsAt = new Date(Date.now() + config.suggestions.votingTimeLimit);
        
        db().run(
            'INSERT INTO suggestions (messageId, userId, content, votingEndsAt) VALUES (?, ?, ?, ?)',
            [message.id, interaction.user.id, suggestionText, votingEndsAt.toISOString()],
            function(err) {
                if (err) {
                    logger.error('Error saving suggestion:', err);
                } else {
                    logger.info(`Suggestion saved with ID: ${this.lastID}`);
                    
                    // Set timer for voting end
                    setTimeout(() => {
                        checkSuggestionVotes(interaction.client, this.lastID);
                    }, config.suggestions.votingTimeLimit);
                }
            }
        );

        await interaction.reply({ content: '✅ Your suggestion has been submitted successfully!', ephemeral: true });
    } catch (error) {
        logger.error('Error handling suggestion submit:', error);
        await interaction.reply({ content: 'Error submitting suggestion.', ephemeral: true });
    }
}

async function checkSuggestionVotes(client, suggestionId) {
    try {
        const config = JSON.parse(fs.readFileSync(configPath, 'utf8'));
        
        db().get(
            'SELECT * FROM suggestions WHERE id = ?',
            [suggestionId],
            async (err, suggestion) => {
                if (err || !suggestion) {
                    logger.error('Error fetching suggestion:', err);
                    return;
                }

                const channel = await client.channels.fetch(config.suggestions.mainChannelId);
                const message = await channel.messages.fetch(suggestion.messageId);

                if (!message) {
                    logger.warn('Suggestion message not found');
                    return;
                }

                // Count reactions
                const upvoteReaction = message.reactions.cache.get('👍🏻');
                const downvoteReaction = message.reactions.cache.get('👎');

                const upvotes = upvoteReaction ? upvoteReaction.count - 1 : 0; // -1 for bot reaction
                const downvotes = downvoteReaction ? downvoteReaction.count - 1 : 0;

                // Update suggestion in database
                db().run(
                    'UPDATE suggestions SET upvotes = ?, downvotes = ? WHERE id = ?',
                    [upvotes, downvotes, suggestionId]
                );

                // Check if it meets threshold for staff review
                if (upvotes >= config.suggestions.upvoteThreshold) {
                    await sendToStaffChannel(client, suggestion, upvotes, downvotes);
                }
            }
        );
    } catch (error) {
        logger.error('Error checking suggestion votes:', error);
    }
}

async function sendToStaffChannel(client, suggestion, upvotes, downvotes) {
    try {
        const config = JSON.parse(fs.readFileSync(configPath, 'utf8'));
        
        if (!config.suggestions.staffChannelId) {
            logger.warn('Staff channel not configured');
            return;
        }

        const staffChannel = await client.channels.fetch(config.suggestions.staffChannelId);
        if (!staffChannel) {
            logger.warn('Staff channel not found');
            return;
        }

        const embed = new EmbedBuilder()
            .setTitle('📊 Staff Vote Required')
            .setDescription(suggestion.content)
            .setColor(0xFFAA00)
            .addFields(
                { name: 'Community Votes', value: `👍🏻 ${upvotes} | 👎 ${downvotes}`, inline: false },
                { name: 'Status', value: 'Awaiting staff decision', inline: false }
            )
            .setTimestamp()
            .setFooter({ text: `Original suggestion ID: ${suggestion.id}` });

        const row = new ActionRowBuilder()
            .addComponents(
                new ButtonBuilder()
                    .setCustomId(`staff_approve_${suggestion.id}`)
                    .setLabel('Approve')
                    .setStyle(ButtonStyle.Success)
                    .setEmoji('✅'),
                new ButtonBuilder()
                    .setCustomId(`staff_reject_${suggestion.id}`)
                    .setLabel('Reject')
                    .setStyle(ButtonStyle.Danger)
                    .setEmoji('❌')
            );

        let content = '';
        if (config.suggestions.staffRoleId) {
            content = `<@&${config.suggestions.staffRoleId}> A suggestion needs your review!`;
        }

        const staffMessage = await staffChannel.send({
            content,
            embeds: [embed],
            components: [row]
        });

        // Update suggestion with staff message ID
        db().run(
            'UPDATE suggestions SET staffMessageId = ?, status = ?, staffVotingEndsAt = ? WHERE id = ?',
            [
                staffMessage.id, 
                'staff_review', 
                new Date(Date.now() + config.suggestions.staffVotingTimeLimit).toISOString(),
                suggestion.id
            ]
        );

        // Set timer for staff voting end
        setTimeout(() => {
            finalizeStaffVoting(client, suggestion.id);
        }, config.suggestions.staffVotingTimeLimit);

    } catch (error) {
        logger.error('Error sending to staff channel:', error);
    }
}

async function handleStaffVote(interaction) {
    try {
        const suggestionId = interaction.customId.split('_')[2];
        const voteType = interaction.customId.split('_')[1]; // 'approve' or 'reject'

        // Check if user has staff role
        const config = JSON.parse(fs.readFileSync(configPath, 'utf8'));
        if (config.suggestions.staffRoleId && !interaction.member.roles.cache.has(config.suggestions.staffRoleId)) {
            await interaction.reply({ content: 'You do not have permission to vote on this suggestion.', ephemeral: true });
            return;
        }

        // Record vote
        db().run(
            'INSERT OR REPLACE INTO staff_votes (suggestionId, userId, vote) VALUES (?, ?, ?)',
            [suggestionId, interaction.user.id, voteType],
            (err) => {
                if (err) {
                    logger.error('Error recording staff vote:', err);
                }
            }
        );

        await interaction.reply({ content: `✅ Your ${voteType === 'approve' ? 'approval' : 'rejection'} vote has been recorded.`, ephemeral: true });

        // Check if all staff have voted
        checkStaffVotingComplete(interaction.client, suggestionId);

    } catch (error) {
        logger.error('Error handling staff vote:', error);
        await interaction.reply({ content: 'Error recording your vote.', ephemeral: true });
    }
}

async function checkStaffVotingComplete(client, suggestionId) {
    try {
        const config = JSON.parse(fs.readFileSync(configPath, 'utf8'));
        
        if (!config.suggestions.staffRoleId) {
            return;
        }

        const guild = client.guilds.cache.first();
        const staffRole = guild.roles.cache.get(config.suggestions.staffRoleId);
        
        if (!staffRole) {
            return;
        }

        const staffMemberCount = staffRole.members.size;

        db().all(
            'SELECT vote, COUNT(*) as count FROM staff_votes WHERE suggestionId = ? GROUP BY vote',
            [suggestionId],
            async (err, votes) => {
                if (err) {
                    logger.error('Error checking staff votes:', err);
                    return;
                }

                const totalVotes = votes.reduce((sum, vote) => sum + vote.count, 0);
                
                if (totalVotes >= staffMemberCount) {
                    await finalizeStaffVoting(client, suggestionId);
                }
            }
        );
    } catch (error) {
        logger.error('Error checking staff voting completion:', error);
    }
}

async function finalizeStaffVoting(client, suggestionId) {
    try {
        const config = JSON.parse(fs.readFileSync(configPath, 'utf8'));

        db().all(
            'SELECT vote, COUNT(*) as count FROM staff_votes WHERE suggestionId = ? GROUP BY vote',
            [suggestionId],
            async (err, votes) => {
                if (err) {
                    logger.error('Error finalizing staff voting:', err);
                    return;
                }

                const approvals = votes.find(v => v.vote === 'approve')?.count || 0;
                const rejections = votes.find(v => v.vote === 'reject')?.count || 0;
                
                const approved = approvals > rejections;
                const status = approved ? 'approved' : 'rejected';

                // Update suggestion status
                db().run(
                    'UPDATE suggestions SET status = ? WHERE id = ?',
                    [status, suggestionId]
                );

                // Get suggestion details
                db().get(
                    'SELECT * FROM suggestions WHERE id = ?',
                    [suggestionId],
                    async (err, suggestion) => {
                        if (err || !suggestion) {
                            logger.error('Error getting suggestion for announcement:', err);
                            return;
                        }

                        await announceResult(client, suggestion, approved, approvals, rejections);
                    }
                );
            }
        );
    } catch (error) {
        logger.error('Error finalizing staff voting:', error);
    }
}

async function announceResult(client, suggestion, approved, approvals, rejections) {
    try {
        const config = JSON.parse(fs.readFileSync(configPath, 'utf8'));
        
        if (!config.suggestions.announcementChannelId) {
            logger.warn('Announcement channel not configured');
            return;
        }

        const announcementChannel = await client.channels.fetch(config.suggestions.announcementChannelId);
        if (!announcementChannel) {
            logger.warn('Announcement channel not found');
            return;
        }

        const embed = new EmbedBuilder()
            .setTitle(approved ? '✅ Suggestion Approved!' : '❌ Suggestion Rejected')
            .setDescription(suggestion.content)
            .setColor(approved ? 0x00FF00 : 0xFF0000)
            .addFields(
                { name: 'Community Votes', value: `👍🏻 ${suggestion.upvotes} | 👎 ${suggestion.downvotes}`, inline: true },
                { name: 'Staff Decision', value: `✅ ${approvals} | ❌ ${rejections}`, inline: true }
            )
            .setTimestamp()
            .setFooter({ text: `Suggestion ID: ${suggestion.id}` });

        let content = '';
        if (config.suggestions.mainRoleId) {
            content = `<@&${config.suggestions.mainRoleId}> Suggestion decision announced!`;
        }

        await announcementChannel.send({
            content,
            embeds: [embed]
        });

        logger.info(`Suggestion ${suggestion.id} announced as ${approved ? 'approved' : 'rejected'}`);
    } catch (error) {
        logger.error('Error announcing result:', error);
    }
}

module.exports = {
    handleSubmitButton,
    handleSuggestionSubmit,
    handleStaffVote,
    checkSuggestionVotes
};
