/**
 * Social Media Integration Handler
 *
 * Captures likes, bookmarks, and saves from social platforms
 * and processes them through THE SEED
 *
 * Supported platforms:
 * - Twitter/X: Likes and bookmarks
 * - Instagram: Saved posts
 * - YouTube: Watch later and liked videos
 * - Pocket/Instapaper: Saved articles
 */

import { Router, Request, Response } from 'express';
import axios from 'axios';
import { randomUUID } from 'crypto';
import { getDb } from '../db/index.js';
import { processIdea } from '../processor/seed.js';

const router = Router();

// Types for social captures
interface SocialCapture {
    platform: string;
    action_type: string;
    external_id: string;
    content_url?: string;
    content_text?: string;
    content_author?: string;
}

/**
 * Generic webhook endpoint for social media events
 * POST /social/webhook
 *
 * This can receive webhooks from various automation services like:
 * - IFTTT
 * - Zapier
 * - Make (Integromat)
 * - Custom scripts
 */
router.post('/webhook', async (req: Request, res: Response) => {
    try {
        const {
            platform,
            action_type,
            external_id,
            content_url,
            content_text,
            content_author,
            api_key
        } = req.body;

        // Simple API key validation
        if (api_key !== process.env.SOCIAL_WEBHOOK_KEY) {
            return res.status(401).json({ error: 'Invalid API key' });
        }

        if (!platform || !action_type || !external_id) {
            return res.status(400).json({ error: 'Missing required fields: platform, action_type, external_id' });
        }

        console.log(`[Social] Capture from ${platform}: ${action_type} - ${external_id}`);

        // Store the capture
        const captureId = await storeSocialCapture({
            platform,
            action_type,
            external_id,
            content_url,
            content_text,
            content_author
        });

        // Process immediately if we have content
        if (content_text || content_url) {
            await processSocialCapture(captureId);
        }

        res.json({ success: true, capture_id: captureId });

    } catch (error) {
        console.error('[Social] Webhook error:', error);
        res.status(500).json({ error: 'Internal server error' });
    }
});

/**
 * Twitter-specific webhook (for Twitter API v2 webhook events)
 * POST /social/twitter/webhook
 */
router.post('/twitter/webhook', async (req: Request, res: Response) => {
    // Twitter sends a CRC challenge for webhook verification
    if (req.query.crc_token) {
        const crypto = await import('crypto');
        const hmac = crypto.createHmac('sha256', process.env.TWITTER_API_SECRET || '');
        hmac.update(req.query.crc_token as string);
        const response_token = 'sha256=' + hmac.digest('base64');
        return res.json({ response_token });
    }

    try {
        const events = req.body;

        // Handle favorite (like) events
        if (events.favorite_events) {
            for (const event of events.favorite_events) {
                await storeSocialCapture({
                    platform: 'twitter',
                    action_type: 'like',
                    external_id: event.favorited_status.id_str,
                    content_text: event.favorited_status.text,
                    content_author: event.favorited_status.user.screen_name,
                    content_url: `https://twitter.com/${event.favorited_status.user.screen_name}/status/${event.favorited_status.id_str}`
                });
            }
        }

        res.sendStatus(200);

    } catch (error) {
        console.error('[Social] Twitter webhook error:', error);
        res.status(500).json({ error: 'Internal server error' });
    }
});

/**
 * Pocket webhook endpoint
 * POST /social/pocket/webhook
 */
router.post('/pocket/webhook', async (req: Request, res: Response) => {
    try {
        const { url, title, excerpt } = req.body;

        const captureId = await storeSocialCapture({
            platform: 'pocket',
            action_type: 'save',
            external_id: url,
            content_url: url,
            content_text: `${title}\n\n${excerpt || ''}`.trim(),
        });

        await processSocialCapture(captureId);

        res.json({ success: true });

    } catch (error) {
        console.error('[Social] Pocket webhook error:', error);
        res.status(500).json({ error: 'Internal server error' });
    }
});

/**
 * IFTTT-style generic webhook
 * POST /social/ifttt
 *
 * Expected body:
 * {
 *   "platform": "instagram|twitter|youtube|etc",
 *   "action": "like|save|bookmark|watch_later",
 *   "url": "https://...",
 *   "text": "Content text",
 *   "author": "username"
 * }
 */
router.post('/ifttt', async (req: Request, res: Response) => {
    try {
        const { platform, action, url, text, author, id } = req.body;

        if (!platform || !action) {
            return res.status(400).json({ error: 'Missing platform or action' });
        }

        const captureId = await storeSocialCapture({
            platform: platform.toLowerCase(),
            action_type: action.toLowerCase(),
            external_id: id || url || randomUUID(),
            content_url: url,
            content_text: text,
            content_author: author
        });

        // Process if we have content
        if (text || url) {
            await processSocialCapture(captureId);
        }

        res.json({ success: true, capture_id: captureId });

    } catch (error) {
        console.error('[Social] IFTTT webhook error:', error);
        res.status(500).json({ error: 'Internal server error' });
    }
});

/**
 * Store a social media capture
 */
async function storeSocialCapture(capture: SocialCapture): Promise<string> {
    const db = getDb();
    const id = randomUUID();

    db.prepare(`
        INSERT INTO social_captures (id, platform, action_type, external_id, content_url, content_text, content_author)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    `).run(
        id,
        capture.platform,
        capture.action_type,
        capture.external_id,
        capture.content_url,
        capture.content_text,
        capture.content_author
    );

    return id;
}

/**
 * Process a social capture through SEED
 */
async function processSocialCapture(captureId: string): Promise<void> {
    const db = getDb();
    const capture = db.prepare('SELECT * FROM social_captures WHERE id = ?').get(captureId) as SocialCapture & { id: string };

    if (!capture) {
        throw new Error(`Capture not found: ${captureId}`);
    }

    // Build content for processing
    let content = '';

    if (capture.content_text) {
        content = capture.content_text;
    }

    if (capture.content_url && !content.includes(capture.content_url)) {
        content += `\n\nSource: ${capture.content_url}`;
    }

    if (capture.content_author) {
        content += `\n\nBy: @${capture.content_author}`;
    }

    const sourceLabel = `${capture.platform}-${capture.action_type}`;

    console.log(`[Social] Processing capture: ${sourceLabel}`);

    // Process through SEED
    const result = await processIdea(content.trim(), sourceLabel);

    // Create an idea from this
    const ideaId = randomUUID();
    db.prepare(`
        INSERT INTO ideas (id, source, source_id, raw_content, processed_content, connections, learnings, questions, expansions, importance_score, acknowledged)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, TRUE)
    `).run(
        ideaId,
        sourceLabel,
        capture.external_id,
        content.trim(),
        result.processedContent,
        JSON.stringify(result.connections),
        JSON.stringify(result.learnings),
        JSON.stringify(result.questions),
        JSON.stringify(result.expansions),
        result.importance
    );

    // Mark capture as processed and link to idea
    db.prepare(`
        UPDATE social_captures
        SET processed = TRUE, idea_id = ?
        WHERE id = ?
    `).run(ideaId, captureId);

    console.log(`[Social] Created idea ${ideaId} from ${sourceLabel}`);
}

/**
 * Fetch Twitter likes (for polling mode)
 * Call this periodically if not using webhooks
 */
export async function fetchTwitterLikes(): Promise<void> {
    const bearerToken = process.env.TWITTER_BEARER_TOKEN;
    if (!bearerToken) {
        console.log('[Social] Twitter bearer token not configured');
        return;
    }

    try {
        // This would need your Twitter user ID
        const userId = process.env.TWITTER_USER_ID;
        if (!userId) {
            console.log('[Social] Twitter user ID not configured');
            return;
        }

        const response = await axios.get(
            `https://api.twitter.com/2/users/${userId}/liked_tweets`,
            {
                headers: { Authorization: `Bearer ${bearerToken}` },
                params: {
                    'tweet.fields': 'text,author_id,created_at',
                    'user.fields': 'username',
                    'expansions': 'author_id',
                    'max_results': 10
                }
            }
        );

        const tweets = response.data.data || [];
        const users = response.data.includes?.users || [];

        for (const tweet of tweets) {
            const author = users.find((u: { id: string }) => u.id === tweet.author_id);

            // Check if already captured
            const db = getDb();
            const existing = db.prepare(
                'SELECT id FROM social_captures WHERE platform = ? AND external_id = ?'
            ).get('twitter', tweet.id);

            if (!existing) {
                const captureId = await storeSocialCapture({
                    platform: 'twitter',
                    action_type: 'like',
                    external_id: tweet.id,
                    content_text: tweet.text,
                    content_author: author?.username,
                    content_url: `https://twitter.com/${author?.username}/status/${tweet.id}`
                });

                await processSocialCapture(captureId);
            }
        }

    } catch (error) {
        console.error('[Social] Twitter fetch error:', error);
    }
}

/**
 * Get unprocessed social captures
 */
export function getUnprocessedCaptures(): Array<SocialCapture & { id: string }> {
    const db = getDb();
    return db.prepare(
        'SELECT * FROM social_captures WHERE processed = FALSE ORDER BY captured_at ASC'
    ).all() as Array<SocialCapture & { id: string }>;
}

/**
 * Process all unprocessed captures
 */
export async function processAllUnprocessed(): Promise<number> {
    const captures = getUnprocessedCaptures();
    let processed = 0;

    for (const capture of captures) {
        try {
            await processSocialCapture(capture.id);
            processed++;
        } catch (error) {
            console.error(`[Social] Failed to process capture ${capture.id}:`, error);
        }
    }

    return processed;
}

export default router;
