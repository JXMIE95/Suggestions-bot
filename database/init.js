console.log(`DEBUG - DATABASE_URL: ${process.env.DATABASE_URL}`);

const { Client } = require('pg');
const logger = require('../utils/logger');

const client = new Client({
    connectionString: postgresql://postgres:tBjUJOGVDzGbONEtQLmxNXFRURrQmwON@shortline.proxy.rlwy.net:40558/railway,
    ssl: {
        rejectUnauthorized: false
    }
});

async function init() {
    try {
        await client.connect();
        logger.info('✅ Connected to PostgreSQL database');
        await createTables();
    } catch (err) {
        logger.error('❌ Failed to initialize database:', err);
        throw err;
    }
}

async function createTables() {
    const queries = [
        `CREATE TABLE IF NOT EXISTS suggestions (
            id SERIAL PRIMARY KEY,
            messageId TEXT UNIQUE,
            userId TEXT NOT NULL,
            content TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            upvotes INTEGER DEFAULT 0,
            downvotes INTEGER DEFAULT 0,
            staffMessageId TEXT,
            createdAt TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
            votingEndsAt TIMESTAMPTZ,
            staffVotingEndsAt TIMESTAMPTZ
        )`,
        `CREATE TABLE IF NOT EXISTS suggestion_votes (
            id SERIAL PRIMARY KEY,
            suggestionId INTEGER REFERENCES suggestions(id),
            userId TEXT,
            voteType TEXT,
            UNIQUE(suggestionId, userId)
        )`,
        `CREATE TABLE IF NOT EXISTS staff_votes (
            id SERIAL PRIMARY KEY,
            suggestionId INTEGER REFERENCES suggestions(id),
            userId TEXT,
            vote TEXT,
            UNIQUE(suggestionId, userId)
        )`,
        `CREATE TABLE IF NOT EXISTS roster (
            id SERIAL PRIMARY KEY,
            channelId TEXT NOT NULL,
            userId TEXT NOT NULL,
            username TEXT NOT NULL,
            timeSlot TEXT NOT NULL,
            roleType TEXT NOT NULL,
            date TEXT NOT NULL,
            createdAt TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(channelId, timeSlot, userId)
        )`,
        `CREATE TABLE IF NOT EXISTS notifications (
            id SERIAL PRIMARY KEY,
            type TEXT NOT NULL,
            channelId TEXT NOT NULL,
            timeSlot TEXT NOT NULL,
            date TEXT NOT NULL,
            sent BOOLEAN DEFAULT FALSE,
            createdAt TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
        )`,
        `CREATE TABLE IF NOT EXISTS checkins (
            id SERIAL PRIMARY KEY,
            userId TEXT NOT NULL,
            timeSlot TEXT NOT NULL,
            date TEXT NOT NULL,
            checkedInAt TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
        )`
    ];

    for (let i = 0; i < queries.length; i++) {
        try {
            await client.query(queries[i]);
        } catch (err) {
            logger.error(`❌ Error creating table ${i}:`, err);
            throw err;
        }
    }

    logger.info('✅ All database tables created successfully');
}

function getDatabase() {
    return client;
}

module.exports = {
    init,
    getDatabase
};