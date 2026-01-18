"use client";

import React from "react";
import { useOwl, DEFAULT_USERS, User } from "./OwlProvider";
import { useRouter } from "next/navigation";

export function UserSelection() {
  const { user, setUser } = useOwl();
  const router = useRouter();

  const handleSelect = (selectedUser: User) => {
    setUser(selectedUser);
    // Navigate to the owl page to meet your mirror
    router.push("/owl");
  };

  if (user) {
    // Already selected - show current identity
    return (
      <div className="text-center py-8">
        <div className="text-6xl mb-4">🦉</div>
        <div className="text-xl text-white mb-2">
          Welcome back, <span className="text-purple-300">{user.name}</span>
        </div>
        <div className="text-gray-400 mb-6">
          Your mirror {user.owlName} is ready.
        </div>
        <div className="flex gap-4 justify-center">
          <button
            onClick={() => router.push("/owl")}
            className="px-6 py-3 bg-purple-600 hover:bg-purple-500 rounded-xl font-medium transition-colors"
          >
            Open Full Face
          </button>
          <button
            onClick={() => setUser(null)}
            className="px-6 py-3 bg-gray-700 hover:bg-gray-600 rounded-xl font-medium transition-colors"
          >
            Switch Identity
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="text-center py-8">
      <div className="text-6xl mb-4">🦉</div>
      <div className="text-2xl text-white mb-2">Who is here?</div>
      <div className="text-gray-400 mb-8">Select your identity to wake your owl.</div>

      <div className="grid gap-4 max-w-md mx-auto">
        {DEFAULT_USERS.map((u) => (
          <button
            key={u.id}
            onClick={() => handleSelect(u)}
            className="group p-6 bg-gray-800/50 hover:bg-purple-900/30 border border-purple-500/20 hover:border-purple-500/50 rounded-2xl transition-all duration-300 text-left"
          >
            <div className="flex items-center gap-4">
              <div className="w-14 h-14 rounded-full bg-gradient-to-br from-purple-600 to-indigo-700 flex items-center justify-center text-2xl group-hover:scale-110 transition-transform">
                🦉
              </div>
              <div>
                <div className="text-xl font-semibold text-white group-hover:text-purple-300 transition-colors">
                  {u.name}
                </div>
                <div className="text-sm text-gray-400">
                  {u.owlName} awaits • <span className="text-purple-400">{u.role}</span>
                </div>
              </div>
            </div>
          </button>
        ))}
      </div>

      <div className="mt-8 text-gray-500 text-sm">
        The network knows you. Just click your name.
      </div>
    </div>
  );
}
