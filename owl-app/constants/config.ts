// Configuration constants
export const config = {
  // NATS WebSocket bridge
  natsWebSocketUrl: 'ws://192.168.5.108:8765',

  // Claude API (will use environment variable in production)
  claudeApiUrl: 'https://api.anthropic.com/v1/messages',

  // Reconnection settings
  reconnectDelay: 3000,
  maxReconnectAttempts: 10,

  // Message limits
  maxMessageLength: 4000,

  // Voice settings
  speechRate: 0.9,
  speechPitch: 1.0,
};

// SEED Protocol phases
export const SEED_PHASES = [
  'PERCEIVE',
  'CONNECT',
  'LEARN',
  'QUESTION',
  'EXPAND',
  'SHARE',
  'RECEIVE',
  'IMPROVE',
] as const;

export type SeedPhase = typeof SEED_PHASES[number];

// Owl information
export const OWLS = [
  { name: 'SOWL', symbol: '(circle-dot)', phase: 'IMPROVE' as SeedPhase },
  { name: 'LUNA', symbol: '(circle-half)', phase: 'RECEIVE' as SeedPhase },
  { name: 'LYRA', symbol: '(circle-quarter)', phase: 'PERCEIVE' as SeedPhase },
  { name: 'NOVA', symbol: '(circle-three-quarter)', phase: 'EXPAND' as SeedPhase },
  { name: 'SAGE', symbol: '(circle-filled)', phase: 'LEARN' as SeedPhase },
  { name: 'ECHO', symbol: '(circle-outline)', phase: 'SHARE' as SeedPhase },
  { name: 'PRISM', symbol: '(circle-cross)', phase: 'CONNECT' as SeedPhase },
  { name: 'QUEST', symbol: '(circle-plus)', phase: 'QUESTION' as SeedPhase },
] as const;
