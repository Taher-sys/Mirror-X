'use client';

import React, { useEffect, useState, useCallback } from 'react';
import {
  Rocket,
  ShieldCheck,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  RotateCcw,
  Sparkles,
  GitCommit,
  Hash,
  FileCheck,
  HelpCircle,
  Lock,
  Layers,
  Bot,
  Zap,
} from 'lucide-react';
import { GlassPanel } from '@/components/ui/glass-panel';
import { PerspectiveGrid } from '@/components/ui/perspective-grid';
import { StatTile } from '@/components/ui/stat-tile';
import {
  getReleases,
  createRelease,
  getReleasePassport,
  issueReleasePassport,
  ReleaseItem,
  ReleasePassportItem,
} from '@/lib/api';

export default function ReleasesPage() {
  const [releases, setReleases] = useState<ReleaseItem[]>([]);
  const [selectedReleaseId, setSelectedReleaseId] = useState<string | null>(null);
  const [passport, setPassport] = useState<ReleasePassportItem | null>(null);
  const [loading, setLoading] = useState(true);
  const [evaluating, setEvaluating] = useState(false);

  const fetchReleasesData = useCallback(async () => {
    try {
      setLoading(true);
      const list = await getReleases();

      if (list.length === 0) {
        // Seed an initial release candidate for demonstration
        const rel = await createRelease({
          name: 'Sprint 24 Staging Deployment',
          version: 'v1.2.0-rc1',
          target_environment: 'staging',
          commit_hash: '9f8e7d6c5b4a3210fe4d3c2b1a0987654321fedc',
        });
        setReleases([rel]);
        setSelectedReleaseId(rel.id);
        const pass = await issueReleasePassport(rel.id);
        setPassport(pass);
      } else {
        setReleases(list);
        setSelectedReleaseId((prev) => prev || list[0].id);
        try {
          const pass = await getReleasePassport(list[0].id);
          setPassport(pass);
        } catch {
          // Passport may not yet be issued
        }
      }
    } catch (err) {
      console.error('Failed to load releases:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchReleasesData();
  }, [fetchReleasesData]);

  const handleSelectRelease = async (id: string) => {
    setSelectedReleaseId(id);
    try {
      const pass = await getReleasePassport(id);
      setPassport(pass);
    } catch {
      setPassport(null);
    }
  };

  const handleIssuePassport = async () => {
    if (!selectedReleaseId) return;
    try {
      setEvaluating(true);
      const newPassport = await issueReleasePassport(selectedReleaseId);
      setPassport(newPassport);
    } catch (err) {
      console.error('Failed to issue passport:', err);
    } finally {
      setEvaluating(false);
    }
  };

  const selectedRelease = releases.find((r) => r.id === selectedReleaseId) || releases[0];

  const getStatusBadge = (status: string) => {
    const s = status.toUpperCase();
    if (s === 'PASS') {
      return (
        <span className="font-mono text-xs font-bold uppercase px-2.5 py-0.5 rounded border border-emerald-500/40 bg-emerald-950/60 text-emerald-400">
          PASS
        </span>
      );
    }
    if (s === 'FAIL') {
      return (
        <span className="font-mono text-xs font-bold uppercase px-2.5 py-0.5 rounded border border-rose-500/40 bg-rose-950/60 text-rose-400">
          FAIL
        </span>
      );
    }
    if (s === 'HUMAN_REVIEW_REQUIRED') {
      return (
        <span className="font-mono text-xs font-bold uppercase px-2.5 py-0.5 rounded border border-orange-500/40 bg-orange-950/60 text-orange-400">
          HUMAN REVIEW
        </span>
      );
    }
    if (s === 'WARNING') {
      return (
        <span className="font-mono text-xs font-bold uppercase px-2.5 py-0.5 rounded border border-amber-500/40 bg-amber-950/60 text-amber-400">
          WARNING
        </span>
      );
    }
    return (
      <span className="font-mono text-xs font-bold uppercase px-2.5 py-0.5 rounded border border-white/10 bg-zinc-900 text-zinc-300">
        NOT EVALUATED
      </span>
    );
  };

  return (
    <div className="relative min-h-[calc(100vh-3.5rem)] overflow-hidden canvas-textured text-white p-6 space-y-6">
      <PerspectiveGrid />

      {/* Header */}
      <div className="relative z-10 flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-white/10 pb-5">
        <div className="flex items-center gap-3.5">
          <div className="flex h-11 w-11 items-center justify-center rounded-2xl border-2 border-orange-500/40 bg-orange-950/40 text-orange-400 shadow-[0_0_20px_rgba(249,115,22,0.3)]">
            <Rocket className="h-5 w-5 drop-shadow-[0_0_8px_rgba(249,115,22,0.6)]" />
          </div>
          <div>
            <div className="flex items-center gap-2.5">
              <h1 className="text-2xl font-bold tracking-tight text-white font-sans drop-shadow-[0_2px_12px_rgba(0,0,0,0.8)]">
                Release Passport
              </h1>
              <span className="font-mono text-xs font-bold uppercase tracking-wider text-orange-400 bg-orange-950/60 border border-orange-500/40 px-2.5 py-0.5 rounded shadow-[0_0_10px_rgba(249,115,22,0.25)]">
                VERIFIABLE CERTIFICATION
              </span>
            </div>
            <p className="mt-1 font-mono text-sm font-semibold text-zinc-200">
              Evidence-based cryptographic certification synthesizing code change analysis, scenarios, agent runs, and policies
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={handleIssuePassport}
            disabled={evaluating || !selectedReleaseId}
            className="inline-flex items-center gap-2 rounded-xl border-2 border-orange-500/50 bg-gradient-to-r from-orange-950/70 via-zinc-900/90 to-orange-950/70 px-4 py-2 font-mono text-xs font-bold uppercase tracking-wider text-orange-400 transition-all duration-300 ease-out hover:scale-[1.02] active:scale-[0.98] hover:border-orange-400 hover:shadow-[0_0_20px_rgba(249,115,22,0.4)] shadow-lg disabled:opacity-50"
          >
            {evaluating ? (
              <RotateCcw className="h-3.5 w-3.5 animate-spin text-orange-400" />
            ) : (
              <Sparkles className="h-3.5 w-3.5" />
            )}
            <span>{evaluating ? 'Synthesizing Telemetry...' : 'Issue / Re-Evaluate Passport'}</span>
          </button>
        </div>
      </div>

      {/* KPI Ribbon */}
      <div className="relative z-10 grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatTile
          label="Overall Status"
          value={passport ? passport.overall_status : 'PENDING'}
          subvalue="certification verdict"
          accent={
            passport?.overall_status === 'PASS'
              ? 'emerald'
              : passport?.overall_status === 'FAIL'
              ? 'crimson'
              : passport?.overall_status === 'HUMAN_REVIEW_REQUIRED'
              ? 'orange'
              : 'amber'
          }
          icon={ShieldCheck}
        />
        <StatTile
          label="Release Version"
          value={selectedRelease ? selectedRelease.version : 'N/A'}
          subvalue="candidate bundle"
          accent="orange"
          icon={Rocket}
        />
        <StatTile
          label="Verification Domains"
          value="6 / 6"
          subvalue="multi-domain analysis"
          accent="amber"
          icon={Layers}
        />
        <StatTile
          label="Evidence Provenance"
          value={passport ? `${Math.round(passport.evidence_completeness.completeness_score * 100)}%` : '0%'}
          subvalue="anchor completeness"
          accent="emerald"
          icon={FileCheck}
        />
      </div>

      {/* Dual Pane Layout: Release Candidates (Left) & Verifiable Passport (Right) */}
      <div className="relative z-10 grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Left Column: Release Candidates */}
        <div className="lg:col-span-4 space-y-3">
          <GlassPanel className="p-5 space-y-4">
            <div className="flex items-center justify-between border-b border-white/10 pb-3">
              <span className="font-mono text-xs uppercase font-bold text-orange-400">
                Release Candidates ({releases.length})
              </span>
            </div>

            <div className="space-y-2.5">
              {releases.map((rel) => {
                const isSelected = selectedRelease?.id === rel.id;
                return (
                  <div
                    key={rel.id}
                    onClick={() => handleSelectRelease(rel.id)}
                    className={`cursor-pointer rounded-2xl border-2 border-t-2 p-4 backdrop-blur-3xl transition-all duration-300 ease-out hover:scale-[1.01] shadow-[0_16px_40px_rgba(0,0,0,0.85)] ${
                      isSelected
                        ? 'border-orange-500/60 border-t-white/35 bg-zinc-950/95 shadow-[0_0_25px_rgba(249,115,22,0.2)]'
                        : 'border-orange-500/35 border-t-white/20 bg-zinc-950/85 hover:border-orange-500/50'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-mono text-xs font-bold text-white">
                        {rel.version}
                      </span>
                      <span className="font-mono text-[10px] font-bold uppercase tracking-wider text-orange-400 bg-orange-950/60 border border-orange-500/40 px-2 py-0.5 rounded">
                        {rel.target_environment}
                      </span>
                    </div>

                    <p className="mt-1 text-xs font-medium text-zinc-200 font-sans">
                      {rel.name}
                    </p>

                    <div className="mt-2 font-mono text-[11px] text-zinc-400 truncate">
                      Commit: <strong className="text-orange-400 font-semibold">{rel.commit_hash.slice(0, 12)}</strong>
                    </div>
                  </div>
                );
              })}
            </div>
          </GlassPanel>
        </div>

        {/* Right Column: Verifiable Release Passport Artifact */}
        <div className="lg:col-span-8">
          {!passport ? (
            <GlassPanel className="py-24 text-center">
              <ShieldCheck className="mx-auto h-12 w-12 text-orange-400" />
              <h4 className="mt-3 font-mono text-sm font-bold uppercase tracking-wider text-white">
                Release Passport Not Issued
              </h4>
              <p className="mt-1 text-sm font-medium text-zinc-300">
                Click &quot;Issue / Re-Evaluate Passport&quot; above to synthesize multi-domain verification telemetry.
              </p>
            </GlassPanel>
          ) : (
            <GlassPanel className="p-6 space-y-6">
              {/* Passport Header Banner */}
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-white/10 pb-4">
                <div>
                  <div className="flex items-center gap-2.5">
                    <h3 className="font-mono text-lg font-bold text-white tracking-wide">
                      RELEASE PASSPORT // {selectedRelease.version}
                    </h3>
                    {getStatusBadge(passport.overall_status)}
                  </div>
                  <p className="mt-1 font-mono text-xs font-semibold text-zinc-300">
                    Cryptographic Seal: <span className="text-orange-400 font-bold">{passport.passport_hash}</span>
                  </p>
                </div>
              </div>

              {/* Uncertainty Notes (Explicit Transparency Mandate) */}
              <div className="rounded-2xl border-2 border-orange-500/35 border-t-2 border-white/25 bg-zinc-950/90 p-4 space-y-2 backdrop-blur-3xl shadow-[0_12px_32px_rgba(0,0,0,0.8)]">
                <div className="flex items-center gap-2 font-mono text-xs uppercase font-bold text-orange-400 tracking-wider">
                  <AlertTriangle className="h-4 w-4" />
                  <span>Truthful Uncertainty Disclosure (No Hidden Telemetry)</span>
                </div>
                <div className="font-mono text-xs text-zinc-200 whitespace-pre-line leading-relaxed bg-black/60 p-3 rounded-xl border border-white/10">
                  {passport.uncertainty_notes}
                </div>
              </div>

              {/* 6 Verification Domain Cards */}
              <div className="space-y-3">
                <h4 className="font-mono text-xs uppercase font-bold text-orange-400 tracking-wider">
                  Evaluation Domains Breakdown (6 Dimensions)
                </h4>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3.5">
                  {/* Domain 1: Code Change Analysis */}
                  <div className="rounded-2xl border-2 border-orange-500/35 border-t-2 border-white/25 bg-zinc-950/90 p-4 space-y-2 backdrop-blur-3xl">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2 font-mono text-xs font-bold text-white">
                        <GitCommit className="h-4 w-4 text-orange-400" />
                        <span>Code Change Analysis</span>
                      </div>
                      {getStatusBadge(passport.code_change_analysis.status)}
                    </div>
                    <div className="font-mono text-xs text-zinc-300 space-y-1">
                      <div>Total Changes: <strong className="text-white font-bold">{passport.code_change_analysis.total_changes}</strong></div>
                      <div>Breaking Changes: <strong className="text-orange-400 font-bold">{passport.code_change_analysis.breaking_changes_count}</strong></div>
                      <div>Max Risk Score: <strong className="text-white font-bold">{passport.code_change_analysis.max_risk_score}/100</strong></div>
                    </div>
                  </div>

                  {/* Domain 2: Context Findings */}
                  <div className="rounded-2xl border-2 border-orange-500/35 border-t-2 border-white/25 bg-zinc-950/90 p-4 space-y-2 backdrop-blur-3xl">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2 font-mono text-xs font-bold text-white">
                        <Layers className="h-4 w-4 text-orange-400" />
                        <span>Context Findings</span>
                      </div>
                      {getStatusBadge(passport.context_findings.status)}
                    </div>
                    <div className="font-mono text-xs text-zinc-300 space-y-1">
                      <div>Total Discrepancies: <strong className="text-white font-bold">{passport.context_findings.total_findings}</strong></div>
                      <div>Critical Drifts: <strong className="text-rose-400 font-bold">{passport.context_findings.critical_count}</strong></div>
                      <div>Open Findings: <strong className="text-orange-400 font-bold">{passport.context_findings.open_findings}</strong></div>
                    </div>
                  </div>

                  {/* Domain 3: Scenario Testing */}
                  <div className="rounded-2xl border-2 border-orange-500/35 border-t-2 border-white/25 bg-zinc-950/90 p-4 space-y-2 backdrop-blur-3xl">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2 font-mono text-xs font-bold text-white">
                        <Zap className="h-4 w-4 text-orange-400" />
                        <span>Scenario Testing</span>
                      </div>
                      {getStatusBadge(passport.scenario_testing.status)}
                    </div>
                    <div className="font-mono text-xs text-zinc-300 space-y-1">
                      <div>Total Scenarios: <strong className="text-white font-bold">{passport.scenario_testing.total_scenarios}</strong></div>
                      <div>Passed Invariants: <strong className="text-emerald-400 font-bold">{passport.scenario_testing.passed_count}</strong></div>
                      <div>Failed Checks: <strong className="text-rose-400 font-bold">{passport.scenario_testing.failed_count}</strong></div>
                    </div>
                  </div>

                  {/* Domain 4: Agent Testing */}
                  <div className="rounded-2xl border-2 border-orange-500/35 border-t-2 border-white/25 bg-zinc-950/90 p-4 space-y-2 backdrop-blur-3xl">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2 font-mono text-xs font-bold text-white">
                        <Bot className="h-4 w-4 text-orange-400" />
                        <span>Agent Behavior Lab</span>
                      </div>
                      {getStatusBadge(passport.agent_testing.status)}
                    </div>
                    <div className="font-mono text-xs text-zinc-300 space-y-1">
                      <div>Runs Captured: <strong className="text-white font-bold">{passport.agent_testing.total_runs}</strong></div>
                      <div>Policy Violations: <strong className="text-rose-400 font-bold">{passport.agent_testing.policy_violations}</strong></div>
                      <div>Evaluated Models: <strong className="text-orange-400 font-bold">{passport.agent_testing.evaluated_models.join(', ') || 'None'}</strong></div>
                    </div>
                  </div>

                  {/* Domain 5: Policy Validation */}
                  <div className="rounded-2xl border-2 border-orange-500/35 border-t-2 border-white/25 bg-zinc-950/90 p-4 space-y-2 backdrop-blur-3xl">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2 font-mono text-xs font-bold text-white">
                        <ShieldCheck className="h-4 w-4 text-orange-400" />
                        <span>Trust Layer Validation</span>
                      </div>
                      {getStatusBadge(passport.policy_validation.status)}
                    </div>
                    <div className="font-mono text-xs text-zinc-300 space-y-1">
                      <div>Evaluations: <strong className="text-white font-bold">{passport.policy_validation.total_evaluations}</strong></div>
                      <div>Explicit Denials: <strong className="text-rose-400 font-bold">{passport.policy_validation.denied_count}</strong></div>
                      <div>Pending Reviews: <strong className="text-orange-400 font-bold">{passport.policy_validation.review_required_count}</strong></div>
                    </div>
                  </div>

                  {/* Domain 6: Evidence Completeness */}
                  <div className="rounded-2xl border-2 border-orange-500/35 border-t-2 border-white/25 bg-zinc-950/90 p-4 space-y-2 backdrop-blur-3xl">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2 font-mono text-xs font-bold text-white">
                        <FileCheck className="h-4 w-4 text-orange-400" />
                        <span>Evidence Ledger Provenance</span>
                      </div>
                      {getStatusBadge(passport.evidence_completeness.status)}
                    </div>
                    <div className="font-mono text-xs text-zinc-300 space-y-1">
                      <div>Total Evidence Records: <strong className="text-white font-bold">{passport.evidence_completeness.total_evidence_records}</strong></div>
                      <div>Anchor Completeness: <strong className="text-emerald-400 font-bold">{Math.round(passport.evidence_completeness.completeness_score * 100)}%</strong></div>
                    </div>
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
