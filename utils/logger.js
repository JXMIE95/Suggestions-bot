const fs = require('fs');
const path = require('path');

// Create logs directory if it doesn't exist
const logsDir = path.join(__dirname, '..', 'logs');
if (!fs.existsSync(logsDir)) {
    fs.mkdirSync(logsDir);
}

class Logger {
    constructor() {
        this.logFile = path.join(logsDir, `bot-${new Date().toISOString().split('T')[0]}.log`);
    }

    formatMessage(level, message, ...args) {
        const timestamp = new Date().toISOString();
        const formattedArgs = args.length > 0 ? ' ' + args.map(arg => 
            typeof arg === 'object' ? JSON.stringify(arg, null, 2) : String(arg)
        ).join(' ') : '';
        
        return `[${timestamp}] [${level.toUpperCase()}] ${message}${formattedArgs}`;
    }

    writeToFile(formattedMessage) {
        try {
            fs.appendFileSync(this.logFile, formattedMessage + '\n');
        } catch (error) {
            console.error('Failed to write to log file:', error);
        }
    }

    info(message, ...args) {
        const formatted = this.formatMessage('info', message, ...args);
        console.log(formatted);
        this.writeToFile(formatted);
    }

    warn(message, ...args) {
        const formatted = this.formatMessage('warn', message, ...args);
        console.warn(formatted);
        this.writeToFile(formatted);
    }

    error(message, ...args) {
        const formatted = this.formatMessage('error', message, ...args);
        console.error(formatted);
        this.writeToFile(formatted);
    }

    debug(message, ...args) {
        const formatted = this.formatMessage('debug', message, ...args);
        console.debug(formatted);
        this.writeToFile(formatted);
    }
}

module.exports = new Logger();