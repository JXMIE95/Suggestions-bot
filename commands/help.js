const { SlashCommandBuilder, EmbedBuilder } = require('discord.js');

module.exports = {
    data: new SlashCommandBuilder()
        .setName('help')
        .setDescription('Display help information about the bot'),
    
    async execute(interaction) {
        const embed = new EmbedBuilder()
            .setTitle('🤖 Discord Bot Help')
            .setDescription('Comprehensive Discord bot with suggestions voting and scheduling systems')
            .setColor(0x00AE86)
            .addFields(
                {
                    name: '📝 Suggestions System',
                    value: `• Use the "Submit Suggestion" button in the suggestions channel
                    • Members vote with 👍🏻/👎 reactions
                    • Staff vote on approved suggestions with ✅/❌
                    • Results are announced automatically`,
                    inline: false
                },
                {
                    name: '📅 Scheduler System',
                    value: `• Daily channels auto-generated for roster management
                    • 24-hour time slots (00:00-23:00 UTC)
                    • Add/Cancel/Edit availability with buttons
                    • 5-minute shift notifications
                    • Max 2 people per time slot`,
                    inline: false
                },
                {
                    name: '⚙️ Commands',
                    value: `• \`/help\` - Show this help menu
                    • \`/config\` - Configure bot settings (Admin only)`,
                    inline: false
                }
            )
            .setTimestamp()
            .setFooter({ text: 'Discord Bot v1.0' });

        await interaction.reply({ embeds: [embed], ephemeral: true });
    },
};
