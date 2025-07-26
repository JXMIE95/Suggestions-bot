
const { Events } = require('discord.js');
const { postSuggestionButton } = require('../systems/suggestions');
const config = require('../config.json');

module.exports = {
    name: Events.InteractionCreate,
    async execute(interaction) {
        if (interaction.isChatInputCommand()) {
            const { commandName } = interaction;

            if (commandName === 'help') {
                return interaction.reply({
                    content: '📘 **Help**\n\nUse `/config suggestions` to configure suggestions.\nUse `/config show` to display current settings.\nUse the suggestions button to submit your ideas!',
                    ephemeral: true
                });
            }

            if (commandName === 'config') {
                const sub = interaction.options.getSubcommand();

                if (sub === 'show') {
                    const suggestionsConfig = config.suggestions;
                    return interaction.reply({
                        content: `⚙️ **Suggestions Config**\n\nEnabled: ${suggestionsConfig.enabled}\nSubmit Channel ID: ${suggestionsConfig.submitChannelId || 'Not set'}`,
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
            }
        }
    }
};
