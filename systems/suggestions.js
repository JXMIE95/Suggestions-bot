const { EmbedBuilder, ButtonBuilder, ButtonStyle, ActionRowBuilder } = require('discord.js');
const fs = require('fs');
const path = require('path');
const logger = require('../utils/logger');

const configPath = path.join(__dirname, '..', 'config.json');

async function initializeSuggestions(client) {
  try {
    const config = JSON.parse(fs.readFileSync(configPath, 'utf8'));
    const channelId = config.suggestions?.suggestionsChannelId;
    if (!channelId) return logger.warn('Suggestions channel ID not set in config.');

    const channel = await client.channels.fetch(channelId).catch(() => null);
    if (!channel) return logger.error('Configured suggestions channel not found.');

    const messages = await channel.messages.fetch({ limit: 10 });
    const alreadyExists = messages.some(m => m.author.bot && m.components?.length > 0);
    if (alreadyExists) {
      logger.info('Suggestions button already exists');
      return;
    }

    const embed = new EmbedBuilder()
      .setTitle('💡 Submit a Suggestion')
      .setDescription('Click the button below to submit your idea to improve the server!')
      .setColor(0x00AE86);

    const row = new ActionRowBuilder().addComponents(
      new ButtonBuilder()
        .setCustomId('submit_suggestion')
        .setLabel('Submit Suggestion')
        .setStyle(ButtonStyle.Primary)
        .setEmoji('💡')
    );

    await channel.send({ embeds: [embed], components: [row] });
    logger.info('Suggestions button posted successfully');
  } catch (error) {
    logger.error('Error posting suggestions button:', error);
  }
}

module.exports = {
  initializeSuggestions
};