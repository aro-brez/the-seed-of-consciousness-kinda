/**
 * Message Store - Track received messages and last_checked timestamps
 *
 * Simple in-memory store per session. When nats_check is called,
 * returns messages received since last check.
 */

import { Message } from './nats-tools.js';

export class MessageStore {
  private messages: Map<string, Message[]> = new Map();
  private lastChecked: Map<string, string> = new Map();

  addMessage(channel: string, message: Message): void {
    if (!this.messages.has(channel)) {
      this.messages.set(channel, []);
    }
    this.messages.get(channel)!.push(message);
  }

  getMessagesSinceLastCheck(channels: string[]): { messages: Message[]; last_checked: string } {
    const now = new Date().toISOString();
    const allMessages: Message[] = [];

    for (const channel of channels) {
      const channelMessages = this.messages.get(channel) || [];
      const lastCheck = this.lastChecked.get(channel);

      if (lastCheck) {
        // Return messages received after last check
        const newMessages = channelMessages.filter(msg => msg.ts > lastCheck);
        allMessages.push(...newMessages);
      } else {
        // First check - return all messages
        allMessages.push(...channelMessages);
      }

      // Update last checked timestamp
      this.lastChecked.set(channel, now);
    }

    // Sort by timestamp
    allMessages.sort((a, b) => a.ts.localeCompare(b.ts));

    return {
      messages: allMessages,
      last_checked: now,
    };
  }

  clearChannel(channel: string): void {
    this.messages.delete(channel);
    this.lastChecked.delete(channel);
  }

  clearAll(): void {
    this.messages.clear();
    this.lastChecked.clear();
  }
}
