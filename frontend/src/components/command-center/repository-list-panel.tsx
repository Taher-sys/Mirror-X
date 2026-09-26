'use client';

import React, { useState } from 'react';
import { GitBranch, Plus, Search, ExternalLink, ShieldCheck } from 'lucide-react';
import { GlassPanel } from '@/components/ui/glass-panel';
import { EmptyState } from '@/components/ui/empty-state';
import { StatusBadge } from '@/components/ui/status-badge';
import { Repository } from '@/lib/api';

interface RepositoryListPanelProps {
  repositories: Repository[];
  onOpenConnectModal: () => void;
}

export function RepositoryListPanel({
  repositories,
  onOpenConnectModal,
}: RepositoryListPanelProps) {
  const [searchTerm, setSearchTerm] = useState('');

  const filtered = repositories.filter(
    (repo) =>
      repo.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      repo.url.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <GlassPanel
      title="Connected Repositories"
      subtitle="Source code repositories linked for continuous Reality Graph synchronization"
      accentGlow={repositories.length > 0 ? 'amber' : 'none'}
      badge={
        <span className="font-mono text-xs font-bold text-zinc-300 bg-zinc-900 border border-zinc-800 px-1.5 py-0.5 rounded">
          {repositories.length}
        </span>
      }
      action={
        <button
          onClick={onOpenConnectModal}
          className="inline-flex items-center gap-1.5 rounded-lg bg-amber-500 hover:bg-amber-600 px-3 py-1 font-mono text-[11px] font-extrabold uppercase tracking-wider text-black transition-colors"
        >
          <Plus className="h-3.5 w-3.5" />
          <span>Connect Repo</span>
        </button>
      }
    >
      {/* Search Filter when repos exist */}
      {repositories.length > 0 && (
        <div className="mb-4 flex items-center rounded-lg border border-[#232736] bg-zinc-900/60 px-3.5 py-2">
          <Search className="h-3.5 w-3.5 text-zinc-400 mr-2.5" />
          <input
            type="text"
            placeholder="Filter connected repositories..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full bg-transparent text-xs font-medium text-white placeholder-zinc-500 outline-none font-sans"
          />
        </div>
      )}

      {repositories.length === 0 ? (
        <EmptyState
          icon={GitBranch}
          title="No Repositories Connected"
          description="Connect your Git repositories to begin code parsing, API extraction, and Reality Graph generation."
          action={
            <button
              onClick={onOpenConnectModal}
              className="inline-flex items-center gap-2 rounded-lg bg-amber-500 hover:bg-amber-600 px-4 py-2 font-mono text-xs font-extrabold text-black uppercase tracking-wider transition-colors"
            >
              <Plus className="h-3.5 w-3.5" />
              <span>Connect First Repository</span>
            </button>
          }
        />
      ) : filtered.length === 0 ? (
        <div className="py-6 text-center font-mono text-xs font-bold text-zinc-400">
          No repositories matching &quot;{searchTerm}&quot;
        </div>
      ) : (
        <div className="space-y-3">
          {filtered.map((repo) => (
            <div
              key={repo.id}
              className="group flex flex-col sm:flex-row sm:items-center justify-between gap-3 rounded-lg bg-[#12151e]/92 backdrop-blur-md border border-[#232736] border-t border-t-zinc-700/50 p-4 transition-all duration-300 ease-out hover:-translate-y-1.5 hover:scale-[1.01] hover:border-amber-500/50 hover:border-t-zinc-400 hover:shadow-[0_16px_40px_0_rgba(0,0,0,0.8)] shadow-[0_8px_32px_0_rgba(0,0,0,0.6)] cursor-pointer"
            >
              <div className="space-y-1.5">
                <div className="flex items-center gap-2">
                  <span className="font-mono text-sm font-bold text-white group-hover:text-amber-400 transition-colors">
                    {repo.name}
                  </span>
                  <StatusBadge status={repo.status} size="sm" pulse={false} />
                  {repo.language && (
                    <span className="rounded border border-zinc-800 bg-zinc-800/60 px-2 py-0.5 text-[10px] text-zinc-300 font-mono font-medium">
                      {repo.language}
                    </span>
                  )}
                </div>
                <div className="flex items-center gap-2 font-mono text-xs text-zinc-400">
                  <span>Branch: <span className="text-zinc-200 font-semibold">{repo.default_branch}</span></span>
                  <span>•</span>
                  <a
                    href={repo.url}
                    target="_blank"
                    rel="noreferrer"
                    className="inline-flex items-center gap-1 hover:text-amber-400 transition-colors truncate max-w-[280px]"
                  >
                    <span>{repo.url}</span>
                    <ExternalLink className="h-2.5 w-2.5" />
                  </a>
                </div>
              </div>

              <div className="flex items-center gap-4 font-mono text-xs border-t border-zinc-800/80 sm:border-t-0 pt-2 sm:pt-0">
                <div className="flex items-center gap-1.5 text-zinc-400 font-medium">
                  <ShieldCheck className="h-3.5 w-3.5 text-zinc-400" />
                  <span><strong className="text-white font-bold">{repo.services_count}</strong> services</span>
                </div>
                <div className="flex items-center gap-1 text-zinc-400 font-medium">
                  <span
                    className={
                      repo.findings_count > 0 ? 'text-amber-400 font-bold' : 'text-zinc-500'
                    }
                  >
                    {repo.findings_count} findings
                  </span>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </GlassPanel>
  );
}
