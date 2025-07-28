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
        .setDescription('Channel for suggestion submission')
        .addChannelTypes(ChannelType.GuildText)
        .setRequired(false))
    .addChannelOption(option =>
      option.setName('general_channel')
        .setDescription('Channel where suggestions are posted for public voting')
        .addChannelTypes(ChannelType.GuildText)
        .setRequired(false))
    .addChannelOption(option =>
      option.setName('staff_channel')
        .setDescription('Staff review channel')
        .addChannelTypes(ChannelType.GuildText)
        .setRequired(false))
    .addChannelOption(option =>
      option.setName('announcement_channel')
        .setDescription('Channel where accepted/rejected suggestions are announced')
        .addChannelTypes(ChannelType.GuildText)
        .setRequired(false))
    .addRoleOption(option =>
      option.setName('staff_role')
        .setDescription('Role used for staff voting')
        .setRequired(false))
    .addIntegerOption(option =>
      option.setName('upvote_threshold')
        .setDescription('Number of 👍 votes required to escalate')
        .setMinValue(1)
        .setRequired(false))
    .addIntegerOption(option =>
      option.setName('decision_delay')
        .setDescription('Delay in hours before posting result (0 to wait for all staff)')
        .setMinValue(0)
        .setRequired(false)),

  async execute(interaction) {
    try {
      const config = fs.existsSync(configPath)
        ? JSON.parse(fs.readFileSync(configPath, 'utf8'))
        : {};

      config.suggestions = {
        suggestionsChannelId: interaction.options.getChannel('suggestions_channel')?.id || config.suggestions?.suggestionsChannelId || null,
        generalChannelId: interaction.options.getChannel('general_channel')?.id || config.suggestions?.generalChannelId || null,
        staffChannelId: interaction.options.getChannel('staff_channel')?.id || config.suggestions?.staffChannelId || null,
        announcementChannelId: interaction.options.getChannel('announcement_channel')?.id || config.suggestions?.announcementChannelId || null,
        staffRoleId: interaction.options.getRole('staff_role')?.id || config.suggestions?.staffRoleId || null,
        upvoteThreshold: interaction.options.getInteger('upvote_threshold') ?? config.suggestions?.upvoteThreshold ?? 5,
        decisionDelayHours: interaction.options.getInteger('decision_delay') ?? config.suggestions?.decisionDelayHours ?? 24
      };

      fs.writeFileSync(configPath, JSON.stringify(config, null, 2));
      await interaction.reply({ content: '✅ Configuration saved.', ephemeral: true });
    } catch (error) {
      console.error('[CONFIG ERROR]', error);
      await interaction.reply({ content: '❌ Failed to save config.', ephemeral: true });
    }
  }
};