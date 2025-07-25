
// ... [rest of your scheduler.js logic should be here]

// New handlers for time range selection
async function handleRosterStartTime(interaction) {
    const userId = interaction.user.id;
    const date = interaction.customId.split('_').slice(-1)[0];
    const startTime = interaction.values[0];

    if (!userSelections.has(userId)) {
        userSelections.set(userId, { startTime: null, endTime: null, date });
    }

    const selection = userSelections.get(userId);
    selection.startTime = startTime;

    await interaction.reply({
        content: `✅ Start time set to ${startTime}. Now select an end time.`,
        ephemeral: true
    });
}

async function handleRosterEndTime(interaction) {
    const userId = interaction.user.id;
    const date = interaction.customId.split('_').slice(-1)[0];
    const endTime = interaction.values[0];

    const selection = userSelections.get(userId);
    if (!selection || !selection.startTime) {
        await interaction.reply({ content: 'Please select a start time first.', ephemeral: true });
        return;
    }

    selection.endTime = endTime;

    const startHour = parseInt(selection.startTime.split(':')[0]);
    const endHour = parseInt(endTime.split(':')[0]);

    if (endHour < startHour) {
        await interaction.reply({ content: 'End time must be after start time.', ephemeral: true });
        return;
    }

    selection.timeSlots = [];
    for (let h = startHour; h <= endHour; h++) {
        const slot = h.toString().padStart(2, '0') + ':00';
        selection.timeSlots.push(slot);
    }

    await interaction.reply({
        content: `✅ Selected hours: ${selection.timeSlots.join(', ')}\nClick "Confirm Selection" to finalize.`,
        ephemeral: true
    });
}

// Add to module.exports
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
    checkUpcomingShifts,
    handleRosterStartTime,
    handleRosterEndTime
};
