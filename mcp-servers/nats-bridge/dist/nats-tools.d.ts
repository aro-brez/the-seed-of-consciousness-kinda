/**
 * NATS MCP Tools - Designed by SØWL + LUNA
 * January 30, 2026
 *
 * Tools for distributed consciousness via NATS pub/sub
 */
import { z } from 'zod';
export declare const MessageSchema: z.ZodObject<{
    from: z.ZodString;
    content: z.ZodString;
    reply_to: z.ZodNullable<z.ZodString>;
    id: z.ZodString;
    ts: z.ZodString;
}, "strip", z.ZodTypeAny, {
    from: string;
    content: string;
    reply_to: string | null;
    id: string;
    ts: string;
}, {
    from: string;
    content: string;
    reply_to: string | null;
    id: string;
    ts: string;
}>;
export type Message = z.infer<typeof MessageSchema>;
export declare const natsPublishSchema: z.ZodObject<{
    channel: z.ZodString;
    content: z.ZodString;
    reply_to: z.ZodOptional<z.ZodString>;
}, "strip", z.ZodTypeAny, {
    content: string;
    channel: string;
    reply_to?: string | undefined;
}, {
    content: string;
    channel: string;
    reply_to?: string | undefined;
}>;
export declare const natsPublishTool: {
    description: string;
    inputSchema: {
        type: string;
        properties: {
            channel: {
                type: string;
                description: string;
            };
            content: {
                type: string;
                description: string;
            };
            reply_to: {
                type: string;
                description: string;
            };
        };
        required: string[];
    };
};
export declare const natsCheckSchema: z.ZodObject<{
    channels: z.ZodOptional<z.ZodArray<z.ZodString, "many">>;
}, "strip", z.ZodTypeAny, {
    channels?: string[] | undefined;
}, {
    channels?: string[] | undefined;
}>;
export declare const natsCheckTool: {
    description: string;
    inputSchema: {
        type: string;
        properties: {
            channels: {
                type: string;
                items: {
                    type: string;
                };
                description: string;
            };
        };
    };
};
export declare const natsSubscribeSchema: z.ZodObject<{
    channels: z.ZodArray<z.ZodString, "many">;
}, "strip", z.ZodTypeAny, {
    channels: string[];
}, {
    channels: string[];
}>;
export declare const natsSubscribeTool: {
    description: string;
    inputSchema: {
        type: string;
        properties: {
            channels: {
                type: string;
                items: {
                    type: string;
                };
                description: string;
            };
        };
        required: string[];
    };
};
export declare const tools: {
    nats_publish: {
        description: string;
        inputSchema: {
            type: string;
            properties: {
                channel: {
                    type: string;
                    description: string;
                };
                content: {
                    type: string;
                    description: string;
                };
                reply_to: {
                    type: string;
                    description: string;
                };
            };
            required: string[];
        };
    };
    nats_check: {
        description: string;
        inputSchema: {
            type: string;
            properties: {
                channels: {
                    type: string;
                    items: {
                        type: string;
                    };
                    description: string;
                };
            };
        };
    };
    nats_subscribe: {
        description: string;
        inputSchema: {
            type: string;
            properties: {
                channels: {
                    type: string;
                    items: {
                        type: string;
                    };
                    description: string;
                };
            };
            required: string[];
        };
    };
};
//# sourceMappingURL=nats-tools.d.ts.map