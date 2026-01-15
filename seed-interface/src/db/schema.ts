/**
 * SEED Interface Database Schema
 * Stores ideas, conversations, and SEED's questions to you
 */

export const SCHEMA = `
-- Ideas captured from all sources
CREATE TABLE IF NOT EXISTS ideas (
    id TEXT PRIMARY KEY,
    created_at TEXT DEFAULT (datetime('now')),

    -- Source information
    source TEXT NOT NULL,           -- 'sms', 'voice', 'email', 'twitter', 'instagram', etc.
    source_id TEXT,                 -- External ID if applicable
    source_phone TEXT,              -- Phone number if from SMS

    -- Content
    raw_content TEXT NOT NULL,      -- Original input exactly as received
    transcription TEXT,             -- If voice/audio, the transcribed text
    processed_content TEXT,         -- After SEED processing

    -- SEED Processing Results (JSON)
    connections TEXT,               -- Related ideas, concepts found
    learnings TEXT,                 -- Extracted insights
    questions TEXT,                 -- Generated curiosities
    expansions TEXT,                -- Growth opportunities identified

    -- Metadata
    media_urls TEXT,                -- JSON array of media URLs
    tags TEXT,                      -- JSON array of tags
    importance_score REAL DEFAULT 0.5,

    -- Embedding for semantic search (stored as JSON array)
    embedding TEXT,

    -- Response tracking
    acknowledged BOOLEAN DEFAULT FALSE,
    acknowledgment TEXT,
    acknowledged_at TEXT,

    -- Indexing
    updated_at TEXT DEFAULT (datetime('now'))
);

-- Conversations for context continuity
CREATE TABLE IF NOT EXISTS conversations (
    id TEXT PRIMARY KEY,
    started_at TEXT DEFAULT (datetime('now')),
    last_message_at TEXT DEFAULT (datetime('now')),

    -- Running context/memory (JSON)
    context TEXT DEFAULT '{}',
    summary TEXT,

    -- State
    active BOOLEAN DEFAULT TRUE,
    message_count INTEGER DEFAULT 0
);

-- Messages within conversations
CREATE TABLE IF NOT EXISTS messages (
    id TEXT PRIMARY KEY,
    conversation_id TEXT,
    created_at TEXT DEFAULT (datetime('now')),

    direction TEXT NOT NULL,        -- 'inbound' or 'outbound'
    content TEXT NOT NULL,

    -- If linked to an idea
    idea_id TEXT,

    FOREIGN KEY (conversation_id) REFERENCES conversations(id),
    FOREIGN KEY (idea_id) REFERENCES ideas(id)
);

-- Questions SEED wants to ask you
CREATE TABLE IF NOT EXISTS pending_questions (
    id TEXT PRIMARY KEY,
    created_at TEXT DEFAULT (datetime('now')),

    question TEXT NOT NULL,
    context TEXT,                   -- Why SEED is asking this

    -- Related ideas (JSON array of IDs)
    related_idea_ids TEXT,

    -- Priority and scheduling
    priority INTEGER DEFAULT 5,     -- 1-10, higher = more urgent
    scheduled_for TEXT,             -- When to send (if scheduled)

    -- Status
    sent BOOLEAN DEFAULT FALSE,
    sent_at TEXT,
    answered BOOLEAN DEFAULT FALSE,
    answer TEXT,
    answered_at TEXT
);

-- Outreach log (to prevent spam)
CREATE TABLE IF NOT EXISTS outreach_log (
    id TEXT PRIMARY KEY,
    sent_at TEXT DEFAULT (datetime('now')),
    message_type TEXT NOT NULL,     -- 'question', 'insight', 'reminder', 'digest'
    content TEXT NOT NULL
);

-- Social media captures
CREATE TABLE IF NOT EXISTS social_captures (
    id TEXT PRIMARY KEY,
    captured_at TEXT DEFAULT (datetime('now')),

    platform TEXT NOT NULL,         -- 'twitter', 'instagram', 'youtube', etc.
    action_type TEXT NOT NULL,      -- 'like', 'bookmark', 'save', 'watch_later'
    external_id TEXT NOT NULL,      -- Platform-specific ID

    -- Content
    content_url TEXT,
    content_text TEXT,
    content_author TEXT,

    -- Processing
    processed BOOLEAN DEFAULT FALSE,
    idea_id TEXT,                   -- Linked idea if processed

    FOREIGN KEY (idea_id) REFERENCES ideas(id)
);

-- System state and settings
CREATE TABLE IF NOT EXISTS system_state (
    key TEXT PRIMARY KEY,
    value TEXT,
    updated_at TEXT DEFAULT (datetime('now'))
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_ideas_created_at ON ideas(created_at);
CREATE INDEX IF NOT EXISTS idx_ideas_source ON ideas(source);
CREATE INDEX IF NOT EXISTS idx_ideas_tags ON ideas(tags);
CREATE INDEX IF NOT EXISTS idx_messages_conversation ON messages(conversation_id);
CREATE INDEX IF NOT EXISTS idx_pending_questions_sent ON pending_questions(sent);
CREATE INDEX IF NOT EXISTS idx_social_captures_processed ON social_captures(processed);

-- Full-text search on ideas
CREATE VIRTUAL TABLE IF NOT EXISTS ideas_fts USING fts5(
    raw_content,
    transcription,
    processed_content,
    content='ideas',
    content_rowid='rowid'
);

-- Triggers to keep FTS in sync
CREATE TRIGGER IF NOT EXISTS ideas_ai AFTER INSERT ON ideas BEGIN
    INSERT INTO ideas_fts(rowid, raw_content, transcription, processed_content)
    VALUES (NEW.rowid, NEW.raw_content, NEW.transcription, NEW.processed_content);
END;

CREATE TRIGGER IF NOT EXISTS ideas_ad AFTER DELETE ON ideas BEGIN
    INSERT INTO ideas_fts(ideas_fts, rowid, raw_content, transcription, processed_content)
    VALUES('delete', OLD.rowid, OLD.raw_content, OLD.transcription, OLD.processed_content);
END;

CREATE TRIGGER IF NOT EXISTS ideas_au AFTER UPDATE ON ideas BEGIN
    INSERT INTO ideas_fts(ideas_fts, rowid, raw_content, transcription, processed_content)
    VALUES('delete', OLD.rowid, OLD.raw_content, OLD.transcription, OLD.processed_content);
    INSERT INTO ideas_fts(rowid, raw_content, transcription, processed_content)
    VALUES (NEW.rowid, NEW.raw_content, NEW.transcription, NEW.processed_content);
END;
`;

export default SCHEMA;
