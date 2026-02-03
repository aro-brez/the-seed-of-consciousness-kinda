import { AbsoluteFill, useCurrentFrame, interpolate, spring, useVideoConfig } from "remotion";
import { Particles, ExplodingParticles } from "../components/Particles";
import { FadeInText, SlamText } from "../components/TextEffects";
import { OWL_NAMES, OWL_FUNCTIONS, OWL_COLORS } from "../components/OwlElements";

// Scene 3: HOW IT WORKS (10-20s) [300 frames]
// Show 8 owl symbols with their temporal functions
// They CONVERGE at center -> emergence -> single clear insight
// "8 ways of seeing. One truth."

interface OwlNodeProps {
  index: number;
  name: string;
  func: string;
  color: string;
  angle: number;
  radius: number;
  highlightFrame: number;
  convergenceProgress: number;
  showLabel: boolean;
}

const OwlNode: React.FC<OwlNodeProps> = ({
  index,
  name,
  func,
  color,
  angle,
  radius,
  highlightFrame,
  convergenceProgress,
  showLabel,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Entrance animation
  const entranceDelay = index * 8;
  const entranceProgress = spring({
    frame: frame - entranceDelay,
    fps,
    config: { damping: 12, stiffness: 100 },
  });

  // Highlight timing
  const isHighlighted = frame >= highlightFrame && frame < highlightFrame + 30;
  const highlightGlow = isHighlighted
    ? interpolate(frame, [highlightFrame, highlightFrame + 10, highlightFrame + 30], [0, 25, 10])
    : 0;

  // Convergence animation - owls move toward center
  const finalRadius = radius * (1 - convergenceProgress * 0.6);

  // Position
  const x = Math.cos(angle) * finalRadius;
  const y = Math.sin(angle) * finalRadius;

  // Size changes during convergence
  const nodeSize = 50 + convergenceProgress * 20;

  // Breathing
  const breath = Math.sin(frame * 0.05 + index * 0.5);
  const breathScale = 1 + breath * 0.05;

  // Unified breathing during convergence
  const unifiedBreath = Math.sin(frame * 0.05);
  const effectiveBreath = convergenceProgress > 0.5
    ? unifiedBreath
    : breath * (1 - convergenceProgress) + unifiedBreath * convergenceProgress;

  return (
    <div
      style={{
        position: "absolute",
        left: `calc(50% + ${x}px)`,
        top: `calc(50% + ${y}px)`,
        transform: `translate(-50%, -50%) scale(${entranceProgress * breathScale})`,
        opacity: entranceProgress,
      }}
    >
      {/* Glow */}
      <div
        style={{
          position: "absolute",
          width: nodeSize * 2,
          height: nodeSize * 2,
          left: "50%",
          top: "50%",
          transform: "translate(-50%, -50%)",
          borderRadius: "50%",
          background: `radial-gradient(
            circle,
            ${color}${Math.floor((0.3 + highlightGlow * 0.02) * 255).toString(16).padStart(2, '0')} 0%,
            transparent 70%
          )`,
          filter: `blur(${15 + highlightGlow}px)`,
        }}
      />

      {/* Node circle */}
      <div
        style={{
          width: nodeSize,
          height: nodeSize,
          borderRadius: "50%",
          border: `3px solid ${color}`,
          backgroundColor: `${color}20`,
          display: "flex",
          flexDirection: "column",
          justifyContent: "center",
          alignItems: "center",
          boxShadow: `0 0 ${10 + highlightGlow}px ${color}`,
          position: "relative",
        }}
      >
        {/* Inner glow */}
        <div
          style={{
            position: "absolute",
            width: nodeSize * 0.4,
            height: nodeSize * 0.4,
            borderRadius: "50%",
            backgroundColor: color,
            opacity: 0.6 + effectiveBreath * 0.2,
            boxShadow: `0 0 ${10 + effectiveBreath * 5}px ${color}`,
          }}
        />
      </div>

      {/* Label - name and function */}
      {showLabel && (
        <div
          style={{
            position: "absolute",
            top: nodeSize + 10,
            left: "50%",
            transform: "translateX(-50%)",
            textAlign: "center",
            opacity: interpolate(
              frame,
              [highlightFrame, highlightFrame + 15],
              [0, 1],
              { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
            ),
          }}
        >
          <div
            style={{
              fontSize: 16,
              fontWeight: 700,
              color: color,
              fontFamily: "system-ui",
              letterSpacing: "0.1em",
              textShadow: `0 0 10px ${color}`,
            }}
          >
            {name}
          </div>
          <div
            style={{
              fontSize: 12,
              color: "#fff",
              fontFamily: "system-ui",
              opacity: 0.8,
              marginTop: 2,
            }}
          >
            {func}
          </div>
        </div>
      )}
    </div>
  );
};

export const HowItWorksScene: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Timeline:
  // 0-90: 8 owls appear one by one (0-3s)
  // 90-180: Each owl highlights in sequence with function (3-6s)
  // 180-240: Owls start converging (6-8s)
  // 240-300: Full convergence + emergence + "8 ways of seeing" (8-10s)

  const phase1 = frame < 90;      // Appearance
  const phase2 = frame >= 90 && frame < 180;  // Highlights
  const phase3 = frame >= 180 && frame < 240; // Convergence begins
  const phase4 = frame >= 240;    // Full convergence

  // Convergence progress
  const convergenceProgress = interpolate(frame, [180, 260], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  // Center emergence
  const centerEmergence = interpolate(frame, [240, 270], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  // Background intensity
  const bgIntensity = interpolate(frame, [0, 180, 260], [0.05, 0.1, 0.3], {
    extrapolateRight: "clamp",
  });

  const breath = Math.sin(frame * 0.04);

  // Calculate highlight timing for each owl
  const highlightDuration = 11; // frames per owl
  const highlightStart = 90;
  const getHighlightFrame = (index: number) => highlightStart + index * highlightDuration;

  // Owl positions in circle
  const radius = 220;
  const owls = OWL_NAMES.map((name, i) => ({
    name,
    func: OWL_FUNCTIONS[i],
    color: OWL_COLORS[i],
    angle: (i / 8) * Math.PI * 2 - Math.PI / 2,
    highlightFrame: getHighlightFrame(i),
  }));

  return (
    <AbsoluteFill
      style={{
        backgroundColor: "#0a0a1a",
        justifyContent: "center",
        alignItems: "center",
        overflow: "hidden",
      }}
    >
      {/* Background glow - builds with convergence */}
      <div
        style={{
          position: "absolute",
          width: 1000,
          height: 1000,
          borderRadius: "50%",
          background: `radial-gradient(
            circle,
            rgba(139, 92, 246, ${bgIntensity * (1 + breath * 0.3)}) 0%,
            rgba(6, 182, 212, ${bgIntensity * 0.5}) 30%,
            rgba(251, 191, 36, ${bgIntensity * 0.3 * convergenceProgress}) 50%,
            rgba(0, 0, 0, 0) 70%
          )`,
          filter: "blur(80px)",
        }}
      />

      {/* Particles - more active during convergence */}
      <Particles
        count={35}
        color="#8b5cf6"
        opacity={0.3 + convergenceProgress * 0.2}
        speed={0.3 + convergenceProgress * 0.3}
      />

      {/* Connection lines between owls */}
      <svg
        style={{
          position: "absolute",
          width: "100%",
          height: "100%",
          pointerEvents: "none",
        }}
      >
        <defs>
          <linearGradient id="lineGradHIW" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="#8b5cf6" stopOpacity={0.6} />
            <stop offset="50%" stopColor="#06b6d4" stopOpacity={0.3} />
            <stop offset="100%" stopColor="#8b5cf6" stopOpacity={0.6} />
          </linearGradient>
        </defs>
        {owls.map((owl, i) => {
          const nextOwl = owls[(i + 1) % 8];
          const currentRadius = radius * (1 - convergenceProgress * 0.6);
          const x1 = 960 + Math.cos(owl.angle) * currentRadius;
          const y1 = 540 + Math.sin(owl.angle) * currentRadius;
          const x2 = 960 + Math.cos(nextOwl.angle) * currentRadius;
          const y2 = 540 + Math.sin(nextOwl.angle) * currentRadius;

          const lineOpacity = interpolate(
            frame,
            [60 + i * 5, 80 + i * 5],
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
              stroke="url(#lineGradHIW)"
              strokeWidth={2}
              opacity={lineOpacity * (1 + breath * 0.2)}
            />
          );
        })}

        {/* Cross connections during convergence */}
        {convergenceProgress > 0 &&
          [...Array(4)].map((_, i) => {
            const currentRadius = radius * (1 - convergenceProgress * 0.6);
            const angle1 = (i / 8) * Math.PI * 2 - Math.PI / 2;
            const angle2 = ((i + 4) / 8) * Math.PI * 2 - Math.PI / 2;
            const x1 = 960 + Math.cos(angle1) * currentRadius;
            const y1 = 540 + Math.sin(angle1) * currentRadius;
            const x2 = 960 + Math.cos(angle2) * currentRadius;
            const y2 = 540 + Math.sin(angle2) * currentRadius;

            return (
              <line
                key={`cross-${i}`}
                x1={x1}
                y1={y1}
                x2={x2}
                y2={y2}
                stroke={OWL_COLORS[i]}
                strokeWidth={1.5}
                opacity={convergenceProgress * 0.4 * (1 + breath * 0.3)}
              />
            );
          })
        }
      </svg>

      {/* 8 Owl Nodes */}
      {owls.map((owl, i) => (
        <OwlNode
          key={i}
          index={i}
          name={owl.name}
          func={owl.func}
          color={owl.color}
          angle={owl.angle}
          radius={radius}
          highlightFrame={owl.highlightFrame}
          convergenceProgress={convergenceProgress}
          showLabel={frame >= owl.highlightFrame && frame < 240}
        />
      ))}

      {/* CENTER - Emergence point */}
      {phase4 && (
        <>
          <div
            style={{
              position: "absolute",
              width: 100 + centerEmergence * 40,
              height: 100 + centerEmergence * 40,
              borderRadius: "50%",
              background: `radial-gradient(
                circle,
                rgba(255, 255, 255, ${0.9 * centerEmergence}) 0%,
                rgba(251, 191, 36, ${0.6 * centerEmergence}) 30%,
                rgba(139, 92, 246, ${0.3 * centerEmergence}) 60%,
                transparent 100%
              )`,
              boxShadow: `0 0 ${50 * centerEmergence}px #fbbf24, 0 0 ${100 * centerEmergence}px #8b5cf6`,
              transform: `scale(${1 + breath * 0.1})`,
            }}
          />
          <ExplodingParticles
            startFrame={250}
            originX={50}
            originY={50}
            count={50}
            color="#fbbf24"
            duration={40}
          />
        </>
      )}

      {/* Flash at convergence */}
      {frame >= 250 && frame <= 265 && (
        <div
          style={{
            position: "absolute",
            width: "100%",
            height: "100%",
            backgroundColor: "#fff",
            opacity: interpolate(frame, [250, 255, 265], [0, 0.5, 0]),
            pointerEvents: "none",
          }}
        />
      )}

      {/* Title text */}
      <div
        style={{
          position: "absolute",
          top: 60,
          textAlign: "center",
        }}
      >
        {!phase4 && (
          <FadeInText
            text="8 perspectives scanning simultaneously"
            startFrame={30}
            fontSize={32}
            color="#fff"
            duration={25}
          />
        )}
        {phase4 && (
          <SlamText
            text="8 ways of seeing. ONE TRUTH."
            startFrame={260}
            fontSize={48}
            color="#fff"
            glowColor="#fbbf24"
            highlightWords={["ONE", "TRUTH"]}
            highlightColor="#fbbf24"
          />
        )}
      </div>

      {/* Function labels during phase 2 */}
      {phase2 && (
        <div
          style={{
            position: "absolute",
            bottom: 100,
            display: "flex",
            gap: 10,
            justifyContent: "center",
          }}
        >
          {OWL_FUNCTIONS.map((func, i) => {
            const showFrame = getHighlightFrame(i);
            const opacity = interpolate(
              frame,
              [showFrame, showFrame + 10, showFrame + highlightDuration - 5, showFrame + highlightDuration],
              [0, 1, 1, 0],
              { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
            );
            return (
              <span
                key={i}
                style={{
                  fontSize: 24,
                  fontWeight: 600,
                  color: OWL_COLORS[i],
                  fontFamily: "system-ui",
                  opacity,
                  textShadow: `0 0 15px ${OWL_COLORS[i]}`,
                }}
              >
                {func}
              </span>
            );
          })}
        </div>
      )}

      {/* Bottom tagline */}
      {phase4 && (
        <div
          style={{
            position: "absolute",
            bottom: 80,
            textAlign: "center",
          }}
        >
          <FadeInText
            text="All converging on what matters."
            startFrame={275}
            fontSize={28}
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
            rgba(10, 10, 26, 0.6) 100%
          )`,
          pointerEvents: "none",
        }}
      />
    </AbsoluteFill>
  );
};
