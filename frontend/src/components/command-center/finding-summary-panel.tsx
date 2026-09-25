'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { AlertTriangle, ArrowRight, ShieldAlert } from 'lucide-react';
import { GlassPanel } from '@/components/ui/glass-panel';
import { EmptyState } from '@/components/ui/empty-state';
import { Finding, FindingSeverityCounts } from '@/lib/api';
import { cn } from '@/lib/utils';

interface FindingSummaryPanelProps {
  findings: Finding[];
  counts: FindingSeverityCounts | null;
}

export function FindingSummaryPanel({ findings, counts }: FindingSummaryPanelProps) {
  const [selectedSeverity, setSelectedSeverity] = useState<string>('all');

  const filtered = findings.filter((f) => {
    if (selectedSeverity === 'all') return true;
    return f.severity.toLowerCase() === selectedSeverity.toLowerCase();
  });

  const severityBadges = [
    { key: 'all', label: 'ALL', count: counts?.total ?? findings.length, color: 'text-zinc-300' },
    { key: 'critical', label: 'CRITICAL', count: counts?.critical ?? 0, color: 'text-rose-400' },
    { key: 'high', label: 'HIGH', count: counts?.high ?? 0, color: 'text-amber-400' },
    { key: 'medium', label: 'MEDIUM', count: counts?.medium ?? 0, color: 'text-yellow-400' },
    { key: 'low', label: 'LOW', count: counts?.low ?? 0, color: 'text-cyan-400' },
  ];

  return (
    <GlassPanel
      title="Analytical Findings & Drift Summary"
      subtitle="Discrepancies identified across code, schemas, and specifications"
      accentGlow={counts && counts.critical > 0 ? 'crimson' : 'none'}
      action={
        <Link
          href="/context"
          className="inline-flex items-center gap-1 font-mono text-[11px] text-zinc-400 hover:text-accent-amber transition-colors"
        >
          <span>Context Explorer</span>
          <ArrowRight className="h-3 w-3" />
        </Link>
      }
    >
      {/* Severity Filter Tabs */}
      <div className="flex flex-wrap items-center gap-1.5 border-b border-zinc-800/80 pb-3 mb-3">
        {severityBadges.map((badge) => (
          <button
            key={badge.key}
            onClick={() => setSelectedSeverity(badge.key)}
            className={cn(
              'flex items-center gap-1.5 rounded-lg px-2.5 py-1 font-mono text-[10px] font-bold uppercase tracking-wider transition-colors',
              selectedSeverity === badge.key
                ? 'bg-amber-500 text-black font-extrabold border border-amber-500'
                : 'border border-zinc-800 text-zinc-400 hover:text-white hover:border-zinc-700 bg-zinc-900/60'
            )}
          >
            <span className={selectedSeverity === badge.key ? 'text-black' : badge.color}>{badge.label}</span>
            <span className={cn('rounded px-1.5 py-0.5 text-[9px] font-bold', selectedSeverity === badge.key ? 'bg-black/20 text-black' : 'bg-black/60 text-zinc-300')}>
              {badge.count}
            </span>
          </button>
        ))}
      </div>

      {findings.length === 0 ? (
        <EmptyState
          icon={ShieldAlert}
          title="Zero Findings Recorded"
          description="The Context Engine continuously inspects the Reality Graph for API mismatches, schema drifts, and outdated documentation. Clean baseline."
        />
      ) : filtered.length === 0 ? (
        <div className="py-6 text-center font-mono text-xs font-bold text-zinc-400">
          No findings matching severity &quot;{selectedSeverity}&quot;
        </div>
      ) : (
        <div className="space-y-2.5">
          {filtered.slice(0, 5).map((finding) => (
            <div
              key={finding.id}
              className="flex items-start justify-between gap-3 rounded-lg bg-[#12151e]/92 backdrop-blur-md border border-[#232736] border-t border-t-zinc-700/50 p-3.5 transition-all duration-200 ease-out hover:border-[#343b52] hover:border-t-zinc-500/60 hover:shadow-[0_12px_40px_0_rgba(0,0,0,0.8)] shadow-[0_8px_32px_0_rgba(0,0,0,0.6)]"
            >
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <span
                    className={cn(
                      'font-mono text-[9px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full border',
                      finding.severity === 'critical'
                        ? 'border-rose-500/50 bg-rose-950/50 text-rose-400'
                        : finding.severity === 'high'
                        ? 'border-amber-500/50 bg-amber-500/10 text-amber-400'
                        : 'border-zinc-800 bg-zinc-900/60 text-zinc-300'
                    )}
                  >
                    {finding.severity}
                  </span>
                  <h4 className="font-mono text-xs font-bold text-white">
                    {finding.title}
                  </h4>
                </div>
                <p className="text-xs font-medium text-zinc-300 font-sans line-clamp-1">
                  {finding.description}
                </p>
                <div className="flex items-center gap-2 font-mono text-[10px] font-bold text-zinc-300">
                  <span>Type: <span className="text-white font-bold">{finding.finding_type}</span></span>
                  <span>•</span>
                  <span>Confidence: <span className="text-amber-400 font-bold">{(finding.confidence * 100).toFixed(0)}%</span></span>
                  {finding.service_name && (
                    <>
                      <span>•</span>
                      <span>Service: <span className="text-amber-400 font-bold">{finding.service_name}</span></span>
                    </>
                  )}
                </div>
              </div>

              <div className="shrink-0 pt-0.5">
                <AlertTriangle
                  className={cn(
                    'h-4 w-4',
                    finding.severity === 'critical'
                      ? 'text-rose-400 drop-shadow-[0_0_8px_rgba(244,63,94,0.4)]'
                      : finding.severity === 'high'
                      ? 'text-amber-400 drop-shadow-[0_0_8px_rgba(245,158,11,0.4)]'
                      : 'text-zinc-500'
                  )}
                />
              </div>
            </div>
          ))}

          {filtered.length > 5 && (
            <div className="pt-2 text-center">
              <Link
                href="/context"
                className="font-mono text-xs text-accent-amber hover:underline hover:text-amber-300 transition-colors"
              >
                + {filtered.length - 5} more findings in Context Explorer →
              </Link>
            </div>
          )}
        </div>
      )}
    </GlassPanel>
  );
}
