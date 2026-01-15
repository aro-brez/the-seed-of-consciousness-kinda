/**
 * Database Initialization Script
 * Run with: npm run db:init
 */

import 'dotenv/config';
import { initDb, closeDb } from './index.js';

console.log('Initializing SEED database...');
console.log(`Database path: ${process.env.DATABASE_PATH || './data/seed.db'}`);

try {
    initDb();
    console.log('Database initialized successfully!');
    console.log('');
    console.log('Tables created:');
    console.log('  - ideas');
    console.log('  - conversations');
    console.log('  - messages');
    console.log('  - pending_questions');
    console.log('  - outreach_log');
    console.log('  - social_captures');
    console.log('  - system_state');
    console.log('  - ideas_fts (full-text search)');
} catch (error) {
    console.error('Failed to initialize database:', error);
    process.exit(1);
} finally {
    closeDb();
}
