const fs = require('fs');
const path = require('path');

const configPath = path.join(__dirname, '..', 'config.json');

function hasRole(member, roleId) {
    if (!roleId || !member) return false;
    return member.roles.cache.has(roleId);
}

function isStaff(member) {
    try {
        const config = JSON.parse(fs.readFileSync(configPath, 'utf8'));
        return hasRole(member, config.suggestions.staffRoleId);
    } catch (error) {
        return false;
    }
}

function isKing(member) {
    try {
        const config = JSON.parse(fs.readFileSync(configPath, 'utf8'));
        return hasRole(member, config.scheduler.kingRoleId);
    } catch (error) {
        return false;
    }
}

function isBuffGiver(member) {
    try {
        const config = JSON.parse(fs.readFileSync(configPath, 'utf8'));
        return hasRole(member, config.scheduler.buffGiverRoleId);
    } catch (error) {
        return false;
    }
}

function isAdmin(member) {
    return member.permissions.has('Administrator');
}

function canManageRoster(member) {
    return isAdmin(member) || isKing(member);
}

function canCheckIn(member) {
    return isKing(member) || isBuffGiver(member);
}

module.exports = {
    hasRole,
    isStaff,
    isKing,
    isBuffGiver,
    isAdmin,
    canManageRoster,
    canCheckIn
};