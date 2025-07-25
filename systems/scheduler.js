
const { EmbedBuilder, ActionRowBuilder, ButtonBuilder, ButtonStyle, ModalBuilder, TextInputBuilder, TextInputStyle, ChannelType, StringSelectMenuBuilder, StringSelectMenuOptionBuilder } = require('discord.js');
const fs = require('fs');
const path = require('path');
const db = require('../database/init').getDatabase;
const logger = require('../utils/logger');

const configPath = path.join(__dirname, '..', 'config.json');

// Temporary storage for user selections during multi-step process
const userSelections = new Map();

async function initializeScheduler(client) {
    try {
        await createDailyChannels(client);
        logger.info('Scheduler initialized successfully');
    } catch (error) {
        logger.error('Error initializing scheduler:', error);
    }
}

async function createDailyChannels(client) {
    const config = JSON.parse(fs.readFileSync(configPath, 'utf8'));
    if (!config.scheduler.enabled || !config.scheduler.categoryId) return;

    const guild = client.guilds.cache.first();
    const category = guild.channels.cache.get(config.scheduler.categoryId);
    if (!category) return;

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
                .setEmoji('✏️')
        );

    await channel.send({ embeds: [embed], components: [row] });
}

async function handleRosterStartTime(interaction) {
    const userId = interaction.user.id;
    const date = interaction.customId.split('_').slice(-1)[0];
    const startTime = interaction.values[0];

    if (!userSelections.has(userId)) {
        userSelections.set(userId, { startTime: null, endTime: null, date });
    }

    const selection = userSelections.get(userId);
    selection.startTime = startTime;

    await interaction.reply({
        content: `✅ Start time set to ${startTime}. Now select an end time.`,
        ephemeral: true
    });
}

async function handleRosterEndTime(interaction) {
    const userId = interaction.user.id;
    const date = interaction.customId.split('_').slice(-1)[0];
    const endTime = interaction.values[0];

    const selection = userSelections.get(userId);
    if (!selection || !selection.startTime) {
        await interaction.reply({ content: 'Please select a start time first.', ephemeral: true });
        return;
    }

    selection.endTime = endTime;

    const startHour = parseInt(selection.startTime.split(':')[0]);
    const endHour = parseInt(endTime.split(':')[0]);

    if (endHour < startHour) {
        await interaction.reply({ content: 'End time must be after start time.', ephemeral: true });
        return;
    }

    selection.timeSlots = [];
    for (let h = startHour; h <= endHour; h++) {
        const slot = h.toString().padStart(2, '0') + ':00';
        selection.timeSlots.push(slot);
    }

    await interaction.reply({
        content: `✅ Selected hours: ${selection.timeSlots.join(', ')}
Click "Confirm Selection" to finalize.`,
        ephemeral: true
    });
}

// Placeholder stubs for other expected exports
async function handleRosterAdd() {}
async function handleRosterAddModal() {}
async function handleRosterTimeSelect() {}
async function handleRosterConfirm() {}
async function handleRosterCancelSelection() {}
async function handleRosterCancel() {}
async function handleRosterEdit() {}
async function handleRosterEditModal() {}
async function handleShiftCheckin() {}
async function checkUpcomingShifts() {}

module.exports = {
    initializeScheduler,
    createDailyChannels,
    setupRosterMessage,
    handleRosterAdd,
    handleRosterAddModal,
    handleRosterTimeSelect,
    handleRosterConfirm,
    handleRosterCancelSelection,
    handleRosterCancel,
    handleRosterEdit,
    handleRosterEditModal,
    handleShiftCheckin,
    checkUpcomingShifts,
    handleRosterStartTime,
    handleRosterEndTime
};
