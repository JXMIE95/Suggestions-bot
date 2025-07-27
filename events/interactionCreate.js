
const { Events } = require('discord.js');
const { updateSuggestionsConfig } = require('../commands/suggestions');
const { updateSchedulerConfig } = require('../commands/scheduler');
const { updateConfig } = require('../commands/config');

module.exports = {
    name: Events.InteractionCreate,
    async execute(interaction) {
        if (interaction.isChatInputCommand()) {
            const { commandName } = interaction;

            if (commandName === 'config') {
                const sub = interaction.options.getSubcommand();
                if (sub === 'suggestions') {
                    try {
                        return await updateSuggestionsConfig(interaction);
                    } catch (err) {
                        console.error(err);
                        try {
                            return await interaction.reply({ content: '❌ Error updating suggestions config.', ephemeral: true });
                        } catch {}
                    }
                }

                if (sub === 'scheduler') {
                    try {
                        return await updateSchedulerConfig(interaction);
                    } catch (err) {
                        console.error(err);
                        try {
                            return await interaction.reply({ content: '❌ Error updating scheduler config.', ephemeral: true });
                        } catch {}
                    }
                }

                try {
                    return await updateConfig(interaction);
                } catch (err) {
                    console.error(err);
                    try {
                        return await interaction.reply({ content: '❌ Error updating config.', ephemeral: true });
                    } catch {}
                }
            }
        }
    }
};
