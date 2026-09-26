'use client';

import React from 'react';
import { History, Activity as ActivityIcon, Terminal } from 'lucide-react';
import { GlassPanel } from '@/components/ui/glass-panel';
import { EmptyState } from '@/components/ui/empty-state';
import { Activity } from '@/lib/api';

interface RecentActivityPanelProps {
  activities: Activity[];
}

export function RecentActivityPanel({ activities }: RecentActivityPanelProps) {
  return (
    <GlassPanel
      title="Recent Audit & Event Log"
      subtitle="Chronological stream of system actions and entity lifecycle events"
      badge={
        <span className="font-mono text-xs font-bold text-zinc-300 bg-zinc-900 border border-zinc-800 px-1.5 py-0.5 rounded">
          {activities.length} events
        </span>
      }
    >
      {activities.length === 0 ? (
        <EmptyState
          icon={History}
          title="No Recent Activity Logged"
          description="Operational events such as repository scans, policy audits, and finding updates will stream here in real time."
        />
      ) : (
        <div className="relative pl-4 space-y-3.5 before:absolute before:left-1.5 before:top-2 before:bottom-2 before:w-px before:bg-white/10">
          {activities.map((act) => {
            const timeStr = new Date(act.created_at).toLocaleTimeString([], {
              hour: '2-digit',
              minute: '2-digit',
              second: '2-digit',
            });

            return (
              <div key={act.id} className="relative group">
                {/* Timeline node dot */}
                <div className="absolute -left-[19px] top-2.5 h-2.5 w-2.5 rounded-full border-2 border-zinc-700 bg-zinc-900 group-hover:border-amber-500 group-hover:bg-amber-500 transition-colors" />

                <div className="rounded-lg bg-[#12151e]/92 backdrop-blur-md border border-[#232736] border-t border-t-zinc-700/50 p-3.5 transition-all duration-300 ease-out hover:-translate-y-1 hover:scale-[1.01] hover:border-[#343b52] hover:border-t-zinc-400 hover:shadow-[0_14px_36px_0_rgba(0,0,0,0.8)] shadow-[0_8px_32px_0_rgba(0,0,0,0.6)] cursor-pointer">
                  <div className="flex items-center justify-between font-mono text-xs">
                    <div className="flex items-center gap-2">
                      <span className="text-zinc-400 font-medium" suppressHydrationWarning>{timeStr}</span>
                      <span className="rounded bg-zinc-800 border border-zinc-700/80 px-2 py-0.5 text-[9px] uppercase font-bold text-zinc-300">
                        {act.action.replace('_', ' ')}
                      </span>
                    </div>
                    <span className="text-xs text-zinc-400">
                      by [<span className="text-zinc-200 font-semibold">{act.actor}</span>]
                    </span>
                  </div>

                  <div className="mt-2 flex items-center gap-1.5 text-xs font-mono text-zinc-300">
                    <Terminal className="h-3.5 w-3.5 text-zinc-400 shrink-0" />
                    <span className="truncate">
                      {act.entity_type}: <strong className="text-white font-bold">{act.entity_name}</strong>
                    </span>
                  </div>

                  {act.details && (
                    <p className="mt-1.5 text-xs text-zinc-200 font-sans font-medium line-clamp-2">
                      {act.details}
                    </p>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </GlassPanel>
  );
}
