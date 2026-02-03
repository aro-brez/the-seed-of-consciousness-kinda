import { AbsoluteFill, useCurrentFrame, interpolate, spring, useVideoConfig } from "remotion";
import { SlamText } from "../components/TextEffects";
import { ExplodingParticles, Particles, DataStream } from "../components/Particles";

// Scene 1: HOOK (0-2s) [60 frames]
// Person overwhelmed by data - "What if you could see what you're missing?"
// Relatable frustration - "that's me"

interface DashboardItemProps {
  x: number;
  y: number;
  width: number;
  height: number;
  delay: number;
  type: "chart" | "number" | "notification" | "list";
}

const DashboardItem: React.FC<DashboardItemProps> = ({ x, y, width, height, delay, type }) => {
  const frame = useCurrentFrame();
  const relativeFrame = frame - delay;

  if (relativeFrame < 0) return null;

  const opacity = interpolate(relativeFrame, [0, 10], [0, 0.6], {
    extrapolateRight: "clamp",
  });

  const shake = Math.sin(relativeFrame * 0.5 + delay) * 2;

  const renderContent = () => {
    switch (type) {
      case "chart":
        return (
          <svg width="100%" height="100%" viewBox="0 0 100 60">
            {[...Array(6)].map((_, i) => (
              <rect
                key={i}
                x={10 + i * 15}
                y={60 - Math.random() * 40 - 10}
                width={10}
                height={Math.random() * 40 + 10}
                fill="#06b6d4"
                opacity={0.6}
              />
            ))}
          </svg>
        );
      case "number":
        return (
          <div style={{
            fontSize: 24,
            fontFamily: "monospace",
            color: "#f472b6",
            fontWeight: "bold",
          }}>
            {Math.floor(Math.random() * 9000 + 1000)}
          </div>
        );
      case "notification":
        return (
          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <div style={{
              width: 8,
              height: 8,
              borderRadius: "50%",
              backgroundColor: "#f87171",
              boxShadow: "0 0 10px #f87171",
            }} />
            <div style={{
              fontSize: 11,
              color: "#fff",
              opacity: 0.8,
              fontFamily: "system-ui",
            }}>
              Action required
            </div>
          </div>
        );
      case "list":
        return (
          <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
            {[...Array(3)].map((_, i) => (
              <div key={i} style={{
                height: 6,
                backgroundColor: "#8b5cf6",
                opacity: 0.4,
                borderRadius: 3,
                width: `${70 + Math.random() * 30}%`,
              }} />
            ))}
          </div>
        );
    }
  };

  return (
    <div
      style={{
        position: "absolute",
        left: `${x}%`,
        top: `${y}%`,
        width,
        height,
        transform: `translate(-50%, -50%) translateX(${shake}px)`,
        opacity,
        backgroundColor: "rgba(15, 15, 35, 0.9)",
        borderRadius: 8,
        border: "1px solid rgba(139, 92, 246, 0.3)",
        padding: 12,
        display: "flex",
        justifyContent: "center",
        alignItems: "center",
        overflow: "hidden",
      }}
    >
      {renderContent()}
    </div>
  );
};

export const HookScene: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Flash effect at start
  const flashOpacity = interpolate(frame, [0, 3, 10], [0.8, 0.5, 0], {
    extrapolateRight: "clamp",
  });

  // Background pulse - anxiety feeling
  const bgPulse = interpolate(
    Math.sin(frame * 0.2),
    [-1, 1],
    [0.02, 0.08]
  );

  // Screen shake - overwhelm
  const screenShake = frame < 45
    ? Math.sin(frame * 0.8) * (2 + frame * 0.05)
    : interpolate(frame, [45, 60], [3, 0]);

  // Dashboard items flooding in
  const dashboardItems: DashboardItemProps[] = [
    { x: 15, y: 20, width: 140, height: 80, delay: 2, type: "chart" },
    { x: 35, y: 15, width: 100, height: 50, delay: 5, type: "number" },
    { x: 55, y: 25, width: 120, height: 40, delay: 8, type: "notification" },
    { x: 75, y: 18, width: 130, height: 70, delay: 4, type: "list" },
    { x: 85, y: 35, width: 100, height: 50, delay: 10, type: "number" },
    { x: 20, y: 40, width: 110, height: 45, delay: 6, type: "notification" },
    { x: 45, y: 38, width: 90, height: 60, delay: 12, type: "chart" },
    { x: 65, y: 42, width: 115, height: 55, delay: 7, type: "list" },
    { x: 25, y: 60, width: 130, height: 50, delay: 9, type: "chart" },
    { x: 50, y: 58, width: 100, height: 45, delay: 14, type: "notification" },
    { x: 75, y: 55, width: 120, height: 65, delay: 11, type: "number" },
    { x: 15, y: 75, width: 100, height: 40, delay: 13, type: "list" },
    { x: 40, y: 78, width: 90, height: 50, delay: 16, type: "number" },
    { x: 60, y: 72, width: 110, height: 55, delay: 15, type: "chart" },
    { x: 85, y: 75, width: 95, height: 45, delay: 18, type: "notification" },
  ];

  // Text fade in timing
  const textOpacity = interpolate(frame, [15, 30], [0, 1], {
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
      {/* Screen shake container */}
      <div
        style={{
          position: "absolute",
          width: "100%",
          height: "100%",
          transform: `translateX(${screenShake}px) translateY(${screenShake * 0.5}px)`,
        }}
      >
        {/* Data streams - chaos */}
        <DataStream direction="up" count={20} speed={2} opacity={0.15} />
        <DataStream direction="down" count={15} speed={1.5} opacity={0.1} />

        {/* Ambient particles - scattered */}
        <Particles count={40} color="#8b5cf6" opacity={0.25} speed={0.8} />

        {/* Dashboard items flooding in */}
        {dashboardItems.map((item, i) => (
          <DashboardItem key={i} {...item} />
        ))}
      </div>

      {/* Flash on entry */}
      <div
        style={{
          position: "absolute",
          width: "100%",
          height: "100%",
          backgroundColor: "#fff",
          opacity: flashOpacity,
          pointerEvents: "none",
        }}
      />

      {/* Anxiety vignette - tighter, more claustrophobic */}
      <div
        style={{
          position: "absolute",
          width: "100%",
          height: "100%",
          background: `radial-gradient(
            circle at center,
            transparent 20%,
            rgba(10, 10, 26, 0.6) 50%,
            rgba(10, 10, 26, 0.95) 100%
          )`,
          pointerEvents: "none",
        }}
      />

      {/* Background anxiety pulse */}
      <div
        style={{
          position: "absolute",
          width: 1200,
          height: 1200,
          borderRadius: "50%",
          background: `radial-gradient(
            circle,
            rgba(248, 113, 113, ${bgPulse}) 0%,
            rgba(139, 92, 246, ${bgPulse * 0.5}) 30%,
            rgba(0, 0, 0, 0) 60%
          )`,
          filter: "blur(100px)",
        }}
      />

      {/* Main text - "What if you could see what you're missing?" */}
      <div
        style={{
          position: "absolute",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          gap: 0,
          opacity: textOpacity,
          zIndex: 10,
        }}
      >
        <SlamText
          text="What if you could see"
          startFrame={15}
          fontSize={52}
          color="#fff"
          glowColor="#8b5cf6"
        />
        <div style={{ marginTop: 5 }}>
          <SlamText
            text="what you're MISSING?"
            startFrame={22}
            fontSize={72}
            color="#fff"
            glowColor="#fbbf24"
            highlightWords={["MISSING"]}
            highlightColor="#fbbf24"
          />
        </div>
      </div>

      {/* Particle explosion from text */}
      <ExplodingParticles
        startFrame={22}
        originX={50}
        originY={50}
        count={30}
        color="#fbbf24"
        duration={35}
      />
    </AbsoluteFill>
  );
};
