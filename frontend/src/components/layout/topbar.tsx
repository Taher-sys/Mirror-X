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
    <header className="relative z-10 m-3 mb-0 flex h-16 items-center justify-between rounded-2xl border border-[#232736] border-t border-t-zinc-700/50 bg-[#12151e]/92 px-6 backdrop-blur-md shadow-[0_8px_32px_0_rgba(0,0,0,0.6)]">
      <div className="flex items-center gap-6">
        <WorkspaceSelector />
        <button
          type="button"
          onClick={onOpenCommandPalette}
          className="hidden md:flex items-center gap-3 rounded-lg border border-zinc-800 bg-zinc-900/80 px-3.5 py-1.5 font-mono text-xs text-zinc-300 shadow-sm transition-all duration-150 hover:border-zinc-700 hover:text-white"
        >
          <Search className="h-3.5 w-3.5 text-zinc-400" />
          <span className="text-xs font-semibold tracking-tight text-zinc-300">Command search or jump to...</span>
          <kbd className="inline-flex items-center gap-0.5 rounded border border-zinc-700/60 bg-zinc-800 px-1.5 py-0.5 font-mono text-[10px] font-bold text-zinc-300">
            <Command className="h-2.5 w-2.5" /> K
          </kbd>
        </button>
      </div>
      <NotificationArea onOpenCommandPalette={onOpenCommandPalette} />
    </header>
  );
}