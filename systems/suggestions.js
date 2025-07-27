
const { ActionRowBuilder, ButtonBuilder, ButtonStyle, ChannelType } = require('discord.js');
const db = require('../database/init').getDatabase;
const logger = require('../utils/logger');

async function initializeSuggestions(client) {
    try {
        const config = await getConfig();
        if (!config || !config.suggestions || !config.suggestions.enabled || !config.suggestions.channelId) {
            logger.warn('Suggestions system not configured yet. Skipping button post.');
            return;
        }

        const channel = await client.channels.fetch(config.suggestions.channelId).catch(() => null);
        if (!channel || channel.type !== ChannelType.GuildText) {
            logger.error('Invalid or unknown suggestions channel. Skipping suggestions button post.');
            return;
        }

        const existing = await findExistingButtonMessage(channel);
        if (existing) {
            logger.info('Suggestions button already exists');
            return;
        }

        const row = new ActionRowBuilder().addComponents(
            new ButtonBuilder()
                .setCustomId('suggestion_button')
                .setLabel('Submit a Suggestion')
                .setStyle(ButtonStyle.Primary)
        );

        await channel.send({
            content: 'Got a suggestion? Click the button below!',
            components: [row]
        });

        logger.info('Suggestions button posted successfully');
    } catch (error) {
        logger.error('Error posting suggestions button:', error);
    }
}

async function findExistingButtonMessage(channel) {
    try {
        const messages = await channel.messages.fetch({ limit: 20 });
        return messages.find(
            msg =>
                msg.author.bot &&
                msg.components.length > 0 &&
                msg.components[0].components.find(btn => btn.customId === 'suggestion_button')
        );
    } catch (error) {
        return null;
    }
}

async function getConfig() {
    return new Promise((resolve, reject) => {
        db().get('SELECT * FROM config LIMIT 1', (err, row) => {
            if (err) return reject(err);
            try {
                const parsed = JSON.parse(row.config_json);
                resolve(parsed);
            } catch {
                resolve(null);
            }
        });
    });
}

module.exports = {
    initializeSuggestions
};
