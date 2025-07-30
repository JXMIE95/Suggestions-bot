const fs = require('fs');
const path = require('path');
const { Client, Collection, GatewayIntentBits } = require('discord.js');
const { token } = require('./config.json');
const logger = require('./utils/logger');
const db = require('./database/init'); // ✅ Add DB init

const client = new Client({
    intents: [GatewayIntentBits.Guilds, GatewayIntentBits.GuildMessages, GatewayIntentBits.MessageContent]
});

client.commands = new Collection();
const commandsPath = path.join(__dirname, 'commands');
const commandFiles = fs.readdirSync(commandsPath).filter(file => file.endsWith('.js'));

for (const file of commandFiles) {
    const filePath = path.join(commandsPath, file);
    const command = require(filePath);
    if (command.data && command.execute) {
        client.commands.set(command.data.name, command);
    } else {
        logger.warn(`Command at ${filePath} is missing "data" or "execute" property.`);
    }
}

const eventsPath = path.join(__dirname, 'events');
const eventFiles = fs.readdirSync(eventsPath).filter(file => file.endsWith('.js'));

for (const file of eventFiles) {
    const filePath = path.join(eventsPath, file);
    const event = require(filePath);
    if (event.once) {
        client.once(event.name, (...args) => event.execute(...args, client));
    } else {
        client.on(event.name, (...args) => event.execute(...args, client));
    }
}

// ✅ Initialize the database BEFORE starting the bot
db.init()
  .then(() => {
      logger.info('Database initialized. Logging in bot...');
      client.login(token);
  })
  .catch((err) => {
      logger.error('Failed to initialize database. Bot will not start.', err);
      process.exit(1); // Exit the process if DB fails
  });

// ✅ Improved uncaught exception logging
process.on('uncaughtException', (error) => {
    console.error('Uncaught Exception:', error);
    logger.error(`Uncaught Exception: ${error.stack || error.message || error}`);
});

process.on('unhandledRejection', (reason, promise) => {
    console.error('Unhandled Rejection at:', promise, 'reason:', reason);
    logger.error(`Unhandled Rejection: ${reason.stack || reason}`);
});