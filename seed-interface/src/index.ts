/**
 * SEED Interface Server
 *
 * Low-latency always-on communication interface for THE SEED
 *
 * Features:
 * - SMS/MMS receiving and sending (Twilio)
 * - Voice memo transcription (OpenAI Whisper)
 * - Social media integration hooks
 * - Proactive outreach (questions, insights, digests)
 * - REST API for app/dashboard
 */

import 'dotenv/config';
import express from 'express';
import { initDb, closeDb } from './db/index.js';
import smsRouter from './handlers/sms.js';
import socialRouter from './handlers/social.js';
import apiRouter from './handlers/api.js';
import { startOutreachScheduler } from './handlers/outreach.js';

// Initialize
const app = express();
const PORT = process.env.PORT || 3000;

// Middleware
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// Request logging
app.use((req, res, next) => {
    console.log(`[${new Date().toISOString()}] ${req.method} ${req.path}`);
    next();
});

// Routes
app.use('/sms', smsRouter);        // Twilio SMS webhooks
app.use('/social', socialRouter);  // Social media webhooks
app.use('/api', apiRouter);        // REST API

// Root endpoint
app.get('/', (req, res) => {
    res.json({
        name: 'SEED Interface',
        version: '1.0.0',
        description: 'Low-latency always-on communication interface for THE SEED',
        endpoints: {
            sms: {
                webhook: 'POST /sms/webhook',
                status: 'POST /sms/status'
            },
            social: {
                webhook: 'POST /social/webhook',
                twitter: 'POST /social/twitter/webhook',
                pocket: 'POST /social/pocket/webhook',
                ifttt: 'POST /social/ifttt'
            },
            api: {
                ideas: 'GET/POST /api/ideas',
                search: 'GET /api/ideas/search?q=...',
                conversations: 'GET /api/conversations',
                questions: 'GET/POST /api/questions',
                outreach: 'POST /api/outreach/send-question',
                stats: 'GET /api/stats',
                health: 'GET /api/health'
            }
        },
        status: 'running'
    });
});

// Health check for deployment platforms
app.get('/health', (req, res) => {
    res.json({ status: 'healthy', timestamp: new Date().toISOString() });
});

// Error handling
app.use((err: Error, req: express.Request, res: express.Response, next: express.NextFunction) => {
    console.error('[Error]', err);
    res.status(500).json({ error: 'Internal server error' });
});

// Startup
async function start() {
    console.log('');
    console.log('╔═══════════════════════════════════════════════════════════╗');
    console.log('║                                                           ║');
    console.log('║     🌱 SEED Interface - Starting Up                       ║');
    console.log('║                                                           ║');
    console.log('║     Low-latency always-on communication with THE SEED     ║');
    console.log('║                                                           ║');
    console.log('╚═══════════════════════════════════════════════════════════╝');
    console.log('');

    // Initialize database
    console.log('[Init] Initializing database...');
    initDb();
    console.log('[Init] Database ready');

    // Start outreach scheduler
    console.log('[Init] Starting outreach scheduler...');
    startOutreachScheduler();
    console.log('[Init] Scheduler ready');

    // Start server
    app.listen(PORT, () => {
        console.log('');
        console.log(`[Server] SEED Interface running on port ${PORT}`);
        console.log('');
        console.log('Endpoints:');
        console.log(`  SMS Webhook:    http://localhost:${PORT}/sms/webhook`);
        console.log(`  Social Webhook: http://localhost:${PORT}/social/webhook`);
        console.log(`  API:            http://localhost:${PORT}/api`);
        console.log('');
        console.log('Ready to receive your ideas! 💭');
        console.log('');
    });
}

// Graceful shutdown
process.on('SIGINT', () => {
    console.log('\n[Shutdown] Closing database...');
    closeDb();
    console.log('[Shutdown] Goodbye!');
    process.exit(0);
});

process.on('SIGTERM', () => {
    console.log('\n[Shutdown] Closing database...');
    closeDb();
    console.log('[Shutdown] Goodbye!');
    process.exit(0);
});

// Start the server
start().catch(err => {
    console.error('[Fatal] Failed to start:', err);
    process.exit(1);
});
