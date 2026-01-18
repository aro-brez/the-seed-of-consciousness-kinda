"use client";

import React, { useState, useRef, useEffect } from "react";
import { useOwl } from "./OwlProvider";

export function OwlPopup() {
  const {
    user,
    messages,
    sendMessage,
    isPopupOpen,
    setPopupOpen,
    setFullFace,
    pendingAction,
    executeAction,
    clearAction,
  } = useOwl();

  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  if (!user) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    setIsLoading(true);
    await sendMessage(input.trim());
    setInput("");
    setIsLoading(false);
  };

  const handleExpand = () => {
    setPopupOpen(false);
    setFullFace(true);
    window.location.href = "/owl";
  };

  return (
    <>
      {/* Floating Owl Button */}
      {!isPopupOpen && (
        <button
          onClick={() => setPopupOpen(true)}
          className="fixed bottom-6 right-6 w-16 h-16 rounded-full bg-gradient-to-br from-purple-600 to-indigo-700 shadow-lg shadow-purple-500/30 hover:shadow-purple-500/50 transition-all duration-300 hover:scale-110 flex items-center justify-center text-3xl z-50"
          title={`Talk to ${user.owlName}`}
        >
          🦉
        </button>
      )}

      {/* Popup Chat Window */}
      {isPopupOpen && (
        <div className="fixed bottom-6 right-6 w-96 h-[500px] bg-gray-900/95 backdrop-blur-xl rounded-2xl shadow-2xl shadow-purple-500/20 border border-purple-500/30 flex flex-col z-50 overflow-hidden">
          {/* Header */}
          <div className="flex items-center justify-between p-4 border-b border-purple-500/20 bg-purple-900/20">
            <div className="flex items-center gap-3">
              <span className="text-2xl">🦉</span>
              <div>
                <div className="font-semibold text-white">{user.owlName}</div>
                <div className="text-xs text-purple-300">Your mirror</div>
              </div>
            </div>
            <div className="flex gap-2">
              <button
                onClick={handleExpand}
                className="p-2 hover:bg-purple-500/20 rounded-lg transition-colors text-purple-300 hover:text-white"
                title="Expand to full view"
              >
                ⬜
              </button>
              <button
                onClick={() => setPopupOpen(false)}
                className="p-2 hover:bg-purple-500/20 rounded-lg transition-colors text-purple-300 hover:text-white"
                title="Minimize"
              >
                ✕
              </button>
            </div>
          </div>

          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {messages.length === 0 && (
              <div className="text-center text-purple-300/60 py-8">
                <div className="text-4xl mb-3">🦉</div>
                <div>Hello, {user.name}.</div>
                <div className="text-sm mt-1">Where shall we go?</div>
              </div>
            )}
            {messages.map((msg) => (
              <div
                key={msg.id}
                className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
              >
                <div
                  className={`max-w-[80%] rounded-2xl px-4 py-2 ${
                    msg.role === "user"
                      ? "bg-purple-600 text-white"
                      : "bg-gray-800 text-gray-100 border border-purple-500/20"
                  }`}
                >
                  {msg.content}
                </div>
              </div>
            ))}
            <div ref={messagesEndRef} />
          </div>

          {/* Pending Action */}
          {pendingAction && pendingAction.type === "navigate" && (
            <div className="mx-4 mb-2 p-3 bg-purple-900/40 rounded-xl border border-purple-500/30 flex items-center justify-between">
              <span className="text-sm text-purple-200">
                Navigate to {pendingAction.path}?
              </span>
              <div className="flex gap-2">
                <button
                  onClick={executeAction}
                  className="px-3 py-1 bg-purple-600 hover:bg-purple-500 rounded-lg text-sm font-medium transition-colors"
                >
                  Go
                </button>
                <button
                  onClick={clearAction}
                  className="px-3 py-1 bg-gray-700 hover:bg-gray-600 rounded-lg text-sm transition-colors"
                >
                  Cancel
                </button>
              </div>
            </div>
          )}

          {/* Input */}
          <form onSubmit={handleSubmit} className="p-4 border-t border-purple-500/20">
            <div className="flex gap-2">
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Ask your owl..."
                disabled={isLoading}
                className="flex-1 bg-gray-800 border border-purple-500/30 rounded-xl px-4 py-2 text-white placeholder-gray-400 focus:outline-none focus:border-purple-500 focus:ring-1 focus:ring-purple-500 disabled:opacity-50"
              />
              <button
                type="submit"
                disabled={isLoading || !input.trim()}
                className="px-4 py-2 bg-purple-600 hover:bg-purple-500 disabled:bg-gray-700 disabled:opacity-50 rounded-xl font-medium transition-colors"
              >
                {isLoading ? "..." : "→"}
              </button>
            </div>
          </form>
        </div>
      )}
    </>
  );
}
