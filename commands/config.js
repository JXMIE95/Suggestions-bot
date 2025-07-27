
const { SlashCommandBuilder, ChannelType } = require('discord.js');
const fs = require('fs');
const config = require('../config.json');
const { postSuggestionButton } = require('../systems/suggestions');

function saveConfig() {
    fs.writeFileSync('./config.json', JSON.stringify(config, null, 2));
}

async function showConfig(interaction) {
    const embed = {
        title: 'Current Configuration',
        fields: [
            {
                name: 'Suggestions',
                value: `Enabled: ${config.suggestions.enabled}\nSubmit Channel: <#${config.suggestions.submitChannelId}>`
            },
            {
                name: 'Scheduler',
                value: `Enabled: ${config.scheduler.enabled}\nCategory ID: ${config.scheduler.categoryId}\nNotification Channel: <#${config.scheduler.notificationChannelId}>\nKing Role: <@&${config.scheduler.kingRoleId}>\nBuff Giver Role: <@&${config.scheduler.buffGiverRoleId}>`
            }
        ]
    };

    await interaction.reply({ embeds: [embed], ephemeral: true });
}

async function configureSuggestions(interaction) {
    const channel = interaction.options.getChannel('submit-channel');
    const enabled = interaction.options.getBoolean('enabled');

    config.suggestions.submitChannelId = channel.id;
    config.suggestions.enabled = enabled;

    saveConfig();

    try {
        await postSuggestionButton(interaction.client);
        await interaction.reply({ content: '✅ Suggestions config saved and button posted!', ephemeral: true });
    } catch (err) {
        console.error(err);
        await interaction.reply({ content: '❌ Config saved, but failed to post button.', ephemeral: true });
    }
}

async function configureScheduler(interaction) {
    const category = interaction.options.getChannel('category');
    const notifyChannel = interaction.options.getChannel('notification-channel');
    const kingRole = interaction.options.getRole('king-role');
    const buffRole = interaction.options.getRole('buff-giver-role');

    config.scheduler.enabled = true;
    config.scheduler.categoryId = category.id;
    config.scheduler.notificationChannelId = notifyChannel.id;
    config.scheduler.kingRoleId = kingRole.id;
    config.scheduler.buffGiverRoleId = buffRole.id;

    saveConfig();
    await interaction.reply({ content: '✅ Scheduler configuration saved!', ephemeral: true });
}

async function configureRoles(interaction) {
    const kingRole = interaction.options.getRole('king-role');
    const buffRole = interaction.options.getRole('buff-giver-role');

    config.scheduler.kingRoleId = kingRole.id;
    config.scheduler.buffGiverRoleId = buffRole.id;

    saveConfig();
    await interaction.reply({ content: '✅ Roles updated successfully.', ephemeral: true });
}

module.exports = {
    data: new SlashCommandBuilder()
        .setName('config')
        .setDescription('Manage bot configuration')
        .addSubcommand(sub =>
            sub.setName('show')
                .setDescription('Show current configuration'))
        .addSubcommand(sub =>
            sub.setName('suggestions')
                .setDescription('Configure suggestion system')
                .addChannelOption(opt =>
                    opt.setName('submit-channel')
                        .setDescription('Channel for suggestion submissions')
                        .addChannelTypes(ChannelType.GuildText)
                        .setRequired(true))
                .addBooleanOption(opt =>
                    opt.setName('enabled')
                        .setDescription('Enable or disable suggestions')
                        .setRequired(true)))
        .addSubcommand(sub =>
            sub.setName('scheduler')
                .setDescription('Configure scheduler system')
                .addChannelOption(opt =>
                    opt.setName('category')
                        .setDescription('Category for daily channels')
                        .addChannelTypes(ChannelType.GuildCategory)
                        .setRequired(true))
                .addChannelOption(opt =>
                    opt.setName('notification-channel')
                        .setDescription('Channel to post shift reminders')
                        .addChannelTypes(ChannelType.GuildText)
                        .setRequired(true))
                .addRoleOption(opt =>
                    opt.setName('king-role')
                        .setDescription('Role ID for King')
                        .setRequired(true))
                .addRoleOption(opt =>
                    opt.setName('buff-giver-role')
                        .setDescription('Role ID for Buff Giver')
                        .setRequired(true)))
        .addSubcommand(sub =>
            sub.setName('roles')
                .setDescription('Update role IDs')
                .addRoleOption(opt =>
                    opt.setName('king-role')
                        .setDescription('Role for King')
                        .setRequired(true))
                .addRoleOption(opt =>
                    opt.setName('buff-giver-role')
                        .setDescription('Role for Buff Giver')
                        .setRequired(true))),
    async execute(interaction) {
        const subcommand = interaction.options.getSubcommand();

        if (subcommand === 'show') {
            await showConfig(interaction);
        } else if (subcommand === 'suggestions') {
            await configureSuggestions(interaction);
        } else if (subcommand === 'scheduler') {
            await configureScheduler(interaction);
        } else if (subcommand === 'roles') {
            await configureRoles(interaction);
        }
    }
};
