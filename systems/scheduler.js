const { EmbedBuilder, ActionRowBuilder, ButtonBuilder, ButtonStyle, ModalBuilder, TextInputBuilder, TextInputStyle, ChannelType, StringSelectMenuBuilder, StringSelectMenuOptionBuilder } = require('discord.js');
const fs = require('fs');
const path = require('path');
const db = require('../database/init').getDatabase;
const logger = require('../utils/logger');

const configPath = path.join(__dirname, '..', 'config.json');

// Temporary storage for user selections during multi-step process
const userSelections = new Map();

async function initializeScheduler(client) {
    try {
        await createDailyChannels(client);
        logger.info('Scheduler initialized successfully');
    } catch (error) {
        logger.error('Error initializing scheduler:', error);
    }
}

async function createDailyChannels(client) {
    try {
        const config = JSON.parse(fs.readFileSync(configPath, 'utf8'));
        
        if (!config.scheduler.enabled || !config.scheduler.categoryId) {
            return;
        }

        const guild = client.guilds.cache.first();
        const category = guild.channels.cache.get(config.scheduler.categoryId);
        
        if (!category) {
            logger.warn('Scheduler category not found');
            return;
        }

        // Create channels for the next 7 days
        for (let i = 0; i < 7; i++) {
            const date = new Date();
            date.setUTCDate(date.getUTCDate() + i);
            const dateString = date.toISOString().split('T')[0]; // YYYY-MM-DD format
            
            // Check if channel already exists
            const existingChannel = category.children.cache.find(channel => 
                channel.name === dateString
            );
            
            if (!existingChannel) {
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
        // Create 24-hour roster (00:00 to 23:00)
        const timeSlots = [];
        for (let hour = 0; hour < 24; hour++) {
            const timeString = hour.toString().padStart(2, '0') + ':00';
            timeSlots.push({
                time: timeString,
                users: []
            });
        }

        const embed = new EmbedBuilder()
            .setTitle(`📅 Roster for ${date}`)
            .setDescription('24-hour schedule (UTC time)')
            .setColor(0x00AE86)
            .setTimestamp();

        // Add fields for each time slot
        for (const slot of timeSlots) {
            const fieldValue = slot.users.length > 0 
                ? slot.users.map(user => `• ${user.username} (${user.role})`).join('\n')
                : 'No one scheduled';
            
            embed.addFields({
                name: `${slot.time} UTC`,
                value: fieldValue,
                inline: true
            });
        }

        const row = new ActionRowBuilder()
            .addComponents(
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
                    .setEmoji('✏️')
            );

        await channel.send({
            embeds: [embed],
            components: [row]
        });
    } catch (error) {
        logger.error('Error setting up roster message:', error);
    }
}

async function cleanupOldChannels(client) {
    try {
        const config = JSON.parse(fs.readFileSync(configPath, 'utf8'));
        
        if (!config.scheduler.enabled || !config.scheduler.categoryId) {
            return;
        }

        const guild = client.guilds.cache.first();
        const category = guild.channels.cache.get(config.scheduler.categoryId);
        
        if (!category) {
            return;
        }

        const today = new Date().toISOString().split('T')[0];
        const todayTime = new Date(today).getTime();

        for (const [channelId, channel] of category.children.cache) {
            const channelDate = channel.name;
            const channelTime = new Date(channelDate).getTime();
            
            // Delete channels older than today
            if (channelTime < todayTime) {
                await channel.delete();
                logger.info(`Deleted old channel: ${channelDate}`);
                
                // Clean up database entries for this date
                db().run('DELETE FROM roster WHERE date = ?', [channelDate]);
                db().run('DELETE FROM notifications WHERE date = ?', [channelDate]);
                db().run('DELETE FROM checkins WHERE date = ?', [channelDate]);
            }
        }
    } catch (error) {
        logger.error('Error cleaning up old channels:', error);
    }
}

async function handleRosterAdd(interaction) {
    try {
        const date = interaction.customId.split('_')[2];
        
        // Get current roster entries for this date to determine available slots
        db().all(
            'SELECT timeSlot, COUNT(*) as count FROM roster WHERE channelId = ? GROUP BY timeSlot',
            [interaction.channel.id],
            async (err, occupiedSlots) => {
                if (err) {
                    logger.error('Error fetching occupied slots:', err);
                    await interaction.reply({ content: 'Database error occurred', ephemeral: true });
                    return;
                }

                // Create options for all 24 hours, marking which are available
                const timeOptions = [];
                const config = JSON.parse(fs.readFileSync(configPath, 'utf8'));
                const maxUsers = config.scheduler.maxConcurrentUsers;

                for (let hour = 0; hour < 24; hour++) {
                    const timeString = hour.toString().padStart(2, '0') + ':00';
                    const occupied = occupiedSlots.find(slot => slot.timeSlot === timeString);
                    const currentCount = occupied ? occupied.count : 0;
                    const available = currentCount < maxUsers;
                    
                    const label = `${timeString} UTC ${available ? '✅' : '❌ (Full)'}`;
                    const description = available ? 
                        `Available (${currentCount}/${maxUsers} slots taken)` : 
                        `Full (${currentCount}/${maxUsers} slots taken)`;
                    
                    timeOptions.push(
                        new StringSelectMenuOptionBuilder()
                            .setLabel(label)
                            .setDescription(description)
                            .setValue(timeString)
                            .setDefault(false)
                    );
                }

                // Split into multiple select menus (Discord limit is 25 options per menu)
                const selectMenus = [];
                for (let i = 0; i < timeOptions.length; i += 25) {
                    const menuOptions = timeOptions.slice(i, i + 25);
                    const menuNumber = Math.floor(i / 25) + 1;
                    
                    const selectMenu = new StringSelectMenuBuilder()
                        .setCustomId(`roster_time_select_${date}_${menuNumber}`)
                        .setPlaceholder(`Select time slots (Hours ${i}-${Math.min(i + 24, 23)})`)
                        .setMinValues(1)
                        .setMaxValues(Math.min(menuOptions.length, 25))
                        .addOptions(menuOptions);

                    selectMenus.push(new ActionRowBuilder().addComponents(selectMenu));
                }

                // Role is automatically set to "Buff Giver" - no selection needed

                const embed = new EmbedBuilder()
                    .setTitle('📅 Add Your Availability')
                    .setDescription(`**Select multiple time slots for ${date}**\n\n` +
                        '1️⃣ Choose one or more time slots from the list below\n' +
                        '2️⃣ Click the "Confirm Selection" button\n\n' +
                        '✅ = Available slots\n' +
                        '❌ = Full slots (2/2 people already scheduled)\n\n' +
                        '*All availability is automatically set as Buff Giver role*')
                    .setColor(0x00AE86);

                // Add confirm button
                const confirmButton = new ActionRowBuilder()
                    .addComponents(
                        new ButtonBuilder()
                            .setCustomId(`roster_confirm_${date}`)
                            .setLabel('Confirm Selection')
                            .setStyle(ButtonStyle.Success)
                            .setEmoji('✅'),
                        new ButtonBuilder()
                            .setCustomId(`roster_cancel_selection_${date}`)
                            .setLabel('Cancel')
                            .setStyle(ButtonStyle.Secondary)
                            .setEmoji('❌')
                    );

                selectMenus.push(confirmButton);

                await interaction.reply({
                    embeds: [embed],
                    components: selectMenus,
                    ephemeral: true
                });
            }
        );
    } catch (error) {
        logger.error('Error handling roster add:', error);
        await interaction.reply({ content: 'Error processing request', ephemeral: true });
    }
}

async function handleRosterAddModal(interaction) {
    try {
        const date = interaction.customId.split('_')[3];
        const timeSlot = interaction.fields.getTextInputValue('time_slot');
        const roleType = interaction.fields.getTextInputValue('role_type').toLowerCase();

        // Validate time format
        if (!/^\d{2}:\d{2}$/.test(timeSlot)) {
            await interaction.reply({ content: 'Invalid time format. Please use HH:MM format (e.g., 14:00)', ephemeral: true });
            return;
        }

        // Validate role
        if (roleType !== 'king' && roleType !== 'buff giver') {
            await interaction.reply({ content: 'Invalid role. Please specify either "King" or "Buff Giver"', ephemeral: true });
            return;
        }

        // Check if user already has a slot at this time
        db().get(
            'SELECT * FROM roster WHERE channelId = ? AND timeSlot = ? AND userId = ?',
            [interaction.channel.id, timeSlot, interaction.user.id],
            async (err, existing) => {
                if (err) {
                    logger.error('Error checking existing roster entry:', err);
                    await interaction.reply({ content: 'Database error occurred', ephemeral: true });
                    return;
                }

                if (existing) {
                    await interaction.reply({ content: 'You already have a slot at this time!', ephemeral: true });
                    return;
                }

                // Check if slot is full (max 2 people)
                db().all(
                    'SELECT * FROM roster WHERE channelId = ? AND timeSlot = ?',
                    [interaction.channel.id, timeSlot],
                    async (err, slots) => {
                        if (err) {
                            logger.error('Error checking slot availability:', err);
                            await interaction.reply({ content: 'Database error occurred', ephemeral: true });
                            return;
                        }

                        const config = JSON.parse(fs.readFileSync(configPath, 'utf8'));
                        
                        if (slots.length >= config.scheduler.maxConcurrentUsers) {
                            await interaction.reply({ content: 'This time slot is full (maximum 2 people)', ephemeral: true });
                            return;
                        }

                        // Add to roster
                        db().run(
                            'INSERT INTO roster (channelId, userId, username, timeSlot, roleType, date) VALUES (?, ?, ?, ?, ?, ?)',
                            [interaction.channel.id, interaction.user.id, interaction.user.username, timeSlot, roleType, date],
                            async function(err) {
                                if (err) {
                                    logger.error('Error adding to roster:', err);
                                    await interaction.reply({ content: 'Error adding to roster', ephemeral: true });
                                    return;
                                }

                                await updateRosterMessage(interaction.channel, date);
                                await interaction.reply({ content: `✅ Added to roster at ${timeSlot} as ${roleType}`, ephemeral: true });
                            }
                        );
                    }
                );
            }
        );
    } catch (error) {
        logger.error('Error handling roster add modal:', error);
        await interaction.reply({ content: 'Error processing request', ephemeral: true });
    }
}

async function handleRosterTimeSelect(interaction) {
    try {
        const parts = interaction.customId.split('_');
        const date = parts[3];
        const userId = interaction.user.id;
        
        // Initialize user selection if not exists (role is automatically "buff giver")
        if (!userSelections.has(userId)) {
            userSelections.set(userId, { timeSlots: [], role: 'buff giver', date: date });
        }
        
        const selection = userSelections.get(userId);
        
        // Add selected time slots (avoiding duplicates)
        const newTimeSlots = interaction.values.filter(timeSlot => !selection.timeSlots.includes(timeSlot));
        selection.timeSlots.push(...newTimeSlots);
        
        logger.info(`User ${interaction.user.username} selected time slots: ${interaction.values.join(', ')}`);
        
        await interaction.reply({ 
            content: `✅ Selected ${interaction.values.length} time slot(s): ${interaction.values.join(', ')}\n` +
                     `Total selected: ${selection.timeSlots.join(', ')}\n\n` +
                     `Click "Confirm Selection" to add your availability as Buff Giver!`, 
            flags: 64 
        });
    } catch (error) {
        logger.error('Error handling time slot selection:', error);
        await interaction.reply({ content: 'Error processing time selection', ephemeral: true });
    }
}

// Role selection removed - all availability is automatically set to "buff giver"

async function handleRosterConfirm(interaction) {
    try {
        const date = interaction.customId.split('_')[2];
        const userId = interaction.user.id;
        const selection = userSelections.get(userId);
        
        if (!selection || selection.timeSlots.length === 0) {
            await interaction.reply({ 
                content: 'Please select time slots before confirming!', 
                flags: 64 
            });
            return;
        }
        
        logger.info(`Confirming roster for user ${interaction.user.username}: ${JSON.stringify(selection)}`);
        
        // Process each selected time slot
        const successfulSlots = [];
        const failedSlots = [];
        const config = JSON.parse(fs.readFileSync(configPath, 'utf8'));
        
        for (const timeSlot of selection.timeSlots) {
            try {
                // Check if user already has this slot
                const existing = await new Promise((resolve, reject) => {
                    db().get(
                        'SELECT * FROM roster WHERE channelId = ? AND timeSlot = ? AND userId = ?',
                        [interaction.channel.id, timeSlot, userId],
                        (err, row) => {
                            if (err) reject(err);
                            else resolve(row);
                        }
                    );
                });
                
                if (existing) {
                    failedSlots.push(`${timeSlot} (already scheduled)`);
                    continue;
                }
                
                // Check if slot is full
                const slots = await new Promise((resolve, reject) => {
                    db().all(
                        'SELECT * FROM roster WHERE channelId = ? AND timeSlot = ?',
                        [interaction.channel.id, timeSlot],
                        (err, rows) => {
                            if (err) reject(err);
                            else resolve(rows);
                        }
                    );
                });
                
                if (slots.length >= config.scheduler.maxConcurrentUsers) {
                    failedSlots.push(`${timeSlot} (full)`);
                    continue;
                }
                
                // Add to roster
                await new Promise((resolve, reject) => {
                    db().run(
                        'INSERT INTO roster (channelId, userId, username, timeSlot, roleType, date) VALUES (?, ?, ?, ?, ?, ?)',
                        [interaction.channel.id, userId, interaction.user.username, timeSlot, selection.role, date],
                        function(err) {
                            if (err) reject(err);
                            else resolve();
                        }
                    );
                });
                
                successfulSlots.push(timeSlot);
                
            } catch (error) {
                logger.error(`Error processing slot ${timeSlot}:`, error);
                failedSlots.push(`${timeSlot} (error)`);
            }
        }
        
        // Clear user selection
        userSelections.delete(userId);
        
        // Update roster message
        await updateRosterMessage(interaction.channel, date);
        
        // Send response
        let response = '';
        if (successfulSlots.length > 0) {
            response += `✅ Successfully added to roster:\n${successfulSlots.map(slot => `• ${slot} as ${selection.role}`).join('\n')}`;
        }
        if (failedSlots.length > 0) {
            response += `\n\n❌ Failed to add:\n${failedSlots.map(slot => `• ${slot}`).join('\n')}`;
        }
        
        await interaction.reply({ content: response, ephemeral: true });
        
    } catch (error) {
        logger.error('Error confirming roster selection:', error);
        await interaction.reply({ content: 'Error processing confirmation', ephemeral: true });
    }
}

async function handleRosterCancelSelection(interaction) {
    try {
        const userId = interaction.user.id;
        userSelections.delete(userId);
        
        await interaction.reply({ 
            content: '❌ Selection cancelled. Your choices have been cleared.', 
            flags: 64 
        });
    } catch (error) {
        logger.error('Error cancelling selection:', error);
        await interaction.reply({ content: 'Error cancelling selection', ephemeral: true });
    }
}

async function handleRosterCancel(interaction) {
    try {
        const date = interaction.customId.split('_')[2];

        // Get user's current roster entries for this date
        db().all(
            'SELECT * FROM roster WHERE channelId = ? AND userId = ?',
            [interaction.channel.id, interaction.user.id],
            async (err, entries) => {
                if (err) {
                    logger.error('Error fetching user roster entries:', err);
                    await interaction.reply({ content: 'Database error occurred', ephemeral: true });
                    return;
                }

                if (entries.length === 0) {
                    await interaction.reply({ content: 'You have no scheduled slots to cancel', ephemeral: true });
                    return;
                }

                // Remove all user entries for this date
                db().run(
                    'DELETE FROM roster WHERE channelId = ? AND userId = ?',
                    [interaction.channel.id, interaction.user.id],
                    async (err) => {
                        if (err) {
                            logger.error('Error canceling roster entries:', err);
                            await interaction.reply({ content: 'Error canceling availability', ephemeral: true });
                            return;
                        }

                        await updateRosterMessage(interaction.channel, date);
                        await interaction.reply({ content: `✅ Canceled all your availability for ${date}`, ephemeral: true });
                    }
                );
            }
        );
    } catch (error) {
        logger.error('Error handling roster cancel:', error);
    }
}

async function handleRosterEdit(interaction) {
    try {
        const date = interaction.customId.split('_')[2];

        // Get user's current roster entries
        db().all(
            'SELECT * FROM roster WHERE channelId = ? AND userId = ?',
            [interaction.channel.id, interaction.user.id],
            async (err, entries) => {
                if (err) {
                    logger.error('Error fetching user roster entries:', err);
                    await interaction.reply({ content: 'Database error occurred', ephemeral: true });
                    return;
                }

                if (entries.length === 0) {
                    await interaction.reply({ content: 'You have no scheduled slots to edit', ephemeral: true });
                    return;
                }

                const modal = new ModalBuilder()
                    .setCustomId(`roster_edit_modal_${date}`)
                    .setTitle(`Edit Availability - ${date}`);

                const currentSlots = entries.map(e => `${e.timeSlot} (${e.roleType})`).join(', ');

                const newTimeInput = new TextInputBuilder()
                    .setCustomId('new_time_slot')
                    .setLabel('New Time Slot (HH:00 format)')
                    .setStyle(TextInputStyle.Short)
                    .setPlaceholder('e.g., 15:00')
                    .setRequired(true)
                    .setMaxLength(5);

                const newRoleInput = new TextInputBuilder()
                    .setCustomId('new_role_type')
                    .setLabel('New Role (King or Buff Giver)')
                    .setStyle(TextInputStyle.Short)
                    .setPlaceholder('King or Buff Giver')
                    .setRequired(true)
                    .setMaxLength(20);

                const currentInput = new TextInputBuilder()
                    .setCustomId('current_info')
                    .setLabel('Current Slots (for reference)')
                    .setStyle(TextInputStyle.Paragraph)
                    .setValue(currentSlots)
                    .setRequired(false);

                modal.addComponents(
                    new ActionRowBuilder().addComponents(currentInput),
                    new ActionRowBuilder().addComponents(newTimeInput),
                    new ActionRowBuilder().addComponents(newRoleInput)
                );

                await interaction.showModal(modal);
            }
        );
    } catch (error) {
        logger.error('Error handling roster edit:', error);
    }
}

async function handleRosterEditModal(interaction) {
    try {
        const date = interaction.customId.split('_')[3];
        const newTimeSlot = interaction.fields.getTextInputValue('new_time_slot');
        const newRoleType = interaction.fields.getTextInputValue('new_role_type').toLowerCase();

        // Validate time format
        if (!/^\d{2}:\d{2}$/.test(newTimeSlot)) {
            await interaction.reply({ content: 'Invalid time format. Please use HH:MM format (e.g., 14:00)', ephemeral: true });
            return;
        }

        // Validate role
        if (newRoleType !== 'king' && newRoleType !== 'buff giver') {
            await interaction.reply({ content: 'Invalid role. Please specify either "King" or "Buff Giver"', ephemeral: true });
            return;
        }

        // Remove existing entries and add new one
        db().run(
            'DELETE FROM roster WHERE channelId = ? AND userId = ?',
            [interaction.channel.id, interaction.user.id],
            (err) => {
                if (err) {
                    logger.error('Error removing existing roster entries:', err);
                    return;
                }

                // Add new entry
                db().run(
                    'INSERT INTO roster (channelId, userId, username, timeSlot, roleType, date) VALUES (?, ?, ?, ?, ?, ?)',
                    [interaction.channel.id, interaction.user.id, interaction.user.username, newTimeSlot, newRoleType, date],
                    async (err) => {
                        if (err) {
                            logger.error('Error adding new roster entry:', err);
                            await interaction.reply({ content: 'Error updating roster', ephemeral: true });
                            return;
                        }

                        await updateRosterMessage(interaction.channel, date);
                        await interaction.reply({ content: `✅ Updated availability to ${newTimeSlot} as ${newRoleType}`, ephemeral: true });
                    }
                );
            }
        );
    } catch (error) {
        logger.error('Error handling roster edit modal:', error);
    }
}

async function updateRosterMessage(channel, date) {
    try {
        // Get roster data from database
        db().all(
            'SELECT * FROM roster WHERE channelId = ? ORDER BY timeSlot',
            [channel.id],
            async (err, roster) => {
                if (err) {
                    logger.error('Error fetching roster data:', err);
                    return;
                }

                // Group by time slot
                const timeSlots = {};
                for (let hour = 0; hour < 24; hour++) {
                    const timeString = hour.toString().padStart(2, '0') + ':00';
                    timeSlots[timeString] = [];
                }

                roster.forEach(entry => {
                    if (timeSlots[entry.timeSlot]) {
                        timeSlots[entry.timeSlot].push({
                            username: entry.username,
                            role: entry.roleType
                        });
                    }
                });

                const embed = new EmbedBuilder()
                    .setTitle(`📅 Roster for ${date}`)
                    .setDescription('24-hour schedule (UTC time)')
                    .setColor(0x00AE86)
                    .setTimestamp();

                // Add fields for each time slot
                for (const [time, users] of Object.entries(timeSlots)) {
                    const fieldValue = users.length > 0 
                        ? users.map(user => `• ${user.username} (${user.role})`).join('\n')
                        : 'No one scheduled';
                    
                    embed.addFields({
                        name: `${time} UTC`,
                        value: fieldValue,
                        inline: true
                    });
                }

                // Find the roster message and update it
                const messages = await channel.messages.fetch({ limit: 50 });
                const rosterMessage = messages.find(msg => 
                    msg.author.bot && 
                    msg.embeds.length > 0 && 
                    msg.embeds[0].title?.includes('Roster for')
                );

                if (rosterMessage) {
                    const row = new ActionRowBuilder()
                        .addComponents(
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
                                .setEmoji('✏️')
                        );

                    await rosterMessage.edit({
                        embeds: [embed],
                        components: [row]
                    });
                }
            }
        );
    } catch (error) {
        logger.error('Error updating roster message:', error);
    }
}

async function checkUpcomingShifts(client) {
    try {
        const config = JSON.parse(fs.readFileSync(configPath, 'utf8'));
        
        if (!config.scheduler.enabled || !config.scheduler.notificationChannelId) {
            return;
        }

        const now = new Date();
        const currentDate = now.toISOString().split('T')[0];
        const currentTime = now.toISOString().split('T')[1].substring(0, 5); // HH:MM
        
        // Calculate notification time (5 minutes before)
        const notificationTime = new Date(now.getTime() + (config.scheduler.notificationMinutes * 60 * 1000));
        const notificationTimeString = notificationTime.toISOString().split('T')[1].substring(0, 2) + ':00'; // Round to hour

        // Get shifts starting in 5 minutes
        db().all(
            'SELECT DISTINCT timeSlot, channelId FROM roster WHERE date = ? AND timeSlot = ?',
            [currentDate, notificationTimeString],
            async (err, shifts) => {
                if (err) {
                    logger.error('Error checking upcoming shifts:', err);
                    return;
                }

                for (const shift of shifts) {
                    // Check if notification already sent
                    db().get(
                        'SELECT * FROM notifications WHERE date = ? AND timeSlot = ? AND sent = 1',
                        [currentDate, shift.timeSlot],
                        async (err, existing) => {
                            if (err || existing) {
                                return;
                            }

                            await sendShiftNotification(client, shift, currentDate);
                            
                            // Mark as sent
                            db().run(
                                'INSERT OR REPLACE INTO notifications (type, channelId, timeSlot, date, sent) VALUES (?, ?, ?, ?, ?)',
                                ['shift_reminder', shift.channelId, shift.timeSlot, currentDate, true]
                            );
                        }
                    );
                }
            }
        );
    } catch (error) {
        logger.error('Error checking upcoming shifts:', error);
    }
}

async function sendShiftNotification(client, shift, date) {
    try {
        const config = JSON.parse(fs.readFileSync(configPath, 'utf8'));
        
        const notificationChannel = await client.channels.fetch(config.scheduler.notificationChannelId);
        if (!notificationChannel) {
            return;
        }

        // Get users for this shift
        db().all(
            'SELECT * FROM roster WHERE channelId = ? AND timeSlot = ? AND date = ?',
            [shift.channelId, shift.timeSlot, date],
            async (err, users) => {
                if (err || users.length === 0) {
                    return;
                }

                const embed = new EmbedBuilder()
                    .setTitle('⏰ Shift Starting Soon!')
                    .setDescription(`Shift starts in ${config.scheduler.notificationMinutes} minutes`)
                    .setColor(0xFFAA00)
                    .addFields(
                        { name: 'Time', value: `${shift.timeSlot} UTC`, inline: true },
                        { name: 'Date', value: date, inline: true },
                        { name: 'Scheduled Users', value: users.map(u => `• ${u.username} (${u.roleType})`).join('\n'), inline: false }
                    )
                    .setTimestamp();

                const row = new ActionRowBuilder()
                    .addComponents(
                        new ButtonBuilder()
                            .setCustomId(`shift_checkin_${date}_${shift.timeSlot}`)
                            .setLabel('Check In')
                            .setStyle(ButtonStyle.Primary)
                            .setEmoji('✅')
                    );

                let mentions = '';
                if (config.scheduler.kingRoleId) {
                    mentions += `<@&${config.scheduler.kingRoleId}> `;
                }
                if (config.scheduler.buffGiverRoleId) {
                    mentions += `<@&${config.scheduler.buffGiverRoleId}>`;
                }

                await notificationChannel.send({
                    content: mentions,
                    embeds: [embed],
                    components: [row]
                });
            }
        );
    } catch (error) {
        logger.error('Error sending shift notification:', error);
    }
}

async function handleShiftCheckin(interaction) {
    try {
        const [, , date, timeSlot] = interaction.customId.split('_');
        
        // Record check-in
        db().run(
            'INSERT OR REPLACE INTO checkins (userId, timeSlot, date) VALUES (?, ?, ?)',
            [interaction.user.id, timeSlot, date],
            async (err) => {
                if (err) {
                    logger.error('Error recording check-in:', err);
                    await interaction.reply({ content: 'Error recording check-in', ephemeral: true });
                    return;
                }

                await interaction.reply({ content: `✅ Checked in for ${timeSlot} UTC shift on ${date}`, ephemeral: true });
            }
        );
    } catch (error) {
        logger.error('Error handling shift check-in:', error);
    }
}

module.exports = {
    initializeScheduler,
    createDailyChannels,
    cleanupOldChannels,
    handleRosterAdd,
    handleRosterAddModal,
    handleRosterTimeSelect,
    handleRosterConfirm,
    handleRosterCancelSelection,
    handleRosterCancel,
    handleRosterEdit,
    handleRosterEditModal,
    handleShiftCheckin,
    checkUpcomingShifts
};
