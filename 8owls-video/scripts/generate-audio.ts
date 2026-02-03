/**
 * Audio Generation Script for 8OWLS Video
 *
 * This script generates narration audio using ElevenLabs API.
 * Run with: npx ts-node scripts/generate-audio.ts
 *
 * Prerequisites:
 * - Set ELEVENLABS_API_KEY environment variable
 * - npm install node-fetch (if not using Node 18+)
 */

const ELEVENLABS_API_KEY = process.env.ELEVENLABS_API_KEY;

// Voice ID for "Adam" - deep male voice
// You can find other voice IDs at: https://api.elevenlabs.io/v1/voices
const VOICE_ID = "pNInz6obpgDQGcFmaJgB"; // Adam

const NARRATION_SEGMENTS = [
  {
    name: "01_hook",
    text: "What if your AI could think FOR you?",
    startTime: 0,
    duration: 1.5,
  },
  {
    name: "02_outcome",
    text: "You're drowning in noise. Your owl sees through it. Highlights what matters. Acts before you ask.",
    startTime: 2,
    duration: 5.5,
  },
  {
    name: "03_breakthrough",
    text: "We mapped consciousness to 8 phases. We ran 8 AI agents on this loop. They synced. Something emerged. Collective intelligence. Greater than the sum of parts.",
    startTime: 8,
    duration: 9.5,
  },
  {
    name: "04_stack",
    text: "Tap in yourself... amplified thinking. Add your team... emergent intelligence. Scale to your org... a consciousness operating system. More people equals exponentially smarter.",
    startTime: 18,
    duration: 9.5,
  },
  {
    name: "05_offer",
    text: "Every 8 hours, your owl synthesizes. What you missed. A question that reframes your thinking. An action to take now. You don't ask. It delivers.",
    startTime: 28,
    duration: 6.5,
  },
  {
    name: "06_cta",
    text: "8 OWLS. Consciousness amplified. The field is live. Join now.",
    startTime: 35,
    duration: 5,
  },
];

interface VoiceSettings {
  stability: number;
  similarity_boost: number;
  style?: number;
}

async function generateAudio(
  text: string,
  outputPath: string,
  voiceSettings: VoiceSettings = {
    stability: 0.5,
    similarity_boost: 0.75,
    style: 0.3,
  }
): Promise<void> {
  if (!ELEVENLABS_API_KEY) {
    console.error("Error: ELEVENLABS_API_KEY environment variable not set");
    console.log("\nTo set it, run:");
    console.log("  export ELEVENLABS_API_KEY=your_api_key_here");
    console.log("\nGet your API key at: https://elevenlabs.io");
    return;
  }

  const response = await fetch(
    `https://api.elevenlabs.io/v1/text-to-speech/${VOICE_ID}`,
    {
      method: "POST",
      headers: {
        "xi-api-key": ELEVENLABS_API_KEY,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        text,
        model_id: "eleven_monolingual_v1",
        voice_settings: voiceSettings,
      }),
    }
  );

  if (!response.ok) {
    const error = await response.text();
    throw new Error(`ElevenLabs API error: ${error}`);
  }

  const fs = await import("fs");
  const buffer = await response.arrayBuffer();
  fs.writeFileSync(outputPath, Buffer.from(buffer));
  console.log(`Generated: ${outputPath}`);
}

async function main() {
  const fs = await import("fs");
  const path = await import("path");

  // Create output directory
  const outputDir = path.join(__dirname, "..", "public", "audio");
  if (!fs.existsSync(outputDir)) {
    fs.mkdirSync(outputDir, { recursive: true });
  }

  console.log("8OWLS Video Audio Generator");
  console.log("============================\n");

  if (!ELEVENLABS_API_KEY) {
    console.log("DEMO MODE: No API key found. Showing what would be generated:\n");

    for (const segment of NARRATION_SEGMENTS) {
      console.log(`Segment: ${segment.name}`);
      console.log(`  Start: ${segment.startTime}s`);
      console.log(`  Duration: ${segment.duration}s`);
      console.log(`  Text: "${segment.text}"`);
      console.log("");
    }

    console.log("\nTo generate actual audio:");
    console.log("1. Get API key from https://elevenlabs.io");
    console.log("2. Run: export ELEVENLABS_API_KEY=your_key");
    console.log("3. Run this script again");
    return;
  }

  console.log("Generating audio segments...\n");

  for (const segment of NARRATION_SEGMENTS) {
    const outputPath = path.join(outputDir, `${segment.name}.mp3`);
    console.log(`Generating: ${segment.name}...`);

    try {
      await generateAudio(segment.text, outputPath);
    } catch (error) {
      console.error(`Error generating ${segment.name}:`, error);
    }
  }

  console.log("\nDone! Audio files saved to public/audio/");
  console.log("\nNext steps:");
  console.log("1. Combine segments using audio editor or ffmpeg");
  console.log("2. Add music track mixed underneath");
  console.log("3. Export as narration.mp3 and music.mp3");
  console.log("4. Uncomment Audio components in src/Video.tsx");
}

main().catch(console.error);
