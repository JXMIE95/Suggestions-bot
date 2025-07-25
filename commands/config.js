const { SlashCommandBuilder, EmbedBuilder, PermissionFlagsBits, ChannelType } = require('discord.js');
const fs = require('fs');
const path = require('path');
const logger = require('../utils/logger');

const configPath = path.join(__dirname, '..', 'config.json');

module.exports = {
    data: new SlashCommandBuilder()
        .setName('config')
        .setDescription('Configure bot settings')
        .setDefaultMemberPermissions(PermissionFlagsBits.Administrator)
        .addSubcommand(subcommand =>
            subcommand
                .setName('show')
                .setDescription('Show current configuration'))
        .addSubcommand(subcommand =>
            subcommand
                .setName('suggestions')
                .setDescription('Configure suggestions system')
                .addChannelOption(option =>
                    option.setName('submit_channel')
                        .setDescription('Channel where users submit suggestions')
                        .setRequired(false))
                .addChannelOption(option =>
                    option.setName('main_channel')
                        .setDescription('Channel where suggestions are posted for voting')
                        .setRequired(false))
                .addChannelOption(option =>
                    option.setName('staff_channel')
                        .setDescription('Channel where staff vote on suggestions')
                        .setRequired(false))
                .addChannelOption(option =>
                    option.setName('announcement_channel')
                        .setDescription('Channel where results are announced')
                        .setRequired(false))
                .addRoleOption(option =>
                    option.setName('main_role')
                        .setDescription('Role to notify for new suggestions')
                        .setRequired(false))
                .addRoleOption(option =>
                    option.setName('staff_role')
                        .setDescription('Role that votes on suggestions')
                        .setRequired(false))
                .addIntegerOption(option =>
                    option.setName('upvote_threshold')
                        .setDescription('Number of upvotes needed to send to staff')
                        .setMinValue(1)
                        .setRequired(false)))
        .addSubcommand(subcommand =>
            subcommand
                .setName('scheduler')
                .setDescription('Configure scheduler system')
                .addChannelOption(option =>
                    option.setName('category')
                        .setDescription('Category where daily channels are created')
                        .addChannelTypes(ChannelType.GuildCategory)
                        .setRequired(false))
                .addChannelOption(option =>
                    option.setName('notification_channel')
                        .setDescription('Channel for shift notifications')
                        .setRequired(false))
                .addRoleOption(option =>
                    option.setName('king_role')
                        .setDescription('King role for roster management')
                        .setRequired(false))
                .addRoleOption(option =>
                    option.setName('buff_giver_role')
                        .setDescription('Buff giver role')
                        .setRequired(false)))
        .addSubcommand(subcommand =>
            subcommand
                .setName('roles')
                .setDescription('Configure roles using role IDs')
                .addStringOption(option =>
                    option.setName('king_role_id')
                        .setDescription('King role ID')
                        .setRequired(false))
                .addStringOption(option =>
                    option.setName('buff_giver_role_id')
                        .setDescription('Buff giver role ID')
                        .setRequired(false))
                .addStringOption(option =>
                    option.setName('main_role_id')
                        .setDescription('Main role ID for suggestions')
                        .setRequired(false))
                .addStringOption(option =>
                    option.setName('staff_role_id')
                        .setDescription('Staff role ID for suggestions')
                        .setRequired(false))),

    async execute(interaction) {
        const subcommand = interaction.options.getSubcommand();
        logger.info(`Config subcommand: ${subcommand} by ${interaction.user.username}`);

        try {
            if (subcommand === 'show') {
                await showConfig(interaction);
            } else if (subcommand === 'suggestions') {
                await configureSuggestions(interaction);
            } else if (subcommand === 'scheduler') {
                await configureScheduler(interaction);
            } else if (subcommand === 'roles') {
                await configureRoles(interaction);
            }
        } catch (error) {
            logger.error(`Config command error: ${error.message}`, error);
            if (!interaction.replied) {
                await interaction.reply({ content: `Configuration error: ${error.message}`, flags: 64 });
            }
        }
    },
};

async function showConfig(interaction) {
    try {
        const config = JSON.parse(fs.readFileSync(configPath, 'utf8'));
        
        const embed = new EmbedBuilder()
            .setTitle('⚙️ Bot Configuration')
            .setColor(0x00AE86)
            .addFields(
                {
                    name: '📝 Suggestions System',
                    value: `Enabled: ${config.suggestions.enabled ? '✅' : '❌'}
                    Submit Channel: ${config.suggestions.submitChannelId ? `<#${config.suggestions.submitChannelId}>` : 'Not set'}
                    Main Channel: ${config.suggestions.mainChannelId ? `<#${config.suggestions.mainChannelId}>` : 'Not set'}
                    Staff Channel: ${config.suggestions.staffChannelId ? `<#${config.suggestions.staffChannelId}>` : 'Not set'}
                    Announcement Channel: ${config.suggestions.announcementChannelId ? `<#${config.suggestions.announcementChannelId}>` : 'Not set'}
                    Main Role: ${config.suggestions.mainRoleId ? `<@&${config.suggestions.mainRoleId}>` : 'Not set'}
                    Staff Role: ${config.suggestions.staffRoleId ? `<@&${config.suggestions.staffRoleId}>` : 'Not set'}
                    Upvote Threshold: ${config.suggestions.upvoteThreshold}`,
                    inline: false
                },
                {
                    name: '📅 Scheduler System',
                    value: `Enabled: ${config.scheduler.enabled ? '✅' : '❌'}
                    Category: ${config.scheduler.categoryId ? `<#${config.scheduler.categoryId}>` : 'Not set'}
                    Notification Channel: ${config.scheduler.notificationChannelId ? `<#${config.scheduler.notificationChannelId}>` : 'Not set'}
                    King Role: ${config.scheduler.kingRoleId ? `<@&${config.scheduler.kingRoleId}>` : 'Not set'}
                    Buff Giver Role: ${config.scheduler.buffGiverRoleId ? `<@&${config.scheduler.buffGiverRoleId}>` : 'Not set'}
                    Max Concurrent: ${config.scheduler.maxConcurrentUsers}`,
                    inline: false
                }
            )
            .setTimestamp();

        await interaction.reply({ embeds: [embed], flags: 64 }); // 64 = EPHEMERAL
    } catch (error) {
        logger.error('Error showing config:', error);
        await interaction.reply({ content: 'Error reading configuration.', flags: 64 });
    }
}

async function configureSuggestions(interaction) {
    try {
        const config = JSON.parse(fs.readFileSync(configPath, 'utf8'));
        let updated = false;

        const submitChannel = interaction.options.getChannel('submit_channel');
        const mainChannel = interaction.options.getChannel('main_channel');
        const staffChannel = interaction.options.getChannel('staff_channel');
        const announcementChannel = interaction.options.getChannel('announcement_channel');
        const mainRole = interaction.options.getRole('main_role');
        const staffRole = interaction.options.getRole('staff_role');
        const upvoteThreshold = interaction.options.getInteger('upvote_threshold');

        logger.info(`Config update attempt - MainRole: ${mainRole?.id}, StaffRole: ${staffRole?.id}`);

        if (submitChannel) {
            config.suggestions.submitChannelId = submitChannel.id;
            updated = true;
        }
        if (mainChannel) {
            config.suggestions.mainChannelId = mainChannel.id;
            updated = true;
        }
        if (staffChannel) {
            config.suggestions.staffChannelId = staffChannel.id;
            updated = true;
        }
        if (announcementChannel) {
            config.suggestions.announcementChannelId = announcementChannel.id;
            updated = true;
        }
        if (mainRole) {
            config.suggestions.mainRoleId = mainRole.id;
            updated = true;
        }
        if (staffRole) {
            config.suggestions.staffRoleId = staffRole.id;
            updated = true;
        }
        if (upvoteThreshold) {
            config.suggestions.upvoteThreshold = upvoteThreshold;
            updated = true;
        }

        if (updated) {
            fs.writeFileSync(configPath, JSON.stringify(config, null, 4));
            await interaction.reply({ content: '✅ Suggestions configuration updated successfully!', flags: 64 });
        } else {
            await interaction.reply({ content: 'No changes were made to the configuration.', flags: 64 });
        }
    } catch (error) {
        logger.error('Error configuring suggestions:', error);
        await interaction.reply({ content: `Error updating suggestions configuration: ${error.message}`, flags: 64 });
    }
}

async function configureScheduler(interaction) {
    try {
        const config = JSON.parse(fs.readFileSync(configPath, 'utf8'));
        let updated = false;

        const category = interaction.options.getChannel('category');
        const notificationChannel = interaction.options.getChannel('notification_channel');
        const kingRole = interaction.options.getRole('king_role');
        const buffGiverRole = interaction.options.getRole('buff_giver_role');

        logger.info(`Scheduler config - KingRole: ${kingRole?.name} (${kingRole?.id}), BuffGiverRole: ${buffGiverRole?.name} (${buffGiverRole?.id})`);
        logger.info(`User permissions: ${interaction.member.permissions.toArray().join(', ')}`);

        if (category) {
            config.scheduler.categoryId = category.id;
            updated = true;
        }
        if (notificationChannel) {
            config.scheduler.notificationChannelId = notificationChannel.id;
            updated = true;
        }
        if (kingRole) {
            logger.info(`Setting king role: ${kingRole.name} (${kingRole.id})`);
            config.scheduler.kingRoleId = kingRole.id;
            updated = true;
        }
        if (buffGiverRole) {
            logger.info(`Setting buff giver role: ${buffGiverRole.name} (${buffGiverRole.id})`);
            config.scheduler.buffGiverRoleId = buffGiverRole.id;
            updated = true;
        }

        if (updated) {
            fs.writeFileSync(configPath, JSON.stringify(config, null, 4));
            await interaction.reply({ content: '✅ Scheduler configuration updated successfully!', flags: 64 });
        } else {
            await interaction.reply({ content: 'No changes were made to the configuration.', flags: 64 });
        }
    } catch (error) {
        logger.error('Error configuring scheduler:', error);
        await interaction.reply({ content: `Error updating scheduler configuration: ${error.message}`, flags: 64 });
    }
}

async function configureRoles(interaction) {
    try {
        const config = JSON.parse(fs.readFileSync(configPath, 'utf8'));
        let updated = false;

        const kingRoleId = interaction.options.getString('king_role_id');
        const buffGiverRoleId = interaction.options.getString('buff_giver_role_id');
        const mainRoleId = interaction.options.getString('main_role_id');
        const staffRoleId = interaction.options.getString('staff_role_id');

        logger.info(`Role ID config - King: ${kingRoleId}, Buff: ${buffGiverRoleId}, Main: ${mainRoleId}, Staff: ${staffRoleId}`);

        if (kingRoleId) {
            config.scheduler.kingRoleId = kingRoleId;
            updated = true;
            logger.info(`Set king role ID: ${kingRoleId}`);
        }
        if (buffGiverRoleId) {
            config.scheduler.buffGiverRoleId = buffGiverRoleId;
            updated = true;
            logger.info(`Set buff giver role ID: ${buffGiverRoleId}`);
        }
        if (mainRoleId) {
            config.suggestions.mainRoleId = mainRoleId;
            updated = true;
            logger.info(`Set main role ID: ${mainRoleId}`);
        }
        if (staffRoleId) {
            config.suggestions.staffRoleId = staffRoleId;
            updated = true;
            logger.info(`Set staff role ID: ${staffRoleId}`);
        }

        if (updated) {
            fs.writeFileSync(configPath, JSON.stringify(config, null, 4));
            await interaction.reply({ content: '✅ Roles configured successfully using role IDs!', flags: 64 });
        } else {
            await interaction.reply({ content: 'No role IDs were provided to configure.', flags: 64 });
        }
    } catch (error) {
        logger.error('Error configuring roles:', error);
        await interaction.reply({ content: `Error configuring roles: ${error.message}`, flags: 64 });
    }
}
