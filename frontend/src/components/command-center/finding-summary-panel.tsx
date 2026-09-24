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
      <div className="flex flex-wrap items-center gap-1.5 border-b border-white/10 pb-3 mb-3">
        {severityBadges.map((badge) => (
          <button
            key={badge.key}
            onClick={() => setSelectedSeverity(badge.key)}
            className={cn(
              'flex items-center gap-1.5 rounded-xl px-3 py-1 font-mono text-[10px] font-bold uppercase tracking-wider transition-all duration-300 ease-out hover:scale-[1.02] active:scale-[0.98]',
              selectedSeverity === badge.key
                ? 'border-2 border-orange-500/50 bg-orange-950/60 text-white shadow-[0_0_15px_rgba(249,115,22,0.25)]'
                : 'border border-white/10 text-zinc-400 hover:text-white hover:border-orange-500/30 bg-zinc-900/40'
            )}
          >
            <span className={badge.color}>{badge.label}</span>
            <span className="rounded-lg bg-black/60 px-1.5 py-0.5 text-[9px] font-bold text-zinc-200">
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
              className="flex items-start justify-between gap-3 rounded-2xl border-2 border-orange-500/30 border-t-2 border-white/20 bg-zinc-950/85 p-3.5 transition-all duration-300 ease-out hover:scale-[1.01] hover:border-orange-500/50 hover:shadow-[0_20px_45px_rgba(0,0,0,0.95)] backdrop-blur-3xl shadow-[0_12px_32px_rgba(0,0,0,0.8)]"
            >
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <span
                    className={cn(
                      'font-mono text-[9px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full border',
                      finding.severity === 'critical'
                        ? 'border-rose-500/50 bg-rose-950/50 text-rose-400 shadow-[0_0_8px_rgba(244,63,94,0.35)]'
                        : finding.severity === 'high'
                        ? 'border-orange-500/50 bg-orange-950/50 text-orange-400 shadow-[0_0_8px_rgba(249,115,22,0.35)]'
                        : 'border-white/10 bg-black/50 text-zinc-300'
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
                  <span>Confidence: <span className="text-orange-400 font-bold">{(finding.confidence * 100).toFixed(0)}%</span></span>
                  {finding.service_name && (
                    <>
                      <span>•</span>
                      <span>Service: <span className="text-orange-400 font-bold">{finding.service_name}</span></span>
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
