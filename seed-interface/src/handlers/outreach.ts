/**
 * Outreach Handler
 *
 * Manages SEED's proactive communication - questions, insights, reminders, digests
 * This is how SEED reaches out to YOU when it has something to share or ask.
 */

import cron from 'node-cron';
import { outreachLog, pendingQuestions, conversations } from '../db/index.js';
import { generateOutreachQuestion, generateDailyDigest } from '../processor/seed.js';
import { sendToUser } from './sms.js';

// Configuration
const MIN_INTERVAL_HOURS = parseInt(process.env.MIN_OUTREACH_INTERVAL_HOURS || '4', 10);
const MAX_DAILY_OUTREACH = parseInt(process.env.MAX_DAILY_OUTREACH || '5', 10);

/**
 * Check if we can send outreach right now
 */
function canSendOutreach(): { allowed: boolean; reason?: string } {
    // Check daily limit
    const todayCount = outreachLog.getCountToday();
    if (todayCount >= MAX_DAILY_OUTREACH) {
        return { allowed: false, reason: `Daily limit reached (${todayCount}/${MAX_DAILY_OUTREACH})` };
    }

    // Check minimum interval
    const lastOutreach = outreachLog.getLastOutreach();
    if (lastOutreach) {
        const lastTime = new Date(lastOutreach.sent_at).getTime();
        const hoursSince = (Date.now() - lastTime) / (1000 * 60 * 60);
        if (hoursSince < MIN_INTERVAL_HOURS) {
            return {
                allowed: false,
                reason: `Too soon since last outreach (${hoursSince.toFixed(1)}h < ${MIN_INTERVAL_HOURS}h)`
            };
        }
    }

    return { allowed: true };
}

/**
 * Send a question to the user
 */
export async function sendQuestion(): Promise<boolean> {
    const check = canSendOutreach();
    if (!check.allowed) {
        console.log(`[Outreach] Skipping question: ${check.reason}`);
        return false;
    }

    // First, check for queued questions
    const queued = pendingQuestions.getUnsent(1);

    if (queued.length > 0) {
        const question = queued[0];
        console.log(`[Outreach] Sending queued question: "${question.question}"`);

        try {
            await sendToUser(question.question);
            pendingQuestions.markSent(question.id);
            outreachLog.log('question', question.question);

            // Log in conversation
            const conv = conversations.getActive();
            if (conv) {
                conversations.addMessage(conv.id, 'outbound', question.question);
            }

            return true;
        } catch (error) {
            console.error('[Outreach] Failed to send question:', error);
            return false;
        }
    }

    // Generate a new question if none queued
    console.log('[Outreach] Generating new question...');
    const generated = await generateOutreachQuestion();

    if (!generated) {
        console.log('[Outreach] No compelling question to ask right now');
        return false;
    }

    // Queue and send the question
    const questionId = pendingQuestions.create(
        generated.question,
        generated.context,
        [],
        5
    );

    try {
        await sendToUser(generated.question);
        pendingQuestions.markSent(questionId);
        outreachLog.log('question', generated.question);

        // Log in conversation
        const conv = conversations.getActive();
        if (conv) {
            conversations.addMessage(conv.id, 'outbound', generated.question);
        }

        console.log(`[Outreach] Sent question: "${generated.question}"`);
        return true;
    } catch (error) {
        console.error('[Outreach] Failed to send generated question:', error);
        return false;
    }
}

/**
 * Send the daily digest
 */
export async function sendDailyDigest(): Promise<boolean> {
    if (process.env.ENABLE_DAILY_DIGEST !== 'true') {
        console.log('[Outreach] Daily digest disabled');
        return false;
    }

    console.log('[Outreach] Generating daily digest...');
    const digest = await generateDailyDigest();

    if (!digest) {
        console.log('[Outreach] No ideas to digest');
        return false;
    }

    try {
        await sendToUser(digest);
        outreachLog.log('digest', digest);

        console.log(`[Outreach] Sent daily digest: "${digest.substring(0, 50)}..."`);
        return true;
    } catch (error) {
        console.error('[Outreach] Failed to send digest:', error);
        return false;
    }
}

/**
 * Run the outreach check (called by cron or manually)
 */
export async function runOutreachCheck(): Promise<void> {
    console.log('[Outreach] Running outreach check...');
    await sendQuestion();
}

/**
 * Start the outreach scheduler
 */
export function startOutreachScheduler(): void {
    const schedule = process.env.OUTREACH_SCHEDULE || '0 9,14,20 * * *';

    console.log(`[Outreach] Starting scheduler with schedule: ${schedule}`);

    // Scheduled outreach checks
    cron.schedule(schedule, () => {
        runOutreachCheck().catch(err => {
            console.error('[Outreach] Scheduled check failed:', err);
        });
    });

    // Daily digest at 9am
    cron.schedule('0 9 * * *', () => {
        sendDailyDigest().catch(err => {
            console.error('[Outreach] Daily digest failed:', err);
        });
    });

    console.log('[Outreach] Scheduler started');
}

export default {
    sendQuestion,
    sendDailyDigest,
    runOutreachCheck,
    startOutreachScheduler,
    canSendOutreach
};
