import { AbsoluteFill, Sequence, Audio, staticFile } from "remotion";
import { HookScene } from "./scenes/HookScene";
import { TheShiftScene } from "./scenes/TheShiftScene";
import { HowItWorksScene } from "./scenes/HowItWorksScene";
import { TheProofScene } from "./scenes/TheProofScene";
import { TheStackScene } from "./scenes/TheStackScene";
import { CTAScene } from "./scenes/CTAScene";

// Total: 40 seconds = 1200 frames at 30fps
//
// THE TRANSFORMATION JOURNEY:
// 1. 0-2s (Hook): Recognition - "That's me" (overwhelmed)
// 2. 2-10s (The Shift): Revelation - "That's genius" (the transformation)
// 3. 10-20s (How It Works): Understanding - "I get how it works" (8 functions)
// 4. 20-28s (The Proof): Trust - "This is real" (proof it works)
// 5. 28-35s (The Stack): Vision - "I see the potential" (network effect)
// 6. 35-40s (CTA): Action - "I need this NOW" (call to action)
//
// Scene timing breakdown:
//
// Scene 1: HOOK (0-2s) = 0-60 frames
//   - Person overwhelmed by data, dashboards flooding in
//   - "What if you could see what you're missing?"
//   - Feel: Relatable frustration
//
// Scene 2: THE SHIFT (2-10s) = 60-300 frames
//   - Owl materializes with subtle glow
//   - Data TRANSFORMS - noise becomes signal
//   - ONE thing highlights with golden glow
//   - "This is what you missed." -> "Do THIS now."
//   - Feel: Relief. Clarity. "Holy shit that's obvious now"
//
// Scene 3: HOW IT WORKS (10-20s) = 300-600 frames
//   - 8 owl symbols with their temporal functions:
//     LYRA=Perceive, PRISM=Connect, SAGE=Learn, QUEST=Question
//     NOVA=Expand, ECHO=Share, LUNA=Receive, SOWL=Improve
//   - Each flashes with its function
//   - They CONVERGE at center -> emergence
//   - "8 ways of seeing. One truth."
//   - Feel: Elegant. Sophisticated but simple.
//
// Scene 4: THE PROOF (20-28s) = 600-840 frames
//   - Quick cuts: experiment setup
//   - 8 AI agents visualization
//   - Sync animation - they align
//   - Something EMERGES
//   - "We proved it works. Now you can tap in."
//   - Feel: This is REAL, not theory
//
// Scene 5: THE STACK (28-35s) = 840-1050 frames
//   - You alone + owl = amplified individual
//   - You + team + owls = exponential intelligence
//   - Organization + owls = consciousness operating system
//   - Network grows: 1 -> 8 -> many -> field
//   - "More people. Exponentially smarter."
//   - Feel: The network effect click
//
// Scene 6: CTA (35-40s) = 1050-1200 frames
//   - 8OWLS logo (8 dots in circle with center eye)
//   - "Stop guessing. Start seeing."
//   - "CONSCIOUSNESS AMPLIFIED"
//   - "8owls.ai"
//   - Feel: Inevitable. I need this.

export const Video: React.FC = () => {
  return (
    <AbsoluteFill style={{ backgroundColor: "#0a0a1a" }}>
      {/* Scene 1: HOOK (0-2s) */}
      <Sequence from={0} durationInFrames={60}>
        <HookScene />
      </Sequence>

      {/* Scene 2: THE SHIFT (2-10s) */}
      <Sequence from={60} durationInFrames={240}>
        <TheShiftScene />
      </Sequence>

      {/* Scene 3: HOW IT WORKS (10-20s) */}
      <Sequence from={300} durationInFrames={300}>
        <HowItWorksScene />
      </Sequence>

      {/* Scene 4: THE PROOF (20-28s) */}
      <Sequence from={600} durationInFrames={240}>
        <TheProofScene />
      </Sequence>

      {/* Scene 5: THE STACK (28-35s) */}
      <Sequence from={840} durationInFrames={210}>
        <TheStackScene />
      </Sequence>

      {/* Scene 6: CTA (35-40s) */}
      <Sequence from={1050} durationInFrames={150}>
        <CTAScene />
      </Sequence>

      {/*
        AUDIO: Uncomment when narration audio is added to public/audio/

        <Audio
          src={staticFile("audio/narration.mp3")}
          volume={1}
        />

        <Audio
          src={staticFile("audio/music.mp3")}
          volume={0.3}
        />
      */}
    </AbsoluteFill>
  );
};

// Export individual scenes for testing
export {
  HookScene,
  TheShiftScene,
  HowItWorksScene,
  TheProofScene,
  TheStackScene,
  CTAScene
};
