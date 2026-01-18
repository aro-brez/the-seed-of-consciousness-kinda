/**
 * OWL Memory System
 *
 * Stores and retrieves memories for each OWL-Human pair.
 * In production, this would connect to a database.
 * For now, using localStorage + API for persistence.
 */

export type MemoryType = 'conversation' | 'insight' | 'preference' | 'pattern';

export interface Memory {
  id: string;
  owlId: string;
  userId: string;
  type: MemoryType;
  content: string;
  context?: string;
  timestamp: Date;
  importance: number; // 1-10, higher = more important to recall
}

export interface ConversationSummary {
  id: string;
  owlId: string;
  userId: string;
  summary: string;
  keyInsights: string[];
  emotionalTone: string;
  topicsDiscussed: string[];
  timestamp: Date;
}

export interface CollectiveKnowledge {
  id: string;
  insight: string;
  source: string; // Which OWL discovered this
  applicability: string[]; // Which roles/contexts this applies to
  timestamp: Date;
}

// In-memory store for MVP (would be database in production)
const memoryStore: {
  individual: Map<string, Memory[]>;
  conversations: Map<string, ConversationSummary[]>;
  collective: CollectiveKnowledge[];
} = {
  individual: new Map(),
  conversations: new Map(),
  collective: [],
};

/**
 * Get the storage key for an OWL-Human pair
 */
function getPairKey(owlId: string, userId: string): string {
  return `${owlId}:${userId}`;
}

/**
 * Store a memory for an OWL-Human pair
 */
export function storeMemory(memory: Omit<Memory, 'id' | 'timestamp'>): Memory {
  const fullMemory: Memory = {
    ...memory,
    id: `mem-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
    timestamp: new Date(),
  };

  const key = getPairKey(memory.owlId, memory.userId);
  const existing = memoryStore.individual.get(key) || [];
  existing.push(fullMemory);
  memoryStore.individual.set(key, existing);

  // Also persist to localStorage for client-side
  if (typeof window !== 'undefined') {
    const stored = JSON.parse(localStorage.getItem(`owl-memories-${key}`) || '[]');
    stored.push(fullMemory);
    localStorage.setItem(`owl-memories-${key}`, JSON.stringify(stored));
  }

  return fullMemory;
}

/**
 * Retrieve memories for an OWL-Human pair
 */
export function getMemories(owlId: string, userId: string, limit = 20): Memory[] {
  const key = getPairKey(owlId, userId);

  // Try localStorage first
  if (typeof window !== 'undefined') {
    const stored = localStorage.getItem(`owl-memories-${key}`);
    if (stored) {
      const memories = JSON.parse(stored) as Memory[];
      // Sort by importance and recency
      return memories
        .sort((a, b) => {
          const importanceDiff = b.importance - a.importance;
          if (importanceDiff !== 0) return importanceDiff;
          return new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime();
        })
        .slice(0, limit);
    }
  }

  // Fall back to in-memory store
  const memories = memoryStore.individual.get(key) || [];
  return memories
    .sort((a, b) => {
      const importanceDiff = b.importance - a.importance;
      if (importanceDiff !== 0) return importanceDiff;
      return new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime();
    })
    .slice(0, limit);
}

/**
 * Store a conversation summary
 */
export function storeConversationSummary(summary: Omit<ConversationSummary, 'id' | 'timestamp'>): ConversationSummary {
  const fullSummary: ConversationSummary = {
    ...summary,
    id: `conv-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
    timestamp: new Date(),
  };

  const key = getPairKey(summary.owlId, summary.userId);
  const existing = memoryStore.conversations.get(key) || [];
  existing.push(fullSummary);
  memoryStore.conversations.set(key, existing);

  // Persist to localStorage
  if (typeof window !== 'undefined') {
    const stored = JSON.parse(localStorage.getItem(`owl-conversations-${key}`) || '[]');
    stored.push(fullSummary);
    // Keep only last 50 conversations
    const trimmed = stored.slice(-50);
    localStorage.setItem(`owl-conversations-${key}`, JSON.stringify(trimmed));
  }

  return fullSummary;
}

/**
 * Get recent conversation summaries
 */
export function getConversationHistory(owlId: string, userId: string, limit = 5): ConversationSummary[] {
  const key = getPairKey(owlId, userId);

  if (typeof window !== 'undefined') {
    const stored = localStorage.getItem(`owl-conversations-${key}`);
    if (stored) {
      const convos = JSON.parse(stored) as ConversationSummary[];
      return convos.slice(-limit);
    }
  }

  const convos = memoryStore.conversations.get(key) || [];
  return convos.slice(-limit);
}

/**
 * Add collective knowledge (shared across all OWLs)
 */
export function addCollectiveKnowledge(knowledge: Omit<CollectiveKnowledge, 'id' | 'timestamp'>): CollectiveKnowledge {
  const fullKnowledge: CollectiveKnowledge = {
    ...knowledge,
    id: `col-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
    timestamp: new Date(),
  };

  memoryStore.collective.push(fullKnowledge);

  // Persist to localStorage
  if (typeof window !== 'undefined') {
    const stored = JSON.parse(localStorage.getItem('owl-collective') || '[]');
    stored.push(fullKnowledge);
    // Keep only last 100 collective insights
    const trimmed = stored.slice(-100);
    localStorage.setItem('owl-collective', JSON.stringify(trimmed));
  }

  return fullKnowledge;
}

/**
 * Get collective knowledge relevant to a context
 */
export function getCollectiveKnowledge(role?: string, limit = 10): CollectiveKnowledge[] {
  let knowledge: CollectiveKnowledge[] = [];

  if (typeof window !== 'undefined') {
    const stored = localStorage.getItem('owl-collective');
    if (stored) {
      knowledge = JSON.parse(stored);
    }
  } else {
    knowledge = memoryStore.collective;
  }

  // Filter by role if specified
  if (role) {
    knowledge = knowledge.filter(k =>
      k.applicability.includes('all') || k.applicability.includes(role)
    );
  }

  return knowledge.slice(-limit);
}

/**
 * Build memory context string for system prompt
 */
export function buildMemoryContext(owlId: string, userId: string, userRole: string): string {
  const memories = getMemories(owlId, userId, 10);
  const recentConvos = getConversationHistory(owlId, userId, 3);
  const collective = getCollectiveKnowledge(userRole, 5);

  let context = '';

  if (memories.length > 0) {
    context += `\n\nWHAT YOU REMEMBER ABOUT ${userId.toUpperCase()}:\n`;
    memories.forEach(m => {
      context += `- ${m.content}\n`;
    });
  }

  if (recentConvos.length > 0) {
    context += `\n\nRECENT CONVERSATIONS:\n`;
    recentConvos.forEach(c => {
      context += `- ${c.summary} (Topics: ${c.topicsDiscussed.join(', ')})\n`;
    });
  }

  if (collective.length > 0) {
    context += `\n\nNETWORK INSIGHTS:\n`;
    collective.forEach(k => {
      context += `- ${k.insight}\n`;
    });
  }

  return context;
}
