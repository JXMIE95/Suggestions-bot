
const { Events, ActivityType, ActionRowBuilder, ButtonBuilder, ButtonStyle } = require('discord.js');
const fs = require('fs');
const path = require('path');
const logger = require('../utils/logger');
const scheduler = require('../systems/scheduler');
const { initializeSuggestions } = require('../systems/suggestions');

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
        await initializeSuggestions(client);

        // Initialize scheduler channels
        await scheduler.initializeScheduler(client);
    },
};
