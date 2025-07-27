
const { Events } = require('discord.js');
const suggestions = require('../systems/suggestions');
const scheduler = require('../systems/scheduler');
const configCommand = require('../commands/config');

module.exports = {
    name: Events.InteractionCreate,
    async execute(interaction) {
        if (interaction.isChatInputCommand()) {
            if (interaction.commandName === 'config') {
                return configCommand.execute(interaction);
            }
        }

        if (interaction.isButton()) {
            if (interaction.customId === 'suggest_button') {
                return suggestions.handleSuggestionButton(interaction);
            }

            if (interaction.customId.startsWith('roster_')) {
                return scheduler.handleRosterButton(interaction);
            }

            if (interaction.customId.startsWith('shift_checkin_')) {
                return scheduler.handleShiftCheckin(interaction);
            }
        }

        if (interaction.isModalSubmit()) {
            if (interaction.customId.startsWith('suggest_modal')) {
                return suggestions.handleSuggestionModal(interaction);
            }

            if (interaction.customId.startsWith('roster_add_modal')) {
                return scheduler.handleRosterAddModal(interaction);
            }

            if (interaction.customId.startsWith('roster_edit_modal')) {
                return scheduler.handleRosterEditModal(interaction);
            }
        }

        if (interaction.isStringSelectMenu()) {
            if (interaction.customId.startsWith('roster_time_select_')) {
                return scheduler.handleRosterTimeSelect(interaction);
            }
        }
    },
};
