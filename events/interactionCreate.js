const { Events } = require('discord.js');
const suggestions = require('../systems/suggestions');
const scheduler = require('../systems/scheduler');

module.exports = {
    name: Events.InteractionCreate,
    async execute(interaction) {
        try {
            if (interaction.isCommand()) {
                const command = interaction.client.commands.get(interaction.commandName);
                if (!command) return;
                await command.execute(interaction);
            }

            if (interaction.isButton()) {
                if (interaction.customId === 'confirm_availability') {
                    await scheduler.handleConfirmAvailability(interaction);
                } else if (interaction.customId.startsWith('suggest_')) {
                    await suggestions.handleSuggestion(interaction);
                } else if (interaction.customId.startsWith('roster_add_')) {
                    await scheduler.handleRosterAdd(interaction);
                } else if (interaction.customId.startsWith('roster_cancel_')) {
                    await scheduler.handleRosterCancel(interaction);
                } else if (interaction.customId.startsWith('roster_edit_')) {
                    await scheduler.handleRosterEdit(interaction);
                } else if (interaction.customId.startsWith('roster_confirm_')) {
                    await scheduler.handleRosterConfirm(interaction);
                } else if (interaction.customId.startsWith('roster_cancel_selection_')) {
                    await scheduler.handleRosterCancelSelection(interaction);
                } else if (interaction.customId.startsWith('shift_checkin_')) {
                    await scheduler.handleShiftCheckin(interaction);
                }
            }

            if (interaction.isModalSubmit()) {
                if (interaction.customId.startsWith('roster_add_modal_')) {
                    await scheduler.handleRosterAddModal(interaction);
                } else if (interaction.customId.startsWith('roster_edit_modal_')) {
                    await scheduler.handleRosterEditModal(interaction);
                }
            }

            if (interaction.isStringSelectMenu()) {
                 if (interaction.customId === 'select_date') {
                    await scheduler.handleSelectDate(interaction);
                } else if (interaction.customId === 'select_start') {
                    await scheduler.handleSelectStart(interaction);
                } else if (interaction.customId === 'select_end') {
                    await scheduler.handleSelectEnd(interaction);
                } else if (interaction.customId.startsWith('roster_time_select_')) {
                    await scheduler.handleRosterTimeSelect(interaction);
                }
            }
            
        } catch (err) {
            console.error('[ERROR] Uncaught Exception:', err);
        }
    }
};