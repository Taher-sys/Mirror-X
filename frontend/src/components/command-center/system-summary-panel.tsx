'use client';

import React from 'react';
import { GitBranch, Cpu, AlertTriangle, Database } from 'lucide-react';
import { StatTile } from '@/components/ui/stat-tile';
import { StatusBadge } from '@/components/ui/status-badge';
import { SystemStatus, SystemSummary } from '@/lib/api';

interface SystemSummaryPanelProps {
  summary: SystemSummary | null;
  status: SystemStatus | null;
}

export function SystemSummaryPanel({ summary, status }: SystemSummaryPanelProps) {
  const repoCount = summary?.repositories_count ?? 0;
  const svcCount = summary?.services_count ?? 0;
  const findingsTotal = summary?.findings_count ?? 0;
  const criticalCount = summary?.findings_by_severity.critical ?? 0;
  const highCount = summary?.findings_by_severity.high ?? 0;

  const dbDialect = status?.database_dialect || 'database';
  const dbLatency = status ? `${status.database_latency_ms}ms` : '0.0ms';

  const systemStatus = summary?.system_status || (repoCount === 0 ? 'uninitialized' : 'healthy');

  return (
    <div className="space-y-4">
      {/* Top Telemetry Header Bar */}
      <div className="flex flex-wrap items-center justify-between gap-4 rounded-xl bg-[#12151e]/92 backdrop-blur-md border border-[#232736] border-t border-t-zinc-700/50 p-4 shadow-[0_8px_32px_0_rgba(0,0,0,0.6)]">
        <div className="flex items-center gap-3.5">
          <div className="relative flex h-3 w-3 items-center justify-center">
            <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-75" />
            <span className="relative inline-flex h-2 w-2 rounded-full bg-emerald-400" />
          </div>
          <div>
            <h2 className="font-mono text-sm font-bold uppercase tracking-wider text-white">
              System Control Telemetry
            </h2>
            <p className="font-mono text-xs font-bold text-zinc-400">
              Live daemon link • Version <span className="font-bold text-white">{status?.api_version || '0.1.0'}</span> • Dialect [<span className="font-bold text-amber-400">{dbDialect}</span>]
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3 font-mono text-sm">
          <span className="text-zinc-300 font-bold uppercase tracking-wider">Core Status:</span>
          <StatusBadge status={systemStatus} />
        </div>
      </div>

      {/* Primary KPI Bento Row */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatTile
          label="Connected Repositories"
          value={repoCount}
          subvalue={repoCount === 1 ? '1 active git link' : `${repoCount} git links`}
          icon={GitBranch}
          accent={repoCount > 0 ? 'amber' : 'none'}
        />

        <StatTile
          label="Discovered Services"
          value={svcCount}
          subvalue={
            summary
              ? `${summary.services_healthy_count} healthy / ${summary.services_degraded_count} degraded`
              : '0 registered'
          }
          icon={Cpu}
          accent={svcCount > 0 ? 'amber' : 'none'}
        />

        <StatTile
          label="Active Findings"
          value={findingsTotal}
          subvalue={
            findingsTotal > 0
              ? `${criticalCount} crit / ${highCount} high`
              : '0 drift observations'
          }
          icon={AlertTriangle}
          accent={criticalCount > 0 ? 'crimson' : findingsTotal > 0 ? 'amber' : 'none'}
        />

        <StatTile
          label="Database Telemetry"
          value={dbLatency}
          subvalue={status?.database_connected ? 'Connected (online)' : 'Disconnected'}
          icon={Database}
          accent={status?.database_connected ? 'amber' : 'crimson'}
        />
      </div>
    </div>
  );
}
