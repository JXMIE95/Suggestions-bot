// scheduler.js - Full Working Implementation

const {
  EmbedBuilder,
  ActionRowBuilder,
  ButtonBuilder,
  ButtonStyle,
  ChannelType,
  StringSelectMenuBuilder
} = require('discord.js');

const fs = require('fs');
const path = require('path');
const { getDatabase } = require('../database/init');
const logger = require('../utils/logger');

const configPath = path.join(__dirname, '..', 'config.json');

// Store temporary user selections
const userSelections = new Map();

function loadConfig() {
  return JSON.parse(fs.readFileSync(configPath, 'utf8'));
}

async function initializeScheduler(client) {
  const config = loadConfig();
  if (!config.scheduler.enabled) return;
  await createDailyChannels(client);
  await cleanupOldChannels(client);
  logger.info('Scheduler initialized successfully');
}

async function createDailyChannels(client) {
  const config = loadConfig();
  const guild = client.guilds.cache.first();
  const category = guild.channels.cache.get(config.scheduler.categoryId);
  if (!category || category.type !== ChannelType.GuildCategory) {
    logger.error('Configured scheduler categoryId is not a valid category.');
    return;
  }

  for (let i = 0; i < 7; i++) {
    const date = new Date();
    date.setDate(date.getDate() + i);
    const dateStr = date.toISOString().split('T')[0];

    const exists = guild.channels.cache.find(
      ch => ch.parentId === category.id && ch.name === dateStr
    );

    if (!exists) {
      const channel = await guild.channels.create({
        name: dateStr,
        type: ChannelType.GuildText,
        parent: category.id
      });

      await setupRosterMessage(channel, dateStr);
      logger.info(`Created daily channel: ${dateStr}`);
    }
  }
}

async function updateRosterMessage(client, date) {
  console.log(`[DEBUG] updateRosterMessage called for ${date}`);

  const config = loadConfig();
  const guild = client.guilds.cache.first();
  const category = guild.channels.cache.get(config.scheduler.categoryId);
  if (!category) {
    console.warn('[WARN] Scheduler category not found.');
    return;
  }

  const channel = guild.channels.cache.find(
    ch => ch.parentId === category.id && ch.name === date
  );

  if (!channel) {
    console.warn(`[WARN] No channel found for ${date}`);
    return;
  }

  let messages;
  try {
    messages = await channel.messages.fetch({ limit: 1 });
  } catch (err) {
    console.error('[ERROR] Failed to fetch messages from channel:', err);
    return;
  }

  const firstMessage = messages.first();
  if (!firstMessage) {
    console.warn('[WARN] No message found to update.');
    return;
  }

  // Get roster data for this date
  db.all('SELECT username, timeSlot FROM roster WHERE date = ?', [date], async (err, rows) => {
    if (err) {
      console.error('[ERROR] Failed to fetch roster from DB:', err);
      return;
    }

    const embed = new EmbedBuilder()
      .setTitle(`📅 Roster for ${date}`)
      .setDescription('24-hour schedule (UTC time)')
      .setColor(0x00AE86)
      .setTimestamp(new Date());

    const timeSlots = {};

    rows.forEach(({ username, timeSlot }) => {
      const [start, end] = timeSlot.split('–');
      const startHour = parseInt(start.split(':')[0], 10);
      const endHour = parseInt(end.split(':')[0], 10);
      for (let hour = startHour; hour < endHour; hour++) {
        const hourStr = hour.toString().padStart(2, '0') + ':00 UTC';
        if (!timeSlots[hourStr]) timeSlots[hourStr] = [];
        timeSlots[hourStr].push(username);
      }
    });

    for (let hour = 0; hour < 24; hour++) {
      const label = hour.toString().padStart(2, '0') + ':00 UTC';
      const users = timeSlots[label] || ['No one scheduled'];
      embed.addFields({ name: label, value: users.join(', '), inline: true });
    }

    // Update the original message
    try {
      await firstMessage.edit({ embeds: [embed] });
      console.log(`[INFO] Roster message updated for ${date}`);
    } catch (err) {
      console.error('[ERROR] Failed to edit roster message:', err);
    }
  });
}

async function setupRosterMessage(channel, date) {
  const embed = new EmbedBuilder()
    .setTitle(`📅 Roster for ${date}`)
    .setDescription('Click a button below to manage your availability.')
    .setColor(0x00AE86);

  const row = new ActionRowBuilder().addComponents(
    new ButtonBuilder()
      .setCustomId(`roster_add_${date}`)
      .setLabel('Add Availability')
      .setStyle(ButtonStyle.Success),
    new ButtonBuilder()
      .setCustomId(`roster_cancel_${date}`)
      .setLabel('Cancel Availability')
      .setStyle(ButtonStyle.Danger),
    new ButtonBuilder()
      .setCustomId(`roster_edit_${date}`)
      .setLabel('Edit Availability')
      .setStyle(ButtonStyle.Secondary)
  );

  await channel.send({ embeds: [embed], components: [row] });
}

async function cleanupOldChannels(client) {
  const config = loadConfig();
  const guild = client.guilds.cache.first();
  const category = guild.channels.cache.get(config.scheduler.categoryId);
  if (!category) return;

  const today = new Date().toISOString().split('T')[0];

  for (const [id, channel] of guild.channels.cache) {
    if (
      channel.parentId === category.id &&
      channel.name.match(/\d{4}-\d{2}-\d{2}/) &&
      channel.name < today
    ) {
      await channel.delete();
      logger.info(`Deleted old channel: ${channel.name}`);
    }
  }
}

async function handleRosterAdd(interaction) {
  const today = new Date();
  const dateOptions = [];

  for (let i = 0; i < 7; i++) {
    const date = new Date(today);
    date.setDate(today.getDate() + i);
    const dateStr = date.toISOString().split('T')[0];
    dateOptions.push({
      label: dateStr,
      value: dateStr,
    });
  }

  const timeOptions = [];
  for (let hour = 0; hour < 24; hour++) {
    const formatted = hour.toString().padStart(2, '0') + ':00';
    timeOptions.push({
      label: formatted,
      value: formatted,
    });
  }

  const row1 = new ActionRowBuilder().addComponents(
    new StringSelectMenuBuilder()
      .setCustomId('select_date')
      .setPlaceholder('Select Date')
      .addOptions(dateOptions)
  );

  const row2 = new ActionRowBuilder().addComponents(
    new StringSelectMenuBuilder()
      .setCustomId('select_start')
      .setPlaceholder('Select Start Time')
      .addOptions(timeOptions)
  );

  const row3 = new ActionRowBuilder().addComponents(
    new StringSelectMenuBuilder()
      .setCustomId('select_end')
      .setPlaceholder('Select End Time')
      .addOptions(timeOptions)
  );

  const confirmRow = new ActionRowBuilder().addComponents(
    new ButtonBuilder()
      .setCustomId('confirm_availability')
      .setLabel('✅ Confirm Availability')
      .setStyle(ButtonStyle.Success)
  );

  await interaction.reply({
    content: 'Please select your availability:',
    components: [row1, row2, row3, confirmRow],
    ephemeral: true
  });
}

async function handleSelectDate(interaction) {
  const userId = interaction.user.id;
  const selectedDate = interaction.values[0];

  if (!userSelections.has(userId)) {
    userSelections.set(userId, {});
  }

  userSelections.get(userId).date = selectedDate;

  await interaction.deferUpdate({
    content: `📅 Date selected: **${selectedDate}**`,
    ephemeral: true,
  });
}

async function handleSelectStart(interaction) {
  const userId = interaction.user.id;
  const startTime = interaction.values[0];

  if (!userSelections.has(userId)) {
    userSelections.set(userId, {});
  }

  userSelections.get(userId).start = startTime;

  await interaction.deferUpdate({
    content: `🕓 Start time selected: **${startTime}**`,
    ephemeral: true,
  });
}

async function handleSelectEnd(interaction) {
  const userId = interaction.user.id;
  const endTime = interaction.values[0];

  if (!userSelections.has(userId)) {
    userSelections.set(userId, {});
  }

  userSelections.get(userId).end = endTime;

  await interaction.deferUpdate({
    content: `🕔 End time selected: **${endTime}**`,
    ephemeral: true,
  });
}

async function handleConfirmAvailability(interaction) {
  try {
    console.log('[DEBUG] Confirm availability handler triggered');

    const db = getDatabase(); // ✅ GET db HERE
    if (!db) {
      logger.error('Database not initialized');
      return interaction.reply({
        content: '❌ Internal DB error.',
        ephemeral: true
      });
    }

    const userId = interaction.user.id;
    const username = interaction.user.username;
    const selection = userSelections.get(userId);

    console.log('[DEBUG] Current selection:', selection);

    if (!selection || !selection.date || !selection.start || !selection.end) {
      return await interaction.reply({
        content: '⚠️ Please select a date, start, and end time before confirming.',
        ephemeral: true,
      });
    }

    const timeSlot = `${selection.start}–${selection.end}`;

    db.run(
      'INSERT OR REPLACE INTO roster (userId, username, date, timeSlot) VALUES (?, ?, ?, ?)',
      [userId, username, selection.date, timeSlot],
      async err => {
        if (err) {
          console.error('[ERROR] DB insert failed:', err);
          return interaction.reply({
            content: '❌ Failed to save your availability.',
            ephemeral: true,
          });
        }

        userSelections.delete(userId);

        await interaction.reply({
          content: `✅ Availability submitted for **${selection.date}**: **${timeSlot}**`,
          ephemeral: true,
        });

        try {
          await updateRosterMessage(interaction.client, selection.date);
        } catch (updateErr) {
          console.warn('[WARN] Roster message update failed:', updateErr);
        }
      }
    );
  } catch (error) {
    console.error('[ERROR] handleConfirmAvailability failed:', error);
    if (!interaction.replied && !interaction.deferred) {
      await interaction.reply({
        content: '❌ An unexpected error occurred.',
        ephemeral: true,
      });
    }
  }
}

async function handleRosterCancel(interaction) {
  const date = interaction.customId.split('_')[2];
  const db = getDatabase();
  if (!db) {
    logger.error('Database not initialized');
    return interaction.reply({
      content: '❌ Internal DB error.',
      ephemeral: true
    });
  }

  db.run(
    'DELETE FROM roster WHERE userId = ? AND date = ?',
    [interaction.user.id, date],
    async err => {
      if (err) {
        logger.error('DB error:', err);
        return interaction.reply({ content: 'Error removing availability.', ephemeral: true });
      }
      await interaction.reply({
        content: `✅ Your availability for ${date} has been removed.`,
        ephemeral: true
      });
    }
  );
}

async function handleRosterEdit(interaction) {
  const date = interaction.customId.split('_')[2];
  const key = interaction.user.id;

  userSelections.set(key, { date, edit: true });
  await interaction.reply({
    content: `Please enter your new time slot for ${date}:`,
    ephemeral: true
  });
}

async function handleShiftCheckin(interaction) {
  const [, , date, timeSlot] = interaction.customId.split('_');
  const db = getDatabase();
  if (!db) {
    logger.error('Database not initialized');
    return interaction.reply({
      content: '❌ Internal DB error.',
      ephemeral: true
    });
  }

  db.run(
    'INSERT OR IGNORE INTO checkins (userId, date, timeSlot) VALUES (?, ?, ?)',
    [interaction.user.id, date, timeSlot],
    async err => {
      if (err) {
        logger.error('Check-in error:', err);
        return interaction.reply({ content: 'Check-in failed.', ephemeral: true });
      }

      await interaction.reply({
        content: `✅ Checked in for ${timeSlot} on ${date}`,
        ephemeral: true
      });
    }
  );
}

async function checkUpcomingShifts(client) {
  const config = loadConfig();
  const db = getDatabase();
  if (!db) {
    logger.error('Database not initialized');
    return;
  }

  const now = new Date();
  const currentDate = now.toISOString().split('T')[0];
  const hour = new Date(now.getTime() + config.scheduler.notificationMinutes * 60000)
    .toISOString().substring(11, 13);
  const timeSlot = `${hour}:00`;

  db.all(
    'SELECT * FROM roster WHERE date = ? AND timeSlot = ?',
    [currentDate, timeSlot],
    async (err, rows) => {
      if (err || rows.length === 0) return;

      const channel = await client.channels.fetch(config.scheduler.notificationChannelId);
      if (!channel) return;

      const embed = new EmbedBuilder()
        .setTitle(`⏰ Upcoming Shift @ ${timeSlot}`)
        .setDescription(`Check in now if you're available.`)
        .setColor(0xFFA500);

      const row = new ActionRowBuilder().addComponents(
        new ButtonBuilder()
          .setCustomId(`shift_checkin_${currentDate}_${timeSlot}`)
          .setLabel('Check In')
          .setStyle(ButtonStyle.Primary)
      );

      await channel.send({ embeds: [embed], components: [row] });
    }
  );
}

module.exports = {
  initializeScheduler,
  createDailyChannels,
  cleanupOldChannels,
  handleRosterAdd,
  handleSelectDate,
  handleSelectStart,
  handleSelectEnd,
  handleConfirmAvailability,
  handleRosterCancel,
  handleRosterEdit,
  handleShiftCheckin,
  checkUpcomingShifts
};