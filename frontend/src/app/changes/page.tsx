'use client';

import React, { useState } from 'react';
import {
  AlertTriangle,
  ArrowRight,
  Code2,
  Database,
  ExternalLink,
  FileCode,
  GitBranch,
  GitPullRequest,
  Layers,
  Play,
  RotateCcw,
  ShieldAlert,
  Zap,
} from 'lucide-react';
import Link from 'next/link';
import { GlassPanel } from '@/components/ui/glass-panel';
import { PerspectiveGrid } from '@/components/ui/perspective-grid';
import { StatTile } from '@/components/ui/stat-tile';
import {
  analyzeChangeImpact,
  ChangeImpactAnalysisResult,
} from '@/lib/api';

const PRESET_DIFFS = [
  {
    id: 'orders_logic',
    name: 'Modify Orders Logic',
    branch: 'feature/fast-orders',
    title: 'PR #104: Optimize order processing pipeline',
    diff: `diff --git a/services/orders/main.py b/services/orders/main.py
index 45a6102..78f3c91 100644
--- a/services/orders/main.py
+++ b/services/orders/main.py
@@ -24,4 +24,5 @@ def process_checkout(order_id: str):
-    validate_cart_v1(order_id)
+    validate_cart_v2(order_id)
+    emit_telemetry_event("checkout_started", order_id)
     return {"status": "processing"}
`,
  },
  {
    id: 'breaking_schema',
    name: 'Breaking Schema Migration',
    branch: 'fix/remove-legacy-cols',
    title: 'PR #108: Drop legacy customer columns from schema',
    diff: `diff --git a/schema/orders.sql b/schema/orders.sql
index 1122334..5566778 100644
--- a/schema/orders.sql
+++ b/schema/orders.sql
@@ -10,3 +10,2 @@ CREATE TABLE orders (
-    legacy_auth_token VARCHAR(255),
-    ALTER TABLE orders DROP COLUMN legacy_auth_token;
+    auth_token VARCHAR(512) NOT NULL,
`,
  },
  {
    id: 'delete_service',
    name: 'Retire Auth Service',
    branch: 'refactor/deprecate-v1-auth',
    title: 'PR #112: Delete legacy auth service',
    diff: `diff --git a/services/auth/Dockerfile b/services/auth/Dockerfile
deleted file mode 100644
index 89abcde..0000000
--- a/services/auth/Dockerfile
+++ /dev/null
@@ -1,6 +0,0 @@
-FROM python:3.11-slim
-EXPOSE 8080
-CMD ["python", "main.py"]
`,
  },
];

export default function ChangesPage() {
  const [title, setTitle] = useState(PRESET_DIFFS[0].title);
  const [branch, setBranch] = useState(PRESET_DIFFS[0].branch);
  const [diffText, setDiffText] = useState(PRESET_DIFFS[0].diff);
  const [analyzing, setAnalyzing] = useState(false);
  const [impactResult, setImpactResult] = useState<ChangeImpactAnalysisResult | null>(null);
  const [categoryFilter, setCategoryFilter] = useState('all');

  const handleSelectPreset = (preset: typeof PRESET_DIFFS[0]) => {
    setTitle(preset.title);
    setBranch(preset.branch);
    setDiffText(preset.diff);
    setImpactResult(null);
  };

  const handleAnalyze = async () => {
    if (!diffText.trim()) return;
    try {
      setAnalyzing(true);
      const result = await analyzeChangeImpact({
        title,
        git_diff: diffText,
        branch,
        author: 'developer@mirror-x.internal',
      });
      setImpactResult(result);
    } catch (err) {
      console.error('Impact analysis failed:', err);
    } finally {
      setAnalyzing(false);
    }
  };

  const filteredNodes = impactResult
    ? [...(impactResult.direct_nodes || []), ...(impactResult.indirect_nodes || [])].filter((n) => {
        if (categoryFilter === 'all') return true;
        return n.node_type.toLowerCase() === categoryFilter.toLowerCase();
      })
    : [];

  return (
    <div className="relative min-h-[calc(100vh-3.5rem)] overflow-hidden canvas-textured text-white p-6 space-y-6">
      <PerspectiveGrid />

      {/* Header */}
      <div className="relative z-10 flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-white/10 pb-5">
        <div className="flex items-center gap-3.5">
          <div className="flex h-11 w-11 items-center justify-center rounded-2xl border-2 border-orange-500/40 bg-orange-950/40 text-orange-400 shadow-[0_0_20px_rgba(249,115,22,0.3)]">
            <GitPullRequest className="h-5 w-5 drop-shadow-[0_0_8px_rgba(249,115,22,0.6)]" />
          </div>
          <div>
            <div className="flex items-center gap-2.5">
              <h1 className="text-2xl font-bold tracking-tight text-white font-sans drop-shadow-[0_2px_12px_rgba(0,0,0,0.8)]">
                Change Twin
              </h1>
              <span className="font-mono text-xs font-bold uppercase tracking-wider text-orange-400 bg-orange-950/60 border border-orange-500/40 px-2.5 py-0.5 rounded shadow-[0_0_10px_rgba(249,115,22,0.25)]">
                BLAST RADIUS CASCADE
              </span>
            </div>
            <p className="mt-1 font-mono text-sm font-semibold text-zinc-200">
              Dual-pane predictive impact simulation contrasting code diffs against reality graph topology
            </p>
          </div>
        </div>

        {/* Preset Selector & Action */}
        <div className="flex items-center gap-2.5 flex-wrap">
          <span className="font-mono text-xs uppercase text-orange-400 font-bold mr-1">Presets:</span>
          {PRESET_DIFFS.map((preset) => (
            <button
              key={preset.id}
              onClick={() => handleSelectPreset(preset)}
              className={`px-3 py-1.5 rounded-xl border font-mono text-xs font-bold transition-all duration-300 ease-out hover:scale-[1.02] active:scale-[0.98] backdrop-blur-2xl ${
                diffText === preset.diff
                  ? 'border-2 border-orange-500/60 bg-orange-950/60 text-white shadow-[0_0_12px_rgba(249,115,22,0.3)]'
                  : 'border border-white/10 bg-zinc-900/50 text-zinc-300 hover:border-orange-500/30 hover:text-white'
              }`}
            >
              {preset.name}
            </button>
          ))}
          <button
            onClick={handleAnalyze}
            disabled={analyzing || !diffText.trim()}
            className="inline-flex items-center gap-2 rounded-xl border-2 border-orange-500/50 bg-gradient-to-r from-orange-950/70 via-zinc-900/90 to-orange-950/70 px-4 py-2 font-mono text-xs font-bold uppercase tracking-wider text-orange-400 transition-all duration-300 ease-out hover:scale-[1.02] active:scale-[0.98] hover:border-orange-400 hover:shadow-[0_0_20px_rgba(249,115,22,0.4)] shadow-lg disabled:opacity-50 ml-2"
          >
            {analyzing ? (
              <>
                <RotateCcw className="h-3.5 w-3.5 animate-spin text-orange-400" />
                <span>Simulating...</span>
              </>
            ) : (
              <>
                <Play className="h-3.5 w-3.5 fill-current" />
                <span>Simulate Blast Radius</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* Main Dual-Pane Layout */}
      <div className="relative z-10 grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* LEFT PANE: Proposed Change (Git Diff) */}
        <div className="lg:col-span-6 space-y-4">
          <GlassPanel className="p-5 space-y-4">
            <div className="flex items-center justify-between border-b border-white/10 pb-3">
              <div className="flex items-center gap-2">
                <FileCode className="h-4 w-4 text-orange-400" />
                <h3 className="font-mono text-xs font-bold uppercase tracking-wider text-white">
                  Proposed Git Change
                </h3>
              </div>
              <span className="font-mono text-xs font-bold text-orange-400">UNIFIED DIFF</span>
            </div>

            {/* Change Metadata Inputs */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div>
                <label className="block font-mono text-xs uppercase font-bold text-zinc-300 mb-1">
                  Change / PR Title
                </label>
                <input
                  type="text"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  className="w-full rounded-xl border-2 border-orange-500/30 bg-zinc-950/90 px-3.5 py-2 font-mono text-xs font-bold text-white placeholder-zinc-500 focus:border-orange-500/60 focus:outline-none"
                  placeholder="e.g. PR #102: Migrate auth routes"
                />
              </div>

              <div>
                <label className="block font-mono text-xs uppercase font-bold text-zinc-300 mb-1">
                  Target Branch
                </label>
                <div className="flex items-center gap-2 rounded-xl border-2 border-orange-500/30 bg-zinc-950/90 px-3.5 py-2">
                  <GitBranch className="h-3.5 w-3.5 text-orange-400" />
                  <input
                    type="text"
                    value={branch}
                    onChange={(e) => setBranch(e.target.value)}
                    className="w-full bg-transparent font-mono text-xs font-bold text-white placeholder-zinc-500 focus:outline-none"
                    placeholder="main"
                  />
                </div>
              </div>
            </div>

            {/* Diff Editor / Viewer */}
            <div>
              <label className="block font-mono text-xs uppercase text-zinc-300 mb-2 flex items-center justify-between font-bold">
                <span>Git Unified Diff</span>
                <span className="text-xs font-bold text-orange-400">Standard unified format</span>
              </label>

              <textarea
                value={diffText}
                onChange={(e) => setDiffText(e.target.value)}
                rows={14}
                className="w-full rounded-xl border-2 border-orange-500/30 bg-black/90 p-4 font-mono text-xs font-bold text-orange-200/90 focus:border-orange-500/60 focus:outline-none leading-relaxed resize-y scrollbar-thin backdrop-blur-2xl shadow-inner"
                placeholder="diff --git a/... b/..."
              />
            </div>
          </GlassPanel>
        </div>

        {/* RIGHT PANE: Impact Analysis & Blast Radius */}
        <div className="lg:col-span-6 space-y-4">
          {!impactResult ? (
            <GlassPanel className="py-24 text-center">
              <div className="flex flex-col items-center justify-center p-6">
                <div className="flex h-12 w-12 items-center justify-center rounded-xl border-2 border-orange-500/40 bg-orange-950/40 text-orange-400 mb-3 shadow-[0_0_15px_rgba(249,115,22,0.3)]">
                  <Zap className="h-6 w-6 stroke-[1.5]" />
                </div>
                <h4 className="font-mono text-sm font-bold uppercase tracking-wider text-zinc-200">
                  Awaiting Impact Simulation
                </h4>
                <p className="mt-1.5 max-w-sm text-sm font-medium text-zinc-300 font-sans leading-relaxed">
                  Provide a unified Git diff in the left pane and click &quot;Simulate Blast Radius&quot; to calculate direct entity impacts and indirect graph propagation cascades.
                </p>
                <div className="mt-4">
                  <button
                    onClick={handleAnalyze}
                    className="inline-flex items-center gap-2 rounded-xl border-2 border-orange-500/50 bg-orange-950/60 px-4 py-2 font-mono text-xs font-bold uppercase tracking-wider text-orange-400 hover:bg-orange-900/60 transition-all shadow-[0_0_15px_rgba(249,115,22,0.25)]"
                  >
                    <Play className="h-3 w-3 fill-current" />
                    <span>Run Simulation</span>
                  </button>
                </div>
              </div>
            </GlassPanel>
          ) : (
            <div className="space-y-4 animate-fade-in">
              {/* Blast Radius KPI Ribbon */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                <StatTile
                  label="Risk Rating"
                  value={impactResult.risk_level.toUpperCase()}
                  subvalue={`score: ${impactResult.risk_score}/100`}
                  accent={
                    impactResult.risk_level === 'critical'
                      ? 'crimson'
                      : impactResult.risk_level === 'high'
                      ? 'amber'
                      : 'orange'
                  }
                  icon={ShieldAlert}
                />
                <StatTile
                  label="Direct Nodes"
                  value={impactResult.direct_impact_count}
                  subvalue="modified entities"
                  accent="orange"
                  icon={Code2}
                />
                <StatTile
                  label="Indirect Nodes"
                  value={impactResult.indirect_impact_count}
                  subvalue="cascade dependents"
                  accent="amber"
                  icon={Layers}
                />
                <StatTile
                  label="Total Blast"
                  value={impactResult.total_impacted_nodes}
                  subvalue="ecosystem entities"
                  accent="crimson"
                  icon={Zap}
                />
              </div>

              {/* Breaking Changes Warnings */}
              {impactResult.breaking_changes && impactResult.breaking_changes.length > 0 && (
                <div className="rounded-2xl border-2 border-rose-500/40 border-t-2 border-white/25 bg-rose-950/30 p-4 space-y-3 shadow-[0_12px_32px_rgba(0,0,0,0.8)] backdrop-blur-3xl">
                  <div className="flex items-center gap-2 font-mono text-xs uppercase font-bold text-rose-400">
                    <AlertTriangle className="h-4 w-4 drop-shadow-[0_0_8px_rgba(244,63,94,0.4)]" />
                    <span>Breaking Changes Detected ({impactResult.breaking_changes.length})</span>
                  </div>
                  {impactResult.breaking_changes.map((bc, idx) => (
                    <div
                      key={idx}
                      className="rounded-xl border border-rose-500/30 bg-black/60 p-3.5 space-y-1.5 font-mono text-xs"
                    >
                      <div className="flex items-center justify-between text-white font-bold">
                        <span>{bc.title}</span>
                        <span className="text-[10px] text-rose-400 font-bold uppercase bg-rose-950/70 border border-rose-500/40 px-2 py-0.5 rounded shadow-[0_0_8px_rgba(244,63,94,0.3)]">
                          {bc.severity}
                        </span>
                      </div>
                      <p className="text-zinc-200 font-sans text-xs font-medium">{bc.description}</p>
                      {bc.impacted_nodes.length > 0 && (
                        <div className="pt-1 text-xs font-bold text-zinc-300">
                          Downstream affected:{' '}
                          <span className="text-orange-400">{bc.impacted_nodes.join(', ')}</span>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}

              {/* Impacted Nodes Explorer */}
              <GlassPanel className="p-4 space-y-3">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-white/10 pb-2.5">
                  <div className="flex items-center gap-2">
                    <Database className="h-4 w-4 text-orange-400" />
                    <h4 className="font-mono text-xs font-bold uppercase tracking-wider text-white">
                      Impacted Topology Entities ({filteredNodes.length})
                    </h4>
                  </div>

                  {/* Category Filter Pills */}
                  <div className="flex items-center gap-1.5 overflow-x-auto pb-1">
                    {['all', 'service', 'database', 'table', 'api', 'infrastructure', 'documentation'].map(
                      (cat) => (
                        <button
                          key={cat}
                          onClick={() => setCategoryFilter(cat)}
                          className={`px-2.5 py-1 rounded-xl font-mono text-xs font-bold uppercase tracking-wider transition-all duration-300 ease-out hover:scale-[1.02] active:scale-[0.98] ${
                            categoryFilter === cat
                              ? 'bg-orange-950/60 text-white font-bold border border-orange-500/50 shadow-[0_0_8px_rgba(249,115,22,0.25)]'
                              : 'bg-zinc-900/60 text-zinc-400 hover:text-white border border-white/5'
                          }`}
                        >
                          {cat}
                        </button>
                      )
                    )}
                  </div>
                </div>

                {/* Nodes List */}
                <div className="space-y-2.5 max-h-[460px] overflow-y-auto pr-1 scrollbar-thin">
                  {filteredNodes.length === 0 ? (
                    <div className="py-8 text-center font-mono text-xs font-bold text-zinc-400">
                      No entities in this category are impacted by the change.
                    </div>
                  ) : (
                    filteredNodes.map((n) => {
                      const isDirect = n.depth === undefined || n.depth === 0;
                      return (
                        <div
                          key={n.node_id}
                          className={`rounded-2xl border-2 border-t-2 p-3.5 backdrop-blur-3xl transition-all duration-300 ease-out hover:scale-[1.005] shadow-[0_12px_32px_rgba(0,0,0,0.8)] ${
                            isDirect
                              ? 'border-orange-500/40 border-t-orange-400/60 bg-zinc-950/90 shadow-[0_4px_20px_rgba(249,115,22,0.1)]'
                              : 'border-white/10 border-t-white/20 bg-zinc-950/80'
                          }`}
                        >
                          <div className="flex items-center justify-between gap-2">
                            <div className="flex items-center gap-2">
                              <span
                                className={`font-mono text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full border ${
                                  isDirect
                                    ? 'bg-orange-950/60 text-orange-400 border-orange-500/50 shadow-[0_0_8px_rgba(249,115,22,0.25)]'
                                    : 'bg-zinc-900/80 text-zinc-300 border-white/10'
                                }`}
                              >
                                {isDirect ? 'DIRECT' : `INDIRECT (DEPTH ${n.depth || 1})`}
                              </span>
                              <span className="font-mono text-xs font-bold text-white">
                                {n.name}
                              </span>
                              <span className="font-mono text-xs font-bold text-orange-400 uppercase bg-black/60 border border-orange-500/30 px-2 py-0.5 rounded-lg">
                                {n.node_type}
                              </span>
                            </div>

                            <Link
                              href="/graph"
                              className="text-zinc-400 hover:text-orange-400 transition-colors"
                              title="Inspect in Reality Graph"
                            >
                              <ExternalLink className="h-3.5 w-3.5" />
                            </Link>
                          </div>

                          <div className="mt-2 text-xs font-medium text-zinc-200 font-sans">
                            {n.reason}
                          </div>

                          {n.propagation_path && n.propagation_path.length > 0 && (() => {
                            const path = n.propagation_path;
                            return (
                              <div className="mt-2.5 flex items-center gap-1.5 font-mono text-xs text-zinc-300 overflow-x-auto bg-black/60 p-2.5 rounded-xl border border-white/10">
                                <span className="text-orange-400 font-bold uppercase tracking-wider">Cascade:</span>
                                {path.map((step, idx) => (
                                  <React.Fragment key={idx}>
                                    <span
                                      className={
                                        step.startsWith('(') ? 'text-orange-400 font-bold drop-shadow-[0_0_6px_rgba(249,115,22,0.4)]' : 'text-zinc-200'
                                      }
                                    >
                                      {step}
                                    </span>
                                    {idx < path.length - 1 && (
                                      <ArrowRight className="h-2.5 w-2.5 text-zinc-600 shrink-0" />
                                    )}
                                  </React.Fragment>
                                ))}
                              </div>
                            );
                          })()}
                        </div>
                      );
                    })
                  )}
                </div>
              </GlassPanel>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
