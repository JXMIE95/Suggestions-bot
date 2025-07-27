const { SlashCommandBuilder } = require('discord.js');
const fs = require('fs');
const path = require('path');
const configPath = path.join(__dirname, '..', 'config.json');
let config = require(configPath);

module.exports = {
  data: new SlashCommandBuilder()
    .setName('config')
    .setDescription('Configure the bot settings')
    .addSubcommand(sub =>
      sub.setName('scheduler')
        .setDescription('Configure scheduler settings')
        .addChannelOption(opt =>
          opt.setName('category')
            .setDescription('Category for daily channels')
            .setRequired(true))
        .addChannelOption(opt =>
          opt.setName('notification')
            .setDescription('Channel for shift notifications')
            .setRequired(true))
        .addRoleOption(opt =>
          opt.setName('king-role')
            .setDescription('Role for King')
            .setRequired(true))
        .addRoleOption(opt =>
          opt.setName('buff-giver-role')
            .setDescription('Role for Buff Giver')
            .setRequired(true))
    )
    .addSubcommand(sub =>
      sub.setName('suggestions')
        .setDescription('Configure suggestions settings')
        .addChannelOption(opt =>
          opt.setName('main')
            .setDescription('Main channel for suggestions')
            .setRequired(true))
        .addChannelOption(opt =>
          opt.setName('submit')
            .setDescription('Channel where users submit suggestions')
            .setRequired(true))
        .addChannelOption(opt =>
          opt.setName('announce')
            .setDescription('Channel for accepted announcements')
            .setRequired(true))
        .addChannelOption(opt =>
          opt.setName('staff')
            .setDescription('Private staff discussion channel')
            .setRequired(true))
        .addRoleOption(opt =>
          opt.setName('main-role')
            .setDescription('Main role to notify')
            .setRequired(true))
        .addRoleOption(opt =>
          opt.setName('staff-role')
            .setDescription('Staff role to notify')
            .setRequired(true))
    ),

  async execute(interaction) {
    const sub = interaction.options.getSubcommand();

    if (sub === 'scheduler') {
      const category = interaction.options.getChannel('category');
      const notify = interaction.options.getChannel('notification');
      const kingRole = interaction.options.getRole('king-role');
      const buffRole = interaction.options.getRole('buff-giver-role');

      if (!category || !notify || !kingRole || !buffRole) {
        return interaction.reply({ content: '❌ One or more options are missing or invalid.', ephemeral: true });
      }

      config.scheduler.enabled = true;
      config.scheduler.categoryId = category.id;
      config.scheduler.notificationChannelId = notify.id;
      config.scheduler.kingRoleId = kingRole.id;
      config.scheduler.buffGiverRoleId = buffRole.id;

    } else if (sub === 'suggestions') {
      const main = interaction.options.getChannel('main');
      const submit = interaction.options.getChannel('submit');
      const announce = interaction.options.getChannel('announce');
      const staff = interaction.options.getChannel('staff');
      const mainRole = interaction.options.getRole('main-role');
      const staffRole = interaction.options.getRole('staff-role');

      if (!main || !submit || !announce || !staff || !mainRole || !staffRole) {
        return interaction.reply({ content: '❌ One or more options are missing or invalid.', ephemeral: true });
      }

      config.suggestions.enabled = true;
      config.suggestions.mainChannelId = main.id;
      config.suggestions.submitChannelId = submit.id;
      config.suggestions.announcementChannelId = announce.id;
      config.suggestions.staffChannelId = staff.id;
      config.suggestions.mainRoleId = mainRole.id;
      config.suggestions.staffRoleId = staffRole.id;
    }

    try {
      fs.writeFileSync(configPath, JSON.stringify(config, null, 2));
      await interaction.reply({ content: '✅ Configuration updated successfully.', ephemeral: true });
    } catch (err) {
      console.error('Failed to write config file:', err);
      await interaction.reply({ content: '❌ Failed to write config to disk.', ephemeral: true });
    }
  }
};