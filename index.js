const sqlite3 = require('sqlite3').verbose();
const path = require('path');
const logger = require(path.join(__dirname, 'utils', 'logger'));

const dbPath = process.env.DATABASE_URL || path.join(__dirname, '..', 'bot.db');

let db;

function init() {
  return new Promise((resolve, reject) => {
    db = new sqlite3.Database(dbPath, (err) => {
      if (err) {
        logger.error('Error opening database:', err);
        reject(err);
        return;
      }

      logger.info('Connected to SQLite database');

      createTables()
        .then(() => resolve())
        .catch(reject);
    });
  });
}

function createTables() {
  return new Promise((resolve, reject) => {
    const queries = [
      `CREATE TABLE IF NOT EXISTS suggestions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        messageId TEXT UNIQUE,
        userId TEXT NOT NULL,
        content TEXT NOT NULL,
        status TEXT DEFAULT 'pending',
        upvotes INTEGER DEFAULT 0,
        downvotes INTEGER DEFAULT 0,
        staffMessageId TEXT,
        createdAt DATETIME DEFAULT CURRENT_TIMESTAMP,
        votingEndsAt DATETIME,
        staffVotingEndsAt DATETIME
      )`,
      `CREATE TABLE IF NOT EXISTS suggestion_votes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        suggestionId INTEGER,
        userId TEXT,
        voteType TEXT,
        FOREIGN KEY (suggestionId) REFERENCES suggestions (id),
        UNIQUE(suggestionId, userId)
      )`,
      `CREATE TABLE IF NOT EXISTS staff_votes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        suggestionId INTEGER,
        userId TEXT,
        vote TEXT,
        FOREIGN KEY (suggestionId) REFERENCES suggestions (id),
        UNIQUE(suggestionId, userId)
      )`,
      `CREATE TABLE IF NOT EXISTS roster (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        channelId TEXT NOT NULL,
        userId TEXT NOT NULL,
        username TEXT NOT NULL,
        timeSlot TEXT NOT NULL,
        roleType TEXT NOT NULL,
        date TEXT NOT NULL,
        createdAt DATETIME DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(channelId, timeSlot, userId)
      )`,
      `CREATE TABLE IF NOT EXISTS notifications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        type TEXT NOT NULL,
        channelId TEXT NOT NULL,
        timeSlot TEXT NOT NULL,
        date TEXT NOT NULL,
        sent BOOLEAN DEFAULT FALSE,
        createdAt DATETIME DEFAULT CURRENT_TIMESTAMP
      )`,
      `CREATE TABLE IF NOT EXISTS checkins (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        userId TEXT NOT NULL,
        timeSlot TEXT NOT NULL,
        date TEXT NOT NULL,
        checkedInAt DATETIME DEFAULT CURRENT_TIMESTAMP
      )`
    ];

    let completed = 0;
    queries.forEach((query, index) => {
      db.run(query, (err) => {
        if (err) {
          logger.error(`Error creating table ${index}:`, err);
          reject(err);
          return;
        }

        completed++;
        if (completed === queries.length) {
          logger.info('All database tables created successfully');
          resolve();
        }
      });
    });
  });
}

function getDatabase() {
  return db;
}

module.exports = {
  init,
  getDatabase
};