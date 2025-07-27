
const { SlashCommandBuilder, ChannelType, PermissionFlagsBits } = require('discord.js');
const fs = require('fs');
const path = require('path');

// Use a writable directory, such as inside /app/data or fallback to same dir
const configDir = path.join(__dirname, '..', 'data');
const configPath = path.join(configDir, 'config.json');

module.exports = {
  data: new SlashCommandBuilder()
    .setName('config')
    .setDescription('Configure bot settings')
    .setDefaultMemberPermissions(PermissionFlagsBits.Administrator)
    .addChannelOption(option =>
      option.setName('suggestions')
        .setDescription('Suggestions channel')
        .addChannelTypes(ChannelType.GuildText)
        .setRequired(true)
    )
    .addChannelOption(option =>
      option.setName('scheduler_category')
        .setDescription('Category for scheduler channels')
        .addChannelTypes(ChannelType.GuildCategory)
        .setRequired(true)
    )
    .addChannelOption(option =>
      option.setName('notifications')
        .setDescription('Channel for shift reminders')
        .addChannelTypes(ChannelType.GuildText)
        .setRequired(true)
    )
    .addRoleOption(option =>
      option.setName('king_role')
        .setDescription('Role for King')
        .setRequired(true)
    )
    .addRoleOption(option =>
      option.setName('buff_giver_role')
        .setDescription('Role for Buff Giver')
        .setRequired(true)
    ),

  async execute(interaction) {
    try {
      await interaction.deferReply({ ephemeral: true });

      const suggestionsChannel = interaction.options.getChannel('suggestions');
      const schedulerCategory = interaction.options.getChannel('scheduler_category');
      const notificationChannel = interaction.options.getChannel('notifications');
      const kingRole = interaction.options.getRole('king_role');
      const buffGiverRole = interaction.options.getRole('buff_giver_role');

      // Ensure directory exists
      if (!fs.existsSync(configDir)) {
        fs.mkdirSync(configDir, { recursive: true });
      }

      const config = {
        suggestionsChannelId: suggestionsChannel.id,
        scheduler: {
          enabled: true,
          categoryId: schedulerCategory.id,
          notificationChannelId: notificationChannel.id,
          kingRoleId: kingRole.id,
          buffGiverRoleId: buffGiverRole.id,
          notificationMinutes: 5,
          maxConcurrentUsers: 2
        }
      };

      fs.writeFileSync(configPath, JSON.stringify(config, null, 2));
      await interaction.editReply({ content: '✅ Configuration saved successfully!', ephemeral: true });

    } catch (error) {
      console.error('Error saving config:', error);
      try {
        await interaction.editReply({ content: '❌ Failed to save configuration.', ephemeral: true });
      } catch (err) {
        console.error('Secondary error replying to interaction:', err);
      }
    }
  }
};
