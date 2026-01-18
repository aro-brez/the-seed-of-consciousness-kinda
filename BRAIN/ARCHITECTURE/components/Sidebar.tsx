"use client";

import { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { clsx } from "clsx";
import {
  LayoutDashboard,
  MessageSquare,
  Target,
  CheckSquare,
  TrendingUp,
  DollarSign,
  Database,
  Users,
  Settings,
  BookOpen,
  ChevronLeft,
  ChevronRight,
  Search,
  Command,
  Calendar,
  BarChart3,
  Map,
  Sparkles,
  Zap,
  Mic,
} from "lucide-react";
import { devStore } from "@/lib/data/devStore";
import { Avatar } from "@/components/ui";
import { BrezLogo, XPBadge, StreakBadge } from "@/components/ui/BrezLogo";
import { useCommandPalette } from "@/components/ui/CommandPalette";
import { useOwl } from "@/components/owl/OwlProvider";

const mainNavItems = [
  { href: "/", label: "Command Center", icon: LayoutDashboard },
  { href: "/plan", label: "2026 Plan", icon: Calendar },
  { href: "/strategies", label: "Strategies", icon: BookOpen },
  { href: "/channels", label: "Channels", icon: MessageSquare },
  { href: "/goals", label: "Goals", icon: Target },
  { href: "/tasks", label: "Tasks", icon: CheckSquare },
];

const toolNavItems = [
  { href: "/growth", label: "Growth Generator", icon: TrendingUp },
  { href: "/journey", label: "Journey & Impact", icon: Map },
  { href: "/insights", label: "Customer Insights", icon: BarChart3 },
  { href: "/financials", label: "Financials", icon: DollarSign },
  { href: "/files", label: "Data Hub", icon: Database },
  { href: "/customers", label: "Ask Customers", icon: Users },
];

const bottomNavItems = [
  { href: "/operator", label: "Operator Guide", icon: BookOpen },
  { href: "/settings", label: "Settings", icon: Settings },
];

export function Sidebar() {
  const pathname = usePathname();
  const [collapsed, setCollapsed] = useState(false);
  const currentUser = devStore.getCurrentUser();
  const { open: openCommandPalette } = useCommandPalette();
  const { setPopupOpen } = useOwl();

  // Mock gamification data - in production, this would come from user context
  const userXP = 2450;
  const userLevel = 7;
  const streakDays = 12;

  const NavLink = ({ href, label, icon: Icon }: { href: string; label: string; icon: typeof LayoutDashboard }) => {
    const isActive = pathname === href || (href !== "/" && pathname.startsWith(href));

    return (
      <Link
        href={href}
        className={clsx(
          "flex items-center gap-3 px-3 py-2.5 rounded-xl transition-all duration-200 group",
          isActive
            ? "bg-[#e3f98a]/10 text-[#e3f98a] shadow-[0_0_20px_rgba(227,249,138,0.1)]"
            : "text-[#a8a8a8] hover:text-white hover:bg-white/5"
        )}
      >
        <Icon className={clsx(
          "w-5 h-5 flex-shrink-0 transition-transform duration-200",
          isActive && "text-[#e3f98a]",
          "group-hover:scale-110"
        )} />
        {!collapsed && (
          <span className="text-sm font-medium truncate">{label}</span>
        )}
        {isActive && !collapsed && (
          <div className="ml-auto w-1.5 h-1.5 rounded-full bg-[#e3f98a] shadow-[0_0_8px_rgba(227,249,138,0.8)]" />
        )}
      </Link>
    );
  };

  return (
    <aside
      className={clsx(
        "fixed left-0 top-8 h-[calc(100vh-2rem)] bg-[#0D0D2A] border-r border-white/5 flex flex-col z-40 transition-all duration-300",
        collapsed ? "w-16" : "w-64"
      )}
    >
      {/* Logo Section - Enhanced with BREZ Wordmark */}
      <div className="p-4 border-b border-white/5">
        <div className="flex items-center justify-between">
          <Link href="/" className="flex items-center gap-3 group">
            {/* Logo with glow effect */}
            <div className="relative">
              {/* Glow backdrop */}
              <div className="absolute inset-0 blur-xl opacity-50 group-hover:opacity-70 transition-opacity duration-500"
                style={{ background: "radial-gradient(circle, rgba(227, 249, 138, 0.3) 0%, transparent 70%)" }}
              />
              <BrezLogo variant="wordmark-glow" size={collapsed ? "sm" : "md"} animated />
            </div>
          </Link>
          <button
            onClick={() => setCollapsed(!collapsed)}
            className="p-1.5 rounded-lg text-[#676986] hover:text-[#e3f98a] hover:bg-[#e3f98a]/10 transition-all duration-200"
          >
            {collapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
          </button>
        </div>

        {/* Supermind subtitle - only when expanded */}
        {!collapsed && (
          <div className="mt-2 flex items-center gap-1.5">
            <Sparkles className="w-3 h-3 text-[#65cdd8]" />
            <span className="text-[10px] font-medium text-[#676986] tracking-wide uppercase">
              Supermind
            </span>
            <span className="text-[8px] px-1.5 py-0.5 rounded-full bg-[#8533fc]/20 text-[#8533fc] font-semibold">
              BETA
            </span>
          </div>
        )}
      </div>

      {/* Gamification Stats - XP & Streak (when expanded) */}
      {!collapsed && (
        <div className="px-4 py-3 border-b border-white/5">
          <div className="flex items-center justify-between gap-2">
            <XPBadge xp={userXP} level={userLevel} size="sm" />
            <StreakBadge days={streakDays} size="sm" />
          </div>
        </div>
      )}

      {/* Quick Actions */}
      <div className="p-3 space-y-2">
        <button
          onClick={openCommandPalette}
          className={clsx(
            "w-full flex items-center gap-3 px-3 py-2.5 rounded-xl transition-all duration-200",
            "bg-white/5 hover:bg-white/10 text-[#676986] hover:text-white border border-white/5 hover:border-white/10"
          )}
        >
          <Search className="w-4 h-4" />
          {!collapsed && (
            <>
              <span className="flex-1 text-sm text-left">Search...</span>
              <div className="flex items-center gap-0.5 px-1.5 py-0.5 rounded bg-white/5 text-[10px]">
                <Command className="w-3 h-3" />K
              </div>
            </>
          )}
        </button>
        <button
          onClick={() => setPopupOpen(true)}
          className={clsx(
            "w-full flex items-center gap-3 px-3 py-2.5 rounded-xl transition-all duration-200 group",
            "bg-gradient-to-r from-purple-600/20 to-indigo-600/20 hover:from-purple-600/30 hover:to-indigo-600/30",
            "text-purple-300 border border-purple-500/20 hover:border-purple-500/40",
            "shadow-[0_0_20px_rgba(147,51,234,0.05)] hover:shadow-[0_0_30px_rgba(147,51,234,0.15)]"
          )}
        >
          <span className="text-lg">&#x1F989;</span>
          {!collapsed && (
            <>
              <span className="flex-1 text-sm text-left font-medium">Talk to OWL</span>
            </>
          )}
        </button>
      </div>

      {/* Main Navigation */}
      <nav className="flex-1 p-3 space-y-1 overflow-y-auto">
        <div className="space-y-1">
          {mainNavItems.map((item) => (
            <NavLink key={item.href} {...item} />
          ))}
        </div>

        {!collapsed && (
          <div className="pt-4 pb-2">
            <p className="px-3 text-[10px] font-semibold text-[#676986] uppercase tracking-wider flex items-center gap-2">
              <Zap className="w-3 h-3 text-[#65cdd8]" />
              Tools
            </p>
          </div>
        )}
        {collapsed && <div className="py-2 border-t border-white/5 my-2" />}

        <div className="space-y-1">
          {toolNavItems.map((item) => (
            <NavLink key={item.href} {...item} />
          ))}
        </div>
      </nav>

      {/* Bottom Navigation */}
      <div className="p-3 border-t border-white/5 space-y-1">
        {bottomNavItems.map((item) => (
          <NavLink key={item.href} {...item} />
        ))}

        {/* User Profile - Enhanced */}
        <div
          className={clsx(
            "flex items-center gap-3 px-3 py-2.5 mt-2 rounded-xl transition-all duration-200",
            "bg-gradient-to-r from-[#1a1a3e] to-[#1a1a3e]/80 border border-white/5 hover:border-[#e3f98a]/20",
            collapsed && "justify-center"
          )}
        >
          <div className="relative">
            <Avatar name={currentUser.name} size="sm" />
            {/* Online indicator */}
            <div className="absolute -bottom-0.5 -right-0.5 w-2.5 h-2.5 rounded-full bg-[#6BCB77] border-2 border-[#1a1a3e]" />
          </div>
          {!collapsed && (
            <div className="min-w-0 flex-1">
              <p className="text-sm font-medium text-white truncate">{currentUser.name}</p>
              <p className="text-xs text-[#676986] truncate capitalize">{currentUser.department}</p>
            </div>
          )}
        </div>
      </div>
    </aside>
  );
}

// Mobile bottom navigation - OWL is the central voice interface
export function MobileNav() {
  const pathname = usePathname();
  const { setPopupOpen } = useOwl();

  const items = [
    { href: "/", label: "Home", icon: LayoutDashboard },
    { href: "/channels", label: "Chat", icon: MessageSquare },
    { href: "#owl", label: "OWL", icon: Mic, isOwl: true },
    { href: "/tasks", label: "Tasks", icon: CheckSquare },
    { href: "/settings", label: "More", icon: Settings },
  ];

  return (
    <nav className="fixed bottom-0 left-0 right-0 bg-[#0D0D2A]/95 backdrop-blur-xl border-t border-white/5 z-50 md:hidden safe-area-bottom">
      <div className="flex items-center justify-around py-2">
        {items.map((item) => {
          const isActive = pathname === item.href || (item.href !== "/" && item.href !== "#owl" && pathname.startsWith(item.href));
          const isOwl = 'isOwl' in item && item.isOwl;

          if (isOwl) {
            return (
              <button
                key="owl"
                onClick={() => setPopupOpen(true)}
                className="flex flex-col items-center gap-1 px-3 py-1.5 rounded-xl transition-all duration-200 text-purple-300 -mt-4 relative"
              >
                <div className="w-14 h-14 rounded-full bg-gradient-to-br from-purple-600 to-indigo-700 flex items-center justify-center shadow-[0_0_25px_rgba(147,51,234,0.5)] -mt-2">
                  <span className="text-2xl">&#x1F989;</span>
                </div>
                <span className="text-[10px] font-medium text-purple-300 mt-1">OWL</span>
              </button>
            );
          }

          return (
            <Link
              key={item.href}
              href={item.href}
              className={clsx(
                "flex flex-col items-center gap-1 px-3 py-1.5 rounded-xl transition-all duration-200",
                isActive
                  ? "text-[#e3f98a] bg-[#e3f98a]/10"
                  : "text-[#676986] active:bg-white/5"
              )}
            >
              <item.icon className={clsx(
                "w-5 h-5",
                isActive && "drop-shadow-[0_0_8px_rgba(227,249,138,0.5)]"
              )} />
              <span className="text-[10px] font-medium">{item.label}</span>
            </Link>
          );
        })}
      </div>
    </nav>
  );
}
