
const { SlashCommandBuilder, ChannelType } = require('discord.js');
const fs = require('fs');
const path = require('path');
const configPath = path.join(__dirname, '..', 'config.json');

module.exports = {
    data: new SlashCommandBuilder()
        .setName('config')
        .setDescription('Set up bot configuration')
        .addChannelOption(option =>
            option.setName('suggestions_channel')
                .setDescription('Channel for suggestions')
                .setRequired(true))
        .addChannelOption(option =>
            option.setName('scheduler_category')
                .setDescription('Category for scheduler channels')
                .setRequired(true)
                .addChannelTypes(4)) // 4 = GuildCategory
        .addChannelOption(option =>
            option.setName('notification_channel')
                .setDescription('Channel for shift notifications')
                .setRequired(true))
        .addRoleOption(option =>
            option.setName('king_role')
                .setDescription('Role for King participants')
                .setRequired(true))
        .addRoleOption(option =>
            option.setName('buffgiver_role')
                .setDescription('Role for Buff Givers')
                .setRequired(true)),

    async execute(interaction) {
        const suggestionsChannel = interaction.options.getChannel('suggestions_channel');
        const schedulerCategory = interaction.options.getChannel('scheduler_category');
        const notificationChannel = interaction.options.getChannel('notification_channel');
        const kingRole = interaction.options.getRole('king_role');
        const buffGiverRole = interaction.options.getRole('buffgiver_role');

        if (!schedulerCategory || schedulerCategory.type !== 4) {
            return await interaction.reply({ content: 'Scheduler category must be a category!', ephemeral: true });
        }

        const newConfig = {
            suggestionsChannelId: suggestionsChannel.id,
            scheduler: {
                enabled: true,
                categoryId: schedulerCategory.id,
                notificationChannelId: notificationChannel.id,
                kingRoleId: kingRole.id,
                buffGiverRoleId: buffGiverRole.id,
                maxConcurrentUsers: 2,
                notificationMinutes: 5
            }
        };

        fs.writeFileSync(configPath, JSON.stringify(newConfig, null, 2));
        await interaction.reply({ content: '✅ Configuration saved successfully.', ephemeral: true });
    }
};
