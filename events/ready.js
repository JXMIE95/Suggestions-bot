
const { Events } = require('discord.js');
const fs = require('fs');
const path = require('path');
const scheduler = require('../systems/scheduler');
const suggestions = require('../systems/suggestions');
const logger = require('../utils/logger');

module.exports = {
  name: Events.ClientReady,
  once: true,
  async execute(client) {
    logger.info(`Bot is ready! Logged in as ${client.user.tag}`);

    try {
      const commands = client.commands.map(cmd => cmd.data.toJSON());
      await client.application.commands.set(commands);
      logger.info('Successfully registered application commands');
    } catch (err) {
      logger.error('Error registering commands:', err);
    }

    const configPath = path.join(__dirname, '..', 'config.json');
    if (!fs.existsSync(configPath)) {
      logger.warn('No config.json found, skipping system initialization');
      return;
    }

    const config = JSON.parse(fs.readFileSync(configPath, 'utf8'));

    if (config.suggestions?.enabled && config.suggestions.channelId) {
      try {
        await suggestions.setupSuggestionsButton(client);
      } catch (err) {
        logger.error('Error posting suggestions button:', err);
      }
    }

    if (config.scheduler?.enabled && config.scheduler.categoryId) {
      try {
        await scheduler.initializeScheduler(client);
      } catch (err) {
        logger.error('Error initializing scheduler:', err);
      }
    }
  }
};
