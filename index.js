const { Client, GatewayIntentBits, Collection, ActivityType } = require('discord.js');
const fs = require('fs');
const path = require('path');
const cron = require('node-cron');
require('dotenv').config();

const logger = require('./utils/logger');
const db = require('./database/init');
const scheduler = require('./systems/scheduler');

// Initialize Discord client
const client = new Client({
    intents: [
        GatewayIntentBits.Guilds,
        GatewayIntentBits.GuildMessages,
        GatewayIntentBits.GuildMessageReactions,
        GatewayIntentBits.MessageContent,
        GatewayIntentBits.GuildMembers
    ]
});

// Initialize command collection
client.commands = new Collection();

// Load commands
const commandFiles = fs.readdirSync('./commands').filter(file => file.endsWith('.js'));
for (const file of commandFiles) {
    const command = require(`./commands/${file}`);
    client.commands.set(command.data.name, command);
}

// Load events
const eventFiles = fs.readdirSync('./events').filter(file => file.endsWith('.js'));
for (const file of eventFiles) {
    const event = require(`./events/${file}`);
    if (event.once) {
        client.once(event.name, (...args) => event.execute(...args, client));
    } else {
        client.on(event.name, (...args) => event.execute(...args, client));
    }
}

// Initialize database
db.init().then(() => {
    logger.info('Database initialized successfully');
}).catch(err => {
    logger.error('Failed to initialize database:', err);
    process.exit(1);
});

// Schedule daily channel creation and cleanup at midnight UTC
cron.schedule('0 0 * * *', () => {
    logger.info('Running daily scheduler maintenance');
    scheduler.createDailyChannels(client);
    scheduler.cleanupOldChannels(client);
}, {
    timezone: "UTC"
});

// Schedule notification checks every minute
cron.schedule('* * * * *', () => {
    scheduler.checkUpcomingShifts(client);
}, {
    timezone: "UTC"
});

// Error handling
process.on('unhandledRejection', (reason, promise) => {
    logger.error('Unhandled Rejection at:', promise, 'reason:', reason);
});

process.on('uncaughtException', (error) => {
    logger.error('Uncaught Exception:', error);
    process.exit(1);
});

// Login to Discord
client.login(process.env.DISCORD_TOKEN);
