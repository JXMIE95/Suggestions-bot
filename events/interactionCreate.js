const { Events } = require('discord.js');
const { postSuggestionButton } = require('../systems/suggestions');
const { updateSchedulerConfig } = require('../systems/scheduler');
const config = require('../config.json');

module.exports = {
    name: Events.InteractionCreate,
    async execute(interaction) {
        if (interaction.isChatInputCommand()) {
            const { commandName } = interaction;

            if (commandName === 'help') {
                return interaction.reply({
                    content: '📘 **Help**\n\nUse `/config suggestions` to configure suggestions.\nUse `/config scheduler` to configure scheduling.\nUse `/config show` to display settings.',
                    ephemeral: true
                });
            }

            if (commandName === 'config') {
                const sub = interaction.options.getSubcommand();

                if (sub === 'show') {
                    const suggestionsConfig = config.suggestions;
                    const schedulerConfig = config.scheduler;
                    return interaction.reply({
                        content: `⚙️ **Current Config**\n\n` +
                                 `**Suggestions**\nEnabled: ${suggestionsConfig.enabled}\nSubmit Channel ID: ${suggestionsConfig.submitChannelId || 'Not set'}\n\n` +
                                 `**Scheduler**\nEnabled: ${schedulerConfig.enabled}\nCategory ID: ${schedulerConfig.categoryId || 'Not set'}\nMax Concurrent Users: ${schedulerConfig.maxConcurrentUsers || 'Not set'}`,
                        ephemeral: true
                    });
                }

                if (sub === 'suggestions') {
                    try {
                        await postSuggestionButton(interaction.client);
                        return interaction.reply({
                            content: '✅ Suggestions button posted or already exists.',
                            ephemeral: true
                        });
                    } catch (err) {
                        console.error(err);
                        return interaction.reply({
                            content: '❌ Failed to post suggestion button.',
                            ephemeral: true
                        });
                    }
                }

                if (sub === 'scheduler') {
                    try {
                        await updateSchedulerConfig(interaction);
                    } catch (err) {
                        console.error(err);
                        try {
                            await interaction.reply({ content: '❌ Error updating scheduler config.', ephemeral: true });
                        } catch {}
                    }
                }
            }
        }
    }
};