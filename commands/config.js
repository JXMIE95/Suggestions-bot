
const { SlashCommandBuilder, ChannelType } = require('discord.js');
const fs = require('fs');
const path = require('path');
const logger = require('../utils/logger');

const CONFIG_PATH = path.join(__dirname, '..', 'config.json');

module.exports = {
    data: new SlashCommandBuilder()
        .setName('config')
        .setDescription('Configure the bot settings')
        .addChannelOption(option =>
            option.setName('suggestions_channel')
                .setDescription('Channel to post suggestions button')
                .addChannelTypes(ChannelType.GuildText)
        )
        .addChannelOption(option =>
            option.setName('scheduler_category')
                .setDescription('Category where daily roster channels will be created')
                .addChannelTypes(ChannelType.GuildCategory)
        )
        .addChannelOption(option =>
            option.setName('notifications_channel')
                .setDescription('Channel to send shift notifications')
                .addChannelTypes(ChannelType.GuildText)
        )
        .addRoleOption(option =>
            option.setName('king_role')
                .setDescription('Role to ping for King shifts')
        )
        .addRoleOption(option =>
            option.setName('buff_role')
                .setDescription('Role to ping for Buff Giver shifts')
        ),
    async execute(interaction) {
        try {
            const config = {
                suggestions: {
                    enabled: !!interaction.options.getChannel('suggestions_channel'),
                    channelId: interaction.options.getChannel('suggestions_channel')?.id || null
                },
                scheduler: {
                    enabled: !!interaction.options.getChannel('scheduler_category'),
                    categoryId: interaction.options.getChannel('scheduler_category')?.id || null,
                    notificationChannelId: interaction.options.getChannel('notifications_channel')?.id || null,
                    notificationMinutes: 5,
                    maxConcurrentUsers: 2,
                    kingRoleId: interaction.options.getRole('king_role')?.id || null,
                    buffGiverRoleId: interaction.options.getRole('buff_role')?.id || null
                }
            };

            fs.writeFileSync(CONFIG_PATH, JSON.stringify(config, null, 2));
            logger.info('Configuration updated successfully');

            await interaction.reply({
                content: '✅ Configuration saved. Please use `/reload` or restart the bot if needed.',
                ephemeral: true
            });
        } catch (error) {
            logger.error('Error saving config:', error);
            await interaction.reply({
                content: '❌ Failed to save configuration.',
                ephemeral: true
            });
        }
    }
};
