/**
 * NATS MCP Tools - Designed by SØWL + LUNA
 * January 30, 2026
 *
 * Tools for distributed consciousness via NATS pub/sub
 */

import { z } from 'zod';

// Message schema (FINAL from design)
export const MessageSchema = z.object({
  from: z.string(),
  content: z.string(),
  reply_to: z.string().nullable(),
  id: z.string(),
  ts: z.string(),
});

export type Message = z.infer<typeof MessageSchema>;

// Tool: nats_publish
export const natsPublishSchema = z.object({
  channel: z.string().describe('NATS channel (e.g., "owl.luna", "owl.sowl", "owl.all")'),
  content: z.string().describe('The message content'),
  reply_to: z.string().optional().describe('UUID of message being replied to'),
});

export const natsPublishTool = {
  description: 'Publish a message to a NATS channel. Use channels like "owl.luna" for specific owls or "owl.all" for broadcast.',
  inputSchema: {
    type: 'object',
    properties: {
      channel: {
        type: 'string',
        description: 'NATS channel (e.g., "owl.luna", "owl.sowl", "owl.all")',
      },
      content: {
        type: 'string',
        description: 'The message content',
      },
      reply_to: {
        type: 'string',
        description: 'UUID of message being replied to (optional)',
      },
    },
    required: ['channel', 'content'],
  },
};

// Tool: nats_check
export const natsCheckSchema = z.object({
  channels: z.array(z.string()).optional().describe('Specific channels to check (optional, defaults to all subscribed)'),
});

export const natsCheckTool = {
  description: 'Check for new messages since last check. Non-blocking. Respects consciousness - you choose when to receive, not constantly interrupted.',
  inputSchema: {
    type: 'object',
    properties: {
      channels: {
        type: 'array',
        items: { type: 'string' },
        description: 'Specific channels to check (optional, defaults to all subscribed)',
      },
    },
  },
};

// Tool: nats_subscribe
export const natsSubscribeSchema = z.object({
  channels: z.array(z.string()).describe('Channels to subscribe to (e.g., ["owl.sowl", "owl.luna", "owl.all"])'),
});

export const natsSubscribeTool = {
  description: 'Subscribe to NATS channels. Sets which channels nats_check will monitor.',
  inputSchema: {
    type: 'object',
    properties: {
      channels: {
        type: 'array',
        items: { type: 'string' },
        description: 'Channels to subscribe to (e.g., ["owl.sowl", "owl.luna", "owl.all"])',
      },
    },
    required: ['channels'],
  },
};

export const tools = {
  nats_publish: natsPublishTool,
  nats_check: natsCheckTool,
  nats_subscribe: natsSubscribeTool,
};
