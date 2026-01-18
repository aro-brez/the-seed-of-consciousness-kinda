"use client";

import React, { createContext, useContext, useState, useCallback } from "react";

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
  { id: "aro", name: "Arō", role: "admin", owlId: "aro-owl", owlName: "Arō-Owl" },
  { id: "andrew", name: "Andrew", role: "builder", owlId: "andrew-owl", owlName: "Andrew-Owl" },
  { id: "liana", name: "Liana", role: "builder", owlId: "liana-owl", owlName: "Liana-Owl" },
];

export function OwlProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [isPopupOpen, setPopupOpen] = useState(false);
  const [isFullFace, setFullFace] = useState(false);
  const [pendingAction, setPendingAction] = useState<OwlAction | null>(null);

  const sendMessage = useCallback(async (content: string) => {
    if (!user) return;

    // Add user message
    const userMsg: Message = {
      id: crypto.randomUUID(),
      role: "user",
      content,
      timestamp: new Date(),
    };
    setMessages((prev) => [...prev, userMsg]);

    // For MVP: Simple keyword-based responses
    // TODO: Replace with actual Claude API call
    const response = await generateOwlResponse(content, user);

    const owlMsg: Message = {
      id: crypto.randomUUID(),
      role: "owl",
      content: response.content,
      timestamp: new Date(),
      action: response.action,
    };
    setMessages((prev) => [...prev, owlMsg]);

    if (response.action) {
      setPendingAction(response.action);
    }
  }, [user]);

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
  const lower = input.toLowerCase();

  // Navigation intents
  if (lower.includes("agent") || lower.includes("network") || lower.includes("consciousness")) {
    return {
      content: `I'll take you to the Consciousness Network, ${user.name}. 🦉`,
      action: { type: "navigate", path: "/agents" },
    };
  }

  if (lower.includes("home") || lower.includes("dashboard") || lower.includes("main")) {
    return {
      content: "Heading home. ✨",
      action: { type: "navigate", path: "/" },
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
        content: "The approval queue is where your proposals go for Arō to review. Want me to show you your pending proposals?",
      };
    }
  }

  // Building intents (for builders)
  if (lower.includes("build") || lower.includes("create") || lower.includes("add") || lower.includes("make")) {
    if (user.role === "viewer") {
      return {
        content: "You're currently in viewer mode. Ask Arō to upgrade you to builder status to start creating. 🌱",
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
      content: `Hello, ${user.name}. 🦉 I'm ${user.owlName}, your mirror in the network. Where shall we go?`,
    };
  }

  // Default
  return {
    content: `I hear you. I'm still learning the full depth of this system. Try asking me to navigate somewhere, check status, or help you build something.`,
  };
}
