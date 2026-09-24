'use client';

import React, { useEffect, useState, useCallback } from 'react';
import { GitBranch, RefreshCw, UploadCloud, Layers } from 'lucide-react';
import { PerspectiveGrid } from '@/components/ui/perspective-grid';
import { RealityGraphCanvas } from '@/components/graph/reality-graph-canvas';
import { EmptyState } from '@/components/ui/empty-state';
import { LoadingSkeleton } from '@/components/ui/loading-skeleton';
import {
  getGraph,
  getGraphStatistics,
  GraphNode,
  GraphEdge,
  GraphStatistics,
} from '@/lib/api';

export default function GraphPage() {
  const [loading, setLoading] = useState(true);
  const [nodes, setNodes] = useState<GraphNode[]>([]);
  const [edges, setEdges] = useState<GraphEdge[]>([]);
  const [statistics, setStatistics] = useState<GraphStatistics | null>(null);

  const fetchGraphData = useCallback(async () => {
    setLoading(true);
    try {
      const [graphRes, statsRes] = await Promise.allSettled([
        getGraph(),
        getGraphStatistics(),
      ]);

      if (graphRes.status === 'fulfilled') {
        setNodes(graphRes.value.nodes);
        setEdges(graphRes.value.edges);
      }
      if (statsRes.status === 'fulfilled') {
        setStatistics(statsRes.value);
      }
    } catch {
      // In offline testing mode, keep empty lists
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchGraphData();
  }, [fetchGraphData]);

  return (
    <div className="relative min-h-full space-y-4 pb-8">
      <PerspectiveGrid />

      {/* Control Bar Header */}
      <div className="relative z-10 flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-white/10 pb-5">
        <div className="flex items-center gap-3.5">
          <div className="flex h-11 w-11 items-center justify-center rounded-2xl border-2 border-orange-500/40 bg-orange-950/40 text-orange-400 shadow-[0_0_20px_rgba(249,115,22,0.3)]">
            <GitBranch className="h-5 w-5 drop-shadow-[0_0_8px_rgba(249,115,22,0.6)]" />
          </div>
          <div>
            <div className="flex items-center gap-2.5">
              <h1 className="text-2xl font-bold tracking-tight text-white font-sans drop-shadow-[0_2px_12px_rgba(0,0,0,0.8)]">
                Reality Graph
              </h1>
              <span className="font-mono text-[10px] font-bold uppercase tracking-wider text-orange-400 bg-orange-950/60 border border-orange-500/40 px-2 py-0.5 rounded shadow-[0_0_10px_rgba(249,115,22,0.25)]">
                TOPOLOGY MATRIX
              </span>
            </div>
            <p className="mt-1 font-mono text-sm font-bold text-zinc-200">
              Interactive structural ecosystem graph spanning services, APIs, databases, and deployments
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => fetchGraphData()}
            disabled={loading}
            className="inline-flex items-center gap-2 rounded-xl border border-orange-500/40 bg-zinc-900/60 px-4 py-2 font-mono text-xs font-bold text-white transition-all duration-300 ease-out hover:scale-[1.02] active:scale-[0.98] hover:border-orange-500 hover:shadow-[0_0_16px_rgba(249,115,22,0.3)] shadow-sm disabled:opacity-50"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${loading ? 'animate-spin text-orange-400' : ''}`} />
            <span>Sync Graph</span>
          </button>
        </div>
      </div>

      {/* Main Graph Content */}
      <div className="relative z-10">
        {loading && nodes.length === 0 ? (
          <div className="h-[600px] flex items-center justify-center">
            <LoadingSkeleton className="h-[550px] w-full" />
          </div>
        ) : nodes.length === 0 ? (
          <div className="py-16">
            <EmptyState
              icon={GitBranch}
              title="No nodes to display"
              description="No nodes to display. The Reality Graph will visualize your ecosystem topology. Ingest a repository to extract services, APIs, and schemas."
              action={
                <a
                  href="/dashboard"
                  className="inline-flex items-center gap-2 rounded-lg border border-accent-amber/60 bg-accent-amber/10 px-4 py-2 font-mono text-xs font-semibold uppercase tracking-wider text-accent-amber hover:bg-accent-amber/20 transition-all"
                >
                  <UploadCloud className="h-3.5 w-3.5" />
                  <span>Go to Command Center to Ingest</span>
                </a>
              }
            />
          </div>
        ) : (
          <RealityGraphCanvas
            initialNodes={nodes}
            initialEdges={edges}
            statistics={statistics}
          />
        )}
      </div>
    </div>
  );
}
