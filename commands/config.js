const fs = require('fs');
const path = require('path');

const configPath = path.join(__dirname, '..', 'config.json');

const { SlashCommandBuilder, ChannelType } = require('discord.js');

module.exports = {
  data: new SlashCommandBuilder()
    .setName('config')
    .setDescription('Configure scheduler and suggestions')
    .addChannelOption(opt =>
      opt.setName('scheduler_category')
        .addChannelTypes(ChannelType.GuildCategory)
        .setDescription('Category for scheduling')
        .setRequired(true))
    .addChannelOption(opt =>
      opt.setName('suggestions_channel')
        .setDescription('Channel for suggestions')
        .setRequired(true))
    .addChannelOption(opt =>
      opt.setName('notification_channel')
        .setDescription('Channel for notifications')
        .setRequired(true))
    .addRoleOption(opt =>
      opt.setName('king_role')
        .setDescription('Role for King')
        .setRequired(true))
    .addRoleOption(opt =>
      opt.setName('buff_role')
        .setDescription('Role for Buff Givers')
        .setRequired(true)),

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