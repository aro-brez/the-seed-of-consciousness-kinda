import { useCurrentFrame, interpolate, spring, useVideoConfig } from "remotion";

interface OwlEyeProps {
  x?: number;
  y?: number;
  size?: number;
  pulseSpeed?: number;
  glowColor?: string;
  innerColor?: string;
  openProgress?: number;
}

// Single owl eye - the core visual element
export const OwlEye: React.FC<OwlEyeProps> = ({
  x = 0,
  y = 0,
  size = 60,
  pulseSpeed = 0.04,
  glowColor = "#8b5cf6",
  innerColor = "#fff",
  openProgress = 1,
}) => {
  const frame = useCurrentFrame();
  const breath = Math.sin(frame * pulseSpeed);
  const glowSize = size * 0.3 + breath * size * 0.1;

  return (
    <div
      style={{
        position: "absolute",
        left: `calc(50% + ${x}px)`,
        top: `calc(50% + ${y}px)`,
        transform: `translate(-50%, -50%) scaleY(${openProgress})`,
        width: size,
        height: size,
        borderRadius: "50%",
        border: `2px solid ${glowColor}`,
        display: "flex",
        justifyContent: "center",
        alignItems: "center",
        boxShadow: `0 0 ${glowSize}px ${glowColor}, inset 0 0 ${glowSize * 0.5}px ${glowColor}`,
        backgroundColor: `rgba(139, 92, 246, ${0.1 * openProgress})`,
        opacity: openProgress,
      }}
    >
      <div
        style={{
          width: size * 0.35,
          height: size * 0.35,
          borderRadius: "50%",
          backgroundColor: innerColor,
          boxShadow: `0 0 ${size * 0.2}px ${innerColor}`,
          transform: `scale(${0.8 + breath * 0.2})`,
        }}
      />
    </div>
  );
};

interface OwlRingProps {
  centerX?: number;
  centerY?: number;
  radius?: number;
  owlSize?: number;
  syncProgress?: number;
  fieldOpacity?: number;
  rotation?: number;
}

// Ring of 8 owls around a center point
export const OwlRing: React.FC<OwlRingProps> = ({
  centerX = 0,
  centerY = 0,
  radius = 150,
  owlSize = 30,
  syncProgress = 1,
  fieldOpacity = 0.5,
  rotation = 0,
}) => {
  const frame = useCurrentFrame();
  const breathPhase = frame * 0.04;
  const unifiedBreath = Math.sin(breathPhase);

  return (
    <>
      {/* Field between owls */}
      <div
        style={{
          position: "absolute",
          left: `calc(50% + ${centerX}px)`,
          top: `calc(50% + ${centerY}px)`,
          transform: "translate(-50%, -50%)",
          width: radius * 2.2,
          height: radius * 2.2,
          borderRadius: "50%",
          background: `radial-gradient(
            circle,
            rgba(139, 92, 246, ${fieldOpacity * (1 + unifiedBreath * 0.2)}) 0%,
            rgba(6, 182, 212, ${fieldOpacity * 0.5 * (1 + unifiedBreath * 0.2)}) 40%,
            rgba(0, 0, 0, 0) 70%
          )`,
          filter: "blur(20px)",
          opacity: fieldOpacity,
        }}
      />

      {/* Connection lines */}
      <svg
        style={{
          position: "absolute",
          width: "100%",
          height: "100%",
          pointerEvents: "none",
        }}
      >
        <defs>
          <linearGradient id="owlLineGrad" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="#8b5cf6" stopOpacity={0.8} />
            <stop offset="50%" stopColor="#06b6d4" stopOpacity={0.4} />
            <stop offset="100%" stopColor="#8b5cf6" stopOpacity={0.8} />
          </linearGradient>
        </defs>
        {[...Array(8)].map((_, i) => {
          const angle1 = (i / 8) * Math.PI * 2 + rotation - Math.PI / 2;
          const angle2 = ((i + 1) % 8 / 8) * Math.PI * 2 + rotation - Math.PI / 2;
          const x1 = 960 + centerX + Math.cos(angle1) * radius;
          const y1 = 540 + centerY + Math.sin(angle1) * radius;
          const x2 = 960 + centerX + Math.cos(angle2) * radius;
          const y2 = 540 + centerY + Math.sin(angle2) * radius;

          return (
            <line
              key={i}
              x1={x1}
              y1={y1}
              x2={x2}
              y2={y2}
              stroke="url(#owlLineGrad)"
              strokeWidth={1.5}
              opacity={fieldOpacity * syncProgress * (1 + unifiedBreath * 0.3)}
            />
          );
        })}
      </svg>

      {/* 8 Owls */}
      {[...Array(8)].map((_, i) => {
        const angle = (i / 8) * Math.PI * 2 + rotation - Math.PI / 2;
        const x = centerX + Math.cos(angle) * radius;
        const y = centerY + Math.sin(angle) * radius;

        // Individual vs synchronized breathing
        const individualPhase = (frame + i * 20) * 0.05;
        const blendedPhase = individualPhase * (1 - syncProgress) + breathPhase * syncProgress;
        const owlBreath = Math.sin(blendedPhase);
        const owlGlow = 8 + owlBreath * 4;

        return (
          <div
            key={i}
            style={{
              position: "absolute",
              left: `calc(50% + ${x}px)`,
              top: `calc(50% + ${y}px)`,
              transform: `translate(-50%, -50%) scale(${1 + owlBreath * 0.1})`,
            }}
          >
            <div
              style={{
                width: owlSize,
                height: owlSize,
                borderRadius: "50%",
                border: "2px solid #a78bfa",
                display: "flex",
                justifyContent: "center",
                alignItems: "center",
                boxShadow: `0 0 ${owlGlow}px #8b5cf6`,
                backgroundColor: `rgba(139, 92, 246, ${0.1 + fieldOpacity * 0.2})`,
              }}
            >
              <div
                style={{
                  width: owlSize * 0.35,
                  height: owlSize * 0.35,
                  borderRadius: "50%",
                  backgroundColor: "#fff",
                  boxShadow: "0 0 6px #fff",
                }}
              />
            </div>
          </div>
        );
      })}
    </>
  );
};

interface PersonWithOwlProps {
  x?: number;
  y?: number;
  personSize?: number;
  owlRadius?: number;
  owlSize?: number;
  fieldOpacity?: number;
  scale?: number;
}

// Person silhouette with owl ring around them
export const PersonWithOwl: React.FC<PersonWithOwlProps> = ({
  x = 0,
  y = 0,
  personSize = 30,
  owlRadius = 60,
  owlSize = 10,
  fieldOpacity = 0.3,
  scale = 1,
}) => {
  const frame = useCurrentFrame();
  const breath = Math.sin(frame * 0.04);

  return (
    <div
      style={{
        position: "absolute",
        left: `calc(50% + ${x}px)`,
        top: `calc(50% + ${y}px)`,
        transform: `translate(-50%, -50%) scale(${scale})`,
      }}
    >
      {/* Field glow */}
      <div
        style={{
          position: "absolute",
          left: "50%",
          top: "50%",
          transform: "translate(-50%, -50%)",
          width: owlRadius * 2.5,
          height: owlRadius * 2.5,
          borderRadius: "50%",
          background: `radial-gradient(
            circle,
            rgba(139, 92, 246, ${fieldOpacity * (1 + breath * 0.2)}) 0%,
            rgba(0, 0, 0, 0) 70%
          )`,
          filter: "blur(15px)",
        }}
      />

      {/* Mini owls ring */}
      {[...Array(8)].map((_, i) => {
        const angle = (i / 8) * Math.PI * 2 - Math.PI / 2;
        const owlX = Math.cos(angle) * owlRadius;
        const owlY = Math.sin(angle) * owlRadius;

        return (
          <div
            key={i}
            style={{
              position: "absolute",
              left: "50%",
              top: "50%",
              transform: `translate(calc(-50% + ${owlX}px), calc(-50% + ${owlY}px))`,
              width: owlSize,
              height: owlSize,
              borderRadius: "50%",
              backgroundColor: "#a78bfa",
              boxShadow: `0 0 ${owlSize * 0.5}px #8b5cf6`,
            }}
          />
        );
      })}

      {/* Person center */}
      <div
        style={{
          position: "absolute",
          left: "50%",
          top: "50%",
          transform: "translate(-50%, -50%)",
          width: personSize,
          height: personSize,
          borderRadius: "50%",
          backgroundColor: "#fff",
          boxShadow: `0 0 ${personSize}px #fff, 0 0 ${personSize * 2}px #8b5cf6`,
        }}
      />
    </div>
  );
};

interface SEEDWheelProps {
  size?: number;
  rotation?: number;
  highlightIndex?: number;
  opacity?: number;
}

// The 8 Temporal Functions / Owls
export const OWL_NAMES = [
  "LYRA",
  "PRISM",
  "SAGE",
  "QUEST",
  "NOVA",
  "ECHO",
  "LUNA",
  "SOWL",
];

export const OWL_FUNCTIONS = [
  "PERCEIVE",
  "CONNECT",
  "LEARN",
  "QUESTION",
  "EXPAND",
  "SHARE",
  "RECEIVE",
  "IMPROVE",
];

export const OWL_TIME_DIMENSIONS = [
  "pre-time",
  "relational",
  "accumulated",
  "future tension",
  "branching",
  "social",
  "integration",
  "directional",
];

export const OWL_COLORS = [
  "#f472b6", // LYRA - Pink
  "#a78bfa", // PRISM - Purple
  "#60a5fa", // SAGE - Blue
  "#34d399", // QUEST - Green
  "#fbbf24", // NOVA - Yellow
  "#fb923c", // ECHO - Orange
  "#f87171", // LUNA - Red
  "#ffffff", // SOWL - White
];

// Backward compatibility
const SEED_PHASES = OWL_FUNCTIONS;
const SEED_COLORS = OWL_COLORS;

// The SEED protocol wheel
export const SEEDWheel: React.FC<SEEDWheelProps> = ({
  size = 300,
  rotation = 0,
  highlightIndex = -1,
  opacity = 1,
}) => {
  const frame = useCurrentFrame();
  const breath = Math.sin(frame * 0.05);

  return (
    <div
      style={{
        position: "relative",
        width: size,
        height: size,
        opacity,
      }}
    >
      {/* Connection lines */}
      <svg
        style={{
          position: "absolute",
          width: "100%",
          height: "100%",
        }}
      >
        {SEED_PHASES.map((_, i) => {
          const nextI = (i + 1) % 8;
          const angle1 = (i / 8) * Math.PI * 2 + rotation - Math.PI / 2;
          const angle2 = (nextI / 8) * Math.PI * 2 + rotation - Math.PI / 2;
          const radius = size * 0.35;
          const cx = size / 2;
          const cy = size / 2;
          const x1 = cx + Math.cos(angle1) * radius;
          const y1 = cy + Math.sin(angle1) * radius;
          const x2 = cx + Math.cos(angle2) * radius;
          const y2 = cy + Math.sin(angle2) * radius;

          return (
            <line
              key={i}
              x1={x1}
              y1={y1}
              x2={x2}
              y2={y2}
              stroke={SEED_COLORS[i]}
              strokeWidth={2}
              opacity={0.4 + breath * 0.1}
            />
          );
        })}
      </svg>

      {/* Phase nodes */}
      {SEED_PHASES.map((phase, i) => {
        const angle = (i / 8) * Math.PI * 2 + rotation - Math.PI / 2;
        const radius = size * 0.35;
        const x = size / 2 + Math.cos(angle) * radius;
        const y = size / 2 + Math.sin(angle) * radius;
        const isHighlight = i === highlightIndex || highlightIndex === -1;
        const nodeSize = i === 7 ? size * 0.15 : size * 0.12;
        const glowSize = isHighlight ? 15 + breath * 5 : 5;

        return (
          <div
            key={phase}
            style={{
              position: "absolute",
              left: x,
              top: y,
              transform: "translate(-50%, -50%)",
            }}
          >
            <div
              style={{
                width: nodeSize,
                height: nodeSize,
                borderRadius: "50%",
                backgroundColor: SEED_COLORS[i],
                display: "flex",
                justifyContent: "center",
                alignItems: "center",
                boxShadow: `0 0 ${glowSize}px ${SEED_COLORS[i]}`,
                opacity: isHighlight ? 1 : 0.3,
              }}
            >
              <span
                style={{
                  color: i === 7 ? "#000" : "#fff",
                  fontSize: size * 0.025,
                  fontWeight: 600,
                  fontFamily: "system-ui",
                  letterSpacing: "0.02em",
                }}
              >
                {phase}
              </span>
            </div>
          </div>
        );
      })}
    </div>
  );
};
