const { EmbedBuilder, ActionRowBuilder, ButtonBuilder, ButtonStyle, ChannelType } = require('discord.js');
const fs = require('fs');
const path = require('path');
const db = require('../database/init').getDatabase;
const logger = require('../utils/logger');

const configPath = path.join(__dirname, '..', 'config.json');

async function initializeScheduler(client) {
    try {
        if (!fs.existsSync(configPath)) {
            logger.warn('No config file found. Skipping scheduler setup.');
            return;
        }

        const config = JSON.parse(fs.readFileSync(configPath, 'utf8'));
        if (!config.scheduler?.enabled || !config.scheduler.categoryId) {
            logger.warn('Scheduler not enabled or missing categoryId. Skipping scheduler setup.');
            return;
        }

        const guild = client.guilds.cache.first();
        const category = guild.channels.cache.get(config.scheduler.categoryId);
        if (!category || category.type !== ChannelType.GuildCategory) {
            logger.error('Configured scheduler categoryId is not a valid category.');
            return;
        }

        for (let i = 0; i < 7; i++) {
            const date = new Date();
            date.setUTCDate(date.getUTCDate() + i);
            const dateString = date.toISOString().split('T')[0];

            const existingChannel = category.children.cache.find(channel => channel.name === dateString);
            if (!existingChannel) {
                const channel = await guild.channels.create({
                    name: dateString,
                    type: ChannelType.GuildText,
                    parent: category.id,
                    topic: `Roster for ${dateString}`
                });

                await setupRosterMessage(channel, dateString);
                logger.info(`Created daily channel: ${dateString}`);
            }
        }

        logger.info('Scheduler initialized successfully');
    } catch (error) {
        logger.error('Error initializing scheduler:', error);
    }
}

async function setupRosterMessage(channel, date) {
    const embed = new EmbedBuilder()
        .setTitle(`📅 Roster for ${date}`)
        .setDescription('24-hour schedule (UTC time)')
        .setColor(0x00AE86)
        .setTimestamp();

    for (let hour = 0; hour < 24; hour++) {
        const time = hour.toString().padStart(2, '0') + ':00';
        embed.addFields({ name: `${time} UTC`, value: 'No one scheduled', inline: true });
    }

    const row = new ActionRowBuilder()
        .addComponents(
            new ButtonBuilder()
                .setCustomId(`roster_add_${date}`)
                .setLabel('Add Availability')
                .setStyle(ButtonStyle.Success)
                .setEmoji('➕'),
            new ButtonBuilder()
                .setCustomId(`roster_cancel_${date}`)
                .setLabel('Cancel Availability')
                .setStyle(ButtonStyle.Danger)
                .setEmoji('❌'),
            new ButtonBuilder()
                .setCustomId(`roster_edit_${date}`)
                .setLabel('Edit Availability')
                .setStyle(ButtonStyle.Secondary)
                .setEmoji('✍️')
        );

    await channel.send({
        embeds: [embed],
        components: [row]
    });
}

module.exports = {
    initializeScheduler
};

module.exports = {
    initializeScheduler,
    createDailyChannels,
    cleanupOldChannels,
    handleRosterAdd,
    handleRosterAddModal,
    handleRosterTimeSelect,
    handleRosterConfirm,
    handleRosterCancelSelection,
    handleRosterCancel,
    handleRosterEdit,
    handleRosterEditModal,
    handleShiftCheckin,
    checkUpcomingShifts
};