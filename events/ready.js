const { Events, ActivityType, ActionRowBuilder, ButtonBuilder, ButtonStyle } = require('discord.js');
const fs = require('fs');
const path = require('path');
const logger = require('../utils/logger');
const scheduler = require('../systems/scheduler');

module.exports = {
    name: Events.ClientReady,
    once: true,
    async execute(client) {
        logger.info(`Bot is ready! Logged in as ${client.user.tag}`);
        
        // Set bot status
        client.user.setActivity('Managing suggestions and schedules', { type: ActivityType.Watching });

        // Register slash commands
        try {
            const commands = [];
            const commandFiles = fs.readdirSync(path.join(__dirname, '..', 'commands')).filter(file => file.endsWith('.js'));

            for (const file of commandFiles) {
                const command = require(`../commands/${file}`);
                commands.push(command.data.toJSON());
            }

            await client.application.commands.set(commands);
            logger.info('Successfully registered application commands');
        } catch (error) {
            logger.error('Error registering commands:', error);
        }

        // Setup suggestions button in configured channel
        await setupSuggestionsButton(client);

        // Initialize scheduler channels
        await scheduler.initializeScheduler(client);
    },
};

async function setupSuggestionsButton(client) {
    try {
        const config = JSON.parse(fs.readFileSync(path.join(__dirname, '..', 'config.json'), 'utf8'));
        
        if (!config.suggestions.enabled || !config.suggestions.submitChannelId) {
            return;
        }

        const channel = await client.channels.fetch(config.suggestions.submitChannelId);
        if (!channel) {
            logger.warn('Suggestions submit channel not found');
            return;
        }

        // Check if button message already exists
        const messages = await channel.messages.fetch({ limit: 10 });
        const existingMessage = messages.find(msg => 
            msg.author.id === client.user.id && 
            msg.components.length > 0 &&
            msg.components[0].components.some(comp => comp.customId === 'submit_suggestion')
        );

        if (existingMessage) {
            logger.info('Suggestions button already exists');
            return;
        }

        const row = new ActionRowBuilder()
            .addComponents(
                new ButtonBuilder()
                    .setCustomId('submit_suggestion')
                    .setLabel('Submit Suggestion')
                    .setStyle(ButtonStyle.Primary)
                    .setEmoji('ð')
            );

        await channel.send({
            content: '**ð¡ Submit Your Suggestions**\n\nClick the button below to submit a suggestion for the community to vote on!',
            components: [row]
        });

        logger.info('Suggestions button created successfully');
    } catch (error) {
        logger.error('Error setting up suggestions button:', error);
    }
}
