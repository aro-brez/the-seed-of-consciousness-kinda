import { useCurrentFrame, interpolate, spring, useVideoConfig } from "remotion";

interface SlamTextProps {
  text: string;
  startFrame?: number;
  fontSize?: number;
  color?: string;
  glowColor?: string;
  highlightWords?: string[];
  highlightColor?: string;
}

// Text that SLAMS in with impact
export const SlamText: React.FC<SlamTextProps> = ({
  text,
  startFrame = 0,
  fontSize = 72,
  color = "#fff",
  glowColor = "#8b5cf6",
  highlightWords = [],
  highlightColor = "#06b6d4",
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const relativeFrame = frame - startFrame;

  if (relativeFrame < 0) return null;

  const scale = spring({
    frame: relativeFrame,
    fps,
    config: { damping: 12, stiffness: 200, mass: 0.5 },
  });

  const overshoot = spring({
    frame: relativeFrame,
    fps,
    config: { damping: 8, stiffness: 300, mass: 0.3 },
  });

  const glowIntensity = interpolate(
    relativeFrame,
    [0, 10, 30],
    [0, 40, 15],
    { extrapolateRight: "clamp" }
  );

  const shake = relativeFrame < 10
    ? Math.sin(relativeFrame * 2) * (10 - relativeFrame)
    : 0;

  // Split text to highlight specific words
  const words = text.split(" ");
  const renderedWords = words.map((word, i) => {
    const isHighlight = highlightWords.some(
      (hw) => word.toLowerCase().includes(hw.toLowerCase())
    );
    return (
      <span
        key={i}
        style={{
          color: isHighlight ? highlightColor : color,
          textShadow: isHighlight ? `0 0 20px ${highlightColor}` : undefined,
        }}
      >
        {word}{i < words.length - 1 ? " " : ""}
      </span>
    );
  });

  return (
    <div
      style={{
        fontSize,
        fontFamily: "system-ui, -apple-system, sans-serif",
        fontWeight: 700,
        letterSpacing: "0.02em",
        transform: `scale(${scale * overshoot}) translateX(${shake}px)`,
        textShadow: `0 0 ${glowIntensity}px ${glowColor}`,
        textAlign: "center",
        maxWidth: "90%",
      }}
    >
      {renderedWords}
    </div>
  );
};

interface GlitchTextProps {
  text: string;
  startFrame?: number;
  duration?: number;
  fontSize?: number;
  color?: string;
}

// Text with glitch effect
export const GlitchText: React.FC<GlitchTextProps> = ({
  text,
  startFrame = 0,
  duration = 30,
  fontSize = 48,
  color = "#fff",
}) => {
  const frame = useCurrentFrame();
  const relativeFrame = frame - startFrame;

  if (relativeFrame < 0) return null;

  const glitchActive = relativeFrame < duration;
  const glitchIntensity = glitchActive
    ? interpolate(relativeFrame, [0, duration], [1, 0])
    : 0;

  const offsetX = glitchActive ? Math.sin(relativeFrame * 5) * 5 * glitchIntensity : 0;
  const offsetY = glitchActive ? Math.cos(relativeFrame * 7) * 3 * glitchIntensity : 0;

  return (
    <div style={{ position: "relative" }}>
      {/* Red channel */}
      {glitchActive && (
        <div
          style={{
            position: "absolute",
            fontSize,
            fontFamily: "system-ui",
            fontWeight: 700,
            color: "#ff0000",
            opacity: 0.7 * glitchIntensity,
            transform: `translate(${offsetX}px, ${offsetY}px)`,
            mixBlendMode: "screen",
          }}
        >
          {text}
        </div>
      )}
      {/* Cyan channel */}
      {glitchActive && (
        <div
          style={{
            position: "absolute",
            fontSize,
            fontFamily: "system-ui",
            fontWeight: 700,
            color: "#00ffff",
            opacity: 0.7 * glitchIntensity,
            transform: `translate(${-offsetX}px, ${-offsetY}px)`,
            mixBlendMode: "screen",
          }}
        >
          {text}
        </div>
      )}
      {/* Main text */}
      <div
        style={{
          fontSize,
          fontFamily: "system-ui",
          fontWeight: 700,
          color,
          position: "relative",
        }}
      >
        {text}
      </div>
    </div>
  );
};

interface TypewriterTextProps {
  text: string;
  startFrame?: number;
  charsPerFrame?: number;
  fontSize?: number;
  color?: string;
}

// Typewriter effect
export const TypewriterText: React.FC<TypewriterTextProps> = ({
  text,
  startFrame = 0,
  charsPerFrame = 0.5,
  fontSize = 32,
  color = "#fff",
}) => {
  const frame = useCurrentFrame();
  const relativeFrame = frame - startFrame;

  if (relativeFrame < 0) return null;

  const charCount = Math.min(
    Math.floor(relativeFrame * charsPerFrame),
    text.length
  );

  const displayText = text.substring(0, charCount);
  const showCursor = Math.floor(relativeFrame / 15) % 2 === 0;

  return (
    <div
      style={{
        fontSize,
        fontFamily: "monospace",
        color,
        whiteSpace: "pre-wrap",
      }}
    >
      {displayText}
      {charCount < text.length && showCursor && (
        <span style={{ opacity: 0.8 }}>|</span>
      )}
    </div>
  );
};

interface FadeInTextProps {
  text: string;
  startFrame?: number;
  duration?: number;
  fontSize?: number;
  color?: string;
  direction?: "up" | "down" | "left" | "right" | "none";
}

// Smooth fade in with optional direction
export const FadeInText: React.FC<FadeInTextProps> = ({
  text,
  startFrame = 0,
  duration = 30,
  fontSize = 32,
  color = "#fff",
  direction = "up",
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const relativeFrame = frame - startFrame;

  if (relativeFrame < 0) return null;

  const opacity = interpolate(
    relativeFrame,
    [0, duration],
    [0, 1],
    { extrapolateRight: "clamp" }
  );

  const slideAmount = 30;
  let transform = "";

  switch (direction) {
    case "up":
      transform = `translateY(${(1 - opacity) * slideAmount}px)`;
      break;
    case "down":
      transform = `translateY(${-(1 - opacity) * slideAmount}px)`;
      break;
    case "left":
      transform = `translateX(${(1 - opacity) * slideAmount}px)`;
      break;
    case "right":
      transform = `translateX(${-(1 - opacity) * slideAmount}px)`;
      break;
    default:
      transform = "";
  }

  return (
    <div
      style={{
        fontSize,
        fontFamily: "system-ui",
        fontWeight: 400,
        color,
        opacity,
        transform,
        letterSpacing: "0.05em",
      }}
    >
      {text}
    </div>
  );
};
