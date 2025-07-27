
require('dotenv').config();
const fs = require('fs');
const path = require('path');
const { Client, Collection, GatewayIntentBits, Partials } = require('discord.js');
const logger = require('./utils/logger');
const { getDatabase } = require('./database/init');

// Create a new Discord client instance
const client = new Client({
    intents: [
        GatewayIntentBits.Guilds,
        GatewayIntentBits.GuildMessages,
        GatewayIntentBits.MessageContent,
        GatewayIntentBits.GuildMembers,
        GatewayIntentBits.GuildMessageReactions,
    ],
    partials: [Partials.Message, Partials.Channel, Partials.Reaction],
});

// Attach collections
client.commands = new Collection();
client.buttons = new Collection();
client.modals = new Collection();
client.selectMenus = new Collection();

// Load all command files
const commandsPath = path.join(__dirname, 'commands');
const commandFiles = fs.readdirSync(commandsPath).filter(file => file.endsWith('.js'));
for (const file of commandFiles) {
    const command = require(`./commands/${file}`);
    if (command.data && command.execute) {
        client.commands.set(command.data.name, command);
    } else {
        logger.warn(`[WARNING] The command at ${file} is missing "data" or "execute".`);
    }
}

// Event: ready
client.once('ready', async () => {
    logger.info(`Bot is ready! Logged in as ${client.user.tag}`);
    require('./events/ready')(client);
});

// Event: interactionCreate
const interactionHandler = require('./events/interactionCreate');
client.on('interactionCreate', interaction => interactionHandler(interaction, client));

// Connect to database
getDatabase();

// Login the bot
client.login(process.env.BOT_TOKEN);
