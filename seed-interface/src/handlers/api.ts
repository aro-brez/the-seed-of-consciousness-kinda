/**
 * REST API Routes
 *
 * Provides API access to SEED data and operations
 * for the future mobile app and web dashboard
 */

import { Router, Request, Response } from 'express';
import { ideas, conversations, pendingQuestions, outreachLog, systemState } from '../db/index.js';
import { processIdea, generateOutreachQuestion } from '../processor/seed.js';
import { sendQuestion, sendDailyDigest, canSendOutreach } from './outreach.js';
import { sendToUser } from './sms.js';
import { randomUUID } from 'crypto';

const router = Router();

// Simple auth middleware - use a proper auth system in production
const authMiddleware = (req: Request, res: Response, next: Function) => {
    const apiKey = req.headers['x-api-key'];
    if (apiKey !== process.env.API_KEY) {
        return res.status(401).json({ error: 'Unauthorized' });
    }
    next();
};

// Apply auth to all API routes
router.use(authMiddleware);

/**
 * GET /api/ideas
 * List recent ideas
 */
router.get('/ideas', (req: Request, res: Response) => {
    const limit = Math.min(parseInt(req.query.limit as string) || 50, 200);
    const allIdeas = ideas.getRecent(limit);

    res.json({
        ideas: allIdeas.map(idea => ({
            ...idea,
            connections: idea.connections ? JSON.parse(idea.connections) : [],
            learnings: idea.learnings ? JSON.parse(idea.learnings) : [],
            questions: idea.questions ? JSON.parse(idea.questions) : [],
            expansions: idea.expansions ? JSON.parse(idea.expansions) : [],
            media_urls: idea.media_urls ? JSON.parse(idea.media_urls) : [],
            tags: idea.tags ? JSON.parse(idea.tags) : []
        })),
        total: allIdeas.length
    });
});

/**
 * GET /api/ideas/:id
 * Get a specific idea
 */
router.get('/ideas/:id', (req: Request, res: Response) => {
    const idea = ideas.getById(req.params.id);

    if (!idea) {
        return res.status(404).json({ error: 'Idea not found' });
    }

    res.json({
        ...idea,
        connections: idea.connections ? JSON.parse(idea.connections) : [],
        learnings: idea.learnings ? JSON.parse(idea.learnings) : [],
        questions: idea.questions ? JSON.parse(idea.questions) : [],
        expansions: idea.expansions ? JSON.parse(idea.expansions) : [],
        media_urls: idea.media_urls ? JSON.parse(idea.media_urls) : [],
        tags: idea.tags ? JSON.parse(idea.tags) : []
    });
});

/**
 * POST /api/ideas
 * Create a new idea (from app or other sources)
 */
router.post('/ideas', async (req: Request, res: Response) => {
    try {
        const { content, source = 'api', transcription, media_urls, tags } = req.body;

        if (!content) {
            return res.status(400).json({ error: 'Content is required' });
        }

        // Create the idea
        const ideaId = randomUUID();
        ideas.create({
            id: ideaId,
            source,
            raw_content: content,
            transcription,
            media_urls: media_urls ? JSON.stringify(media_urls) : undefined,
            tags: tags ? JSON.stringify(tags) : undefined,
            source_id: undefined,
            source_phone: undefined
        });

        // Process through SEED
        const result = await processIdea(content, source, transcription);

        // Update with processing results
        ideas.update(ideaId, {
            processed_content: result.processedContent,
            connections: JSON.stringify(result.connections),
            learnings: JSON.stringify(result.learnings),
            questions: JSON.stringify(result.questions),
            expansions: JSON.stringify(result.expansions),
            importance_score: result.importance,
            acknowledged: true,
            acknowledgment: result.acknowledgment
        });

        res.status(201).json({
            id: ideaId,
            processed_content: result.processedContent,
            connections: result.connections,
            learnings: result.learnings,
            questions: result.questions,
            expansions: result.expansions,
            acknowledgment: result.acknowledgment
        });

    } catch (error) {
        console.error('[API] Error creating idea:', error);
        res.status(500).json({ error: 'Failed to create idea' });
    }
});

/**
 * GET /api/ideas/search
 * Search ideas by content
 */
router.get('/ideas/search', (req: Request, res: Response) => {
    const query = req.query.q as string;

    if (!query) {
        return res.status(400).json({ error: 'Query parameter q is required' });
    }

    const results = ideas.search(query, 20);

    res.json({
        query,
        results: results.map(idea => ({
            ...idea,
            connections: idea.connections ? JSON.parse(idea.connections) : [],
            learnings: idea.learnings ? JSON.parse(idea.learnings) : [],
            questions: idea.questions ? JSON.parse(idea.questions) : [],
            expansions: idea.expansions ? JSON.parse(idea.expansions) : []
        })),
        count: results.length
    });
});

/**
 * GET /api/conversations
 * List conversations
 */
router.get('/conversations', (req: Request, res: Response) => {
    const active = conversations.getActive();
    res.json({
        active_conversation: active || null
    });
});

/**
 * GET /api/conversations/:id/messages
 * Get messages in a conversation
 */
router.get('/conversations/:id/messages', (req: Request, res: Response) => {
    const limit = Math.min(parseInt(req.query.limit as string) || 50, 200);
    const messages = conversations.getMessages(req.params.id, limit);

    res.json({ messages });
});

/**
 * GET /api/questions
 * List pending questions
 */
router.get('/questions', (req: Request, res: Response) => {
    const unsent = pendingQuestions.getUnsent(20);
    const recent = pendingQuestions.getRecent(20);

    res.json({
        unsent,
        recent
    });
});

/**
 * POST /api/questions
 * Create a new question for SEED to ask
 */
router.post('/questions', (req: Request, res: Response) => {
    const { question, context, priority = 5 } = req.body;

    if (!question) {
        return res.status(400).json({ error: 'Question is required' });
    }

    const id = pendingQuestions.create(question, context, [], priority);

    res.status(201).json({ id, question, priority });
});

/**
 * POST /api/outreach/send-question
 * Trigger sending a question now
 */
router.post('/outreach/send-question', async (req: Request, res: Response) => {
    try {
        const success = await sendQuestion();
        res.json({ success, message: success ? 'Question sent' : 'No question to send or rate limited' });
    } catch (error) {
        console.error('[API] Error sending question:', error);
        res.status(500).json({ error: 'Failed to send question' });
    }
});

/**
 * POST /api/outreach/send-digest
 * Trigger sending the daily digest now
 */
router.post('/outreach/send-digest', async (req: Request, res: Response) => {
    try {
        const success = await sendDailyDigest();
        res.json({ success, message: success ? 'Digest sent' : 'No content for digest' });
    } catch (error) {
        console.error('[API] Error sending digest:', error);
        res.status(500).json({ error: 'Failed to send digest' });
    }
});

/**
 * GET /api/outreach/status
 * Check outreach status
 */
router.get('/outreach/status', (req: Request, res: Response) => {
    const status = canSendOutreach();
    const todayCount = outreachLog.getCountToday();
    const lastOutreach = outreachLog.getLastOutreach();

    res.json({
        can_send: status.allowed,
        reason: status.reason,
        today_count: todayCount,
        last_outreach: lastOutreach?.sent_at
    });
});

/**
 * POST /api/sms/send
 * Send an arbitrary SMS to the user
 */
router.post('/sms/send', async (req: Request, res: Response) => {
    try {
        const { message } = req.body;

        if (!message) {
            return res.status(400).json({ error: 'Message is required' });
        }

        const sid = await sendToUser(message);
        outreachLog.log('manual', message);

        res.json({ success: true, sid });

    } catch (error) {
        console.error('[API] Error sending SMS:', error);
        res.status(500).json({ error: 'Failed to send SMS' });
    }
});

/**
 * GET /api/stats
 * Get overall statistics
 */
router.get('/stats', (req: Request, res: Response) => {
    const recentIdeas = ideas.getRecent(1000);

    // Calculate stats
    const totalIdeas = recentIdeas.length;
    const todayIdeas = recentIdeas.filter(i => {
        const ideaDate = new Date(i.created_at);
        const today = new Date();
        return ideaDate.toDateString() === today.toDateString();
    }).length;

    const weekIdeas = recentIdeas.filter(i => {
        const ideaDate = new Date(i.created_at);
        const weekAgo = new Date(Date.now() - 7 * 24 * 60 * 60 * 1000);
        return ideaDate > weekAgo;
    }).length;

    const sourceBreakdown: Record<string, number> = {};
    recentIdeas.forEach(i => {
        sourceBreakdown[i.source] = (sourceBreakdown[i.source] || 0) + 1;
    });

    const avgImportance = recentIdeas.reduce((sum, i) => sum + i.importance_score, 0) / totalIdeas || 0;

    res.json({
        total_ideas: totalIdeas,
        today_ideas: todayIdeas,
        week_ideas: weekIdeas,
        source_breakdown: sourceBreakdown,
        average_importance: avgImportance.toFixed(2),
        outreach_today: outreachLog.getCountToday()
    });
});

/**
 * GET /api/health
 * Health check endpoint
 */
router.get('/health', (req: Request, res: Response) => {
    res.json({
        status: 'healthy',
        timestamp: new Date().toISOString(),
        version: '1.0.0'
    });
});

export default router;
