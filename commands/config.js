const { SlashCommandBuilder, ChannelType } = require('discord.js');
const fs = require('fs');
const path = require('path');
const configPath = path.join(__dirname, '..', 'config.json');

module.exports = {
  data: new SlashCommandBuilder()
    .setName('config')
    .setDescription('Configure bot settings')
    .addChannelOption(option =>
      option.setName('suggestions_channel')
        .setDescription('Channel to post suggestions')
        .addChannelTypes(ChannelType.GuildText)
        .setRequired(false))
    .addChannelOption(option =>
      option.setName('scheduler_category')
        .setDescription('Category for daily roster channels')
        .addChannelTypes(4)
        .setRequired(false))
    .addChannelOption(option =>
      option.setName('notification_channel')
        .setDescription('Channel to send shift reminders')
        .addChannelTypes(ChannelType.GuildText)
        .setRequired(false))
    .addRoleOption(option =>
      option.setName('king_role')
        .setDescription('Role to mention for king duties')
        .setRequired(false))
    .addRoleOption(option =>
      option.setName('buffgiver_role')
        .setDescription('Role to mention for buff givers')
        .setRequired(false))
    .addIntegerOption(option =>
      option.setName('max_concurrent_users')
        .setDescription('Max users per time slot')
        .setRequired(false))
    .addIntegerOption(option =>
      option.setName('notification_minutes')
        .setDescription('Minutes before a shift to send reminders')
        .setRequired(false)),

  async execute(interaction) {
    try {
      if (!fs.existsSync(configPath)) {
        fs.writeFileSync(configPath, JSON.stringify({}, null, 2));
      }

      const config = JSON.parse(fs.readFileSync(configPath, 'utf8'));

      const suggestionsChannel = interaction.options.getChannel('suggestions_channel');
      const schedulerCategory = interaction.options.getChannel('scheduler_category');
      const notificationChannel = interaction.options.getChannel('notification_channel');
      const kingRole = interaction.options.getRole('king_role');
      const buffGiverRole = interaction.options.getRole('buffgiver_role');
      const maxUsers = interaction.options.getInteger('max_concurrent_users');
      const notificationMinutes = interaction.options.getInteger('notification_minutes');

      if (schedulerCategory && schedulerCategory.type !== ChannelType.GuildCategory) {
        await interaction.reply({
          content: '❌ The selected scheduler category must be a valid **category**, not a text or voice channel.',
          ephemeral: true
        });
        return;
      }

      config.scheduler = config.scheduler || {};

      if (suggestionsChannel) config.suggestionsChannelId = suggestionsChannel.id;
      if (schedulerCategory) config.scheduler.categoryId = schedulerCategory.id;
      if (notificationChannel) config.scheduler.notificationChannelId = notificationChannel.id;
      if (kingRole) config.scheduler.kingRoleId = kingRole.id;
      if (buffGiverRole) config.scheduler.buffGiverRoleId = buffGiverRole.id;
      if (maxUsers !== null) config.scheduler.maxConcurrentUsers = maxUsers;
      if (notificationMinutes !== null) config.scheduler.notificationMinutes = notificationMinutes;

      fs.writeFileSync(configPath, JSON.stringify(config, null, 2));
      await interaction.reply({ content: '✅ Configuration updated successfully.', ephemeral: true });
    } catch (error) {
      console.error('[CONFIG ERROR]', error);
      await interaction.reply({ content: '❌ Failed to update configuration.', ephemeral: true });
    }
  }
};