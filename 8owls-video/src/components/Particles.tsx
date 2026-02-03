import { useCurrentFrame, interpolate } from "remotion";

interface ParticlesProps {
  count?: number;
  color?: string;
  maxSize?: number;
  minSize?: number;
  speed?: number;
  spread?: number;
  opacity?: number;
}

// Floating ambient particles that add life to every scene
export const Particles: React.FC<ParticlesProps> = ({
  count = 50,
  color = "#8b5cf6",
  maxSize = 4,
  minSize = 1,
  speed = 0.5,
  spread = 1,
  opacity = 0.6,
}) => {
  const frame = useCurrentFrame();

  // Generate deterministic particle positions
  const particles = Array.from({ length: count }, (_, i) => {
    const seed = i * 137.5;
    const baseX = ((seed * 7) % 100);
    const baseY = ((seed * 13) % 100);
    const size = minSize + ((seed * 3) % (maxSize - minSize));
    const speedMod = 0.5 + ((seed * 5) % 1);
    const phase = (seed * 11) % (Math.PI * 2);

    return { baseX, baseY, size, speedMod, phase, seed };
  });

  return (
    <div
      style={{
        position: "absolute",
        width: "100%",
        height: "100%",
        overflow: "hidden",
        pointerEvents: "none",
      }}
    >
      {particles.map((p, i) => {
        const t = frame * speed * 0.01 * p.speedMod;
        const x = p.baseX + Math.sin(t + p.phase) * 3 * spread;
        const y = p.baseY + Math.cos(t * 0.7 + p.phase) * 2 * spread;
        const particleOpacity = opacity * (0.3 + Math.sin(t * 2 + p.phase) * 0.7);

        return (
          <div
            key={i}
            style={{
              position: "absolute",
              left: `${x}%`,
              top: `${y}%`,
              width: p.size,
              height: p.size,
              borderRadius: "50%",
              backgroundColor: color,
              opacity: particleOpacity,
              boxShadow: `0 0 ${p.size * 2}px ${color}`,
            }}
          />
        );
      })}
    </div>
  );
};

interface ExplodingParticlesProps {
  startFrame: number;
  originX?: number;
  originY?: number;
  count?: number;
  color?: string;
  duration?: number;
}

// Particles that explode outward from a point
export const ExplodingParticles: React.FC<ExplodingParticlesProps> = ({
  startFrame,
  originX = 50,
  originY = 50,
  count = 30,
  color = "#fff",
  duration = 60,
}) => {
  const frame = useCurrentFrame();
  const relativeFrame = frame - startFrame;

  if (relativeFrame < 0 || relativeFrame > duration) return null;

  const progress = relativeFrame / duration;

  const particles = Array.from({ length: count }, (_, i) => {
    const angle = (i / count) * Math.PI * 2 + ((i * 137.5) % Math.PI);
    const speed = 2 + ((i * 17) % 3);
    const size = 2 + ((i * 7) % 4);

    return { angle, speed, size };
  });

  return (
    <div
      style={{
        position: "absolute",
        width: "100%",
        height: "100%",
        overflow: "hidden",
        pointerEvents: "none",
      }}
    >
      {particles.map((p, i) => {
        const distance = progress * p.speed * 20;
        const x = originX + Math.cos(p.angle) * distance;
        const y = originY + Math.sin(p.angle) * distance;
        const particleOpacity = 1 - progress;

        return (
          <div
            key={i}
            style={{
              position: "absolute",
              left: `${x}%`,
              top: `${y}%`,
              width: p.size,
              height: p.size,
              borderRadius: "50%",
              backgroundColor: color,
              opacity: particleOpacity,
              boxShadow: `0 0 ${p.size * 3}px ${color}`,
              transform: "translate(-50%, -50%)",
            }}
          />
        );
      })}
    </div>
  );
};

interface DataStreamProps {
  direction?: "up" | "down" | "left" | "right";
  count?: number;
  speed?: number;
  opacity?: number;
}

// Data streams flowing in a direction (for chaos scenes)
export const DataStream: React.FC<DataStreamProps> = ({
  direction = "up",
  count = 20,
  speed = 1,
  opacity = 0.5,
}) => {
  const frame = useCurrentFrame();

  const isVertical = direction === "up" || direction === "down";
  const isReverse = direction === "down" || direction === "right";

  const streams = Array.from({ length: count }, (_, i) => {
    const seed = i * 137.5;
    const position = (seed * 7) % 100;
    const length = 20 + ((seed * 3) % 80);
    const speedMod = 0.5 + ((seed * 5) % 1);
    const chars = ["0", "1", "@", "#", "$", "%", "&"][Math.floor(seed) % 7];

    return { position, length, speedMod, chars };
  });

  return (
    <div
      style={{
        position: "absolute",
        width: "100%",
        height: "100%",
        overflow: "hidden",
        pointerEvents: "none",
      }}
    >
      {streams.map((s, i) => {
        const t = (frame * speed * s.speedMod * 2) % 200;
        const offset = isReverse ? 100 - t : t - 100;

        const style: React.CSSProperties = isVertical
          ? { left: `${s.position}%`, top: `${offset}%` }
          : { top: `${s.position}%`, left: `${offset}%` };

        return (
          <div
            key={i}
            style={{
              position: "absolute",
              ...style,
              fontFamily: "monospace",
              fontSize: 12,
              color: "#06b6d4",
              opacity: opacity * 0.5,
              whiteSpace: "nowrap",
              transform: isVertical ? "none" : "rotate(90deg)",
            }}
          >
            {Array.from({ length: Math.floor(s.length / 2) }, () => s.chars).join("")}
          </div>
        );
      })}
    </div>
  );
};
