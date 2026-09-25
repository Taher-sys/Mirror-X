'use client';

import React, { useState } from 'react';
import { Cpu, Server, Filter } from 'lucide-react';
import { GlassPanel } from '@/components/ui/glass-panel';
import { EmptyState } from '@/components/ui/empty-state';
import { StatusBadge } from '@/components/ui/status-badge';
import { Service } from '@/lib/api';

interface ServiceSummaryPanelProps {
  services: Service[];
}

export function ServiceSummaryPanel({ services }: ServiceSummaryPanelProps) {
  const [filterType, setFilterType] = useState<string>('all');

  const filtered = services.filter((s) => {
    if (filterType === 'all') return true;
    return s.service_type === filterType;
  });

  const types = Array.from(new Set(services.map((s) => s.service_type)));

  return (
    <GlassPanel
      title="Service Architecture Summary"
      subtitle="Discovered microservices, APIs, and background processes"
      accentGlow="none"
      badge={
        <span className="font-mono text-xs font-bold text-zinc-300 bg-zinc-900 border border-zinc-800 px-1.5 py-0.5 rounded">
          {services.length} active
        </span>
      }
      action={
        types.length > 0 ? (
          <div className="flex items-center gap-1">
            <Filter className="h-3 w-3 text-zinc-500 mr-1" />
            <select
              value={filterType}
              onChange={(e) => setFilterType(e.target.value)}
              className="rounded border border-zinc-800 bg-zinc-900 px-2 py-0.5 font-mono text-xs font-bold text-zinc-200 outline-none"
            >
              <option value="all">All Types</option>
              {types.map((t) => (
                <option key={t} value={t}>
                  {t.toUpperCase()}
                </option>
              ))}
            </select>
          </div>
        ) : undefined
      }
    >
      {services.length === 0 ? (
        <EmptyState
          icon={Cpu}
          title="No Services Discovered"
          description="Services will be automatically mapped from package.json, Dockerfile, docker-compose.yml, and Kubernetes manifests during ingestion."
        />
      ) : filtered.length === 0 ? (
        <div className="py-6 text-center font-mono text-sm font-bold text-zinc-300">
          No services matching filter type &quot;{filterType}&quot;
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3.5">
          {filtered.map((service) => (
            <div
              key={service.id}
              className="group rounded-lg bg-[#12151e]/92 backdrop-blur-md border border-[#232736] border-t border-t-zinc-700/50 p-4 transition-all duration-200 ease-out hover:border-[#343b52] hover:border-t-zinc-500/60 hover:shadow-[0_12px_40px_0_rgba(0,0,0,0.8)] shadow-[0_8px_32px_0_rgba(0,0,0,0.6)]"
            >
              <div className="flex items-start justify-between gap-2">
                <div className="flex items-center gap-3">
                  <div className="flex h-9 w-9 items-center justify-center rounded-xl border border-zinc-800 bg-zinc-900/80 text-amber-500">
                    <Server className="h-4 w-4" />
                  </div>
                  <div>
                    <h4 className="font-mono text-sm font-bold text-white group-hover:text-amber-400 transition-colors">
                      {service.name}
                    </h4>
                    <p className="font-mono text-xs text-zinc-400">
                      {service.repository_name || 'Repository'}
                    </p>
                  </div>
                </div>
                <StatusBadge status={service.status} size="sm" />
              </div>

              <div className="mt-3.5 flex items-center justify-between border-t border-zinc-800/80 pt-2.5 font-mono text-xs">
                <span className="uppercase text-zinc-400 font-medium">
                  Type: <strong className="text-zinc-200 font-bold">{service.service_type}</strong>
                </span>
                <span className="text-zinc-300 font-medium">{service.runtime || service.version}</span>
              </div>
            </div>
          ))}
        </div>
      )}
    </GlassPanel>
  );
}
