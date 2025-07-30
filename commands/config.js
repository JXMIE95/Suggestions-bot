
const { SlashCommandBuilder, ChannelType } = require('discord.js');
const path = require('path');
const fs = require('fs');

const configPath = path.join(__dirname, '..', 'config.json');

module.exports = {
    data: new SlashCommandBuilder()
        .setName('config')
        .setDescription('Configure bot settings')
        .addChannelOption(option =>
            option
                .setName('suggestions_channel')
                .setDescription('Channel for suggestions')
                .setRequired(true)
        )
        .addChannelOption(option =>
            option
                .setName('scheduler_category')
                .addChannelTypes(ChannelType.GuildCategory)
                .setDescription('Category for roster channels')
                .setRequired(true)
        )
        .addChannelOption(option =>
            option
                .setName('notification_channel')
                .setDescription('Channel for shift reminders')
                .setRequired(true)
        )
        .addRoleOption(option =>
            option
                .setName('king_role')
                .setDescription('Role for Kings')
                .setRequired(true)
        )
        .addRoleOption(option =>
            option
                .setName('buff_giver_role')
                .setDescription('Role for Buff Givers')
                .setRequired(true)
        ),

    async execute(interaction) {
        try {
            const suggestionsChannel = interaction.options.getChannel('suggestions_channel');
            const schedulerCategory = interaction.options.getChannel('scheduler_category');
            const notificationChannel = interaction.options.getChannel('notification_channel');
            const kingRole = interaction.options.getRole('king_role');
            const buffGiverRole = interaction.options.getRole('buff_giver_role');

            if (!schedulerCategory || schedulerCategory.type !== ChannelType.GuildCategory) {
                await interaction.reply({ content: '❌ Please select a valid category.', ephemeral: true });
                return;
            }

            if (!kingRole || !buffGiverRole) {
                await interaction.reply({ content: '❌ Please select valid roles.', ephemeral: true });
                return;
            }

            const config = {
                suggestionsChannelId: suggestionsChannel.id,
                scheduler: {
                    enabled: true,
                    categoryId: schedulerCategory.id,
                    notificationChannelId: notificationChannel.id,
                    notificationMinutes: 5,
                    kingRoleId: kingRole.id,
                    buffGiverRoleId: buffGiverRole.id,
                    maxConcurrentUsers: 2
                }
            };

            fs.writeFileSync(configPath, JSON.stringify(config, null, 2));
            console.log('[CONFIG] Saved configuration:', config);
            await interaction.reply({ content: '✅ Configuration saved successfully!', ephemeral: true });

        } catch (err) {
            console.error('[ERROR] Saving config:', err);
            await interaction.reply({ content: '❌ Failed to save configuration.', ephemeral: true });
        }
    }
};
