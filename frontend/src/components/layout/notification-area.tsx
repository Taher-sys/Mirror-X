'use client';

import React from 'react';
import { Bell, Activity, Command } from 'lucide-react';

interface NotificationAreaProps {
  onOpenCommandPalette?: () => void;
}

export function NotificationArea({ onOpenCommandPalette }: NotificationAreaProps) {
  return (
    <div className="flex items-center gap-3">
      {/* Mobile search trigger */}
      <button
        type="button"
        onClick={onOpenCommandPalette}
        className="flex md:hidden rounded-xl border border-white/10 bg-zinc-900/60 p-2 text-zinc-300 transition-all duration-300 ease-out hover:scale-[1.05] active:scale-[0.95] hover:text-white"
        aria-label="Search"
      >
        <Command className="h-4 w-4 text-orange-400" />
      </button>

      <div className="flex items-center gap-2 rounded-xl border border-orange-500/40 bg-orange-950/40 px-3 py-1.5 shadow-[0_0_12px_rgba(249,115,22,0.2)]">
        <Activity className="h-3.5 w-3.5 text-orange-400 animate-pulse" aria-hidden="true" />
        <span className="font-mono text-[11px] font-bold uppercase tracking-wider text-orange-400">
          TELEMETRY LINKED
        </span>
      </div>

      <button
        type="button"
        className="rounded-xl border border-white/10 bg-zinc-900/60 p-2 text-zinc-300 shadow-[0_4px_12px_rgba(0,0,0,0.4)] transition-all duration-300 ease-out hover:scale-[1.05] active:scale-[0.95] hover:border-orange-500/40 hover:text-white hover:shadow-[0_0_12px_rgba(249,115,22,0.25)] focus:outline-none"
        aria-label="Notifications"
      >
        <Bell className="h-4 w-4" aria-hidden="true" />
      </button>
    </div>
  );
}
