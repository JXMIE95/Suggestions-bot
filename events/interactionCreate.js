
const {
    handleRosterAdd,
    handleRosterAddModal,
    handleRosterTimeSelect,
    handleRosterConfirm,
    handleRosterCancelSelection,
    handleRosterCancel,
    handleRosterEdit,
    handleRosterEditModal,
    handleShiftCheckin,
    handleRosterStartTime,
    handleRosterEndTime
} = require('../systems/scheduler');

module.exports = {
    name: 'interactionCreate',
    async execute(interaction, client) {
        try {
            if (interaction.isButton()) {
                if (interaction.customId.startsWith('roster_add_')) return handleRosterAdd(interaction);
                if (interaction.customId.startsWith('roster_confirm_')) return handleRosterConfirm(interaction);
                if (interaction.customId.startsWith('roster_cancel_selection_')) return handleRosterCancelSelection(interaction);
                if (interaction.customId.startsWith('roster_cancel_')) return handleRosterCancel(interaction);
                if (interaction.customId.startsWith('roster_edit_')) return handleRosterEdit(interaction);
                if (interaction.customId.startsWith('shift_checkin_')) return handleShiftCheckin(interaction);
            }

            if (interaction.isModalSubmit()) {
                if (interaction.customId.startsWith('roster_edit_modal_')) return handleRosterEditModal(interaction);
                if (interaction.customId.startsWith('roster_add_modal_')) return handleRosterAddModal(interaction);
            }

            if (interaction.isStringSelectMenu()) {
                if (interaction.customId.startsWith('roster_time_select_')) return handleRosterTimeSelect(interaction);
                if (interaction.customId.startsWith('roster_start_time_select')) return handleRosterStartTime(interaction);
                if (interaction.customId.startsWith('roster_end_time_select')) return handleRosterEndTime(interaction);
            }
        } catch (error) {
            console.error('Interaction handler error:', error);
            if (interaction.replied || interaction.deferred) {
                await interaction.followUp({ content: 'There was an error handling your action.', ephemeral: true });
            } else {
                await interaction.reply({ content: 'There was an error handling your action.', ephemeral: true });
            }
        }
    }
};
