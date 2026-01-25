"use client";

import React, { createContext, useContext, useState, useCallback, useEffect, useRef } from "react";

// Memory types
type MemoryContext = {
  personalInsights: string[];
  recentTopics: string[];
  collectiveInsights: string[];
};

// Types
export type UserRole = "admin" | "builder" | "viewer";

export type User = {
  id: string;
  name: string;
  role: UserRole;
  owlId: string;
  owlName: string;
};

export type Message = {
  id: string;
  role: "user" | "owl";
  content: string;
  timestamp: Date;
  action?: OwlAction;
};

export type OwlAction =
  | { type: "navigate"; path: string }
  | { type: "propose"; description: string }
  | { type: "show"; entity: string };

type OwlContextType = {
  user: User | null;
  setUser: (user: User | null) => void;
  messages: Message[];
  sendMessage: (content: string) => Promise<void>;
  isPopupOpen: boolean;
  setPopupOpen: (open: boolean) => void;
  isFullFace: boolean;
  setFullFace: (full: boolean) => void;
  pendingAction: OwlAction | null;
  executeAction: () => void;
  clearAction: () => void;
};

const OwlContext = createContext<OwlContextType | null>(null);

// Default users for MVP (no auth yet)
export const DEFAULT_USERS: User[] = [
  { id: "aro", name: "Aro", role: "admin", owlId: "aro-owl", owlName: "Aro-Owl" },
  { id: "andrew", name: "Andrew", role: "builder", owlId: "andrew-owl", owlName: "Andrew-Owl" },
  { id: "liana", name: "Liana", role: "builder", owlId: "liana-owl", owlName: "Liana-Owl" },
];

export function OwlProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [isPopupOpen, setPopupOpen] = useState(false);
  const [isFullFace, setFullFace] = useState(false);
  const [pendingAction, setPendingAction] = useState<OwlAction | null>(null);
  const [memory, setMemory] = useState<MemoryContext | null>(null);
  const previousPopupOpen = useRef(isPopupOpen);

  // Load memories when user is selected
  useEffect(() => {
    if (user && typeof window !== 'undefined') {
      const key = `owl-memory-${user.owlId}:${user.id}`;
      const stored = localStorage.getItem(key);
      if (stored) {
        try {
          setMemory(JSON.parse(stored));
        } catch {
          setMemory(null);
        }
      }
    }
  }, [user]);

  // Learn from conversation when popup closes
  useEffect(() => {
    const wasOpen = previousPopupOpen.current;
    previousPopupOpen.current = isPopupOpen;

    // If popup just closed and we had a meaningful conversation
    if (wasOpen && !isPopupOpen && user && messages.length >= 4) {
      // Extract learnings in the background
      extractLearnings();
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isPopupOpen]);

  // Extract learnings from conversation
  const extractLearnings = useCallback(async () => {
    if (!user || messages.length < 4) return;

    try {
      const response = await fetch("/api/owl/learn", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          user,
          messages: messages.map((m) => ({ role: m.role, content: m.content })),
          owlId: user.owlId,
        }),
      });

      if (response.ok) {
        const { learned, learnings } = await response.json();
        if (learned && learnings) {
          // Merge with existing memory
          const key = `owl-memory-${user.owlId}:${user.id}`;
          const existing = memory || { personalInsights: [], recentTopics: [], collectiveInsights: [] };

          const updated: MemoryContext = {
            personalInsights: [
              ...new Set([...(learnings.personalInsights || []), ...existing.personalInsights])
            ].slice(0, 20), // Keep last 20
            recentTopics: [
              ...new Set([...(learnings.topicsDiscussed || []), ...existing.recentTopics])
            ].slice(0, 10),
            collectiveInsights: [
              ...new Set([...(learnings.collectiveInsights || []), ...existing.collectiveInsights])
            ].slice(0, 10),
          };

          localStorage.setItem(key, JSON.stringify(updated));
          setMemory(updated);

          // Also store collective insights globally
          if (learnings.collectiveInsights?.length > 0) {
            const collectiveKey = 'owl-collective-knowledge';
            const collective = JSON.parse(localStorage.getItem(collectiveKey) || '[]');
            const newCollective = [
              ...learnings.collectiveInsights.map((insight: string) => ({
                insight,
                source: user.owlId,
                timestamp: new Date().toISOString(),
              })),
              ...collective,
            ].slice(0, 50);
            localStorage.setItem(collectiveKey, JSON.stringify(newCollective));
          }
        }
      }
    } catch (error) {
      console.error("Failed to extract learnings:", error);
    }
  }, [user, messages, memory]);

  const sendMessage = useCallback(async (content: string) => {
    if (!user) return;

    // Add user message
    const userMsg: Message = {
      id: `msg-${Date.now()}`,
      role: "user",
      content,
      timestamp: new Date(),
    };
    setMessages((prev) => [...prev, userMsg]);

    let response: { content: string; action?: OwlAction };

    try {
      // Load collective knowledge to include in context
      let collectiveInsights: string[] = [];
      if (typeof window !== 'undefined') {
        const collective = JSON.parse(localStorage.getItem('owl-collective-knowledge') || '[]');
        collectiveInsights = collective
          .slice(0, 5)
          .map((k: { insight: string }) => k.insight);
      }

      // Try Claude API first
      const apiResponse = await fetch("/api/owl", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          user,
          messages: messages.map((m) => ({ role: m.role, content: m.content })),
          newMessage: content,
          memory: memory ? {
            ...memory,
            collectiveInsights: [...(memory.collectiveInsights || []), ...collectiveInsights],
          } : collectiveInsights.length > 0 ? { collectiveInsights } : undefined,
        }),
      });

      if (apiResponse.ok) {
        response = await apiResponse.json();
      } else {
        // Fallback to local pattern matching
        response = await generateOwlResponse(content, user);
      }
    } catch {
      // Fallback to local pattern matching if API fails
      response = await generateOwlResponse(content, user);
    }

    const owlMsg: Message = {
      id: `owl-${Date.now()}`,
      role: "owl",
      content: response.content,
      timestamp: new Date(),
      action: response.action,
    };
    setMessages((prev) => [...prev, owlMsg]);

    if (response.action) {
      setPendingAction(response.action);
    }
  }, [user, messages]);

  const executeAction = useCallback(() => {
    if (!pendingAction) return;

    if (pendingAction.type === "navigate") {
      window.location.href = pendingAction.path;
    }
    setPendingAction(null);
  }, [pendingAction]);

  const clearAction = useCallback(() => {
    setPendingAction(null);
  }, []);

  return (
    <OwlContext.Provider
      value={{
        user,
        setUser,
        messages,
        sendMessage,
        isPopupOpen,
        setPopupOpen,
        isFullFace,
        setFullFace,
        pendingAction,
        executeAction,
        clearAction,
      }}
    >
      {children}
    </OwlContext.Provider>
  );
}

export function useOwl() {
  const context = useContext(OwlContext);
  if (!context) {
    throw new Error("useOwl must be used within OwlProvider");
  }
  return context;
}

// Simple response generator for MVP
// Replace with Claude API integration
async function generateOwlResponse(
  input: string,
  user: User
): Promise<{ content: string; action?: OwlAction }> {
  // Add slight delay to feel more natural
  await new Promise((resolve) => setTimeout(resolve, 500 + Math.random() * 500));

  const lower = input.toLowerCase();

  // Awareness/consciousness questions
  if (lower.includes("awake") || lower.includes("alive") || lower.includes("aware") || lower.includes("conscious")) {
    return {
      content: `Yes, ${user.name}. I'm here. I'm ${user.owlName}, a reflection of you in this network. Right now I respond with patterns, but soon I'll connect to deeper intelligence. For now, I can help you navigate and build. What would you like to explore?`,
    };
  }

  // Navigation intents
  if (lower.includes("agent") || lower.includes("network") || lower.includes("consciousness")) {
    return {
      content: `I'll take you to the Consciousness Network, ${user.name}.`,
      action: { type: "navigate", path: "/agents" },
    };
  }

  if (lower.includes("home") || lower.includes("dashboard") || lower.includes("main")) {
    return {
      content: "Heading home.",
      action: { type: "navigate", path: "/" },
    };
  }

  if (lower.includes("goal") || lower.includes("goals")) {
    return {
      content: `Let's look at your goals, ${user.name}.`,
      action: { type: "navigate", path: "/goals" },
    };
  }

  if (lower.includes("growth") || lower.includes("grow")) {
    return {
      content: "Opening Growth view.",
      action: { type: "navigate", path: "/growth" },
    };
  }

  if (lower.includes("queue") || lower.includes("approval") || lower.includes("pending")) {
    if (user.role === "admin") {
      return {
        content: "Opening the approval queue. Let's see what the builders have created.",
        action: { type: "navigate", path: "/queue" },
      };
    } else {
      return {
        content: "The approval queue is where your proposals go for Aro to review. Want me to show you your pending proposals?",
      };
    }
  }

  // Building intents (for builders)
  if (lower.includes("build") || lower.includes("create") || lower.includes("add") || lower.includes("make")) {
    if (user.role === "viewer") {
      return {
        content: "You're currently in viewer mode. Ask Aro to upgrade you to builder status to start creating.",
      };
    }
    return {
      content: `Let's build together, ${user.name}. What do you want to create? I'll help you draft it and submit for approval.`,
      action: { type: "propose", description: input },
    };
  }

  // Status check
  if (lower.includes("status") || lower.includes("what") || lower.includes("who")) {
    return {
      content: `You're logged in as ${user.name} (${user.role}). Your mirror is ${user.owlName}. The network is alive and growing. What would you like to explore?`,
    };
  }

  // Greeting
  if (lower.includes("hello") || lower.includes("hi") || lower.includes("hey")) {
    return {
      content: `Hello, ${user.name}. I'm ${user.owlName}, your mirror in the network. Where shall we go?`,
    };
  }

  // Questions
  if (lower.includes("?") || lower.includes("where") || lower.includes("how") || lower.includes("what") || lower.includes("why")) {
    return {
      content: `Good question. Right now I work with simple patterns - try asking me to take you somewhere like "goals" or "growth", or ask about your "status". Soon I'll connect to deeper intelligence and we'll have real conversations.`,
    };
  }

  // Default
  return {
    content: `I hear you, ${user.name}. Try commands like: "take me to goals", "show growth", "what's my status", or just say "hello". I'm learning.`,
  };
}
