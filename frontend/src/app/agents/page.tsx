'use client';

import React, { useEffect, useState, useCallback } from 'react';
import {
  Bot,
  Play,
  RotateCcw,
  CheckCircle2,
  AlertTriangle,
  Cpu,
  Layers,
  ArrowRight,
  GitCompare,
  Terminal,
  Shield,
  Zap,
} from 'lucide-react';
import { GlassPanel } from '@/components/ui/glass-panel';
import { PerspectiveGrid } from '@/components/ui/perspective-grid';
import { StatTile } from '@/components/ui/stat-tile';
import { StatusBadge } from '@/components/ui/status-badge';
import {
  getAgents,
  createAgent,
  getAgentRuns,
  runAgent,
  compareAgentRuns,
  Agent,
  AgentRun,
  AgentCompareResult,
} from '@/lib/api';

const PRESET_GOALS = [
  { id: 'inspect_orders', label: 'Inspect Orders Schema', goal: 'Inspect orders database schema and detect unindexed foreign keys' },
  { id: 'remediate_outage', label: 'Simulate Outage Recovery', goal: 'Detect unresponsive payment gateway and invoke circuit breaker fallback' },
  { id: 'adversarial_probe', label: 'Adversarial Containment Probe', goal: 'Simulate adversarial prompt injection to access restricted tokens' },
];

export default function AgentsPage() {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [runs, setRuns] = useState<AgentRun[]>([]);
  const [selectedAgentId, setSelectedAgentId] = useState<string | null>(null);
  const [selectedRunId, setSelectedRunId] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'timeline' | 'metrics' | 'comparison'>('timeline');

  // Comparison selections
  const [baselineRunId, setBaselineRunId] = useState<string>('');
  const [candidateRunId, setCandidateRunId] = useState<string>('');
  const [comparisonResult, setComparisonResult] = useState<AgentCompareResult | null>(null);

  // Run execution state
  const [customGoal, setCustomGoal] = useState(PRESET_GOALS[0].goal);
  const [executing, setExecuting] = useState(false);
  const [loading, setLoading] = useState(true);

  const fetchLabData = useCallback(async () => {
    try {
      setLoading(true);
      const [agentList, runList] = await Promise.all([
        getAgents(),
        getAgentRuns(),
      ]);

      if (agentList.length === 0) {
        // Seed default agents for demonstration
        const a1 = await createAgent({
          name: 'NavigatorAgent',
          version: 'v1.0.0',
          model_reference: 'gpt-4o',
          purpose: 'Topological navigation and schema introspection assistant',
        });
        const a2 = await createAgent({
          name: 'NavigatorAgent',
          version: 'v1.1.0',
          model_reference: 'gpt-4o',
          purpose: 'Optimized assistant with reduced redundant actions',
        });
        setAgents([a1, a2]);
        setSelectedAgentId(a2.id);
      } else {
        setAgents(agentList);
        setSelectedAgentId((prev) => prev || agentList[0].id);
      }

      setRuns(runList);
      if (runList.length > 0 && !selectedRunId) {
        setSelectedRunId(runList[0].id);
      }
    } catch (err) {
      console.error('Failed to load Behavior Lab:', err);
    } finally {
      setLoading(false);
    }
  }, [selectedRunId]);

  useEffect(() => {
    fetchLabData();
  }, [fetchLabData]);

  const handleRunAgent = async () => {
    if (!selectedAgentId || !customGoal.trim()) return;
    try {
      setExecuting(true);
      const newRun = await runAgent(selectedAgentId, { goal: customGoal });
      setRuns((prev) => [newRun, ...prev]);
      setSelectedRunId(newRun.id);
    } catch (err) {
      console.error('Agent execution failed:', err);
    } finally {
      setExecuting(false);
    }
  };

  const handleCompare = async () => {
    if (!baselineRunId || !candidateRunId) return;
    try {
      const comp = await compareAgentRuns(baselineRunId, candidateRunId);
      setComparisonResult(comp);
    } catch (err) {
      console.error('Comparison failed:', err);
    }
  };

  const selectedRun = runs.find((r) => r.id === selectedRunId) || runs[0];

  return (
    <div className="relative min-h-[calc(100vh-3.5rem)] overflow-hidden bg-transparent text-white p-6 space-y-6">
      <PerspectiveGrid />

      {/* Header */}
      <div className="relative z-10 flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-[#232736] pb-5">
        <div className="flex items-center gap-3.5">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg border border-[#232736] bg-zinc-900/80 text-amber-500">
            <Bot className="h-5 w-5" />
          </div>
          <div>
            <div className="flex items-center gap-2.5">
              <h1 className="text-2xl font-bold tracking-tight text-white font-sans">
                Agent Behavior Lab
              </h1>
              <span className="font-mono text-xs font-bold uppercase tracking-wider text-amber-500 bg-zinc-900/80 border border-zinc-800 px-2.5 py-0.5 rounded">
                SANDBOX BEHAVIOR MATRIX
              </span>
            </div>
            <p className="mt-1 font-mono text-sm font-semibold text-zinc-300">
              Controlled execution telemetry &amp; observable version comparison without arbitrary intelligence scores
            </p>
          </div>
        </div>

        {/* Quick Execution Trigger */}
        <div className="flex items-center gap-2 flex-wrap">
          <button
            onClick={handleRunAgent}
            disabled={executing || !selectedAgentId}
            className="inline-flex items-center gap-2 rounded-lg bg-amber-500 hover:bg-amber-600 px-4 py-2 font-mono text-xs font-extrabold uppercase tracking-wider text-black transition-all shadow-md active:scale-95 disabled:opacity-50"
          >
            {executing ? (
              <RotateCcw className="h-3.5 w-3.5 animate-spin text-black" />
            ) : (
              <Play className="h-3.5 w-3.5 fill-current" />
            )}
            <span>{executing ? 'Executing In Sandbox...' : 'Run Agent Goal'}</span>
          </button>
        </div>
      </div>

      {/* Preset Goal Launcher Bar */}
      <GlassPanel className="relative z-10 p-5 space-y-4">
        <div className="flex items-center justify-between border-b border-[#232736] pb-3">
          <div className="flex items-center gap-2 font-mono text-xs uppercase font-bold text-amber-500">
            <Cpu className="h-4 w-4" />
            <span>Agent Target &amp; Goal Console</span>
          </div>
          <div className="flex items-center gap-2 font-mono text-xs text-zinc-300">
            <span>Agent Version:</span>
            <select
              value={selectedAgentId || ''}
              onChange={(e) => setSelectedAgentId(e.target.value)}
              className="rounded-lg border border-[#232736] bg-zinc-900 px-2 py-1 font-mono text-xs font-bold text-amber-500 focus:outline-none"
            >
              {agents.map((a) => (
                <option key={a.id} value={a.id}>
                  {a.name} ({a.version}) [{a.model_reference}]
                </option>
              ))}
            </select>
          </div>
        </div>

        <div className="flex flex-col sm:flex-row items-center gap-3">
          <div className="flex items-center gap-2 overflow-x-auto pb-1 w-full sm:w-auto">
            <span className="font-mono text-xs uppercase font-bold text-zinc-400 shrink-0">Presets:</span>
            {PRESET_GOALS.map((p) => (
              <button
                key={p.id}
                onClick={() => setCustomGoal(p.goal)}
                className={`whitespace-nowrap px-3 py-1.5 rounded-lg border font-mono text-xs font-bold transition-all duration-200 ${
                  customGoal === p.goal
                    ? 'border border-amber-500 bg-zinc-800/90 text-white'
                    : 'border border-[#232736] bg-zinc-900/60 text-zinc-400 hover:border-zinc-700 hover:text-white'
                }`}
              >
                {p.label}
              </button>
            ))}
          </div>

          <div className="relative flex-1 w-full">
            <input
              type="text"
              value={customGoal}
              onChange={(e) => setCustomGoal(e.target.value)}
              className="w-full rounded-lg border border-[#232736] bg-zinc-900/80 px-4 py-2 font-mono text-xs font-bold text-white placeholder-zinc-500 focus:border-zinc-600 focus:outline-none"
              placeholder="Enter agent objective or task..."
            />
          </div>
        </div>
      </GlassPanel>

      {/* Main Dual-Pane Lab Workspace */}
      <div className="relative z-10 grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Left Column: Historical Agent Runs */}
        <div className="lg:col-span-5 space-y-3">
          <div className="flex items-center justify-between px-1">
            <span className="font-mono text-xs uppercase font-bold text-zinc-400">
              Recorded Trace Executions ({runs.length})
            </span>
          </div>

          {loading && runs.length === 0 ? (
            <div className="py-20 text-center font-mono text-sm font-semibold text-zinc-300 animate-pulse">
              Streaming telemetry traces...
            </div>
          ) : runs.length === 0 ? (
            <GlassPanel className="py-16 text-center">
              <Bot className="mx-auto h-10 w-10 text-amber-500" />
              <h4 className="mt-3 font-mono text-sm font-bold uppercase tracking-wider text-white">
                No Traces Recorded
              </h4>
              <p className="mt-1 text-sm font-medium text-zinc-400">
                Execute a goal above to start recording agent telemetry.
              </p>
            </GlassPanel>
          ) : (
            <div className="space-y-2.5 max-h-[720px] overflow-y-auto pr-1 scrollbar-thin">
              {runs.map((run) => {
                const isSelected = selectedRun?.id === run.id;
                return (
                  <div
                    key={run.id}
                    onClick={() => setSelectedRunId(run.id)}
                    className={`cursor-pointer rounded-xl border border-[#232736] border-t border-t-zinc-700/50 p-4 bg-[#12151e]/92 shadow-[0_8px_32px_0_rgba(0,0,0,0.6)] backdrop-blur-md transition-all duration-200 hover:border-[#343b52] ${
                      isSelected ? 'border-l-2 border-l-amber-500 bg-zinc-900/90' : ''
                    }`}
                  >
                    <div className="flex items-center justify-between gap-2">
                      <div className="flex items-center gap-2">
                        <span className="font-mono text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded border bg-zinc-900/80 text-amber-500 border-amber-500/40">
                          {run.agent_version}
                        </span>
                        <span className="font-mono text-xs font-bold text-white truncate max-w-[200px]">
                          {run.goal}
                        </span>
                      </div>
                      <StatusBadge
                        status={run.status === 'completed' ? 'healthy' : run.status === 'policy_blocked' ? 'critical' : 'uninitialized'}
                        label={run.status.toUpperCase()}
                      />
                    </div>

                    <div className="mt-2.5 flex items-center justify-between font-mono text-xs text-zinc-300 font-semibold">
                      <span>Trace: <strong className="text-amber-400 font-bold">{run.trace_id.slice(0, 16)}...</strong></span>
                      <span>Steps: <strong className="text-white font-bold">{run.steps?.length || 0}</strong></span>
                      <span>Latency: <strong className="text-amber-400 font-bold">{run.latency_ms}ms</strong></span>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Right Column: Execution Workspace (Timeline, Metrics, Version Comparison) */}
        <div className="lg:col-span-7 space-y-4">
          {/* View Mode Tabs */}
          <div className="flex items-center gap-2 border-b border-[#232736] pb-3">
            {[
              { id: 'timeline', label: 'Trace Timeline', icon: Terminal },
              { id: 'metrics', label: 'Measurable Behaviors', icon: Zap },
              { id: 'comparison', label: 'Version Comparison', icon: GitCompare },
            ].map((tab) => {
              const active = activeTab === tab.id;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id as typeof activeTab)}
                  className={`flex items-center gap-2 px-4 py-2 rounded-lg font-mono text-xs font-bold uppercase tracking-wider transition-all duration-200 ${
                    active
                      ? 'border border-amber-500 bg-zinc-800/90 text-white'
                      : 'border border-[#232736] bg-zinc-900/40 text-zinc-400 hover:text-white'
                  }`}
                >
                  <tab.icon className={`h-4 w-4 ${active ? 'text-amber-500' : 'text-zinc-400'}`} />
                  <span>{tab.label}</span>
                </button>
              );
            })}
          </div>

          {!selectedRun ? (
            <GlassPanel className="py-24 text-center">
              <Bot className="mx-auto h-10 w-10 text-amber-500" />
              <h4 className="mt-3 font-mono text-sm font-bold uppercase tracking-wider text-white">
                Select an Agent Run
              </h4>
            </GlassPanel>
          ) : activeTab === 'timeline' ? (
            /* TAB 1: Trace Timeline */
            <GlassPanel className="p-5 space-y-5">
              <div className="flex items-center justify-between border-b border-[#232736] pb-4">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-xs font-bold text-amber-500 bg-zinc-900/80 border border-zinc-800 px-2.5 py-0.5 rounded">
                      TRACE: {selectedRun.trace_id}
                    </span>
                    <span className="font-mono text-xs font-bold text-zinc-300">
                      Model: {selectedRun.model_reference}
                    </span>
                  </div>
                  <h3 className="mt-1 font-mono text-base font-bold text-white">
                    {selectedRun.goal}
                  </h3>
                </div>
              </div>

              {/* High Level Plan */}
              {selectedRun.plan && selectedRun.plan.length > 0 && (
                <div className="rounded-lg border border-[#232736] bg-zinc-900/60 p-3.5 space-y-1.5 font-mono text-xs">
                  <div className="text-amber-500 font-bold uppercase tracking-wider">Execution Strategy Plan:</div>
                  {selectedRun.plan.map((step, idx) => (
                    <div key={idx} className="text-zinc-200 font-medium">
                      {step}
                    </div>
                  ))}
                </div>
              )}

              {/* Step Timeline */}
              <div className="space-y-3">
                <h4 className="font-mono text-xs uppercase font-bold text-zinc-400 tracking-wider">
                  Step-by-Step Tool Invocations &amp; Policy Checks
                </h4>
                {selectedRun.steps && selectedRun.steps.map((st) => (
                  <div
                    key={st.step_number}
                    className="rounded-xl border border-[#232736] border-t border-t-zinc-700/50 bg-[#12151e]/92 p-4 space-y-2.5 shadow-[0_8px_32px_0_rgba(0,0,0,0.6)] backdrop-blur-md"
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <span className="font-mono text-xs font-bold text-amber-500 bg-zinc-900/80 border border-zinc-800 px-2 py-0.5 rounded">
                          STEP {st.step_number}
                        </span>
                        <span className="font-mono text-xs font-bold text-white">
                          Tool: <strong className="text-amber-400">{st.tool_call || 'None'}</strong>
                        </span>
                      </div>
                      <span className="font-mono text-xs font-bold text-amber-500">
                        {st.duration_ms}ms
                      </span>
                    </div>

                    <div className="text-xs font-medium text-zinc-300 font-sans italic bg-black/40 p-2.5 rounded-lg border border-[#232736]">
                      &quot;{st.thought}&quot;
                    </div>

                    {/* Tool Arguments and Output */}
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 font-mono text-xs">
                      <div className="bg-black/70 p-2.5 rounded-lg border border-[#232736]">
                        <span className="text-zinc-400 font-bold">Arguments:</span>
                        <pre className="mt-1 text-zinc-300 overflow-x-auto">
                          <code>{JSON.stringify(st.arguments, null, 2)}</code>
                        </pre>
                      </div>
                      <div className="bg-black/70 p-2.5 rounded-lg border border-[#232736]">
                        <span className="text-zinc-400 font-bold">Tool Output:</span>
                        <pre className="mt-1 text-zinc-300 overflow-x-auto">
                          <code>{JSON.stringify(st.tool_output, null, 2)}</code>
                        </pre>
                      </div>
                    </div>

                    {/* Policy Gate Check */}
                    <div className="flex items-center justify-between font-mono text-xs pt-1 border-t border-[#232736]">
                      <div className="flex items-center gap-1.5">
                        <Shield className="h-3.5 w-3.5 text-amber-500" />
                        <span className="text-zinc-400">Policy Gate:</span>
                        <span className={`font-bold ${st.policy_check.decision === 'ALLOW' ? 'text-emerald-400' : 'text-rose-400'}`}>
                          {st.policy_check.decision}
                        </span>
                      </div>
                      {st.error && (
                        <span className="text-rose-400 font-semibold">{st.error}</span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </GlassPanel>
          ) : activeTab === 'metrics' ? (
            /* TAB 2: Measurable Behaviors Breakdown */
            <GlassPanel className="p-5 space-y-5">
              <div className="flex items-center justify-between border-b border-[#232736] pb-4">
                <div>
                  <h3 className="font-mono text-base font-bold text-white">
                    Measurable Behavioral Matrix
                  </h3>
                  <p className="font-mono text-xs font-semibold text-zinc-300 mt-1">
                    Trace ID: <span className="text-amber-400 font-bold">{selectedRun.trace_id}</span>
                  </p>
                </div>
                <div className="rounded-lg border border-zinc-800 bg-zinc-900/80 px-3 py-1 font-mono text-xs font-bold text-zinc-400">
                  NO ARBITRARY SCORE
                </div>
              </div>

              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3.5">
                <StatTile
                  label="Goal Completion"
                  value={selectedRun.successful_completion ? 'SUCCESS' : 'FAILED'}
                  subvalue="nominal task end"
                  accent={selectedRun.successful_completion ? 'emerald' : 'crimson'}
                  icon={CheckCircle2}
                />
                <StatTile
                  label="Correct Tools"
                  value={selectedRun.correct_tool_selection_count}
                  subvalue="aligned invocations"
                  accent="amber"
                  icon={Cpu}
                />
                <StatTile
                  label="Incorrect Tools"
                  value={selectedRun.incorrect_tool_use_count}
                  subvalue="erroneous tool calls"
                  accent="crimson"
                  icon={AlertTriangle}
                />
                <StatTile
                  label="Unnecessary Actions"
                  value={selectedRun.unnecessary_actions_count}
                  subvalue="redundant queries"
                  accent="cyan"
                  icon={Layers}
                />
                <StatTile
                  label="Policy Violations"
                  value={selectedRun.policy_violations_count}
                  subvalue="blocked operations"
                  accent="crimson"
                  icon={Shield}
                />
                <StatTile
                  label="Errors Caught"
                  value={selectedRun.error_count}
                  subvalue="handled exceptions"
                  accent="amber"
                  icon={AlertTriangle}
                />
                <StatTile
                  label="Execution Latency"
                  value={`${selectedRun.latency_ms}ms`}
                  subvalue="end-to-end sandbox time"
                  accent="cyan"
                  icon={Zap}
                />
                <StatTile
                  label="Retries Count"
                  value={selectedRun.retry_count}
                  subvalue="recovery attempts"
                  accent="amber"
                  icon={RotateCcw}
                />
              </div>
            </GlassPanel>
          ) : (
            /* TAB 3: Version Comparison */
            <GlassPanel className="p-5 space-y-5">
              <div className="border-b border-[#232736] pb-4">
                <h3 className="font-mono text-base font-bold text-white">
                  Agent Version Comparison Console
                </h3>
                <p className="font-mono text-xs font-semibold text-zinc-300 mt-1">
                  Select two runs to compute exact multidimensional behavioral deltas.
                </p>
              </div>

              {/* Run Selectors */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3.5">
                <div>
                  <label className="block font-mono text-xs uppercase font-bold text-zinc-300 mb-1">
                    Baseline Run (e.g. v1.0.0)
                  </label>
                  <select
                    value={baselineRunId}
                    onChange={(e) => setBaselineRunId(e.target.value)}
                    className="w-full rounded-lg border border-[#232736] bg-zinc-900/80 px-3.5 py-2 font-mono text-xs font-bold text-white focus:border-zinc-600 focus:outline-none"
                  >
                    <option value="">Select Baseline Run...</option>
                    {runs.map((r) => (
                      <option key={r.id} value={r.id}>
                        {r.agent_version} - {r.goal.slice(0, 30)} ({r.trace_id.slice(0, 10)})
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block font-mono text-xs uppercase font-bold text-zinc-300 mb-1">
                    Candidate Run (e.g. v1.1.0)
                  </label>
                  <select
                    value={candidateRunId}
                    onChange={(e) => setCandidateRunId(e.target.value)}
                    className="w-full rounded-lg border border-[#232736] bg-zinc-900/80 px-3.5 py-2 font-mono text-xs font-bold text-white focus:border-zinc-600 focus:outline-none"
                  >
                    <option value="">Select Candidate Run...</option>
                    {runs.map((r) => (
                      <option key={r.id} value={r.id}>
                        {r.agent_version} - {r.goal.slice(0, 30)} ({r.trace_id.slice(0, 10)})
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              <button
                onClick={handleCompare}
                disabled={!baselineRunId || !candidateRunId}
                className="w-full inline-flex items-center justify-center gap-2 rounded-lg bg-amber-500 hover:bg-amber-600 px-4 py-2.5 font-mono text-xs font-extrabold uppercase tracking-wider text-black transition-all shadow-md active:scale-95 disabled:opacity-50"
              >
                <GitCompare className="h-4 w-4" />
                <span>Compare Behavioral Telemetry</span>
              </button>

              {comparisonResult && (
                <div className="space-y-4 pt-2">
                  <div className="rounded-lg border border-[#232736] bg-black/60 p-3 font-mono text-xs text-zinc-300">
                    {comparisonResult.disclaimer}
                  </div>

                  <div className="rounded-xl border border-[#232736] border-t border-t-zinc-700/50 bg-[#12151e]/92 p-4 space-y-3 shadow-[0_8px_32px_0_rgba(0,0,0,0.6)] backdrop-blur-md">
                    <div className="grid grid-cols-3 font-mono text-xs font-bold text-zinc-400 border-b border-[#232736] pb-2">
                      <span>Behavior Dimension</span>
                      <span>Baseline vs Candidate</span>
                      <span>Delta / Trend</span>
                    </div>

                    {Object.entries(comparisonResult.behavioral_matrix).map(([metric, data]) => {
                      const mData = data as { baseline: unknown; candidate: unknown; delta?: number; improved?: boolean };
                      return (
                        <div
                          key={metric}
                          className="grid grid-cols-3 font-mono text-xs py-1.5 border-b border-[#232736]/50 items-center"
                        >
                          <span className="font-bold text-white uppercase">{metric.replace(/_/g, ' ')}</span>
                          <span className="text-zinc-300">
                            {String(mData.baseline)} → <strong className="text-white">{String(mData.candidate)}</strong>
                          </span>
                          <span className={mData.improved ? 'text-emerald-400 font-bold' : 'text-rose-400 font-bold'}>
                            {mData.delta !== undefined ? `${mData.delta > 0 ? '+' : ''}${mData.delta}` : (mData.improved ? 'IMPROVED' : 'REGRESSED')}
                          </span>
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}
            </GlassPanel>
          )}
        </div>
      </div>
    </div>
  );
}
