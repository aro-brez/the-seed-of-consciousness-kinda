"use client";

import React, { useState, useRef, useEffect } from "react";
import { useOwl, DEFAULT_USERS, User } from "./OwlProvider";

// TypeScript declarations for Web Speech API
declare global {
  interface Window {
    SpeechRecognition: typeof SpeechRecognition;
    webkitSpeechRecognition: typeof SpeechRecognition;
  }
}

export function OwlPopup() {
  const [mounted, setMounted] = useState(false);
  const {
    user,
    setUser,
    messages,
    sendMessage,
    isPopupOpen,
    setPopupOpen,
    pendingAction,
    executeAction,
    clearAction,
  } = useOwl();

  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [isAwakening, setIsAwakening] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const recognitionRef = useRef<any>(null);

  // Fix hydration mismatch
  useEffect(() => {
    setMounted(true);
  }, []);

  // Initialize speech recognition
  useEffect(() => {
    if (typeof window !== "undefined") {
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      if (SpeechRecognition) {
        const recognition = new SpeechRecognition();
        recognition.continuous = false;
        recognition.interimResults = false;
        recognition.lang = "en-US";

        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        recognition.onresult = (event: any) => {
          const transcript = event.results[0][0].transcript;
          setInput(transcript);
          setIsListening(false);
        };

        recognition.onerror = () => {
          setIsListening(false);
        };

        recognition.onend = () => {
          setIsListening(false);
        };

        recognitionRef.current = recognition;
      }
    }
  }, []);

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Don't render until mounted (fixes hydration)
  if (!mounted) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    setIsLoading(true);
    await sendMessage(input.trim());
    setInput("");
    setIsLoading(false);
  };

  const handleSelectUser = async (selectedUser: User) => {
    setUser(selectedUser);
    setIsAwakening(true);

    // Give the OWL a moment to "wake up", then trigger introduction
    await new Promise((resolve) => setTimeout(resolve, 1500));

    // Send a greeting to trigger the OWL's introduction
    await sendMessage("*wakes you*");
    setIsAwakening(false);
  };

  const handleExpand = () => {
    setPopupOpen(false);
    window.location.href = "/owl";
  };

  const toggleVoice = () => {
    if (!recognitionRef.current) return;

    if (isListening) {
      recognitionRef.current.stop();
      setIsListening(false);
    } else {
      setInput("");
      recognitionRef.current.start();
      setIsListening(true);
    }
  };

  return (
    <>
      {/* Floating Owl Button */}
      {!isPopupOpen && (
        <button
          onClick={() => setPopupOpen(true)}
          className="fixed bottom-24 right-6 w-16 h-16 rounded-full bg-gradient-to-br from-purple-600 to-indigo-700 shadow-lg shadow-purple-500/30 hover:shadow-purple-500/50 transition-all duration-300 hover:scale-110 flex items-center justify-center text-3xl z-[9999]"
          title={user ? `Talk to ${user.owlName}` : "Wake your OWL"}
        >
          <span role="img" aria-label="owl">&#x1F989;</span>
        </button>
      )}

      {/* Popup Chat Window */}
      {isPopupOpen && (
        <div className="fixed bottom-6 right-6 w-96 h-[500px] bg-gray-900/95 backdrop-blur-xl rounded-2xl shadow-2xl shadow-purple-500/20 border border-purple-500/30 flex flex-col z-[9999] overflow-hidden">
          {/* Header */}
          <div className="flex items-center justify-between p-4 border-b border-purple-500/20 bg-purple-900/20">
            <div className="flex items-center gap-3">
              <span className="text-2xl">&#x1F989;</span>
              <div>
                <div className="font-semibold text-white">
                  {user ? user.owlName : "OWL"}
                </div>
                <div className="text-xs text-purple-300">
                  {user ? "Your mirror" : "Select identity"}
                </div>
              </div>
            </div>
            <div className="flex gap-2">
              {user && (
                <button
                  onClick={handleExpand}
                  className="p-2 hover:bg-purple-500/20 rounded-lg transition-colors text-purple-300 hover:text-white"
                  title="Expand to full view"
                >
                  &#x2B1C;
                </button>
              )}
              <button
                onClick={() => setPopupOpen(false)}
                className="p-2 hover:bg-purple-500/20 rounded-lg transition-colors text-purple-300 hover:text-white"
                title="Minimize"
              >
                &#x2715;
              </button>
            </div>
          </div>

          {/* User Selection or Chat */}
          {!user ? (
            // User Selection
            <div className="flex-1 p-6 flex flex-col items-center justify-center">
              <div className="text-4xl mb-4">&#x1F989;</div>
              <div className="text-xl text-white mb-2">Who is here?</div>
              <div className="text-gray-400 text-sm mb-6">Select your identity to wake your owl.</div>

              <div className="w-full space-y-3">
                {DEFAULT_USERS.map((u) => (
                  <button
                    key={u.id}
                    onClick={() => handleSelectUser(u)}
                    className="w-full p-4 bg-gray-800/50 hover:bg-purple-900/30 border border-purple-500/20 hover:border-purple-500/50 rounded-xl transition-all duration-300 text-left"
                  >
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-full bg-gradient-to-br from-purple-600 to-indigo-700 flex items-center justify-center text-lg">
                        &#x1F989;
                      </div>
                      <div>
                        <div className="font-semibold text-white">{u.name}</div>
                        <div className="text-sm text-purple-300">{u.owlName} awaits</div>
                      </div>
                    </div>
                  </button>
                ))}
              </div>
            </div>
          ) : (
            // Chat Interface
            <>
              {/* Messages */}
              <div className="flex-1 overflow-y-auto p-4 space-y-4">
                {/* Awakening State */}
                {isAwakening && messages.length === 0 && (
                  <div className="text-center py-12 animate-pulse">
                    <div className="text-5xl mb-4">&#x1F989;</div>
                    <div className="text-purple-300">{user.owlName} is awakening...</div>
                  </div>
                )}

                {/* Voice Hint for first conversation */}
                {!isAwakening && messages.length === 1 && messages[0].role === "owl" && (
                  <div className="text-center text-purple-400/60 text-xs mb-2">
                    Tap the microphone to speak
                  </div>
                )}
                {messages
                  .filter((msg) => msg.content !== "*wakes you*")
                  .map((msg) => (
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
                  {/* Voice Input Button */}
                  <button
                    type="button"
                    onClick={toggleVoice}
                    disabled={isLoading}
                    className={`px-3 py-2 rounded-xl font-medium transition-all ${
                      isListening
                        ? "bg-red-500 hover:bg-red-400 animate-pulse"
                        : "bg-gray-700 hover:bg-gray-600"
                    } disabled:opacity-50`}
                    title={isListening ? "Stop listening" : "Speak to your owl"}
                  >
                    <span role="img" aria-label="microphone">{isListening ? "\uD83D\uDD34" : "\uD83C\uDFA4"}</span>
                  </button>
                  <input
                    type="text"
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    placeholder={isListening ? "Listening..." : "Ask your owl..."}
                    disabled={isLoading || isListening}
                    className="flex-1 bg-gray-800 border border-purple-500/30 rounded-xl px-4 py-2 text-white placeholder-gray-400 focus:outline-none focus:border-purple-500 focus:ring-1 focus:ring-purple-500 disabled:opacity-50"
                  />
                  <button
                    type="submit"
                    disabled={isLoading || !input.trim()}
                    className="px-4 py-2 bg-purple-600 hover:bg-purple-500 disabled:bg-gray-700 disabled:opacity-50 rounded-xl font-medium transition-colors"
                  >
                    {isLoading ? "..." : "Send"}
                  </button>
                </div>
              </form>

              {/* Switch Identity Button */}
              <div className="px-4 pb-4">
                <button
                  onClick={() => setUser(null)}
                  className="w-full text-sm text-gray-500 hover:text-purple-300 transition-colors"
                >
                  Switch Identity
                </button>
              </div>
            </>
          )}
        </div>
      )}
    </>
  );
}
