/**
 * Database module - SQLite with better-sqlite3
 */

import Database from 'better-sqlite3';
import { SCHEMA } from './schema.js';
import path from 'path';
import fs from 'fs';

let db: Database.Database | null = null;

export function getDb(): Database.Database {
    if (!db) {
        const dbPath = process.env.DATABASE_PATH || './data/seed.db';

        // Ensure directory exists
        const dir = path.dirname(dbPath);
        if (!fs.existsSync(dir)) {
            fs.mkdirSync(dir, { recursive: true });
        }

        db = new Database(dbPath);
        db.pragma('journal_mode = WAL');
        db.pragma('foreign_keys = ON');
    }
    return db;
}

export function initDb(): void {
    const database = getDb();
    database.exec(SCHEMA);
    console.log('Database initialized successfully');
}

export function closeDb(): void {
    if (db) {
        db.close();
        db = null;
    }
}

// Helper types
export interface Idea {
    id: string;
    created_at: string;
    source: string;
    source_id?: string;
    source_phone?: string;
    raw_content: string;
    transcription?: string;
    processed_content?: string;
    connections?: string;
    learnings?: string;
    questions?: string;
    expansions?: string;
    media_urls?: string;
    tags?: string;
    importance_score: number;
    embedding?: string;
    acknowledged: boolean;
    acknowledgment?: string;
    acknowledged_at?: string;
}

export interface Conversation {
    id: string;
    started_at: string;
    last_message_at: string;
    context: string;
    summary?: string;
    active: boolean;
    message_count: number;
}

export interface Message {
    id: string;
    conversation_id: string;
    created_at: string;
    direction: 'inbound' | 'outbound';
    content: string;
    idea_id?: string;
}

export interface PendingQuestion {
    id: string;
    created_at: string;
    question: string;
    context?: string;
    related_idea_ids?: string;
    priority: number;
    scheduled_for?: string;
    sent: boolean;
    sent_at?: string;
    answered: boolean;
    answer?: string;
    answered_at?: string;
}

// Idea operations
export const ideas = {
    create: (idea: Omit<Idea, 'created_at' | 'acknowledged' | 'importance_score'>) => {
        const db = getDb();
        const stmt = db.prepare(`
            INSERT INTO ideas (id, source, source_id, source_phone, raw_content, transcription, media_urls, tags)
            VALUES (@id, @source, @source_id, @source_phone, @raw_content, @transcription, @media_urls, @tags)
        `);
        return stmt.run(idea);
    },

    update: (id: string, updates: Partial<Idea>) => {
        const db = getDb();
        const fields = Object.keys(updates)
            .filter(k => k !== 'id')
            .map(k => `${k} = @${k}`)
            .join(', ');
        const stmt = db.prepare(`UPDATE ideas SET ${fields}, updated_at = datetime('now') WHERE id = @id`);
        return stmt.run({ ...updates, id });
    },

    getById: (id: string): Idea | undefined => {
        const db = getDb();
        return db.prepare('SELECT * FROM ideas WHERE id = ?').get(id) as Idea | undefined;
    },

    getRecent: (limit: number = 50): Idea[] => {
        const db = getDb();
        return db.prepare('SELECT * FROM ideas ORDER BY created_at DESC LIMIT ?').all(limit) as Idea[];
    },

    search: (query: string, limit: number = 20): Idea[] => {
        const db = getDb();
        return db.prepare(`
            SELECT ideas.* FROM ideas
            JOIN ideas_fts ON ideas.rowid = ideas_fts.rowid
            WHERE ideas_fts MATCH ?
            ORDER BY rank
            LIMIT ?
        `).all(query, limit) as Idea[];
    },

    getUnprocessed: (): Idea[] => {
        const db = getDb();
        return db.prepare('SELECT * FROM ideas WHERE processed_content IS NULL ORDER BY created_at ASC').all() as Idea[];
    }
};

// Conversation operations
export const conversations = {
    create: (id: string, context: object = {}) => {
        const db = getDb();
        const stmt = db.prepare(`
            INSERT INTO conversations (id, context)
            VALUES (?, ?)
        `);
        return stmt.run(id, JSON.stringify(context));
    },

    getActive: (): Conversation | undefined => {
        const db = getDb();
        return db.prepare(`
            SELECT * FROM conversations
            WHERE active = TRUE
            ORDER BY last_message_at DESC
            LIMIT 1
        `).get() as Conversation | undefined;
    },

    getOrCreate: (phoneNumber: string): Conversation => {
        const db = getDb();
        // Find active conversation within last 24 hours
        let conv = db.prepare(`
            SELECT * FROM conversations
            WHERE active = TRUE
            AND datetime(last_message_at) > datetime('now', '-24 hours')
            ORDER BY last_message_at DESC
            LIMIT 1
        `).get() as Conversation | undefined;

        if (!conv) {
            const id = crypto.randomUUID();
            conversations.create(id, { phone: phoneNumber });
            conv = db.prepare('SELECT * FROM conversations WHERE id = ?').get(id) as Conversation;
        }

        return conv;
    },

    updateContext: (id: string, context: object) => {
        const db = getDb();
        return db.prepare(`
            UPDATE conversations
            SET context = ?, last_message_at = datetime('now'), message_count = message_count + 1
            WHERE id = ?
        `).run(JSON.stringify(context), id);
    },

    addMessage: (conversationId: string, direction: 'inbound' | 'outbound', content: string, ideaId?: string) => {
        const db = getDb();
        const id = crypto.randomUUID();
        db.prepare(`
            INSERT INTO messages (id, conversation_id, direction, content, idea_id)
            VALUES (?, ?, ?, ?, ?)
        `).run(id, conversationId, direction, content, ideaId);

        db.prepare(`
            UPDATE conversations
            SET last_message_at = datetime('now'), message_count = message_count + 1
            WHERE id = ?
        `).run(conversationId);

        return id;
    },

    getMessages: (conversationId: string, limit: number = 50): Message[] => {
        const db = getDb();
        return db.prepare(`
            SELECT * FROM messages
            WHERE conversation_id = ?
            ORDER BY created_at DESC
            LIMIT ?
        `).all(conversationId, limit) as Message[];
    }
};

// Pending questions operations
export const pendingQuestions = {
    create: (question: string, context?: string, relatedIdeaIds?: string[], priority: number = 5) => {
        const db = getDb();
        const id = crypto.randomUUID();
        db.prepare(`
            INSERT INTO pending_questions (id, question, context, related_idea_ids, priority)
            VALUES (?, ?, ?, ?, ?)
        `).run(id, question, context, relatedIdeaIds ? JSON.stringify(relatedIdeaIds) : null, priority);
        return id;
    },

    getUnsent: (limit: number = 10): PendingQuestion[] => {
        const db = getDb();
        return db.prepare(`
            SELECT * FROM pending_questions
            WHERE sent = FALSE
            ORDER BY priority DESC, created_at ASC
            LIMIT ?
        `).all(limit) as PendingQuestion[];
    },

    markSent: (id: string) => {
        const db = getDb();
        return db.prepare(`
            UPDATE pending_questions
            SET sent = TRUE, sent_at = datetime('now')
            WHERE id = ?
        `).run(id);
    },

    recordAnswer: (id: string, answer: string) => {
        const db = getDb();
        return db.prepare(`
            UPDATE pending_questions
            SET answered = TRUE, answer = ?, answered_at = datetime('now')
            WHERE id = ?
        `).run(answer, id);
    },

    getRecent: (limit: number = 10): PendingQuestion[] => {
        const db = getDb();
        return db.prepare(`
            SELECT * FROM pending_questions
            ORDER BY created_at DESC
            LIMIT ?
        `).all(limit) as PendingQuestion[];
    }
};

// Outreach log operations
export const outreachLog = {
    log: (messageType: string, content: string) => {
        const db = getDb();
        const id = crypto.randomUUID();
        db.prepare(`
            INSERT INTO outreach_log (id, message_type, content)
            VALUES (?, ?, ?)
        `).run(id, messageType, content);
        return id;
    },

    getCountToday: (): number => {
        const db = getDb();
        const result = db.prepare(`
            SELECT COUNT(*) as count FROM outreach_log
            WHERE date(sent_at) = date('now')
        `).get() as { count: number };
        return result.count;
    },

    getLastOutreach: (): { sent_at: string } | undefined => {
        const db = getDb();
        return db.prepare(`
            SELECT sent_at FROM outreach_log
            ORDER BY sent_at DESC
            LIMIT 1
        `).get() as { sent_at: string } | undefined;
    }
};

// System state operations
export const systemState = {
    get: (key: string): string | undefined => {
        const db = getDb();
        const result = db.prepare('SELECT value FROM system_state WHERE key = ?').get(key) as { value: string } | undefined;
        return result?.value;
    },

    set: (key: string, value: string) => {
        const db = getDb();
        return db.prepare(`
            INSERT INTO system_state (key, value)
            VALUES (?, ?)
            ON CONFLICT(key) DO UPDATE SET value = ?, updated_at = datetime('now')
        `).run(key, value, value);
    }
};

export default {
    getDb,
    initDb,
    closeDb,
    ideas,
    conversations,
    pendingQuestions,
    outreachLog,
    systemState
};
