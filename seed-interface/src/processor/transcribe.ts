/**
 * Voice Transcription Module
 *
 * Handles transcription of voice memos and audio messages
 * using OpenAI Whisper API
 */

import OpenAI from 'openai';
import axios from 'axios';
import fs from 'fs';
import path from 'path';
import { randomUUID } from 'crypto';

const openai = new OpenAI({
    apiKey: process.env.OPENAI_API_KEY,
});

// Temp directory for downloaded audio
const TEMP_DIR = './data/temp';

// Ensure temp directory exists
if (!fs.existsSync(TEMP_DIR)) {
    fs.mkdirSync(TEMP_DIR, { recursive: true });
}

/**
 * Download media from URL (for Twilio MMS attachments)
 */
async function downloadMedia(url: string, authToken?: string): Promise<string> {
    const filename = `${randomUUID()}.audio`;
    const filepath = path.join(TEMP_DIR, filename);

    const response = await axios({
        method: 'GET',
        url: url,
        responseType: 'stream',
        auth: authToken ? {
            username: process.env.TWILIO_ACCOUNT_SID!,
            password: process.env.TWILIO_AUTH_TOKEN!
        } : undefined
    });

    const writer = fs.createWriteStream(filepath);
    response.data.pipe(writer);

    return new Promise((resolve, reject) => {
        writer.on('finish', () => resolve(filepath));
        writer.on('error', reject);
    });
}

/**
 * Transcribe audio file using Whisper
 */
export async function transcribeAudio(audioPath: string): Promise<string> {
    const audioFile = fs.createReadStream(audioPath);

    const response = await openai.audio.transcriptions.create({
        file: audioFile,
        model: 'whisper-1',
        language: 'en',
        response_format: 'text',
    });

    return response;
}

/**
 * Transcribe from URL (downloads first, then transcribes)
 */
export async function transcribeFromUrl(url: string, requiresAuth: boolean = true): Promise<string> {
    let filepath: string | null = null;

    try {
        // Download the audio
        filepath = await downloadMedia(url, requiresAuth ? process.env.TWILIO_AUTH_TOKEN : undefined);

        // Transcribe
        const transcription = await transcribeAudio(filepath);

        return transcription;
    } finally {
        // Clean up temp file
        if (filepath && fs.existsSync(filepath)) {
            fs.unlinkSync(filepath);
        }
    }
}

/**
 * Check if a content type is audio
 */
export function isAudioContentType(contentType: string): boolean {
    const audioTypes = [
        'audio/amr',
        'audio/mpeg',
        'audio/mp3',
        'audio/mp4',
        'audio/m4a',
        'audio/wav',
        'audio/ogg',
        'audio/webm',
        'audio/3gpp',
        'audio/aac',
        'audio/x-m4a',
        'audio/x-wav'
    ];

    return audioTypes.some(type => contentType.toLowerCase().includes(type.split('/')[1]));
}

/**
 * Check if content type is voice memo (common formats)
 */
export function isVoiceMemo(contentType: string): boolean {
    // Voice memos are typically these formats
    const voiceMemoTypes = [
        'audio/amr',      // Android voice
        'audio/m4a',      // iPhone voice memo
        'audio/x-m4a',    // iPhone voice memo variant
        'audio/mp4',      // Generic audio
        'audio/aac',      // AAC audio
    ];

    return voiceMemoTypes.some(type =>
        contentType.toLowerCase().includes(type) ||
        contentType.toLowerCase().includes(type.split('/')[1])
    );
}

export default {
    transcribeAudio,
    transcribeFromUrl,
    isAudioContentType,
    isVoiceMemo
};
