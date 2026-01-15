/**
 * Manual Outreach Trigger
 *
 * Run with: npm run outreach
 *
 * Manually trigger SEED to send an outreach message
 */

import 'dotenv/config';
import { initDb, closeDb } from '../db/index.js';
import { runOutreachCheck, sendDailyDigest } from '../handlers/outreach.js';

async function main() {
    const command = process.argv[2] || 'question';

    console.log('SEED Outreach - Manual Trigger\n');

    // Initialize database
    initDb();

    try {
        switch (command) {
            case 'question':
                console.log('Sending outreach question...');
                await runOutreachCheck();
                break;

            case 'digest':
                console.log('Sending daily digest...');
                await sendDailyDigest();
                break;

            default:
                console.log('Usage: npm run outreach [question|digest]');
                console.log('');
                console.log('Commands:');
                console.log('  question - Send a follow-up question');
                console.log('  digest   - Send the daily digest');
        }

        console.log('\nDone!');

    } catch (error) {
        console.error('Error:', error);
        process.exit(1);
    } finally {
        closeDb();
    }
}

main();
