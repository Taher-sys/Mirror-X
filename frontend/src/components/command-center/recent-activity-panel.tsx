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
                <div className="absolute -left-[19px] top-2.5 h-2.5 w-2.5 rounded-full border-2 border-orange-500/60 bg-[#14151a] group-hover:bg-orange-400 group-hover:shadow-[0_0_10px_#EA580C] transition-all" />

                <div className="rounded-2xl border-2 border-orange-500/30 border-t-2 border-white/20 bg-zinc-950/85 p-3.5 transition-all duration-300 ease-out hover:scale-[1.01] hover:border-orange-500/50 hover:shadow-[0_20px_45px_rgba(0,0,0,0.95)] backdrop-blur-3xl shadow-[0_12px_32px_rgba(0,0,0,0.8)]">
                  <div className="flex items-center justify-between font-mono text-xs">
                    <div className="flex items-center gap-2">
                      <span className="text-zinc-300 font-bold">{timeStr}</span>
                      <span className="rounded-full bg-orange-950/60 px-2.5 py-0.5 text-[9px] uppercase font-bold text-orange-400 border border-orange-500/40 shadow-[0_0_8px_rgba(249,115,22,0.25)]">
                        {act.action.replace('_', ' ')}
                      </span>
                    </div>
                    <span className="text-xs text-zinc-300 font-bold">
                      by [<span className="text-white font-bold">{act.actor}</span>]
                    </span>
                  </div>

                  <div className="mt-2 flex items-center gap-1.5 text-xs font-mono text-zinc-200">
                    <Terminal className="h-3.5 w-3.5 text-orange-400 shrink-0" />
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
