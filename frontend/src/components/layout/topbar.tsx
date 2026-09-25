'use client';

import React from 'react';
import { Search, Command } from 'lucide-react';
import { WorkspaceSelector } from './workspace-selector';
import { NotificationArea } from './notification-area';

interface TopBarProps {
  onOpenCommandPalette?: () => void;
}

export function TopBar({ onOpenCommandPalette }: TopBarProps) {
  return (
    <header className="relative z-10 m-3 mb-0 flex h-16 items-center justify-between rounded-2xl border-2 border-orange-500/35 border-t-2 border-white/25 bg-zinc-950/90 px-6 backdrop-blur-3xl shadow-[0_20px_50px_rgba(0,0,0,0.9)] transition-all duration-300 ease-out hover:-translate-y-2.5 hover:scale-[1.015] hover:border-orange-500/60 hover:border-t-white/40 hover:shadow-[0_20px_45px_-5px_rgba(249,115,22,0.3)]">
      <div className="flex items-center gap-6">
        <WorkspaceSelector />
        <button
          type="button"
          onClick={onOpenCommandPalette}
          className="hidden md:flex items-center gap-3 rounded-xl border border-orange-500/35 bg-zinc-900/70 px-4 py-2 font-mono text-xs font-bold text-zinc-200 shadow-[0_4px_16px_rgba(0,0,0,0.5)] transition-all duration-300 ease-out hover:scale-[1.02] active:scale-[0.98] hover:border-orange-500/60 hover:text-white hover:shadow-[0_0_16px_rgba(249,115,22,0.25)]"
        >
          <Search className="h-3.5 w-3.5 text-orange-400" />
          <span className="text-xs font-bold tracking-tight">Command search or jump to...</span>
          <kbd className="inline-flex items-center gap-0.5 rounded-lg border border-orange-500/30 bg-black/80 px-2 py-0.5 font-mono text-[10px] font-bold text-orange-400">
            <Command className="h-2.5 w-2.5" /> K
          </kbd>
        </button>
      </div>
      <NotificationArea onOpenCommandPalette={onOpenCommandPalette} />
    </header>
  );
}