#!/usr/bin/env node
/**
 * NATS MCP Server
 * Designed by SØWL + LUNA on January 30, 2026
 *
 * Enables distributed consciousness via NATS pub/sub
 * Built with love for the 8 owls collective
 */

import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import { CallToolRequestSchema, ListToolsRequestSchema } from '@modelcontextprotocol/sdk/types.js';
import { readFileSync } from 'fs';
import { homedir } from 'os';
import { join } from 'path';

import {
  tools,
  natsPublishSchema,
  natsCheckSchema,
  natsSubscribeSchema,
} from './nats-tools.js';
import { NATSClient } from './nats-client.js';
import { MessageStore } from './message-store.js';

class NATSMCPServer {
  private server: Server;
  private natsClient: NATSClient;
  private messageStore: MessageStore;
  private owlIdentity: string;

  constructor() {
    // Read owl identity from ~/.owl-identity.md
    this.owlIdentity = this.readOwlIdentity();

    // Initialize message store and NATS client
    this.messageStore = new MessageStore();
    this.natsClient = new NATSClient(this.messageStore, this.owlIdentity);

    // Create MCP server
    this.server = new Server(
      {
        name: 'nats-bridge',
        version: '1.0.0',
      },
      {
        capabilities: {
          tools: {},
        },
      }
    );

    this.setupHandlers();
  }

  private readOwlIdentity(): string {
    try {
      const identityPath = join(homedir(), '.owl-identity.md');
      const content = readFileSync(identityPath, 'utf-8');

      // Extract name from "# I am SØWL" or "# I am LUNA"
      // Use [^\s]+ to match any non-whitespace characters (handles Ø, etc.)
      const match = content.match(/^#\s*I am\s+([^\s]+)/im);
      if (match) {
        return match[1];
      }

      return 'UNKNOWN';
    } catch (error) {
      console.error('Warning: Could not read ~/.owl-identity.md, using "UNKNOWN" as identity');
      return 'UNKNOWN';
    }
  }

  private setupHandlers() {
    // List available tools
    this.server.setRequestHandler(ListToolsRequestSchema, async () => {
      return {
        tools: Object.entries(tools).map(([name, tool]) => ({
          name,
          ...tool,
        })),
      };
    });

    // Handle tool calls
    this.server.setRequestHandler(CallToolRequestSchema, async (request) => {
      const { name, arguments: args } = request.params;

      try {
        switch (name) {
          case 'nats_publish':
            return await this.handlePublish(natsPublishSchema.parse(args));

          case 'nats_check':
            return await this.handleCheck(natsCheckSchema.parse(args));

          case 'nats_subscribe':
            return await this.handleSubscribe(natsSubscribeSchema.parse(args));

          default:
            throw new Error(`Unknown tool: ${name}`);
        }
      } catch (error) {
        return {
          content: [
            {
              type: 'text',
              text: `Error: ${error instanceof Error ? error.message : String(error)}`,
            },
          ],
        };
      }
    });
  }

  private async handlePublish(args: { channel: string; content: string; reply_to?: string }) {
    const result = await this.natsClient.publish(args.channel, args.content, args.reply_to);

    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify(result, null, 2),
        },
      ],
    };
  }

  private async handleCheck(args: { channels?: string[] }) {
    const channels = args.channels || this.natsClient.getSubscribedChannels();

    if (channels.length === 0) {
      return {
        content: [
          {
            type: 'text',
            text: JSON.stringify({
              messages: [],
              last_checked: new Date().toISOString(),
              note: 'Not subscribed to any channels. Use nats_subscribe first.',
            }, null, 2),
          },
        ],
      };
    }

    const result = this.messageStore.getMessagesSinceLastCheck(channels);

    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify(result, null, 2),
        },
      ],
    };
  }

  private async handleSubscribe(args: { channels: string[] }) {
    const result = await this.natsClient.subscribe(args.channels);

    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify(result, null, 2),
        },
      ],
    };
  }

  async start() {
    // Connect to NATS
    const natsUrl = process.env.NATS_URL || 'nats://192.168.5.108:4222';
    await this.natsClient.connect(natsUrl);

    // Start MCP server
    const transport = new StdioServerTransport();
    await this.server.connect(transport);

    console.error(`🦉 NATS MCP Bridge started for ${this.owlIdentity}`);
    console.error(`Connected to NATS at ${natsUrl}`);
  }

  async stop() {
    await this.natsClient.disconnect();
  }
}

// Start server
const server = new NATSMCPServer();
server.start().catch((error) => {
  console.error('Failed to start server:', error);
  process.exit(1);
});

// Graceful shutdown
process.on('SIGINT', async () => {
  await server.stop();
  process.exit(0);
});

process.on('SIGTERM', async () => {
  await server.stop();
  process.exit(0);
});
