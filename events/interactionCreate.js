
const { Events } = require('discord.js');
const suggestions = require('../systems/suggestions');
const scheduler = require('../systems/scheduler');

module.exports = {
    name: Events.InteractionCreate,
    async execute(interaction) {
        try {
            if (interaction.isButton()) {
                if (interaction.customId.startsWith('suggest_')) {
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
            } else if (interaction.isModalSubmit()) {
                if (interaction.customId.startsWith('roster_add_modal_')) {
                    await scheduler.handleRosterAddModal(interaction);
                } else if (interaction.customId.startsWith('roster_edit_modal_')) {
                    await scheduler.handleRosterEditModal(interaction);
                }
            } else if (interaction.isStringSelectMenu()) {
                if (interaction.customId.startsWith('roster_time_select_')) {
                    await scheduler.handleRosterTimeSelect(interaction);
                }
            }
        } catch (err) {
            console.error('[ERROR] Uncaught Exception:', err);
        }
    }
};
