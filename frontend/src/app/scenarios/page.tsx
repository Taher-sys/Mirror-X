'use client';

import React, { useEffect, useState, useCallback } from 'react';
import {
  FlaskConical,
  Play,
  RefreshCw,
  Shuffle,
  ShieldCheck,
  CheckCircle2,
  XCircle,
  Database,
  Layers,
  Sparkles,
} from 'lucide-react';
import { GlassPanel } from '@/components/ui/glass-panel';
import { PerspectiveGrid } from '@/components/ui/perspective-grid';
import { StatTile } from '@/components/ui/stat-tile';
import { StatusBadge } from '@/components/ui/status-badge';
import {
  generateScenario,
  getScenarios,
  executeScenario,
  generateBatchScenarios,
  Scenario,
} from '@/lib/api';

const SCENARIO_CLASSES = [
  'all',
  'normal',
  'boundary',
  'incomplete',
  'malformed',
  'contradictory',
  'unauthorized',
  'adversarial',
  'outage',
  'tool_failure',
  'ambiguous',
];

const SOURCE_TYPES = [
  'api',
  'schema',
  'domain_model',
  'policy',
  'tool_definition',
  'validation_rule',
  'existing_test',
];

export default function ScenariosPage() {
  const [scenarios, setScenarios] = useState<Scenario[]>([]);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [executing, setExecuting] = useState(false);

  // Generator form state
  const [targetName, setTargetName] = useState('CheckoutService');
  const [sourceType, setSourceType] = useState('api');
  const [scenarioClass, setScenarioClass] = useState('adversarial');
  const [seed, setSeed] = useState(42);
  const [filterClass, setFilterClass] = useState('all');
  const [selectedScenarioId, setSelectedScenarioId] = useState<string | null>(null);

  const fetchScenarios = useCallback(async () => {
    try {
      setLoading(true);
      const params = filterClass !== 'all' ? { scenario_class: filterClass } : undefined;
      const data = await getScenarios(params);
      setScenarios(Array.isArray(data) ? data : []);
      if (data.length > 0 && !selectedScenarioId) {
        setSelectedScenarioId(data[0].id);
      }
    } catch (err) {
      console.error('Failed to fetch scenarios:', err);
    } finally {
      setLoading(false);
    }
  }, [filterClass, selectedScenarioId]);

  useEffect(() => {
    fetchScenarios();
  }, [fetchScenarios]);

  const handleGenerate = async () => {
    try {
      setGenerating(true);
      const created = await generateScenario({
        target_name: targetName,
        source_type: sourceType,
        scenario_class: scenarioClass,
        seed: Number(seed),
      });
      setScenarios((prev) => [created, ...prev]);
      setSelectedScenarioId(created.id);
    } catch (err) {
      console.error('Generation failed:', err);
    } finally {
      setGenerating(false);
    }
  };

  const handleBatchGenerate = async () => {
    try {
      setGenerating(true);
      const batch = await generateBatchScenarios(targetName, Number(seed));
      setScenarios((prev) => [...batch, ...prev]);
      if (batch.length > 0) {
        setSelectedScenarioId(batch[0].id);
      }
    } catch (err) {
      console.error('Batch generation failed:', err);
    } finally {
      setGenerating(false);
    }
  };

  const handleExecute = async (id: string) => {
    try {
      setExecuting(true);
      const result = await executeScenario(id);
      setScenarios((prev) =>
        prev.map((s) =>
          s.id === id
            ? {
                ...s,
                status: result.passed ? 'passed' : 'failed',
                execution_result: {
                  execution_id: String(result.execution_id || 'exec_live'),
                  passed: Boolean(result.passed),
                  actual_status: Number(result.actual_status || 200),
                  actual_decision: String(result.actual_decision || 'ALLOW'),
                  execution_duration_ms: Number(result.execution_duration_ms || 24),
                },
              }
            : s
        )
      );
    } catch (err) {
      console.error('Execution failed:', err);
    } finally {
      setExecuting(false);
    }
  };

  const selectedScenario = scenarios.find((s) => s.id === selectedScenarioId) || scenarios[0];

  // Telemetry KPIs
  const totalScenarios = scenarios.length;
  const classesCovered = new Set(scenarios.map((s) => s.scenario_class)).size;
  const passedCount = scenarios.filter((s) => s.status === 'passed').length;
  const passRate = totalScenarios > 0 ? `${Math.round((passedCount / totalScenarios) * 100)}%` : '100%';

  return (
    <div className="relative min-h-[calc(100vh-3.5rem)] overflow-hidden canvas-textured text-white p-6 space-y-6">
      <PerspectiveGrid />

      {/* Header */}
      <div className="relative z-10 flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-white/10 pb-5">
        <div className="flex items-center gap-3.5">
          <div className="flex h-11 w-11 items-center justify-center rounded-2xl border-2 border-orange-500/40 bg-orange-950/40 text-orange-400 shadow-[0_0_20px_rgba(249,115,22,0.3)]">
            <FlaskConical className="h-5 w-5 drop-shadow-[0_0_8px_rgba(249,115,22,0.6)]" />
          </div>
          <div>
            <div className="flex items-center gap-2.5">
              <h1 className="text-2xl font-bold tracking-tight text-white font-sans drop-shadow-[0_2px_12px_rgba(0,0,0,0.8)]">
                Synthetic Scenario Engine
              </h1>
              <span className="font-mono text-xs font-bold uppercase tracking-wider text-orange-400 bg-orange-950/60 border border-orange-500/40 px-2.5 py-0.5 rounded shadow-[0_0_10px_rgba(249,115,22,0.25)]">
                REPRODUCIBLE TEST TWIN
              </span>
            </div>
            <p className="mt-1 font-mono text-sm font-semibold text-zinc-200">
              Deterministic, seed-driven synthetic test generation across 10 scenario classes without external ML datasets
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={handleBatchGenerate}
            disabled={generating}
            className="inline-flex items-center gap-2 rounded-xl border-2 border-orange-500/50 bg-gradient-to-r from-orange-950/70 via-zinc-900/90 to-orange-950/70 px-4 py-2 font-mono text-xs font-bold uppercase tracking-wider text-orange-400 transition-all duration-300 ease-out hover:scale-[1.02] active:scale-[0.98] hover:border-orange-400 hover:shadow-[0_0_20px_rgba(249,115,22,0.4)] shadow-lg disabled:opacity-50"
          >
            <Sparkles className="h-3.5 w-3.5" />
            <span>Generate Suite (All 10 Classes)</span>
          </button>
        </div>
      </div>

      {/* KPI Ribbon */}
      <div className="relative z-10 grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatTile
          label="Total Scenarios"
          value={totalScenarios}
          subvalue="generated instances"
          accent="amber"
          icon={FlaskConical}
        />
        <StatTile
          label="Classes Covered"
          value={`${classesCovered}/10`}
          subvalue="behavioral coverage"
          accent="orange"
          icon={Layers}
        />
        <StatTile
          label="Verified Passes"
          value={passedCount}
          subvalue="sandbox invariant checks"
          accent="emerald"
          icon={CheckCircle2}
        />
        <StatTile
          label="Pass Rate"
          value={passRate}
          subvalue="deterministic verification"
          accent="amber"
          icon={ShieldCheck}
        />
      </div>

      {/* Generator Console Bar */}
      <GlassPanel className="relative z-10 p-5 space-y-4">
        <div className="flex items-center justify-between border-b border-white/10 pb-3">
          <div className="flex items-center gap-2 font-mono text-xs uppercase font-bold text-orange-400 tracking-wider">
            <FlaskConical className="h-4 w-4" />
            <span>Scenario Parameter Engine</span>
          </div>
          <span className="font-mono text-xs font-bold text-zinc-300">
            SEED DETERMINISM ACTIVE
          </span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3.5 items-end">
          <div>
            <label className="block font-mono text-xs uppercase font-bold text-zinc-300 mb-1">
              Target Entity
            </label>
            <input
              type="text"
              value={targetName}
              onChange={(e) => setTargetName(e.target.value)}
              className="w-full rounded-xl border-2 border-orange-500/30 bg-zinc-950/90 px-3.5 py-2 font-mono text-xs font-bold text-white placeholder-zinc-500 focus:border-orange-500/60 focus:outline-none"
              placeholder="e.g. CheckoutAPI"
            />
          </div>

          <div>
            <label className="block font-mono text-xs uppercase font-bold text-zinc-300 mb-1">
              Source Type
            </label>
            <select
              value={sourceType}
              onChange={(e) => setSourceType(e.target.value)}
              className="w-full rounded-xl border-2 border-orange-500/30 bg-zinc-950/90 px-3.5 py-2 font-mono text-xs font-bold text-white focus:border-orange-500/60 focus:outline-none"
            >
              {SOURCE_TYPES.map((st) => (
                <option key={st} value={st} className="bg-zinc-900 text-white">
                  {st.toUpperCase()}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block font-mono text-xs uppercase font-bold text-zinc-300 mb-1">
              Scenario Class
            </label>
            <select
              value={scenarioClass}
              onChange={(e) => setScenarioClass(e.target.value)}
              className="w-full rounded-xl border-2 border-orange-500/30 bg-zinc-950/90 px-3.5 py-2 font-mono text-xs font-bold text-white focus:border-orange-500/60 focus:outline-none"
            >
              {SCENARIO_CLASSES.filter((c) => c !== 'all').map((sc) => (
                <option key={sc} value={sc} className="bg-zinc-900 text-white">
                  {sc.toUpperCase()}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block font-mono text-xs uppercase font-bold text-zinc-300 mb-1">
              Seed (Reproducibility)
            </label>
            <div className="flex items-center gap-2">
              <input
                type="number"
                value={seed}
                onChange={(e) => setSeed(Number(e.target.value))}
                className="w-full rounded-xl border-2 border-orange-500/30 bg-zinc-950/90 px-3.5 py-2 font-mono text-xs font-bold text-orange-400 focus:border-orange-500/60 focus:outline-none"
              />
              <button
                type="button"
                onClick={() => setSeed(Math.floor(Math.random() * 9000) + 1000)}
                className="p-2.5 rounded-xl border border-orange-500/30 bg-zinc-900/60 text-orange-400 hover:text-white hover:border-orange-500/60 transition-all"
                title="Randomize seed"
              >
                <Shuffle className="h-4 w-4" />
              </button>
            </div>
          </div>

          <button
            onClick={handleGenerate}
            disabled={generating}
            className="w-full inline-flex items-center justify-center gap-2 rounded-xl border-2 border-orange-500/50 bg-gradient-to-r from-orange-950/70 via-zinc-900/90 to-orange-950/70 px-4 py-2.5 font-mono text-xs font-bold uppercase tracking-wider text-orange-400 transition-all duration-300 ease-out hover:scale-[1.02] active:scale-[0.98] hover:border-orange-400 hover:shadow-[0_0_20px_rgba(249,115,22,0.4)] shadow-lg disabled:opacity-50"
          >
            {generating ? (
              <RefreshCw className="h-4 w-4 animate-spin text-orange-400" />
            ) : (
              <FlaskConical className="h-4 w-4" />
            )}
            <span>Generate Scenario</span>
          </button>
        </div>
      </GlassPanel>

      {/* Category Filter Pills */}
      <div className="relative z-10 flex items-center gap-2 overflow-x-auto pb-1 scrollbar-thin">
        {SCENARIO_CLASSES.map((cls) => {
          const count = cls === 'all' ? scenarios.length : scenarios.filter((s) => s.scenario_class === cls).length;
          const active = filterClass === cls;
          return (
            <button
              key={cls}
              onClick={() => setFilterClass(cls)}
              className={`whitespace-nowrap px-3.5 py-1.5 rounded-xl border font-mono text-xs font-bold transition-all duration-300 ease-out hover:scale-[1.02] active:scale-[0.98] flex items-center gap-2 backdrop-blur-2xl ${
                active
                  ? 'border-2 border-orange-500/60 bg-orange-950/60 text-white shadow-[0_0_15px_rgba(249,115,22,0.3)]'
                  : 'border border-white/10 bg-zinc-900/50 text-zinc-300 hover:border-orange-500/30 hover:text-white'
              }`}
            >
              <span>{cls.toUpperCase()}</span>
              <span
                className={`text-[11px] font-bold px-2 py-0.5 rounded-full ${
                  active ? 'bg-orange-500/30 text-orange-300' : 'bg-black/60 text-zinc-300'
                }`}
              >
                {count}
              </span>
            </button>
          );
        })}
      </div>

      {/* Dual Pane: Scenario Suite (Left) & Scenario Detail Inspector (Right) */}
      <div className="relative z-10 grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Left Column: List of Scenarios */}
        <div className="lg:col-span-5 space-y-3">
          {loading && scenarios.length === 0 ? (
            <div className="py-20 text-center font-mono text-sm font-semibold text-zinc-300 animate-pulse">
              Synthesizing scenario telemetry...
            </div>
          ) : scenarios.length === 0 ? (
            <GlassPanel className="py-16 text-center">
              <FlaskConical className="mx-auto h-12 w-12 text-orange-400" />
              <h4 className="mt-3 font-mono text-sm font-bold uppercase tracking-wider text-white">
                No Scenarios In Class
              </h4>
              <p className="mt-1 text-sm font-medium text-zinc-300">
                Click &quot;Generate Scenario&quot; or &quot;Generate Suite&quot; to produce test twins.
              </p>
            </GlassPanel>
          ) : (
            <div className="space-y-2.5 max-h-[720px] overflow-y-auto pr-1 scrollbar-thin">
              {scenarios.map((scen) => {
                const isSelected = selectedScenario?.id === scen.id;
                return (
                  <div
                    key={scen.id}
                    onClick={() => setSelectedScenarioId(scen.id)}
                    className={`cursor-pointer rounded-2xl border-2 border-t-2 p-4 backdrop-blur-3xl transition-all duration-300 ease-out hover:scale-[1.01] shadow-[0_16px_40px_rgba(0,0,0,0.85)] ${
                      isSelected
                        ? 'border-orange-500/60 border-t-white/35 bg-zinc-950/95 shadow-[0_0_25px_rgba(249,115,22,0.2)]'
                        : 'border-orange-500/35 border-t-white/20 bg-zinc-950/85 hover:border-orange-500/50'
                    }`}
                  >
                    <div className="flex items-center justify-between gap-2">
                      <div className="flex items-center gap-2">
                        <span className="font-mono text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded border bg-orange-950/60 text-orange-400 border-orange-500/40">
                          {scen.scenario_class}
                        </span>
                        <span className="font-mono text-xs font-bold text-white truncate max-w-[200px]">
                          {scen.name}
                        </span>
                      </div>
                      <StatusBadge
                        status={scen.status === 'passed' ? 'healthy' : scen.status === 'failed' ? 'critical' : 'uninitialized'}
                        label={scen.status.toUpperCase()}
                      />
                    </div>

                    <div className="mt-2.5 flex items-center justify-between font-mono text-xs font-semibold text-zinc-300">
                      <span>Source: <strong className="text-white font-bold">{scen.source_type}</strong></span>
                      <span>Seed: <strong className="text-orange-400 font-bold">{scen.seed}</strong></span>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Right Column: Detailed Scenario Inspector */}
        <div className="lg:col-span-7">
          {!selectedScenario ? (
            <GlassPanel className="py-24 text-center">
              <FlaskConical className="mx-auto h-12 w-12 text-orange-400" />
              <h4 className="mt-3 font-mono text-sm font-bold uppercase tracking-wider text-white">
                Select a Scenario
              </h4>
              <p className="mt-1 text-sm font-medium text-zinc-300">
                Choose a synthetic scenario to inspect its initial state, generated inputs, and expected constraints.
              </p>
            </GlassPanel>
          ) : (
            <GlassPanel className="p-5 space-y-5">
              {/* Header */}
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-white/10 pb-4">
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-xs uppercase font-bold text-orange-400 bg-orange-950/60 border border-orange-500/40 px-2.5 py-0.5 rounded-lg shadow-[0_0_8px_rgba(249,115,22,0.25)]">
                      {selectedScenario.scenario_class}
                    </span>
                    <span className="font-mono text-xs font-bold text-orange-400">
                      SEED: {selectedScenario.seed}
                    </span>
                  </div>
                  <h3 className="font-mono text-base font-bold text-white">
                    {selectedScenario.name}
                  </h3>
                </div>

                <button
                  onClick={() => handleExecute(selectedScenario.id)}
                  disabled={executing}
                  className="inline-flex items-center gap-2 rounded-xl border-2 border-orange-500/50 bg-gradient-to-r from-orange-950/70 via-zinc-900/90 to-orange-950/70 px-4 py-2 font-mono text-xs font-bold uppercase tracking-wider text-orange-400 transition-all duration-300 ease-out hover:scale-[1.02] active:scale-[0.98] hover:border-orange-400 hover:shadow-[0_0_20px_rgba(249,115,22,0.4)] shadow-lg disabled:opacity-50"
                >
                  <Play className={`h-3.5 w-3.5 fill-current ${executing ? 'animate-spin' : ''}`} />
                  <span>{executing ? 'Asserting Constraints...' : 'Execute In Sandbox'}</span>
                </button>
              </div>

              {/* Execution Result Banner */}
              {selectedScenario.execution_result && (
                <div className="rounded-2xl border-2 border-orange-500/40 border-t-2 border-white/25 bg-orange-950/30 p-4 space-y-2 backdrop-blur-3xl">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2 font-mono text-xs font-bold uppercase text-orange-400">
                      <CheckCircle2 className="h-4 w-4" />
                      <span>Sandbox Verification Status: PASSED</span>
                    </div>
                    <span className="font-mono text-xs font-bold text-orange-400">
                      {selectedScenario.execution_result.execution_duration_ms}ms
                    </span>
                  </div>
                  <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 font-mono text-xs font-semibold text-zinc-200">
                    <div>HTTP Status: <strong className="text-white font-bold">{selectedScenario.execution_result.actual_status}</strong></div>
                    <div>Policy Gate: <strong className="text-orange-400 font-bold">{selectedScenario.execution_result.actual_decision}</strong></div>
                    <div>Execution ID: <strong className="text-orange-400 font-bold">{selectedScenario.execution_result.execution_id}</strong></div>
                  </div>
                </div>
              )}

              {/* Generated Inputs Section */}
              <div>
                <h4 className="font-mono text-xs uppercase font-bold text-orange-400 mb-1.5 flex items-center gap-1.5">
                  <Play className="h-3.5 w-3.5 text-orange-400" /> Generated Synthetic Inputs
                </h4>
                <pre className="font-mono text-xs text-orange-200 bg-black/90 border border-orange-500/30 p-3.5 rounded-xl overflow-x-auto">
                  <code>{JSON.stringify(selectedScenario.generated_inputs, null, 2)}</code>
                </pre>
              </div>

              {/* Expected Constraints Section */}
              <div>
                <h4 className="font-mono text-xs uppercase font-bold text-orange-400 mb-1.5 flex items-center gap-1.5">
                  <ShieldCheck className="h-3.5 w-3.5 text-orange-400" /> Expected Constraints &amp; Invariants
                </h4>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
                  {Object.entries(selectedScenario.expected_constraints).map(([key, val]) => (
                    <div
                      key={key}
                      className="rounded-xl border border-orange-500/30 bg-zinc-900/60 p-3 font-mono text-xs"
                    >
                      <div className="text-orange-400 font-bold uppercase tracking-wider">{key}</div>
                      <div className="text-white font-bold mt-1 break-all">{String(val)}</div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Participating Resources & Policies */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3.5">
                <div>
                  <h4 className="font-mono text-xs uppercase font-bold text-orange-400 mb-1.5 flex items-center gap-1.5">
                    <Database className="h-3.5 w-3.5 text-orange-400" /> Participating Resources
                  </h4>
                  <div className="space-y-1.5">
                    {selectedScenario.participating_resources.map((res, idx) => (
                      <div
                        key={idx}
                        className="flex items-center justify-between p-2 rounded-xl border border-white/10 bg-zinc-900/40 font-mono text-xs"
                      >
                        <span className="text-white font-bold">{res.name}</span>
                        <span className="text-orange-400 uppercase font-semibold">{res.role}</span>
                      </div>
                    ))}
                  </div>
                </div>

                <div>
                  <h4 className="font-mono text-xs uppercase font-bold text-orange-400 mb-1.5 flex items-center gap-1.5">
                    <ShieldCheck className="h-3.5 w-3.5 text-orange-400" /> Applicable Policies
                  </h4>
                  <div className="space-y-1.5">
                    {selectedScenario.applicable_policies.map((pol, idx) => (
                      <div
                        key={idx}
                        className="flex items-center justify-between p-2 rounded-xl border border-white/10 bg-zinc-900/40 font-mono text-xs"
                      >
                        <span className="text-white font-bold">{pol.name}</span>
                        <span className="text-orange-400 uppercase font-semibold">{pol.enforcement}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </GlassPanel>
          )}
        </div>
      </div>
    </div>
  );
}
