/**
 * SMS Handler
 *
 * Handles incoming SMS/MMS messages from Twilio
 * and processes them through THE SEED
 */

import { Router, Request, Response } from 'express';
import twilio from 'twilio';
import { randomUUID } from 'crypto';
import { ideas, conversations, pendingQuestions } from '../db/index.js';
import { processIdea, processQuestionResponse } from '../processor/seed.js';
import { transcribeFromUrl, isAudioContentType } from '../processor/transcribe.js';

const router = Router();

// Twilio client for sending responses
const twilioClient = twilio(
    process.env.TWILIO_ACCOUNT_SID,
    process.env.TWILIO_AUTH_TOKEN
);

// Twilio webhook validation middleware
const validateTwilioRequest = (req: Request, res: Response, next: Function) => {
    // Skip validation in development
    if (process.env.NODE_ENV === 'development') {
        return next();
    }

    const twilioSignature = req.headers['x-twilio-signature'] as string;
    const url = `${req.protocol}://${req.get('host')}${req.originalUrl}`;

    const isValid = twilio.validateRequest(
        process.env.TWILIO_AUTH_TOKEN!,
        twilioSignature,
        url,
        req.body
    );

    if (isValid) {
        next();
    } else {
        res.status(403).send('Invalid Twilio signature');
    }
};

/**
 * Main SMS webhook endpoint
 * POST /sms/webhook
 */
router.post('/webhook', validateTwilioRequest, async (req: Request, res: Response) => {
    try {
        const {
            From: fromNumber,
            To: toNumber,
            Body: messageBody,
            NumMedia: numMediaStr,
            MessageSid: messageSid,
        } = req.body;

        const numMedia = parseInt(numMediaStr || '0', 10);

        console.log(`[SMS] Incoming from ${fromNumber}: "${messageBody}" (${numMedia} media)`);

        // Get or create conversation
        const conversation = conversations.getOrCreate(fromNumber);

        let rawContent = messageBody || '';
        let transcription: string | undefined;
        const mediaUrls: string[] = [];

        // Handle media attachments
        if (numMedia > 0) {
            for (let i = 0; i < numMedia; i++) {
                const mediaUrl = req.body[`MediaUrl${i}`];
                const mediaType = req.body[`MediaContentType${i}`];

                mediaUrls.push(mediaUrl);

                // If it's audio, transcribe it
                if (isAudioContentType(mediaType)) {
                    console.log(`[SMS] Transcribing audio: ${mediaType}`);
                    try {
                        transcription = await transcribeFromUrl(mediaUrl, true);
                        console.log(`[SMS] Transcribed: "${transcription}"`);

                        // If there's no text body, use transcription as raw content
                        if (!rawContent) {
                            rawContent = `[Voice Memo] ${transcription}`;
                        }
                    } catch (error) {
                        console.error('[SMS] Transcription failed:', error);
                        rawContent = rawContent || '[Voice memo - transcription failed]';
                    }
                }
            }
        }

        // Check if this is a response to a pending question
        const recentQuestion = checkForPendingQuestion(conversation.id);

        // Create the idea record
        const ideaId = randomUUID();
        ideas.create({
            id: ideaId,
            source: transcription ? 'voice' : 'sms',
            source_id: messageSid,
            source_phone: fromNumber,
            raw_content: rawContent,
            transcription: transcription,
            media_urls: mediaUrls.length > 0 ? JSON.stringify(mediaUrls) : undefined,
            tags: undefined
        });

        // Add to conversation
        conversations.addMessage(conversation.id, 'inbound', rawContent, ideaId);

        // Process through SEED
        let result;
        if (recentQuestion) {
            result = await processQuestionResponse(recentQuestion.id, rawContent);
        } else {
            result = await processIdea(rawContent, transcription ? 'voice' : 'sms', transcription);
        }

        // Update the idea with processing results
        ideas.update(ideaId, {
            processed_content: result.processedContent,
            connections: JSON.stringify(result.connections),
            learnings: JSON.stringify(result.learnings),
            questions: JSON.stringify(result.questions),
            expansions: JSON.stringify(result.expansions),
            importance_score: result.importance,
            acknowledged: true,
            acknowledgment: result.acknowledgment,
            acknowledged_at: new Date().toISOString()
        });

        // Send acknowledgment via Twilio
        await sendSms(fromNumber, result.acknowledgment);

        // Log outbound message
        conversations.addMessage(conversation.id, 'outbound', result.acknowledgment);

        console.log(`[SMS] Processed idea ${ideaId}, responded: "${result.acknowledgment}"`);

        // Return TwiML response (empty - we're sending via API)
        res.type('text/xml');
        res.send('<Response></Response>');

    } catch (error) {
        console.error('[SMS] Error processing message:', error);
        res.type('text/xml');
        res.send('<Response><Message>Got it! (Processing encountered an issue, but your idea is saved)</Message></Response>');
    }
});

/**
 * Status callback endpoint for delivery receipts
 * POST /sms/status
 */
router.post('/status', async (req: Request, res: Response) => {
    const { MessageSid, MessageStatus, ErrorCode } = req.body;

    console.log(`[SMS] Status update for ${MessageSid}: ${MessageStatus}${ErrorCode ? ` (Error: ${ErrorCode})` : ''}`);

    res.sendStatus(200);
});

/**
 * Send an SMS message
 */
export async function sendSms(to: string, message: string): Promise<string> {
    const result = await twilioClient.messages.create({
        body: message,
        from: process.env.TWILIO_PHONE_NUMBER,
        to: to,
        statusCallback: `${process.env.BASE_URL || 'https://your-domain.com'}/sms/status`
    });

    return result.sid;
}

/**
 * Send SMS to the configured user
 */
export async function sendToUser(message: string): Promise<string> {
    const userPhone = process.env.YOUR_PHONE_NUMBER;
    if (!userPhone) {
        throw new Error('YOUR_PHONE_NUMBER not configured');
    }
    return sendSms(userPhone, message);
}

/**
 * Check if there's a recent pending question this might be answering
 */
function checkForPendingQuestion(conversationId: string) {
    // Get messages in last hour
    const recentMessages = conversations.getMessages(conversationId, 10);

    // Check if last outbound message was a question
    const lastOutbound = recentMessages.find(m => m.direction === 'outbound');

    if (!lastOutbound) return null;

    // Check if it matches a pending question
    const pendingQs = pendingQuestions.getRecent(5);

    for (const q of pendingQs) {
        if (q.sent && !q.answered && lastOutbound.content.includes(q.question)) {
            return q;
        }
    }

    return null;
}

export default router;
