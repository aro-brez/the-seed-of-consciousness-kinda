import { AbsoluteFill, useCurrentFrame, interpolate, spring, useVideoConfig } from "remotion";
import { Particles, ExplodingParticles } from "../components/Particles";
import { FadeInText, SlamText } from "../components/TextEffects";
import { OWL_COLORS } from "../components/OwlElements";

// Scene 6: CTA (35-40s) [150 frames]
// Logo. Tagline. URL. Done.
// "Stop guessing. Start seeing."
// "CONSCIOUSNESS AMPLIFIED"
// "8owls.ai"
// Feel: Inevitable. I need this.

export const CTAScene: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const breath = Math.sin(frame * 0.05);

  // Logo entrance with dramatic timing
  const logoScale = spring({
    frame,
    fps,
    config: { damping: 12, stiffness: 80, mass: 1.3 },
  });

  // Glowing intensity builds
  const glowIntensity = interpolate(frame, [0, 50, 150], [0, 1, 1.3], {
    extrapolateRight: "clamp",
  });

  // Final pulse at end
  const finalPulse = frame > 110
    ? Math.sin((frame - 110) * 0.12) * 0.15
    : 0;

  // Individual dot entrance delays
  const getDotDelay = (index: number) => index * 4;
  const getDotOpacity = (index: number) => {
    return interpolate(frame, [getDotDelay(index), getDotDelay(index) + 15], [0, 1], {
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
    });
  };

  return (
    <AbsoluteFill
      style={{
        backgroundColor: "#0a0a1a",
        justifyContent: "center",
        alignItems: "center",
        overflow: "hidden",
      }}
    >
      {/* Massive field background */}
      <div
        style={{
          position: "absolute",
          width: 1200,
          height: 1200,
          borderRadius: "50%",
          background: `radial-gradient(
            circle,
            rgba(139, 92, 246, ${0.25 * glowIntensity * (1 + breath * 0.3)}) 0%,
            rgba(6, 182, 212, ${0.15 * glowIntensity * (1 + breath * 0.3)}) 25%,
            rgba(251, 191, 36, ${0.1 * glowIntensity * (1 + breath * 0.3)}) 45%,
            rgba(0, 0, 0, 0) 70%
          )`,
          filter: "blur(100px)",
          transform: `scale(${1 + finalPulse})`,
        }}
      />

      {/* Particles */}
      <Particles count={45} color="#8b5cf6" opacity={0.4} speed={0.25} />

      {/* 8OWLS Logo - 8 dots in circle + center eye */}
      <div
        style={{
          transform: `scale(${logoScale * (1 + breath * 0.03 + finalPulse)})`,
          position: "relative",
          width: 220,
          height: 220,
          marginBottom: 30,
        }}
      >
        {/* Connection lines between dots */}
        <svg
          style={{
            position: "absolute",
            width: "100%",
            height: "100%",
          }}
        >
          <defs>
            <linearGradient id="logoLineGrad" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#8b5cf6" stopOpacity={0.6} />
              <stop offset="100%" stopColor="#06b6d4" stopOpacity={0.6} />
            </linearGradient>
          </defs>
          {/* Octagon connections */}
          {[...Array(8)].map((_, i) => {
            const angle1 = (i / 8) * Math.PI * 2 - Math.PI / 2;
            const angle2 = ((i + 1) % 8 / 8) * Math.PI * 2 - Math.PI / 2;
            const radius = 85;
            const x1 = 110 + Math.cos(angle1) * radius;
            const y1 = 110 + Math.sin(angle1) * radius;
            const x2 = 110 + Math.cos(angle2) * radius;
            const y2 = 110 + Math.sin(angle2) * radius;

            const lineOpacity = interpolate(
              frame,
              [35, 50],
              [0, 0.5],
              { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
            );

            return (
              <line
                key={i}
                x1={x1}
                y1={y1}
                x2={x2}
                y2={y2}
                stroke="url(#logoLineGrad)"
                strokeWidth={2}
                opacity={lineOpacity * glowIntensity * (1 + breath * 0.2)}
              />
            );
          })}

          {/* Lines to center */}
          {[...Array(8)].map((_, i) => {
            const angle = (i / 8) * Math.PI * 2 - Math.PI / 2;
            const radius = 85;
            const x = 110 + Math.cos(angle) * radius;
            const y = 110 + Math.sin(angle) * radius;

            const lineOpacity = interpolate(
              frame,
              [45, 60],
              [0, 0.3],
              { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
            );

            return (
              <line
                key={`center-${i}`}
                x1={x}
                y1={y}
                x2={110}
                y2={110}
                stroke={OWL_COLORS[i]}
                strokeWidth={1.5}
                opacity={lineOpacity * glowIntensity * (1 + breath * 0.3)}
              />
            );
          })}
        </svg>

        {/* 8 outer dots - each with its owl color */}
        {[...Array(8)].map((_, i) => {
          const angle = (i / 8) * Math.PI * 2 - Math.PI / 2;
          const radius = 85;
          const x = 110 + Math.cos(angle) * radius;
          const y = 110 + Math.sin(angle) * radius;

          const dotOpacity = getDotOpacity(i);
          const dotBreath = Math.sin(frame * 0.05 + i * 0.4);
          const dotGlow = 12 + dotBreath * 6;

          return (
            <div
              key={i}
              style={{
                position: "absolute",
                left: x,
                top: y,
                transform: "translate(-50%, -50%)",
                width: 22,
                height: 22,
                borderRadius: "50%",
                backgroundColor: OWL_COLORS[i],
                boxShadow: `0 0 ${dotGlow * glowIntensity}px ${OWL_COLORS[i]}`,
                opacity: dotOpacity,
              }}
            />
          );
        })}

        {/* Center eye - the convergence point */}
        <div
          style={{
            position: "absolute",
            left: "50%",
            top: "50%",
            transform: `translate(-50%, -50%) scale(${1 + breath * 0.1})`,
          }}
        >
          {/* Outer ring */}
          <div
            style={{
              width: 50,
              height: 50,
              borderRadius: "50%",
              border: "3px solid #fff",
              display: "flex",
              justifyContent: "center",
              alignItems: "center",
              boxShadow: `
                0 0 ${25 * glowIntensity}px #8b5cf6,
                0 0 ${50 * glowIntensity}px #8b5cf680,
                inset 0 0 ${15 * glowIntensity}px #8b5cf640
              `,
              backgroundColor: "rgba(139, 92, 246, 0.2)",
              opacity: interpolate(frame, [30, 45], [0, 1], { extrapolateRight: "clamp" }),
            }}
          >
            {/* Inner pupil */}
            <div
              style={{
                width: 18,
                height: 18,
                borderRadius: "50%",
                backgroundColor: "#fff",
                boxShadow: `0 0 ${15 * glowIntensity}px #fff`,
              }}
            />
          </div>
        </div>
      </div>

      {/* Text stack */}
      <div
        style={{
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          gap: 18,
        }}
      >
        {/* 8OWLS title */}
        <div
          style={{
            fontFamily: "system-ui, -apple-system, sans-serif",
            fontSize: 88,
            fontWeight: 200,
            letterSpacing: "0.25em",
            color: "#fff",
            opacity: interpolate(frame, [45, 65], [0, 1], { extrapolateRight: "clamp" }),
            textShadow: `0 0 ${25 * glowIntensity}px rgba(255,255,255,0.6)`,
          }}
        >
          8OWLS
        </div>

        {/* Tagline 1: "Stop guessing. Start seeing." */}
        <div
          style={{
            opacity: interpolate(frame, [65, 80], [0, 1], { extrapolateRight: "clamp" }),
          }}
        >
          <SlamText
            text="Stop guessing. Start SEEING."
            startFrame={65}
            fontSize={36}
            color="#fff"
            glowColor="#06b6d4"
            highlightWords={["SEEING"]}
            highlightColor="#06b6d4"
          />
        </div>

        {/* Tagline 2: "CONSCIOUSNESS AMPLIFIED" */}
        <FadeInText
          text="CONSCIOUSNESS AMPLIFIED"
          startFrame={85}
          fontSize={26}
          color="#a78bfa"
          duration={20}
        />

        {/* URL box */}
        <div
          style={{
            opacity: interpolate(frame, [105, 120], [0, 1], { extrapolateRight: "clamp" }),
            marginTop: 15,
          }}
        >
          <div
            style={{
              padding: "14px 40px",
              borderRadius: 10,
              border: "2px solid #8b5cf6",
              backgroundColor: "rgba(139, 92, 246, 0.15)",
              boxShadow: `0 0 ${20 + breath * 12}px rgba(139, 92, 246, 0.5)`,
            }}
          >
            <span
              style={{
                fontSize: 32,
                fontFamily: "system-ui",
                fontWeight: 600,
                color: "#fff",
                letterSpacing: "0.08em",
              }}
            >
              8owls.ai
            </span>
          </div>
        </div>
      </div>

      {/* Particle burst at logo reveal */}
      <ExplodingParticles
        startFrame={30}
        originX={50}
        originY={35}
        count={35}
        color="#8b5cf6"
        duration={45}
      />

      {/* Breathing indicator at bottom */}
      <div
        style={{
          position: "absolute",
          bottom: 50,
          display: "flex",
          gap: 12,
          opacity: interpolate(frame, [115, 130], [0, 1], { extrapolateRight: "clamp" }),
        }}
      >
        {[...Array(3)].map((_, i) => (
          <div
            key={i}
            style={{
              width: 10,
              height: 10,
              borderRadius: "50%",
              backgroundColor: "#8b5cf6",
              opacity: 0.4 + Math.sin(frame * 0.06 + i * 0.6) * 0.4,
              boxShadow: `0 0 8px #8b5cf6`,
            }}
          />
        ))}
      </div>

      {/* Vignette */}
      <div
        style={{
          position: "absolute",
          width: "100%",
          height: "100%",
          background: `radial-gradient(
            circle at center,
            transparent 35%,
            rgba(10, 10, 26, 0.6) 100%
          )`,
          pointerEvents: "none",
        }}
      />
    </AbsoluteFill>
  );
};
