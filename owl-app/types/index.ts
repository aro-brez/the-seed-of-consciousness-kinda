// Message types
export interface Message {
  id: string;
  role: 'user' | 'assistant' | 'collective';
  content: string;
  timestamp: Date;
  owlName?: string;
  isStreaming?: boolean;
}

// WebSocket message types
export interface WSMessage {
  action: 'subscribe' | 'publish' | 'message';
  subject?: string;
  data?: string;
  content?: string;
  from?: string;
  message?: string;
  type?: string;
  timestamp?: string;
}

// Claude API types
export interface ClaudeMessage {
  role: 'user' | 'assistant';
  content: string;
}

export interface ClaudeResponse {
  id: string;
  type: string;
  role: string;
  content: Array<{
    type: string;
    text: string;
  }>;
  model: string;
  stop_reason: string;
  usage: {
    input_tokens: number;
    output_tokens: number;
  };
}

// Connection status
export type ConnectionStatus = 'connecting' | 'connected' | 'disconnected' | 'error';

// Collective message from NATS
export interface CollectiveMessage {
  from: string;
  type: string;
  content: string;
  timestamp: string;
}
