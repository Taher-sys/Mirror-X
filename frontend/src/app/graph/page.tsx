'use client';

import React, { useEffect, useState, useCallback } from 'react';
import { GitBranch, RefreshCw, UploadCloud } from 'lucide-react';
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
      // Keep empty lists in offline mode
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchGraphData();
  }, [fetchGraphData]);

  return (
    <div className="relative min-h-[calc(100vh-3.5rem)] overflow-hidden bg-transparent text-white p-6 space-y-6">
      <PerspectiveGrid />

      {/* Control Bar Header */}
      <div className="relative z-10 flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-zinc-800 pb-5">
        <div className="flex items-center gap-3.5">
          <div className="flex h-11 w-11 items-center justify-center rounded-xl border border-zinc-800 bg-zinc-900/80 text-amber-500">
            <GitBranch className="h-5 w-5" />
          </div>
          <div>
            <div className="flex items-center gap-2.5">
              <h1 className="text-2xl font-bold tracking-tight text-white font-sans drop-shadow-[0_2px_12px_rgba(0,0,0,0.8)]">
                Reality Graph
              </h1>
              <span className="font-mono text-xs font-bold uppercase tracking-wider text-amber-500 bg-zinc-900/80 border border-zinc-800 px-2.5 py-0.5 rounded">
                TOPOLOGY MATRIX
              </span>
            </div>
            <p className="mt-1 font-mono text-sm font-semibold text-zinc-300">
              Interactive structural ecosystem graph spanning services, APIs, databases, and deployments
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => fetchGraphData()}
            disabled={loading}
            className="inline-flex items-center gap-2 rounded-lg bg-amber-500 hover:bg-amber-600 px-4 py-2 font-mono text-xs font-extrabold uppercase tracking-wider text-black transition-all shadow-md active:scale-95 disabled:opacity-50"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${loading ? 'animate-spin text-black' : ''}`} />
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
                  className="inline-flex items-center gap-2 rounded-lg bg-amber-500 hover:bg-amber-600 px-5 py-2.5 font-mono text-xs font-extrabold uppercase tracking-wider text-black transition-all shadow-md active:scale-95"
                >
                  <UploadCloud className="h-4 w-4" />
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
