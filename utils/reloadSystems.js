
const path = require('path');

function clearModuleCache(modulePath) {
    const resolvedPath = require.resolve(modulePath);
    if (require.cache[resolvedPath]) {
        delete require.cache[resolvedPath];
    }
}

function reloadSystems(client) {
    try {
        clearModuleCache(path.resolve(__dirname, '../scheduler.js'));
        clearModuleCache(path.resolve(__dirname, '../suggestions.js'));

        const scheduler = require('../scheduler');
        const suggestions = require('../suggestions');

        scheduler.initializeScheduler(client);
        suggestions.initializeSuggestions(client);

        console.log('[INFO] Systems reloaded successfully');
    } catch (err) {
        console.error('[ERROR] Failed to reload systems:', err);
    }
}

module.exports = reloadSystems;
