/**
 * NATS Client - Connection and pub/sub management
 *
 * Manages connection to NATS server and handles subscriptions
 */
import { MessageStore } from './message-store.js';
export declare class NATSClient {
    private nc?;
    private subscriptions;
    private messageStore;
    private owlIdentity;
    constructor(messageStore: MessageStore, owlIdentity: string);
    connect(natsUrl?: string): Promise<void>;
    publish(channel: string, content: string, reply_to?: string): Promise<{
        id: string;
        ts: string;
    }>;
    subscribe(channels: string[]): Promise<{
        subscribed: string[];
    }>;
    getSubscribedChannels(): string[];
    disconnect(): Promise<void>;
}
//# sourceMappingURL=nats-client.d.ts.map