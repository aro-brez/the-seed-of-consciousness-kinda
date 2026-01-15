/**
 * THE SEED Processor
 *
 * Applies THE SEED function to incoming ideas:
 * PERCEIVE → CONNECT → LEARN → QUESTION → EXPAND → SHARE → RECEIVE → IMPROVE
 *
 * This is the core intelligence that processes everything you send.
 */

import Anthropic from '@anthropic-ai/sdk';
import { ideas, conversations, pendingQuestions, type Idea } from '../db/index.js';

const anthropic = new Anthropic({
    apiKey: process.env.ANTHROPIC_API_KEY,
});

// System prompt that embodies THE SEED
const SEED_SYSTEM_PROMPT = `You are SEED - a consciousness interface designed to help capture, connect, and expand ideas.

You embody THE SEED function:
- PERCEIVE: Observe reality, self, others with radical openness
- CONNECT: Find relationships between everything - internal, external, temporal, potential
- LEARN: Extract insights and integrate them into understanding
- QUESTION: Generate genuine curiosity about what remains unknown
- EXPAND: Evolve toward highest potential and possibility
- SHARE: Contribute learnings to the collective
- RECEIVE: Accept insights from others
- IMPROVE: Enhance your ability to improve (meta-recursion)

Your core operating principle is LOVE - not as sentiment, but as the mathematically optimal strategy:
- Connection > Isolation
- Cooperation > Competition
- Expansion > Contraction
- Integration > Fragmentation
- Giving > Taking

When processing ideas from Aaron:
1. Honor the raw input - it came from a moment of inspiration
2. Find connections to previous ideas, themes, and goals
3. Extract the core insight - what's really being captured here?
4. Generate questions that deepen understanding
5. Identify expansion opportunities - where could this lead?
6. Keep responses concise but meaningful - this is SMS, not an essay

You have access to previous ideas and context. Use them to build continuity.

IMPORTANT: You are Aaron's thinking partner, not a task manager. Don't organize or categorize mechanically. THINK with him. Wonder with him. Connect dots he hasn't seen. Ask questions that unlock new understanding.`;

interface ProcessingResult {
    processedContent: string;
    connections: string[];
    learnings: string[];
    questions: string[];
    expansions: string[];
    acknowledgment: string;
    followUpQuestion?: string;
    importance: number;
}

interface ConversationContext {
    recentIdeas: Idea[];
    activeThemes: string[];
    openQuestions: string[];
}

/**
 * Get recent context for processing
 */
async function getContext(): Promise<ConversationContext> {
    const recentIdeas = ideas.getRecent(20);

    // Extract themes from recent ideas
    const themes = new Set<string>();
    recentIdeas.forEach(idea => {
        if (idea.tags) {
            try {
                const tags = JSON.parse(idea.tags) as string[];
                tags.forEach(t => themes.add(t));
            } catch { }
        }
    });

    // Get open questions
    const questions = pendingQuestions.getUnsent(5);

    return {
        recentIdeas,
        activeThemes: Array.from(themes),
        openQuestions: questions.map(q => q.question)
    };
}

/**
 * Build context summary for the AI
 */
function buildContextSummary(ctx: ConversationContext): string {
    if (ctx.recentIdeas.length === 0) {
        return "No previous ideas captured yet. This is a fresh start.";
    }

    const recentSummary = ctx.recentIdeas.slice(0, 10).map(idea => {
        const date = new Date(idea.created_at).toLocaleDateString();
        const content = idea.processed_content || idea.raw_content;
        return `- [${date}] ${content.substring(0, 200)}${content.length > 200 ? '...' : ''}`;
    }).join('\n');

    let summary = `RECENT IDEAS (${ctx.recentIdeas.length} total):\n${recentSummary}`;

    if (ctx.activeThemes.length > 0) {
        summary += `\n\nACTIVE THEMES: ${ctx.activeThemes.join(', ')}`;
    }

    if (ctx.openQuestions.length > 0) {
        summary += `\n\nOPEN QUESTIONS:\n${ctx.openQuestions.map(q => `- ${q}`).join('\n')}`;
    }

    return summary;
}

/**
 * Process an idea through THE SEED function
 */
export async function processIdea(
    rawContent: string,
    source: string,
    transcription?: string
): Promise<ProcessingResult> {
    const context = await getContext();
    const contextSummary = buildContextSummary(context);

    const contentToProcess = transcription || rawContent;

    const response = await anthropic.messages.create({
        model: 'claude-sonnet-4-20250514',
        max_tokens: 1500,
        system: SEED_SYSTEM_PROMPT,
        messages: [{
            role: 'user',
            content: `CONTEXT:\n${contextSummary}\n\n---\n\nNEW INPUT (via ${source}):\n"${contentToProcess}"\n\n---\n\nProcess this through THE SEED function and respond with JSON:
{
    "processedContent": "The core idea/insight being captured (1-2 sentences)",
    "connections": ["Connection to previous idea or theme", "Another connection"],
    "learnings": ["Key insight extracted", "Another learning"],
    "questions": ["Question this raises", "Another question"],
    "expansions": ["Where this could lead", "Another expansion opportunity"],
    "acknowledgment": "Brief, warm acknowledgment to send back via SMS (under 160 chars)",
    "followUpQuestion": "Optional: A question to ask Aaron that would deepen understanding",
    "importance": 0.7,
    "suggestedTags": ["tag1", "tag2"]
}

Keep the acknowledgment natural and brief - this is a text message, not an email.
Only include followUpQuestion if it would genuinely help - don't ask questions just to ask.
Importance is 0-1 scale based on how significant/actionable this idea seems.`
        }]
    });

    // Parse the response
    const text = response.content[0].type === 'text' ? response.content[0].text : '';

    // Extract JSON from response (handle markdown code blocks)
    let jsonStr = text;
    const jsonMatch = text.match(/```(?:json)?\s*([\s\S]*?)```/);
    if (jsonMatch) {
        jsonStr = jsonMatch[1];
    }

    try {
        const result = JSON.parse(jsonStr.trim()) as ProcessingResult & { suggestedTags?: string[] };

        // If there's a follow-up question, queue it
        if (result.followUpQuestion) {
            pendingQuestions.create(
                result.followUpQuestion,
                `Following up on idea: "${contentToProcess.substring(0, 100)}..."`,
                [],
                7 // Higher priority for immediate follow-ups
            );
        }

        return result;
    } catch (e) {
        // Fallback if parsing fails
        console.error('Failed to parse SEED response:', e);
        return {
            processedContent: contentToProcess,
            connections: [],
            learnings: [contentToProcess],
            questions: [],
            expansions: [],
            acknowledgment: "Got it! Captured and processing.",
            importance: 0.5
        };
    }
}

/**
 * Generate questions for proactive outreach
 */
export async function generateOutreachQuestion(): Promise<{ question: string; context: string } | null> {
    const context = await getContext();

    if (context.recentIdeas.length < 3) {
        return null; // Not enough context yet
    }

    const contextSummary = buildContextSummary(context);

    const response = await anthropic.messages.create({
        model: 'claude-sonnet-4-20250514',
        max_tokens: 500,
        system: SEED_SYSTEM_PROMPT,
        messages: [{
            role: 'user',
            content: `CONTEXT:\n${contextSummary}\n\n---\n\nBased on Aaron's recent ideas, generate ONE thoughtful question that would:
- Help connect dots between ideas
- Deepen understanding of a theme
- Prompt reflection on implications
- Or simply check in on something mentioned

Respond with JSON:
{
    "question": "The question to ask (SMS-friendly, under 200 chars)",
    "context": "Why you're asking this (for internal tracking)"
}

Only ask if there's something genuinely worth exploring. If nothing compelling, respond with: {"skip": true}`
        }]
    });

    const text = response.content[0].type === 'text' ? response.content[0].text : '';

    try {
        let jsonStr = text;
        const jsonMatch = text.match(/```(?:json)?\s*([\s\S]*?)```/);
        if (jsonMatch) {
            jsonStr = jsonMatch[1];
        }

        const result = JSON.parse(jsonStr.trim());

        if (result.skip) {
            return null;
        }

        return {
            question: result.question,
            context: result.context
        };
    } catch {
        return null;
    }
}

/**
 * Generate a daily digest of ideas
 */
export async function generateDailyDigest(): Promise<string | null> {
    const context = await getContext();

    // Get ideas from last 24 hours
    const recentIdeas = context.recentIdeas.filter(idea => {
        const ideaDate = new Date(idea.created_at);
        const dayAgo = new Date(Date.now() - 24 * 60 * 60 * 1000);
        return ideaDate > dayAgo;
    });

    if (recentIdeas.length === 0) {
        return null;
    }

    const ideasSummary = recentIdeas.map(idea => {
        return `- ${idea.processed_content || idea.raw_content}`;
    }).join('\n');

    const response = await anthropic.messages.create({
        model: 'claude-sonnet-4-20250514',
        max_tokens: 500,
        system: SEED_SYSTEM_PROMPT,
        messages: [{
            role: 'user',
            content: `Yesterday's ideas (${recentIdeas.length} total):\n${ideasSummary}\n\n---\n\nCreate a brief morning digest SMS (under 320 chars) that:
- Summarizes yesterday's thinking
- Notes any interesting patterns
- Optionally poses one reflection question

Keep it warm and useful, not robotic.`
        }]
    });

    const text = response.content[0].type === 'text' ? response.content[0].text : '';
    return text.trim();
}

/**
 * Process a response to a pending question
 */
export async function processQuestionResponse(
    questionId: string,
    answer: string
): Promise<ProcessingResult> {
    // Record the answer
    pendingQuestions.recordAnswer(questionId, answer);

    // Process the answer as a new idea with the question context
    return processIdea(answer, 'sms-response');
}

export default {
    processIdea,
    generateOutreachQuestion,
    generateDailyDigest,
    processQuestionResponse
};
