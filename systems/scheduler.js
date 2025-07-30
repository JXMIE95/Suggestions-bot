const { ChannelType, EmbedBuilder, ActionRowBuilder, ButtonBuilder, ButtonStyle } = require('discord.js');
const path = require('path');
const fs = require('fs');
const db = require('../database/init').getDatabase;
const logger = require('../utils/logger');

const configPath = path.join(__dirname, '..', 'config.json');

async function initializeScheduler(client) {
  try {
    const config = JSON.parse(fs.readFileSync(configPath, 'utf8'));
    if (!config.scheduler.enabled || !config.scheduler.categoryId) {
      logger.error('Configured scheduler categoryId is not a valid category.');
      return;
    }
    await createDailyChannels(client);
    logger.info('Scheduler initialized successfully');
  } catch (error) {
    logger.error('Error initializing scheduler:', error);
  }
}

async function createDailyChannels(client) {
  try {
    const config = JSON.parse(fs.readFileSync(configPath, 'utf8'));
    const guild = client.guilds.cache.first();
    const category = guild.channels.cache.get(config.scheduler.categoryId);

    if (!category || category.type !== ChannelType.GuildCategory) {
      logger.error('Configured scheduler categoryId is not a valid category.');
      return;
    }

    for (let i = 0; i < 7; i++) {
      const date = new Date();
      date.setUTCDate(date.getUTCDate() + i);
      const dateString = date.toISOString().split('T')[0];

      const existing = category.children.cache.find(c => c.name === dateString);
      if (!existing) {
        const channel = await guild.channels.create({
          name: dateString,
          type: ChannelType.GuildText,
          parent: category.id,
          topic: `Roster for ${dateString}`
        });

        await setupRosterMessage(channel, dateString);
        logger.info(`Created daily channel: ${dateString}`);
      }
    }
  } catch (error) {
    logger.error('Error creating daily channels:', error);
  }
}

async function setupRosterMessage(channel, date) {
  try {
    const embed = new EmbedBuilder()
      .setTitle(`📅 Roster for ${date}`)
      .setDescription('24-hour schedule (UTC time)')
      .setColor(0x00AE86)
      .setTimestamp();

    for (let hour = 0; hour < 24; hour++) {
      embed.addFields({
        name: `${hour.toString().padStart(2, '0')}:00 UTC`,
        value: 'No one scheduled',
        inline: true
      });
    }

    const row = new ActionRowBuilder().addComponents(
      new ButtonBuilder()
        .setCustomId(`roster_add_${date}`)
        .setLabel('Add Availability')
        .setStyle(ButtonStyle.Success)
        .setEmoji('➕'),
      new ButtonBuilder()
        .setCustomId(`roster_cancel_${date}`)
        .setLabel('Cancel Availability')
        .setStyle(ButtonStyle.Danger)
        .setEmoji('❌'),
      new ButtonBuilder()
        .setCustomId(`roster_edit_${date}`)
        .setLabel('Edit Availability')
        .setStyle(ButtonStyle.Secondary)
        .setEmoji('📝')
    );

    await channel.send({ embeds: [embed], components: [row] });
  } catch (error) {
    logger.error('Error setting up roster message:', error);
  }
}

// Placeholder handler implementations
async function handleRosterAdd(interaction) {
  await interaction.reply({ content: '📥 Add availability feature under construction.', ephemeral: true });
}

async function handleRosterEdit(interaction) {
  await interaction.reply({ content: '✏️ Edit availability feature under construction.', ephemeral: true });
}

async function handleRosterCancel(interaction) {
  await interaction.reply({ content: '❌ Cancel availability feature under construction.', ephemeral: true });
}

async function handleRosterConfirm(interaction) {
  await interaction.reply({ content: '✅ Confirm roster feature under construction.', ephemeral: true });
}

async function handleRosterCancelSelection(interaction) {
  await interaction.reply({ content: '❌ Selection cancelled.', ephemeral: true });
}

async function handleRosterTimeSelect(interaction) {
  await interaction.reply({ content: '🕐 Time slot selected (feature under construction).', ephemeral: true });
}

async function handleRosterAddModal(interaction) {
  await interaction.reply({ content: '📝 Modal form received (feature under construction).', ephemeral: true });
}

async function handleRosterEditModal(interaction) {
  await interaction.reply({ content: '✏️ Edit modal processed (feature under construction).', ephemeral: true });
}

async function handleShiftCheckin(interaction) {
  await interaction.reply({ content: '✅ Check-in confirmed (feature under construction).', ephemeral: true });
}

async function checkUpcomingShifts(client) {
  logger.info('🔔 Checking upcoming shifts... (feature under construction)');
}

module.exports = {
  initializeScheduler,
  createDailyChannels,
  setupRosterMessage,
  handleRosterAdd,
  handleRosterEdit,
  handleRosterCancel,
  handleRosterConfirm,
  handleRosterCancelSelection,
  handleRosterTimeSelect,
  handleRosterAddModal,
  handleRosterEditModal,
  handleShiftCheckin,
  checkUpcomingShifts
};