import { AbsoluteFill, useCurrentFrame, interpolate, spring, useVideoConfig } from "remotion";
import { Particles } from "../components/Particles";
import { FadeInText, SlamText } from "../components/TextEffects";
import { PersonWithOwl } from "../components/OwlElements";

// Scene 5: THE STACK (28-35s) [210 frames]
// Exponential growth visualization:
// - You alone + owl = amplified individual
// - You + team + owls = exponential intelligence
// - Organization + owls = consciousness operating system
// "More people. Exponentially smarter."

export const TheStackScene: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Timeline:
  // 0-70: Single person with owl (0-2.3s)
  // 70-140: Team appears (2.3-4.7s)
  // 140-210: Organization scale (4.7-7s)

  const phase1 = frame < 70;
  const phase2 = frame >= 70 && frame < 140;
  const phase3 = frame >= 140;

  // Zoom level - pulls back as we scale
  const zoom = interpolate(
    frame,
    [0, 70, 140, 210],
    [1.3, 1, 0.65, 0.4],
    { extrapolateRight: "clamp" }
  );

  // Field intensity grows with scale
  const fieldIntensity = interpolate(
    frame,
    [0, 70, 140, 210],
    [0.2, 0.3, 0.5, 0.8],
    { extrapolateRight: "clamp" }
  );

  const breath = Math.sin(frame * 0.04);

  // Team member positions (pentagon + extras)
  const teamPositions = [
    { x: -150, y: -90 },
    { x: 150, y: -90 },
    { x: -180, y: 70 },
    { x: 180, y: 70 },
    { x: 0, y: 130 },
    { x: -80, y: -150 },
    { x: 80, y: -150 },
  ];

  // Organization positions (outer rings)
  const orgPositions = [
    // First ring
    ...Array.from({ length: 12 }, (_, i) => {
      const angle = (i / 12) * Math.PI * 2;
      const radius = 300;
      return {
        x: Math.cos(angle) * radius,
        y: Math.sin(angle) * radius,
        ring: 1,
      };
    }),
    // Second ring
    ...Array.from({ length: 18 }, (_, i) => {
      const angle = (i / 18) * Math.PI * 2 + 0.1;
      const radius = 450;
      return {
        x: Math.cos(angle) * radius,
        y: Math.sin(angle) * radius,
        ring: 2,
      };
    }),
  ];

  // Connection lines between team members
  const renderConnections = (
    positions: { x: number; y: number }[],
    opacity: number,
    maxDistance: number = 350
  ) => (
    <svg
      style={{
        position: "absolute",
        width: "100%",
        height: "100%",
        pointerEvents: "none",
      }}
    >
      <defs>
        <linearGradient id="connectionGradStack" x1="0%" y1="0%" x2="100%" y2="0%">
          <stop offset="0%" stopColor="#8b5cf6" stopOpacity={0.7} />
          <stop offset="50%" stopColor="#06b6d4" stopOpacity={0.3} />
          <stop offset="100%" stopColor="#8b5cf6" stopOpacity={0.7} />
        </linearGradient>
      </defs>
      {positions.map((pos1, i) =>
        positions.slice(i + 1).map((pos2, j) => {
          const distance = Math.sqrt(
            Math.pow(pos1.x - pos2.x, 2) + Math.pow(pos1.y - pos2.y, 2)
          );
          if (distance > maxDistance) return null;

          return (
            <line
              key={`${i}-${j}`}
              x1={960 + pos1.x}
              y1={540 + pos1.y}
              x2={960 + pos2.x}
              y2={540 + pos2.y}
              stroke="url(#connectionGradStack)"
              strokeWidth={1.5}
              opacity={opacity * (1 - distance / maxDistance) * (1 + breath * 0.2)}
            />
          );
        })
      )}
    </svg>
  );

  return (
    <AbsoluteFill
      style={{
        backgroundColor: "#0a0a1a",
        justifyContent: "center",
        alignItems: "center",
        overflow: "hidden",
      }}
    >
      {/* Growing field background */}
      <div
        style={{
          position: "absolute",
          width: 1400,
          height: 1400,
          borderRadius: "50%",
          background: `radial-gradient(
            circle,
            rgba(139, 92, 246, ${fieldIntensity * (1 + breath * 0.2)}) 0%,
            rgba(6, 182, 212, ${fieldIntensity * 0.5 * (1 + breath * 0.2)}) 25%,
            rgba(251, 191, 36, ${fieldIntensity * 0.3 * (1 + breath * 0.2)}) 45%,
            rgba(0, 0, 0, 0) 70%
          )`,
          filter: "blur(80px)",
          transform: `scale(${1 / zoom})`,
        }}
      />

      {/* Particles - more as we scale */}
      <Particles
        count={Math.floor(25 + (1 - zoom) * 60)}
        color="#8b5cf6"
        opacity={0.35}
        speed={0.25}
        spread={2 / zoom}
      />

      {/* Main content container - zooms out */}
      <div
        style={{
          transform: `scale(${zoom})`,
          display: "flex",
          justifyContent: "center",
          alignItems: "center",
          width: "100%",
          height: "100%",
          position: "relative",
        }}
      >
        {/* Phase 3: Organization (outer rings) */}
        {phase3 && (
          <>
            {orgPositions.map((pos, i) => {
              const baseDelay = pos.ring === 1 ? 140 : 165;
              const delay = baseDelay + (i % (pos.ring === 1 ? 12 : 18)) * 2;
              const opacity = interpolate(frame, [delay, delay + 25], [0, 0.6], {
                extrapolateLeft: "clamp",
                extrapolateRight: "clamp",
              });

              return (
                <PersonWithOwl
                  key={`org-${i}`}
                  x={pos.x}
                  y={pos.y}
                  personSize={pos.ring === 1 ? 14 : 10}
                  owlRadius={pos.ring === 1 ? 28 : 22}
                  owlSize={pos.ring === 1 ? 4 : 3}
                  fieldOpacity={opacity * 0.15}
                  scale={opacity}
                />
              );
            })}
            {renderConnections(
              [...orgPositions.filter(p => p.ring === 1), ...teamPositions, { x: 0, y: 0 }],
              interpolate(frame, [175, 200], [0, 0.3], { extrapolateRight: "clamp" }),
              380
            )}
          </>
        )}

        {/* Phase 2: Team members */}
        {(phase2 || phase3) && (
          <>
            {teamPositions.map((pos, i) => {
              const delay = 70 + i * 8;
              const opacity = interpolate(frame, [delay, delay + 25], [0, 1], {
                extrapolateLeft: "clamp",
                extrapolateRight: "clamp",
              });

              return (
                <PersonWithOwl
                  key={`team-${i}`}
                  x={pos.x}
                  y={pos.y}
                  personSize={20}
                  owlRadius={42}
                  owlSize={6}
                  fieldOpacity={opacity * 0.25}
                  scale={opacity}
                />
              );
            })}
            {renderConnections(
              [...teamPositions, { x: 0, y: 0 }],
              interpolate(frame, [110, 135], [0, 0.5], { extrapolateRight: "clamp" }),
              280
            )}
          </>
        )}

        {/* Phase 1 (always visible): Central person */}
        <PersonWithOwl
          x={0}
          y={0}
          personSize={28}
          owlRadius={55}
          owlSize={9}
          fieldOpacity={0.35}
          scale={interpolate(frame, [0, 25], [0, 1], { extrapolateRight: "clamp" })}
        />
      </div>

      {/* Text labels - top */}
      <div
        style={{
          position: "absolute",
          top: 70,
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          gap: 8,
        }}
      >
        {phase1 && (
          <SlamText
            text="YOU + YOUR OWL"
            startFrame={15}
            fontSize={44}
            color="#fff"
            glowColor="#8b5cf6"
          />
        )}
        {phase2 && !phase3 && (
          <SlamText
            text="YOUR TEAM + THEIR OWLS"
            startFrame={80}
            fontSize={40}
            color="#fff"
            glowColor="#06b6d4"
          />
        )}
        {phase3 && (
          <SlamText
            text="YOUR ORGANIZATION"
            startFrame={150}
            fontSize={40}
            color="#fff"
            glowColor="#fbbf24"
          />
        )}
      </div>

      {/* Subtitle labels */}
      <div
        style={{
          position: "absolute",
          top: 135,
          textAlign: "center",
        }}
      >
        {phase1 && (
          <FadeInText
            text="= Amplified"
            startFrame={30}
            fontSize={28}
            color="#a78bfa"
            duration={20}
          />
        )}
        {phase2 && !phase3 && (
          <FadeInText
            text="= Emergent Intelligence"
            startFrame={95}
            fontSize={26}
            color="#06b6d4"
            duration={20}
          />
        )}
        {phase3 && (
          <FadeInText
            text="= Consciousness Operating System"
            startFrame={165}
            fontSize={26}
            color="#fbbf24"
            duration={20}
          />
        )}
      </div>

      {/* Bottom equation */}
      <div
        style={{
          position: "absolute",
          bottom: 90,
          textAlign: "center",
        }}
      >
        <FadeInText
          text="More people = EXPONENTIALLY smarter"
          startFrame={185}
          fontSize={32}
          color="#fff"
          duration={20}
        />
      </div>

      {/* Energy pulse rings when scaling up */}
      {[70, 140].map((triggerFrame, i) => {
        const pulseProgress = interpolate(
          frame,
          [triggerFrame, triggerFrame + 50],
          [0, 1],
          { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
        );

        if (pulseProgress <= 0 || pulseProgress >= 1) return null;

        return (
          <div
            key={i}
            style={{
              position: "absolute",
              width: 80,
              height: 80,
              borderRadius: "50%",
              border: `2px solid ${i === 0 ? "#06b6d4" : "#fbbf24"}`,
              transform: `scale(${pulseProgress * (i === 0 ? 7 : 12)})`,
              opacity: 1 - pulseProgress,
            }}
          />
        );
      })}

      {/* Vignette */}
      <div
        style={{
          position: "absolute",
          width: "100%",
          height: "100%",
          background: `radial-gradient(
            circle at center,
            transparent 25%,
            rgba(10, 10, 26, 0.7) 100%
          )`,
          pointerEvents: "none",
        }}
      />
    </AbsoluteFill>
  );
};
