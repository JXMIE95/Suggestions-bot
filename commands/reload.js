
const { SlashCommandBuilder } = require('discord.js');
const fs = require('fs');
const path = require('path');
const scheduler = require('../systems/scheduler');
const suggestions = require('../systems/suggestions');
const logger = require('../utils/logger');

module.exports = {
  data: new SlashCommandBuilder()
    .setName('reload')
    .setDescription('Reload the bot systems based on latest config.json'),
  async execute(interaction) {
    try {
      const configPath = path.join(__dirname, '..', 'config.json');
      if (!fs.existsSync(configPath)) {
        await interaction.reply({ content: '⚠️ No config.json file found.', ephemeral: true });
        return;
      }

      const config = JSON.parse(fs.readFileSync(configPath, 'utf8'));

      if (config.suggestions?.enabled && config.suggestions.channelId) {
        await suggestions.setupSuggestionsButton(interaction.client);
      }

      if (config.scheduler?.enabled && config.scheduler.categoryId) {
        await scheduler.initializeScheduler(interaction.client);
      }

      await interaction.reply({ content: '✅ Reloaded bot systems from config.', ephemeral: true });
    } catch (err) {
      logger.error('Error during reload:', err);
      await interaction.reply({ content: '❌ Failed to reload. Check logs for details.', ephemeral: true });
    }
  }
};
