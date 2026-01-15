/**
 * Test SMS Sending
 *
 * Run with: npm run test:sms
 *
 * Sends a test message to verify Twilio configuration
 */

import 'dotenv/config';
import twilio from 'twilio';

async function testSms() {
    console.log('Testing SMS configuration...\n');

    // Check required env vars
    const required = [
        'TWILIO_ACCOUNT_SID',
        'TWILIO_AUTH_TOKEN',
        'TWILIO_PHONE_NUMBER',
        'YOUR_PHONE_NUMBER'
    ];

    const missing = required.filter(key => !process.env[key]);
    if (missing.length > 0) {
        console.error('Missing required environment variables:');
        missing.forEach(key => console.error(`  - ${key}`));
        process.exit(1);
    }

    const client = twilio(
        process.env.TWILIO_ACCOUNT_SID,
        process.env.TWILIO_AUTH_TOKEN
    );

    console.log('Configuration:');
    console.log(`  Account SID: ${process.env.TWILIO_ACCOUNT_SID?.slice(0, 10)}...`);
    console.log(`  From: ${process.env.TWILIO_PHONE_NUMBER}`);
    console.log(`  To: ${process.env.YOUR_PHONE_NUMBER}`);
    console.log('');

    try {
        const message = await client.messages.create({
            body: '🌱 SEED Interface is connected! You can now text this number to capture ideas.',
            from: process.env.TWILIO_PHONE_NUMBER,
            to: process.env.YOUR_PHONE_NUMBER!
        });

        console.log('Test message sent successfully!');
        console.log(`  Message SID: ${message.sid}`);
        console.log(`  Status: ${message.status}`);
        console.log('');
        console.log('Check your phone for the test message!');

    } catch (error) {
        console.error('Failed to send test message:', error);
        process.exit(1);
    }
}

testSms();
