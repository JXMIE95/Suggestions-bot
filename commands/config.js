
const { SlashCommandBuilder, ChannelType } = require('discord.js');
const fs = require('fs');
const path = require('path');

const configPath = path.join(__dirname, '..', 'config.json');

module.exports = {
    data: new SlashCommandBuilder()
        .setName('config')
        .setDescription('Set configuration for suggestion and roster systems')
        .addChannelOption(option =>
            option.setName('suggestions_channel')
                .setDescription('Channel to post suggestion buttons')
                .addChannelTypes(ChannelType.GuildText)
                .setRequired(true))
        .addChannelOption(option =>
            option.setName('scheduler_category')
                .setDescription('Category for scheduler channels')
                .addChannelTypes(ChannelType.GuildCategory)
                .setRequired(true)),

    async execute(interaction) {
        const suggestionsChannel = interaction.options.getChannel('suggestions_channel');
        const schedulerCategory = interaction.options.getChannel('scheduler_category');

        const config = {
            suggestions: {
                channelId: suggestionsChannel.id
            },
            scheduler: {
                enabled: true,
                categoryId: schedulerCategory.id,
                notificationMinutes: 5,
                maxConcurrentUsers: 2
            }
        };

        fs.writeFileSync(configPath, JSON.stringify(config, null, 2));
        await interaction.reply({ content: '✅ Configuration saved!', ephemeral: true });
    }
};
