
const fs = require('fs');
const path = require('path');

const configPath = path.join(__dirname, '..', 'config.json');

module.exports = {
    name: 'config',
    description: 'Configure scheduler and suggestion settings',
    options: [
        {
            name: 'scheduler_category',
            type: 7, // CHANNEL
            description: 'Select a category for scheduler channels',
            required: true
        },
        {
            name: 'suggestions_channel',
            type: 7,
            description: 'Select a text channel for suggestions',
            required: true
        },
        {
            name: 'notification_channel',
            type: 7,
            description: 'Channel where reminders will be sent',
            required: true
        },
        {
            name: 'king_role',
            type: 8, // ROLE
            description: 'Role for King',
            required: true
        },
        {
            name: 'buff_role',
            type: 8,
            description: 'Role for Buff Givers',
            required: true
        }
    ],
    async execute(interaction) {
        try {
            const category = interaction.options.getChannel('scheduler_category');
            const suggestionsChannel = interaction.options.getChannel('suggestions_channel');
            const notificationChannel = interaction.options.getChannel('notification_channel');
            const kingRole = interaction.options.getRole('king_role');
            const buffRole = interaction.options.getRole('buff_role');

            if (category.type !== 4) {
                return interaction.reply({ content: 'Please select a valid **category channel**.', ephemeral: true });
            }

            const config = {
                scheduler: {
                    enabled: true,
                    categoryId: category.id,
                    notificationChannelId: notificationChannel.id,
                    kingRoleId: kingRole.id,
                    buffGiverRoleId: buffRole.id,
                    maxConcurrentUsers: 2,
                    notificationMinutes: 5
                },
                suggestions: {
                    enabled: true,
                    channelId: suggestionsChannel.id
                }
            };

            fs.writeFileSync(configPath, JSON.stringify(config, null, 2));
            await interaction.reply({ content: '✅ Configuration saved successfully!', ephemeral: true });
        } catch (err) {
            console.error('Error saving config:', err);
            await interaction.reply({ content: '❌ Failed to save config. Check logs for details.', ephemeral: true });
        }
    }
};
