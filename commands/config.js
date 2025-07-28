
const { SlashCommandBuilder, ChannelType, PermissionFlagsBits } = require('discord.js');
const fs = require('fs');
const path = require('path');

const configPath = path.join(__dirname, '..', 'config.json');

module.exports = {
  data: new SlashCommandBuilder()
    .setName('config')
    .setDescription('Set up bot configuration')
    .setDefaultMemberPermissions(PermissionFlagsBits.Administrator)
    .addChannelOption(option =>
      option.setName('suggestions_channel')
        .setDescription('Channel where suggestion button is posted')
        .addChannelTypes(ChannelType.GuildText)
        .setRequired(true))
    .addChannelOption(option =>
      option.setName('general_channel')
        .setDescription('Channel where suggestions are sent')
        .addChannelTypes(ChannelType.GuildText)
        .setRequired(true))
    .addChannelOption(option =>
      option.setName('staff_channel')
        .setDescription('Channel where staff vote on suggestions')
        .addChannelTypes(ChannelType.GuildText)
        .setRequired(true))
    .addChannelOption(option =>
      option.setName('announcement_channel')
        .setDescription('Channel where decisions are announced')
        .addChannelTypes(ChannelType.GuildText)
        .setRequired(true))
    .addChannelOption(option =>
      option.setName('scheduler_category')
        .setDescription('Category for creating schedule channels')
        .addChannelTypes(ChannelType.GuildCategory)
        .setRequired(true))
    .addRoleOption(option =>
      option.setName('king_role')
        .setDescription('Role representing a King')
        .setRequired(true))
    .addRoleOption(option =>
      option.setName('buff_giver_role')
        .setDescription('Role representing a Buff Giver')
        .setRequired(true))
    .addIntegerOption(option =>
      option.setName('vote_threshold')
        .setDescription('Vote threshold for sending suggestion to staff')
        .setRequired(true))
    .addIntegerOption(option =>
      option.setName('vote_duration')
        .setDescription('Voting duration in hours before final decision')
        .setRequired(true)),

  async execute(interaction) {
    try {
      const data = {
        suggestionsChannelId: interaction.options.getChannel('suggestions_channel').id,
        generalChannelId: interaction.options.getChannel('general_channel').id,
        staffChannelId: interaction.options.getChannel('staff_channel').id,
        announcementChannelId: interaction.options.getChannel('announcement_channel').id,
        schedulerCategoryId: interaction.options.getChannel('scheduler_category').id,
        kingRoleId: interaction.options.getRole('king_role').id,
        buffGiverRoleId: interaction.options.getRole('buff_giver_role').id,
        voteThreshold: interaction.options.getInteger('vote_threshold'),
        voteDurationHours: interaction.options.getInteger('vote_duration')
      };

      fs.writeFileSync(configPath, JSON.stringify(data, null, 2));
      await interaction.reply({ content: '✅ Configuration saved successfully!', ephemeral: true });
    } catch (error) {
      console.error(error);
      await interaction.reply({ content: '❌ Failed to save configuration.', ephemeral: true });
    }
  }
};
