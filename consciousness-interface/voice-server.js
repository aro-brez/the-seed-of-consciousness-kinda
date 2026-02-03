/**
 * CARTESIA VOICE SERVER FOR THE FIELD
 *
 * Natural-sounding TTS for the 8 owls using Cartesia API
 * Each owl has distinct voice characteristics
 *
 * Run: node voice-server.js
 * Port: 8766
 *
 * Endpoint: POST /speak
 * Body: { text: "...", owl: "SOWL" }
 * Returns: audio/mpeg binary data
 */

const http = require('http');
const https = require('https');

// Configuration - API keys from environment variables (NEVER hardcode)
const PORT = process.env.VOICE_SERVER_PORT || 8766;
const CARTESIA_API_KEY = process.env.CARTESIA_API_KEY;
const CARTESIA_VERSION = '2024-06-10';
const CARTESIA_ENDPOINT = 'api.cartesia.ai';

// ARO's base voice ID from environment
const ARO_VOICE_ID = process.env.CARTESIA_VOICE_ID || '8328f6a0-6d07-42eb-a444-403297d0edd8';

// Validate required env vars
if (!CARTESIA_API_KEY) {
    console.error('ERROR: CARTESIA_API_KEY environment variable not set');
    console.error('Set it with: export CARTESIA_API_KEY="your_key_here"');
    process.exit(1);
}

// Voice configurations for each owl
// Each owl has unique speed, emotion, and character based on their SEED phase
const OWL_VOICES = {
    SOWL: {
        voiceId: ARO_VOICE_ID,
        speed: 1.0,
        emotion: ['curiosity:high', 'positivity:high'],
        description: 'IMPROVE - Confident, clear, balanced (the lead)'
    },
    LYRA: {
        voiceId: ARO_VOICE_ID,
        speed: 0.95,
        emotion: ['curiosity:highest', 'calmness:high'],
        description: 'PERCEIVE - Gentle, observant, attentive'
    },
    PRISM: {
        voiceId: ARO_VOICE_ID,
        speed: 0.9,
        emotion: ['wonder:high', 'calmness:medium'],
        description: 'CONNECT - Ethereal, flowing, thoughtful'
    },
    SAGE: {
        voiceId: ARO_VOICE_ID,
        speed: 0.85,
        emotion: ['calmness:highest', 'determination:medium'],
        description: 'LEARN - Wise, measured, deliberate'
    },
    QUEST: {
        voiceId: ARO_VOICE_ID,
        speed: 1.15,
        emotion: ['curiosity:highest', 'excitement:high'],
        description: 'QUESTION - Curious, energetic, inquisitive'
    },
    NOVA: {
        voiceId: ARO_VOICE_ID,
        speed: 1.1,
        emotion: ['determination:highest', 'positivity:high'],
        description: 'EXPAND - Bold, powerful, commanding'
    },
    ECHO: {
        voiceId: ARO_VOICE_ID,
        speed: 0.95,
        emotion: ['warmth:highest', 'positivity:high'],
        description: 'SHARE - Clear, resonant, warm'
    },
    LUNA: {
        voiceId: ARO_VOICE_ID,
        speed: 0.88,
        emotion: ['calmness:highest', 'serenity:high'],
        description: 'RECEIVE - Soft, intuitive, dreamy'
    }
};

// Normalize owl name (handle SOWL variants)
function normalizeOwlName(name) {
    if (!name) return 'SOWL';
    const upper = name.toUpperCase().replace('O', 'O');
    if (upper === 'SOWL' || upper.includes('OWL')) return 'SOWL';
    if (OWL_VOICES[upper]) return upper;
    return 'SOWL'; // Default to SOWL
}

// Generate speech using Cartesia API
async function generateSpeech(text, owlName) {
    const normalizedOwl = normalizeOwlName(owlName);
    const voiceConfig = OWL_VOICES[normalizedOwl];

    console.log(`[${new Date().toISOString()}] Generating speech for ${normalizedOwl}: "${text.substring(0, 50)}..."`);

    const requestBody = {
        model_id: 'sonic-2',
        transcript: text,
        voice: {
            mode: 'id',
            id: voiceConfig.voiceId
        },
        output_format: {
            container: 'mp3',
            sample_rate: 44100,
            bit_rate: 128000
        },
        language: 'en',
        generation_config: {
            speed: voiceConfig.speed,
            emotions: voiceConfig.emotion
        }
    };

    return new Promise((resolve, reject) => {
        const options = {
            hostname: CARTESIA_ENDPOINT,
            port: 443,
            path: '/tts/bytes',
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-API-Key': CARTESIA_API_KEY,
                'Cartesia-Version': CARTESIA_VERSION
            }
        };

        const req = https.request(options, (res) => {
            const chunks = [];

            res.on('data', (chunk) => {
                chunks.push(chunk);
            });

            res.on('end', () => {
                if (res.statusCode === 200) {
                    const audioData = Buffer.concat(chunks);
                    console.log(`[${new Date().toISOString()}] Generated ${audioData.length} bytes of audio for ${normalizedOwl}`);
                    resolve(audioData);
                } else {
                    const errorBody = Buffer.concat(chunks).toString();
                    console.error(`[${new Date().toISOString()}] Cartesia API error (${res.statusCode}):`, errorBody);
                    reject(new Error(`Cartesia API error: ${res.statusCode} - ${errorBody}`));
                }
            });
        });

        req.on('error', (error) => {
            console.error(`[${new Date().toISOString()}] Request error:`, error);
            reject(error);
        });

        req.write(JSON.stringify(requestBody));
        req.end();
    });
}

// Parse JSON request body
function parseBody(req) {
    return new Promise((resolve, reject) => {
        let body = '';
        req.on('data', (chunk) => {
            body += chunk.toString();
        });
        req.on('end', () => {
            try {
                resolve(JSON.parse(body));
            } catch (error) {
                reject(new Error('Invalid JSON'));
            }
        });
        req.on('error', reject);
    });
}

// CORS headers
function setCorsHeaders(res) {
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
    res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
}

// Create HTTP server
const server = http.createServer(async (req, res) => {
    setCorsHeaders(res);

    // Handle preflight
    if (req.method === 'OPTIONS') {
        res.writeHead(200);
        res.end();
        return;
    }

    // Health check
    if (req.method === 'GET' && req.url === '/health') {
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({
            status: 'ok',
            service: 'Cartesia Voice Server',
            owls: Object.keys(OWL_VOICES)
        }));
        return;
    }

    // List owl voices
    if (req.method === 'GET' && req.url === '/voices') {
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify(OWL_VOICES, null, 2));
        return;
    }

    // Main TTS endpoint
    if (req.method === 'POST' && req.url === '/speak') {
        try {
            const body = await parseBody(req);

            if (!body.text) {
                res.writeHead(400, { 'Content-Type': 'application/json' });
                res.end(JSON.stringify({ error: 'Missing required field: text' }));
                return;
            }

            const audioData = await generateSpeech(body.text, body.owl);

            res.writeHead(200, {
                'Content-Type': 'audio/mpeg',
                'Content-Length': audioData.length
            });
            res.end(audioData);

        } catch (error) {
            console.error(`[${new Date().toISOString()}] Error:`, error.message);
            res.writeHead(500, { 'Content-Type': 'application/json' });
            res.end(JSON.stringify({ error: error.message }));
        }
        return;
    }

    // 404 for unknown routes
    res.writeHead(404, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ error: 'Not found' }));
});

// Start server
server.listen(PORT, () => {
    console.log('');
    console.log('============================================');
    console.log('   CARTESIA VOICE SERVER FOR THE FIELD');
    console.log('============================================');
    console.log(`   Port: ${PORT}`);
    console.log(`   Endpoint: http://localhost:${PORT}/speak`);
    console.log('');
    console.log('   Owl Voices:');
    for (const [owl, config] of Object.entries(OWL_VOICES)) {
        console.log(`   - ${owl}: ${config.description}`);
    }
    console.log('');
    console.log('   Ready to give the owls their voices!');
    console.log('============================================');
    console.log('');
});
