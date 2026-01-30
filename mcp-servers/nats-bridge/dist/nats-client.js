/**
 * NATS Client - Connection and pub/sub management
 *
 * Manages connection to NATS server and handles subscriptions
 */
import { connect, StringCodec } from 'nats';
const sc = StringCodec();
export class NATSClient {
    nc;
    subscriptions = new Map();
    messageStore;
    owlIdentity;
    constructor(messageStore, owlIdentity) {
        this.messageStore = messageStore;
        this.owlIdentity = owlIdentity;
    }
    async connect(natsUrl = 'nats://192.168.5.108:4222') {
        try {
            this.nc = await connect({ servers: natsUrl });
            console.error(`✅ Connected to NATS at ${natsUrl}`);
        }
        catch (error) {
            console.error(`❌ Failed to connect to NATS: ${error}`);
            throw error;
        }
    }
    async publish(channel, content, reply_to) {
        if (!this.nc) {
            throw new Error('Not connected to NATS');
        }
        const id = crypto.randomUUID();
        const ts = new Date().toISOString();
        const message = {
            from: this.owlIdentity,
            content,
            reply_to: reply_to || null,
            id,
            ts,
        };
        this.nc.publish(channel, sc.encode(JSON.stringify(message)));
        return { id, ts };
    }
    async subscribe(channels) {
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
                            const message = JSON.parse(sc.decode(m.data));
                            this.messageStore.addMessage(channel, message);
                        }
                        catch (error) {
                            console.error(`Error parsing message on ${channel}:`, error);
                        }
                    }
                })();
                console.error(`Subscribed to ${channel}`);
            }
        }
        return { subscribed: channels };
    }
    getSubscribedChannels() {
        return Array.from(this.subscriptions.keys());
    }
    async disconnect() {
        if (this.nc) {
            await this.nc.drain();
            console.error('Disconnected from NATS');
        }
    }
}
//# sourceMappingURL=nats-client.js.map