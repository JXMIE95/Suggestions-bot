const fs = require('fs');
const path = require('path');
const { SlashCommandBuilder, ChannelType } = require('discord.js');
const configPath = path.join(__dirname, '..', 'config.json');
const logger = require('../utils/logger');

module.exports = {
  data: new SlashCommandBuilder()
    .setName('config')
    .setDescription('Configure bot settings')
    .addChannelOption(option =>
      option.setName('suggestions_channel')
        .setDescription('Channel to post suggestion buttons')
        .setRequired(true)
    )
    .addChannelOption(option =>
      option.setName('scheduler_category')
        .setDescription('Category to create daily roster channels')
        .addChannelTypes(ChannelType.GuildCategory)
        .setRequired(true)
    )
    .addChannelOption(option =>
      option.setName('notification_channel')
        .setDescription('Channel to send shift reminders')
        .setRequired(true)
    )
    .addRoleOption(option =>
      option.setName('king_role')
        .setDescription('Role for Kings')
        .setRequired(true)
    )
    .addRoleOption(option =>
      option.setName('buff_giver_role')
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

      const config = {
        suggestions: {
          channelId: suggestionsChannel.id
        },
        scheduler: {
          enabled: true,
          categoryId: schedulerCategory.id,
          notificationChannelId: notificationChannel.id,
          notificationMinutes: 5,
          maxConcurrentUsers: 2,
          kingRoleId: kingRole.id,
          buffGiverRoleId: buffGiverRole.id
        }
      };

      fs.writeFileSync(configPath, JSON.stringify(config, null, 2));
      logger.info('Configuration saved successfully');

      await interaction.reply({ content: '✅ Configuration saved successfully.', ephemeral: true });
    } catch (error) {
      logger.error('Error saving configuration:', error);
      await interaction.reply({ content: '❌ Failed to save configuration.', ephemeral: true });
    }
  }
};