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
        className="flex md:hidden rounded-lg border border-zinc-800 bg-zinc-900/80 p-2 text-zinc-300 transition-colors hover:border-zinc-700 hover:text-white"
        aria-label="Search"
      >
        <Command className="h-4 w-4 text-zinc-400" />
      </button>

      <div className="flex items-center gap-2 rounded-lg border border-zinc-800 bg-zinc-900/80 px-3 py-1 font-mono text-[11px] font-bold text-emerald-400 shadow-sm">
        <Activity className="h-3.5 w-3.5 text-emerald-400 animate-pulse" aria-hidden="true" />
        <span className="uppercase tracking-wider">
          TELEMETRY LINKED
        </span>
      </div>

      <button
        type="button"
        className="rounded-lg border border-zinc-800 bg-zinc-900/80 p-2 text-zinc-300 shadow-sm transition-colors hover:border-zinc-700 hover:text-white focus:outline-none"
        aria-label="Notifications"
      >
        <Bell className="h-4 w-4" aria-hidden="true" />
      </button>
    </div>
  );
}
