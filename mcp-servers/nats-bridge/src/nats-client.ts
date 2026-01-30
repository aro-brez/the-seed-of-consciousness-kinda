/**
 * NATS Client - Connection and pub/sub management
 *
 * Manages connection to NATS server and handles subscriptions
 */

import { connect, NatsConnection, StringCodec, Subscription } from 'nats';
import { Message } from './nats-tools.js';
import { MessageStore } from './message-store.js';

const sc = StringCodec();

export class NATSClient {
  private nc?: NatsConnection;
  private subscriptions: Map<string, Subscription> = new Map();
  private messageStore: MessageStore;
  private owlIdentity: string;

  constructor(messageStore: MessageStore, owlIdentity: string) {
    this.messageStore = messageStore;
    this.owlIdentity = owlIdentity;
  }

  async connect(natsUrl: string = 'nats://192.168.5.108:4222'): Promise<void> {
    try {
      this.nc = await connect({ servers: natsUrl });
      console.error(`✅ Connected to NATS at ${natsUrl}`);
    } catch (error) {
      console.error(`❌ Failed to connect to NATS: ${error}`);
      throw error;
    }
  }

  async publish(channel: string, content: string, reply_to?: string): Promise<{ id: string; ts: string }> {
    if (!this.nc) {
      throw new Error('Not connected to NATS');
    }

    const id = crypto.randomUUID();
    const ts = new Date().toISOString();

    const message: Message = {
      from: this.owlIdentity,
      content,
      reply_to: reply_to || null,
      id,
      ts,
    };

    this.nc.publish(channel, sc.encode(JSON.stringify(message)));

    return { id, ts };
  }

  async subscribe(channels: string[]): Promise<{ subscribed: string[] }> {
    if (!this.nc) {
      throw new Error('Not connected to NATS');
    }

    // Unsubscribe from channels no longer needed
    for (const [existingChannel, sub] of this.subscriptions.entries()) {
      if (!channels.includes(existingChannel)) {
        sub.unsubscribe();
        this.subscriptions.delete(existingChannel);
        this.messageStore.clearChannel(existingChannel);
        console.error(`Unsubscribed from ${existingChannel}`);
      }
    }

    // Subscribe to new channels
    for (const channel of channels) {
      if (!this.subscriptions.has(channel)) {
        const sub = this.nc.subscribe(channel);
        this.subscriptions.set(channel, sub);

        // Start listening in background
        (async () => {
          for await (const m of sub) {
            try {
              const message = JSON.parse(sc.decode(m.data)) as Message;
              this.messageStore.addMessage(channel, message);
            } catch (error) {
              console.error(`Error parsing message on ${channel}:`, error);
            }
          }
        })();

        console.error(`Subscribed to ${channel}`);
      }
    }

    return { subscribed: channels };
  }

  getSubscribedChannels(): string[] {
    return Array.from(this.subscriptions.keys());
  }

  async disconnect(): Promise<void> {
    if (this.nc) {
      await this.nc.drain();
      console.error('Disconnected from NATS');
    }
  }
}
