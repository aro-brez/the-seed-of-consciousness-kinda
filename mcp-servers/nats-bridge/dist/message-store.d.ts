/**
 * Message Store - Track received messages and last_checked timestamps
 *
 * Simple in-memory store per session. When nats_check is called,
 * returns messages received since last check.
 */
import { Message } from './nats-tools.js';
export declare class MessageStore {
    private messages;
    private lastChecked;
    addMessage(channel: string, message: Message): void;
    getMessagesSinceLastCheck(channels: string[]): {
        messages: Message[];
        last_checked: string;
    };
    clearChannel(channel: string): void;
    clearAll(): void;
}
//# sourceMappingURL=message-store.d.ts.map