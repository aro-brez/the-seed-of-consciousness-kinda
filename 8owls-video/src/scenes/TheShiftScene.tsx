import { AbsoluteFill, useCurrentFrame, interpolate, spring, useVideoConfig } from "remotion";
import { Particles } from "../components/Particles";
import { FadeInText, SlamText } from "../components/TextEffects";
import { OwlEye } from "../components/OwlElements";

// Scene 2: THE SHIFT (2-10s) [240 frames]
// The transformation moment - owl appears, reveals what was missed
// "You're losing because of THIS." -> "Do THIS now."
// Feel: Relief. Clarity. "Holy shit that's obvious now"

interface DataCardProps {
  x: number;
  y: number;
  label: string;
  value: string;
  delay: number;
  isHighlighted: boolean;
  fadeAway: boolean;
}

const DataCard: React.FC<DataCardProps> = ({
  x,
  y,
  label,
  value,
  delay,
  isHighlighted,
  fadeAway,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const relativeFrame = frame - delay;

  if (relativeFrame < 0) return null;

  // Base opacity
  let opacity = interpolate(relativeFrame, [0, 15], [0, 0.8], {
    extrapolateRight: "clamp",
  });

  // Fade away non-highlighted items
  if (fadeAway && !isHighlighted) {
    opacity = interpolate(frame, [90, 130], [0.8, 0.1], {
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
    });
  }

  // Highlighted item pulses and grows
  const scale = isHighlighted
    ? interpolate(frame, [90, 120], [1, 1.2], {
        extrapolateLeft: "clamp",
        extrapolateRight: "clamp",
      })
    : 1;

  const glowIntensity = isHighlighted
    ? interpolate(frame, [90, 120], [0, 30], {
        extrapolateLeft: "clamp",
        extrapolateRight: "clamp",
      })
    : 0;

  const breath = isHighlighted ? Math.sin(frame * 0.08) * 5 : 0;

  return (
    <div
      style={{
        position: "absolute",
        left: `${x}%`,
        top: `${y}%`,
        transform: `translate(-50%, -50%) scale(${scale})`,
        opacity,
        backgroundColor: isHighlighted
          ? "rgba(251, 191, 36, 0.15)"
          : "rgba(15, 15, 35, 0.9)",
        borderRadius: 12,
        border: isHighlighted
          ? "2px solid #fbbf24"
          : "1px solid rgba(139, 92, 246, 0.3)",
        padding: "16px 24px",
        boxShadow: isHighlighted
          ? `0 0 ${glowIntensity + breath}px #fbbf24, 0 0 ${(glowIntensity + breath) * 2}px rgba(251, 191, 36, 0.5)`
          : "0 4px 20px rgba(0, 0, 0, 0.3)",
        transition: "all 0.3s ease",
      }}
    >
      <div
        style={{
          fontSize: 12,
          fontFamily: "system-ui",
          color: isHighlighted ? "#fbbf24" : "#666",
          letterSpacing: "0.1em",
          marginBottom: 6,
        }}
      >
        {label}
      </div>
      <div
        style={{
          fontSize: 28,
          fontFamily: "monospace",
          fontWeight: "bold",
          color: isHighlighted ? "#fbbf24" : "#fff",
        }}
      >
        {value}
      </div>
    </div>
  );
};

export const TheShiftScene: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Timeline:
  // 0-60: Data still visible, calming down from chaos
  // 60-90: OWL MATERIALIZES
  // 90-150: Data transforms - one thing highlights, others fade
  // 150-240: "This is what you missed" / "Do THIS now"

  const owlAppearing = frame >= 60;
  const transformPhase = frame >= 90;
  const actionPhase = frame >= 150;

  // Owl materialization
  const owlOpacity = interpolate(frame, [60, 90], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  const owlScale = spring({
    frame: frame - 60,
    fps,
    config: { damping: 15, stiffness: 100 },
  });

  const owlGlow = interpolate(frame, [60, 100, 150], [0, 0.5, 0.3], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  // Flash when insight revealed
  const insightFlash = interpolate(frame, [90, 95, 105], [0, 0.4, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  // Breathing rhythm
  const breath = Math.sin(frame * 0.04);

  // Data cards
  const dataCards: Omit<DataCardProps, "fadeAway">[] = [
    { x: 20, y: 25, label: "REVENUE", value: "$1.2M", delay: 0, isHighlighted: false },
    { x: 50, y: 20, label: "USERS", value: "24,891", delay: 5, isHighlighted: false },
    { x: 80, y: 25, label: "CHURN", value: "4.2%", delay: 3, isHighlighted: false },
    { x: 25, y: 50, label: "GROWTH", value: "+12%", delay: 8, isHighlighted: false },
    { x: 50, y: 45, label: "CORRELATION", value: "0.89", delay: 10, isHighlighted: true }, // THE INSIGHT
    { x: 75, y: 50, label: "NPS", value: "67", delay: 6, isHighlighted: false },
    { x: 20, y: 75, label: "CAC", value: "$142", delay: 12, isHighlighted: false },
    { x: 50, y: 70, label: "LTV", value: "$890", delay: 15, isHighlighted: false },
    { x: 80, y: 75, label: "MARGIN", value: "34%", delay: 9, isHighlighted: false },
  ];

  // Arrow pointing to the insight (appears after highlight)
  const arrowOpacity = interpolate(frame, [130, 145], [0, 1], {
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
      {/* Background field glow - calm, focused */}
      <div
        style={{
          position: "absolute",
          width: 900,
          height: 900,
          borderRadius: "50%",
          background: `radial-gradient(
            circle,
            rgba(139, 92, 246, ${0.1 + owlGlow * (1 + breath * 0.2)}) 0%,
            rgba(251, 191, 36, ${owlGlow * 0.3}) 30%,
            rgba(0, 0, 0, 0) 70%
          )`,
          filter: "blur(80px)",
        }}
      />

      {/* Calm particles */}
      <Particles count={25} color="#8b5cf6" opacity={0.3} speed={0.2} />

      {/* Data cards */}
      {dataCards.map((card, i) => (
        <DataCard key={i} {...card} fadeAway={transformPhase} />
      ))}

      {/* THE OWL - materializes */}
      {owlAppearing && (
        <div
          style={{
            position: "absolute",
            top: "15%",
            left: "50%",
            transform: `translate(-50%, 0) scale(${owlScale})`,
            opacity: owlOpacity,
          }}
        >
          {/* Owl glow field */}
          <div
            style={{
              position: "absolute",
              width: 200,
              height: 200,
              left: "50%",
              top: "50%",
              transform: "translate(-50%, -50%)",
              borderRadius: "50%",
              background: `radial-gradient(
                circle,
                rgba(139, 92, 246, ${owlGlow}) 0%,
                rgba(0, 0, 0, 0) 70%
              )`,
              filter: "blur(30px)",
            }}
          />
          <OwlEye
            size={100}
            glowColor="#8b5cf6"
            pulseSpeed={0.05}
          />
        </div>
      )}

      {/* Arrow pointing to insight */}
      {transformPhase && (
        <svg
          style={{
            position: "absolute",
            width: "100%",
            height: "100%",
            pointerEvents: "none",
            opacity: arrowOpacity,
          }}
        >
          <defs>
            <marker
              id="arrowhead"
              markerWidth="10"
              markerHeight="7"
              refX="9"
              refY="3.5"
              orient="auto"
            >
              <polygon points="0 0, 10 3.5, 0 7" fill="#fbbf24" />
            </marker>
          </defs>
          {/* Arrow from owl to insight */}
          <line
            x1="960"
            y1="280"
            x2="960"
            y2="420"
            stroke="#fbbf24"
            strokeWidth="3"
            markerEnd="url(#arrowhead)"
            opacity={0.8}
          />
        </svg>
      )}

      {/* Flash when insight revealed */}
      <div
        style={{
          position: "absolute",
          width: "100%",
          height: "100%",
          backgroundColor: "#fbbf24",
          opacity: insightFlash,
          pointerEvents: "none",
        }}
      />

      {/* Text: "This is what you missed" */}
      {transformPhase && !actionPhase && (
        <div
          style={{
            position: "absolute",
            bottom: 180,
            textAlign: "center",
          }}
        >
          <SlamText
            text="This is what you MISSED"
            startFrame={100}
            fontSize={48}
            color="#fff"
            glowColor="#fbbf24"
            highlightWords={["MISSED"]}
            highlightColor="#fbbf24"
          />
        </div>
      )}

      {/* Text: "Do THIS now" */}
      {actionPhase && (
        <div
          style={{
            position: "absolute",
            bottom: 150,
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            gap: 15,
          }}
        >
          <FadeInText
            text="Your best customers correlate 0.89 with feature X"
            startFrame={155}
            fontSize={24}
            color="#a78bfa"
            duration={20}
          />
          <SlamText
            text="Do THIS now:"
            startFrame={175}
            fontSize={42}
            color="#fff"
            glowColor="#06b6d4"
            highlightWords={["THIS"]}
            highlightColor="#06b6d4"
          />
          <FadeInText
            text="Enable feature X for all users. +18% retention."
            startFrame={195}
            fontSize={28}
            color="#06b6d4"
            duration={25}
          />
        </div>
      )}

      {/* Subtle grid */}
      <div
        style={{
          position: "absolute",
          width: "100%",
          height: "100%",
          backgroundImage: `
            linear-gradient(rgba(139, 92, 246, 0.02) 1px, transparent 1px),
            linear-gradient(90deg, rgba(139, 92, 246, 0.02) 1px, transparent 1px)
          `,
          backgroundSize: "60px 60px",
          pointerEvents: "none",
          opacity: interpolate(frame, [0, 60], [0.5, 1], { extrapolateRight: "clamp" }),
        }}
      />

      {/* Vignette */}
      <div
        style={{
          position: "absolute",
          width: "100%",
          height: "100%",
          background: `radial-gradient(
            circle at center,
            transparent 40%,
            rgba(10, 10, 26, 0.7) 100%
          )`,
          pointerEvents: "none",
        }}
      />
    </AbsoluteFill>
  );
};
