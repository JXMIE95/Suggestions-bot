const { Events } = require('discord.js');
const logger = require('../utils/logger');
const suggestions = require('../systems/suggestions');
const scheduler = require('../systems/scheduler');

module.exports = {
    name: Events.InteractionCreate,
    async execute(interaction) {
        try {
            if (interaction.isChatInputCommand()) {
                logger.info(`Command received: ${interaction.commandName} by ${interaction.user.username}`);
                const command = interaction.client.commands.get(interaction.commandName);
                
                if (!command) {
                    logger.warn(`No command matching ${interaction.commandName} was found.`);
                    return;
                }

                await command.execute(interaction);
            } else if (interaction.isButton()) {
                await handleButtonInteraction(interaction);
            } else if (interaction.isModalSubmit()) {
                await handleModalSubmit(interaction);
            } else if (interaction.isStringSelectMenu()) {
                await handleSelectMenuInteraction(interaction);
            }
        } catch (error) {
            logger.error('Error handling interaction:', error);
            
            const errorMessage = { content: 'There was an error while executing this command!', flags: 64 };
            
            if (interaction.replied || interaction.deferred) {
                await interaction.followUp(errorMessage);
            } else {
                await interaction.reply(errorMessage);
            }
        }
    },
};

async function handleButtonInteraction(interaction) {
    const { customId } = interaction;

    if (customId === 'submit_suggestion') {
        await suggestions.handleSubmitButton(interaction);
    } else if (customId.startsWith('staff_approve_') || customId.startsWith('staff_reject_')) {
        await suggestions.handleStaffVote(interaction);
    } else if (customId.startsWith('roster_add_')) {
        await scheduler.handleRosterAdd(interaction);
    } else if (customId.startsWith('roster_cancel_')) {
        await scheduler.handleRosterCancel(interaction);
    } else if (customId.startsWith('roster_edit_')) {
        await scheduler.handleRosterEdit(interaction);
    } else if (customId.startsWith('roster_confirm_')) {
        await scheduler.handleRosterConfirm(interaction);
    } else if (customId.startsWith('roster_cancel_selection_')) {
        await scheduler.handleRosterCancelSelection(interaction);
    } else if (customId.startsWith('shift_checkin_')) {
        await scheduler.handleShiftCheckin(interaction);
    } else {
        logger.warn(`Unknown button interaction: ${customId}`);
    }
}

async function handleModalSubmit(interaction) {
    const { customId } = interaction;

    if (customId === 'suggestion_modal') {
        await suggestions.handleSuggestionSubmit(interaction);
    } else if (customId.startsWith('roster_add_modal_')) {
        await scheduler.handleRosterAddModal(interaction);
    } else if (customId.startsWith('roster_edit_modal_')) {
        await scheduler.handleRosterEditModal(interaction);
    } else {
        logger.warn(`Unknown modal submission: ${customId}`);
    }
}

async function handleSelectMenuInteraction(interaction) {
    const { customId } = interaction;

    if (customId.startsWith('roster_time_select_')) {
        await scheduler.handleRosterTimeSelect(interaction);
    } else {
        logger.warn(`Unknown select menu interaction: ${customId}`);
    }
}
