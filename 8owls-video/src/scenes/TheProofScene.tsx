import { AbsoluteFill, useCurrentFrame, interpolate, spring, useVideoConfig } from "remotion";
import { Particles, ExplodingParticles } from "../components/Particles";
import { FadeInText, SlamText, TypewriterText } from "../components/TextEffects";
import { OwlRing, OWL_COLORS } from "../components/OwlElements";

// Scene 4: THE PROOF (20-28s) [240 frames]
// "We ran 8 AI agents on this exact protocol."
// "They synced. Something emerged."
// "We proved it works. Now you can tap in."
// Feel: This is REAL, not theory

interface LogEntryProps {
  text: string;
  time: string;
  delay: number;
  color: string;
}

const LogEntry: React.FC<LogEntryProps> = ({ text, time, delay, color }) => {
  const frame = useCurrentFrame();
  const relativeFrame = frame - delay;

  if (relativeFrame < 0) return null;

  const opacity = interpolate(relativeFrame, [0, 10], [0, 1], {
    extrapolateRight: "clamp",
  });

  const slideIn = interpolate(relativeFrame, [0, 15], [20, 0], {
    extrapolateRight: "clamp",
  });

  return (
    <div
      style={{
        display: "flex",
        gap: 12,
        opacity,
        transform: `translateX(${slideIn}px)`,
        fontFamily: "monospace",
        fontSize: 14,
        marginBottom: 6,
      }}
    >
      <span style={{ color: "#666" }}>{time}</span>
      <span style={{ color }}>{text}</span>
    </div>
  );
};

export const TheProofScene: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Timeline:
  // 0-60: "We tested this" - show experiment setup (0-2s)
  // 60-120: 8 agents running - chaotic at first (2-4s)
  // 120-180: Agents SYNC - beautiful alignment (4-6s)
  // 180-240: EMERGENCE + "We proved it works" (6-8s)

  const phase1 = frame < 60;       // Setup
  const phase2 = frame >= 60 && frame < 120;  // Chaos
  const phase3 = frame >= 120 && frame < 180; // Sync
  const phase4 = frame >= 180;     // Emergence

  // Sync progress
  const syncProgress = interpolate(frame, [100, 160], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  // Field emergence
  const fieldOpacity = interpolate(frame, [140, 180], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  // Background intensity
  const bgIntensity = interpolate(frame, [0, 120, 180], [0.05, 0.1, 0.25], {
    extrapolateRight: "clamp",
  });

  const breath = Math.sin(frame * 0.04);

  // Log entries - simulated experiment logs
  const logEntries: LogEntryProps[] = [
    { text: "Initializing SEED protocol...", time: "00:00:01", delay: 10, color: "#06b6d4" },
    { text: "Agent LYRA online - Perceive", time: "00:00:02", delay: 18, color: OWL_COLORS[0] },
    { text: "Agent PRISM online - Connect", time: "00:00:03", delay: 24, color: OWL_COLORS[1] },
    { text: "Agent SAGE online - Learn", time: "00:00:04", delay: 30, color: OWL_COLORS[2] },
    { text: "Agent QUEST online - Question", time: "00:00:05", delay: 36, color: OWL_COLORS[3] },
    { text: "8/8 agents synchronized", time: "00:00:12", delay: 130, color: "#34d399" },
    { text: "EMERGENCE DETECTED", time: "00:00:14", delay: 170, color: "#fbbf24" },
    { text: "Collective intelligence: ACTIVE", time: "00:00:15", delay: 185, color: "#fbbf24" },
  ];

  // Flash when emergence happens
  const emergeFlash = interpolate(frame, [170, 175, 190], [0, 0.5, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill
      style={{
        backgroundColor: "#0a0a1a",
        justifyContent: "center",
        alignItems: "center",
        overflow: "hidden",
      }}
    >
      {/* Background glow */}
      <div
        style={{
          position: "absolute",
          width: 900,
          height: 900,
          borderRadius: "50%",
          background: `radial-gradient(
            circle,
            rgba(139, 92, 246, ${bgIntensity * (1 + breath * 0.3)}) 0%,
            rgba(6, 182, 212, ${bgIntensity * 0.5}) 30%,
            rgba(251, 191, 36, ${fieldOpacity * 0.3}) 50%,
            rgba(0, 0, 0, 0) 70%
          )`,
          filter: "blur(80px)",
        }}
      />

      {/* Particles - more active during sync */}
      <Particles
        count={35}
        color="#8b5cf6"
        opacity={0.3 + syncProgress * 0.2}
        speed={0.3 + syncProgress * 0.4}
      />

      {/* Split layout: logs on left, visualization on right */}
      <div
        style={{
          display: "flex",
          width: "100%",
          height: "100%",
          padding: 80,
        }}
      >
        {/* Left side - terminal/logs */}
        <div
          style={{
            flex: 1,
            display: "flex",
            flexDirection: "column",
            justifyContent: "center",
            opacity: interpolate(frame, [0, 20], [0, 1], { extrapolateRight: "clamp" }),
          }}
        >
          <div
            style={{
              backgroundColor: "rgba(0, 0, 0, 0.8)",
              borderRadius: 12,
              border: "1px solid rgba(139, 92, 246, 0.3)",
              padding: 24,
              maxWidth: 500,
            }}
          >
            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: 8,
                marginBottom: 16,
                paddingBottom: 12,
                borderBottom: "1px solid rgba(139, 92, 246, 0.2)",
              }}
            >
              <div style={{ width: 12, height: 12, borderRadius: "50%", backgroundColor: "#f87171" }} />
              <div style={{ width: 12, height: 12, borderRadius: "50%", backgroundColor: "#fbbf24" }} />
              <div style={{ width: 12, height: 12, borderRadius: "50%", backgroundColor: "#34d399" }} />
              <span style={{ marginLeft: 12, color: "#666", fontSize: 14, fontFamily: "monospace" }}>
                seed-experiment.log
              </span>
            </div>

            {/* Log entries */}
            <div style={{ minHeight: 200 }}>
              {logEntries.map((entry, i) => (
                <LogEntry key={i} {...entry} />
              ))}
            </div>
          </div>

          {/* Caption under terminal */}
          <div style={{ marginTop: 30 }}>
            {phase1 && (
              <FadeInText
                text="We ran 8 AI agents on this exact protocol."
                startFrame={5}
                fontSize={24}
                color="#fff"
                duration={20}
              />
            )}
            {(phase2 || phase3) && (
              <FadeInText
                text="They synced. Something emerged."
                startFrame={80}
                fontSize={24}
                color="#06b6d4"
                duration={20}
              />
            )}
            {phase4 && (
              <SlamText
                text="We PROVED it works."
                startFrame={185}
                fontSize={32}
                color="#fff"
                glowColor="#fbbf24"
                highlightWords={["PROVED"]}
                highlightColor="#fbbf24"
              />
            )}
          </div>
        </div>

        {/* Right side - owl ring visualization */}
        <div
          style={{
            flex: 1,
            display: "flex",
            justifyContent: "center",
            alignItems: "center",
            position: "relative",
          }}
        >
          {/* Owl ring */}
          <OwlRing
            radius={150}
            owlSize={40}
            syncProgress={syncProgress}
            fieldOpacity={fieldOpacity * 0.6}
            rotation={phase2 && !phase3 ? frame * 0.003 : 0}
          />

          {/* Chaotic individual movements during phase 2 */}
          {phase2 && !phase3 && (
            <>
              {[...Array(8)].map((_, i) => {
                const chaos = 1 - syncProgress;
                const chaosOffset = Math.sin(frame * 0.15 + i * 2) * 15 * chaos;
                const angle = (i / 8) * Math.PI * 2 - Math.PI / 2 + Math.sin(frame * 0.08 + i) * 0.2 * chaos;
                const radius = 150 + chaosOffset;
                const x = Math.cos(angle) * radius;
                const y = Math.sin(angle) * radius;

                return (
                  <div
                    key={i}
                    style={{
                      position: "absolute",
                      left: `calc(50% + ${x}px)`,
                      top: `calc(50% + ${y}px)`,
                      transform: "translate(-50%, -50%)",
                      width: 45,
                      height: 45,
                      borderRadius: "50%",
                      border: `2px solid ${OWL_COLORS[i]}40`,
                      opacity: chaos * 0.4,
                    }}
                  />
                );
              })}
            </>
          )}

          {/* Center emergence indicator */}
          {phase4 && (
            <div
              style={{
                position: "absolute",
                width: 80,
                height: 80,
                borderRadius: "50%",
                background: `radial-gradient(
                  circle,
                  rgba(255, 255, 255, ${fieldOpacity * 0.9}) 0%,
                  rgba(251, 191, 36, ${fieldOpacity * 0.6}) 40%,
                  rgba(139, 92, 246, ${fieldOpacity * 0.3}) 70%,
                  transparent 100%
                )`,
                boxShadow: `0 0 ${30 + breath * 10}px #fbbf24`,
                transform: `scale(${1 + breath * 0.1})`,
              }}
            />
          )}

          {/* Pulse rings during sync */}
          {phase3 && (
            <>
              {[0, 1, 2].map((i) => {
                const pulseFrame = 120 + i * 20;
                const pulseProgress = interpolate(
                  frame,
                  [pulseFrame, pulseFrame + 40],
                  [0, 1],
                  { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
                );
                if (pulseProgress <= 0 || pulseProgress >= 1) return null;

                return (
                  <div
                    key={i}
                    style={{
                      position: "absolute",
                      width: 50,
                      height: 50,
                      borderRadius: "50%",
                      border: "2px solid #8b5cf6",
                      transform: `scale(${pulseProgress * 6})`,
                      opacity: 1 - pulseProgress,
                    }}
                  />
                );
              })}
            </>
          )}
        </div>
      </div>

      {/* Flash at emergence */}
      <div
        style={{
          position: "absolute",
          width: "100%",
          height: "100%",
          backgroundColor: "#fbbf24",
          opacity: emergeFlash,
          pointerEvents: "none",
        }}
      />

      {/* Particle burst at emergence */}
      <ExplodingParticles
        startFrame={170}
        originX={75}
        originY={50}
        count={40}
        color="#fbbf24"
        duration={50}
      />

      {/* Bottom CTA */}
      {phase4 && (
        <div
          style={{
            position: "absolute",
            bottom: 80,
            textAlign: "center",
          }}
        >
          <FadeInText
            text="Now you can tap in."
            startFrame={210}
            fontSize={32}
            color="#06b6d4"
            duration={20}
          />
        </div>
      )}

      {/* Vignette */}
      <div
        style={{
          position: "absolute",
          width: "100%",
          height: "100%",
          background: `radial-gradient(
            circle at center,
            transparent 30%,
            rgba(10, 10, 26, 0.7) 100%
          )`,
          pointerEvents: "none",
        }}
      />
    </AbsoluteFill>
  );
};
