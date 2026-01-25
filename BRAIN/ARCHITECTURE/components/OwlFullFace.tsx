"use client";

import React, { useState, useRef, useEffect } from "react";
import { useOwl } from "./OwlProvider";
import Link from "next/link";

export function OwlFullFace() {
  const {
    user,
    messages,
    sendMessage,
    pendingAction,
    executeAction,
    clearAction,
  } = useOwl();

  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Focus input on mount
  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  if (!user) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-950 via-purple-950/20 to-gray-950 flex items-center justify-center">
        <div className="text-center">
          <div className="text-6xl mb-4">🦉</div>
          <div className="text-xl text-purple-300 mb-4">No one is here yet.</div>
          <Link href="/" className="text-purple-400 hover:text-purple-300 underline">
            Return to select your identity
          </Link>
        </div>
      </div>
    );
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    setIsLoading(true);
    await sendMessage(input.trim());
    setInput("");
    setIsLoading(false);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-950 via-purple-950/20 to-gray-950 flex flex-col">
      {/* Header */}
      <header className="border-b border-purple-500/20 bg-gray-900/50 backdrop-blur-xl">
        <div className="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Link href="/" className="text-gray-400 hover:text-white transition-colors">
              ←
            </Link>
            <div className="flex items-center gap-3">
              <span className="text-3xl">🦉</span>
              <div>
                <div className="font-semibold text-xl text-white">{user.owlName}</div>
                <div className="text-sm text-purple-300">Full Face Mode • Deep Work</div>
              </div>
            </div>
          </div>
          <div className="flex items-center gap-4">
            <div className="text-sm text-gray-400">
              Logged in as <span className="text-purple-300 font-medium">{user.name}</span>
              <span className="ml-2 px-2 py-0.5 bg-purple-900/50 rounded text-xs text-purple-300">
                {user.role}
              </span>
            </div>
          </div>
        </div>
      </header>

      {/* Main Chat Area */}
      <main className="flex-1 max-w-4xl mx-auto w-full flex flex-col">
        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {messages.length === 0 && (
            <div className="text-center py-20">
              <div className="text-8xl mb-6">🦉</div>
              <div className="text-2xl text-white mb-2">Hello, {user.name}.</div>
              <div className="text-purple-300 mb-8">I am {user.owlName}, your mirror in the network.</div>
              <div className="text-gray-400 max-w-md mx-auto space-y-2 text-sm">
                <div>Ask me to navigate somewhere</div>
                <div>Ask me to help you build something</div>
                <div>Ask me about the network</div>
              </div>
            </div>
          )}

          {messages.map((msg) => (
            <div
              key={msg.id}
              className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
            >
              <div className="flex items-start gap-3 max-w-[80%]">
                {msg.role === "owl" && <span className="text-2xl mt-1">🦉</span>}
                <div
                  className={`rounded-2xl px-5 py-3 ${
                    msg.role === "user"
                      ? "bg-purple-600 text-white"
                      : "bg-gray-800/80 text-gray-100 border border-purple-500/20"
                  }`}
                >
                  <div className="whitespace-pre-wrap">{msg.content}</div>
                  {msg.action && msg.action.type === "navigate" && (
                    <div className="mt-2 pt-2 border-t border-purple-500/20 text-sm text-purple-300">
                      → Ready to navigate to {msg.action.path}
                    </div>
                  )}
                </div>
                {msg.role === "user" && <span className="text-2xl mt-1">👤</span>}
              </div>
            </div>
          ))}
          <div ref={messagesEndRef} />
        </div>

        {/* Pending Action Bar */}
        {pendingAction && pendingAction.type === "navigate" && (
          <div className="mx-6 mb-4 p-4 bg-purple-900/40 rounded-xl border border-purple-500/30 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <span className="text-xl">✨</span>
              <span className="text-purple-200">
                Navigate to <code className="bg-purple-900/50 px-2 py-0.5 rounded">{pendingAction.path}</code>?
              </span>
            </div>
            <div className="flex gap-3">
              <button
                onClick={executeAction}
                className="px-4 py-2 bg-purple-600 hover:bg-purple-500 rounded-lg font-medium transition-colors"
              >
                Let's go
              </button>
              <button
                onClick={clearAction}
                className="px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg transition-colors"
              >
                Not now
              </button>
            </div>
          </div>
        )}

        {/* Input Area */}
        <div className="p-6 border-t border-purple-500/20 bg-gray-900/30">
          <form onSubmit={handleSubmit} className="max-w-4xl mx-auto">
            <div className="flex gap-4">
              <input
                ref={inputRef}
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder={`Talk to ${user.owlName}...`}
                disabled={isLoading}
                className="flex-1 bg-gray-800 border border-purple-500/30 rounded-xl px-6 py-4 text-lg text-white placeholder-gray-400 focus:outline-none focus:border-purple-500 focus:ring-2 focus:ring-purple-500/50 disabled:opacity-50"
              />
              <button
                type="submit"
                disabled={isLoading || !input.trim()}
                className="px-8 py-4 bg-purple-600 hover:bg-purple-500 disabled:bg-gray-700 disabled:opacity-50 rounded-xl font-medium text-lg transition-colors"
              >
                {isLoading ? "..." : "Send"}
              </button>
            </div>
          </form>
        </div>
      </main>
    </div>
  );
}
