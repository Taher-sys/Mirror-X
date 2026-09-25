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
        <span className="font-mono text-xs font-bold uppercase px-2.5 py-0.5 rounded border border-amber-500/40 bg-zinc-900 text-amber-400">
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
      <span className="font-mono text-xs font-bold uppercase px-2.5 py-0.5 rounded border border-zinc-800 bg-zinc-900 text-zinc-400">
        NOT EVALUATED
      </span>
    );
  };

  return (
    <div className="relative min-h-[calc(100vh-3.5rem)] overflow-hidden canvas-textured text-white p-6 space-y-6">
      <PerspectiveGrid />

      {/* Header */}
      <div className="relative z-10 flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-zinc-800 pb-5">
        <div className="flex items-center gap-3.5">
          <div className="flex h-11 w-11 items-center justify-center rounded-xl border border-zinc-800 bg-zinc-900/80 text-amber-500">
            <Rocket className="h-5 w-5" />
          </div>
          <div>
            <div className="flex items-center gap-2.5">
              <h1 className="text-2xl font-bold tracking-tight text-white font-sans drop-shadow-[0_2px_12px_rgba(0,0,0,0.8)]">
                Release Passport
              </h1>
              <span className="font-mono text-xs font-bold uppercase tracking-wider text-amber-500 bg-zinc-900/80 border border-zinc-800 px-2.5 py-0.5 rounded">
                VERIFIABLE CERTIFICATION
              </span>
            </div>
            <p className="mt-1 font-mono text-sm font-semibold text-zinc-300">
              Evidence-based cryptographic certification synthesizing code change analysis, scenarios, agent runs, and policies
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={handleIssuePassport}
            disabled={evaluating || !selectedReleaseId}
            className="inline-flex items-center gap-2 rounded-lg bg-amber-500 hover:bg-amber-600 px-4 py-2 font-mono text-xs font-extrabold uppercase tracking-wider text-black transition-all shadow-md active:scale-95 disabled:opacity-50"
          >
            {evaluating ? (
              <RotateCcw className="h-3.5 w-3.5 animate-spin text-black" />
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
              : 'amber'
          }
          icon={ShieldCheck}
        />
        <StatTile
          label="Release Version"
          value={selectedRelease ? selectedRelease.version : 'N/A'}
          subvalue="candidate bundle"
          accent="amber"
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
            <div className="flex items-center justify-between border-b border-zinc-800 pb-3">
              <span className="font-mono text-xs uppercase font-bold text-amber-500">
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
                    className={`cursor-pointer rounded-xl border border-t p-4 backdrop-blur-md transition-all duration-200 shadow-[0_8px_32px_0_rgba(0,0,0,0.6)] ${
                      isSelected
                        ? 'border-zinc-600 border-t-zinc-400 bg-[#161a25]/95 ring-1 ring-amber-500/40'
                        : 'border-[#232736] border-t-zinc-700/50 bg-[#12151e]/92 hover:border-[#343b52]'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-mono text-xs font-bold text-white">
                        {rel.version}
                      </span>
                      <span className="font-mono text-[10px] font-bold uppercase tracking-wider text-amber-400 bg-zinc-900 border border-zinc-800 px-2 py-0.5 rounded">
                        {rel.target_environment}
                      </span>
                    </div>

                    <p className="mt-1 text-xs font-medium text-zinc-300 font-sans">
                      {rel.name}
                    </p>

                    <div className="mt-2 font-mono text-[11px] text-zinc-400 truncate">
                      Commit: <strong className="text-amber-400 font-semibold">{rel.commit_hash.slice(0, 12)}</strong>
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
              <ShieldCheck className="mx-auto h-12 w-12 text-zinc-500" />
              <h4 className="mt-3 font-mono text-sm font-bold uppercase tracking-wider text-white">
                Release Passport Not Issued
              </h4>
              <p className="mt-1 text-sm font-medium text-zinc-400">
                Click &quot;Issue / Re-Evaluate Passport&quot; above to synthesize multi-domain verification telemetry.
              </p>
            </GlassPanel>
          ) : (
            <GlassPanel className="p-6 space-y-6">
              {/* Passport Header Banner */}
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-zinc-800 pb-4">
                <div>
                  <div className="flex items-center gap-2.5">
                    <h3 className="font-mono text-lg font-bold text-white tracking-wide">
                      RELEASE PASSPORT // {selectedRelease.version}
                    </h3>
                    {getStatusBadge(passport.overall_status)}
                  </div>
                  <p className="mt-1 font-mono text-xs font-semibold text-zinc-400">
                    Cryptographic Seal: <span className="text-amber-400 font-bold">{passport.passport_hash}</span>
                  </p>
                </div>
              </div>

              {/* Verification Summary (Explicit Transparency Mandate) */}
              <div className="rounded-xl border border-[#232736] border-t border-t-zinc-700/50 bg-[#12151e]/92 p-4 space-y-2 backdrop-blur-md shadow-[0_8px_32px_0_rgba(0,0,0,0.6)]">
                <div className="flex items-center gap-2 font-mono text-xs uppercase font-bold text-amber-500 tracking-wider">
                  <AlertTriangle className="h-4 w-4" />
                  <span>Multi-Domain Verification Summary</span>
                </div>
                <div className="font-mono text-xs text-zinc-300 whitespace-pre-line leading-relaxed bg-black/60 p-3 rounded-xl border border-[#232736]">
                  Cryptographic verification completed across 6 independent domains. Passport integrity validated via SHA-256 seal. Uncertainty quantification reflects bounded confidence in incomplete evidence domains. Explicit denials indicate policy violations requiring mitigation before certification elevation.
                </div>
              </div>

              {/* 6 Verification Domain Cards */}
              <div className="space-y-3">
                <h4 className="font-mono text-xs uppercase font-bold text-amber-500 tracking-wider">
                  Evaluation Domains Breakdown (6 Dimensions)
                </h4>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3.5">
                  {/* Domain 1: Code Change Analysis */}
                  <div className="rounded-xl border border-[#232736] border-t border-t-zinc-700/50 bg-[#12151e]/92 p-4 space-y-2 backdrop-blur-md shadow-[0_8px_32px_0_rgba(0,0,0,0.6)]">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2 font-mono text-xs font-bold text-white">
                        <GitCommit className="h-4 w-4 text-amber-400" />
                        <span>Code Change Analysis</span>
                      </div>
                      {getStatusBadge(passport.code_change_analysis.status)}
                    </div>
                    <div className="font-mono text-xs text-zinc-300 space-y-1">
                      <div>Total Changes: <strong className="text-white font-bold">{passport.code_change_analysis.total_changes}</strong></div>
                      <div>Breaking Changes: <strong className="text-amber-400 font-bold">{passport.code_change_analysis.breaking_changes_count}</strong></div>
                      <div>Max Risk Score: <strong className="text-white font-bold">{passport.code_change_analysis.max_risk_score}/100</strong></div>
                    </div>
                  </div>

                  {/* Domain 2: Context Findings */}
                  <div className="rounded-xl border border-[#232736] border-t border-t-zinc-700/50 bg-[#12151e]/92 p-4 space-y-2 backdrop-blur-md shadow-[0_8px_32px_0_rgba(0,0,0,0.6)]">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2 font-mono text-xs font-bold text-white">
                        <Layers className="h-4 w-4 text-amber-400" />
                        <span>Context Findings</span>
                      </div>
                      {getStatusBadge(passport.context_findings.status)}
                    </div>
                    <div className="font-mono text-xs text-zinc-300 space-y-1">
                      <div>Total Discrepancies: <strong className="text-white font-bold">{passport.context_findings.total_findings}</strong></div>
                      <div>Critical Drifts: <strong className="text-rose-400 font-bold">{passport.context_findings.critical_count}</strong></div>
                      <div>Open Findings: <strong className="text-amber-400 font-bold">{passport.context_findings.open_findings}</strong></div>
                    </div>
                  </div>

                  {/* Domain 3: Scenario Testing */}
                  <div className="rounded-xl border border-[#232736] border-t border-t-zinc-700/50 bg-[#12151e]/92 p-4 space-y-2 backdrop-blur-md shadow-[0_8px_32px_0_rgba(0,0,0,0.6)]">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2 font-mono text-xs font-bold text-white">
                        <Zap className="h-4 w-4 text-amber-400" />
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
                  <div className="rounded-xl border border-[#232736] border-t border-t-zinc-700/50 bg-[#12151e]/92 p-4 space-y-2 backdrop-blur-md shadow-[0_8px_32px_0_rgba(0,0,0,0.6)]">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2 font-mono text-xs font-bold text-white">
                        <Bot className="h-4 w-4 text-amber-400" />
                        <span>Agent Behavior Lab</span>
                      </div>
                      {getStatusBadge(passport.agent_testing.status)}
                    </div>
                    <div className="font-mono text-xs text-zinc-300 space-y-1">
                      <div>Runs Captured: <strong className="text-white font-bold">{passport.agent_testing.total_runs}</strong></div>
                      <div>Policy Violations: <strong className="text-rose-400 font-bold">{passport.agent_testing.policy_violations}</strong></div>
                      <div>Evaluated Models: <strong className="text-amber-400 font-bold">{passport.agent_testing.evaluated_models.join(', ') || 'None'}</strong></div>
                    </div>
                  </div>

                  {/* Domain 5: Policy Validation */}
                  <div className="rounded-xl border border-[#232736] border-t border-t-zinc-700/50 bg-[#12151e]/92 p-4 space-y-2 backdrop-blur-md shadow-[0_8px_32px_0_rgba(0,0,0,0.6)]">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2 font-mono text-xs font-bold text-white">
                        <ShieldCheck className="h-4 w-4 text-amber-400" />
                        <span>Trust Layer Validation</span>
                      </div>
                      {getStatusBadge(passport.policy_validation.status)}
                    </div>
                    <div className="font-mono text-xs text-zinc-300 space-y-1">
                      <div>Evaluations: <strong className="text-white font-bold">{passport.policy_validation.total_evaluations}</strong></div>
                      <div>Explicit Denials: <strong className="text-rose-400 font-bold">{passport.policy_validation.denied_count}</strong></div>
                      <div>Pending Reviews: <strong className="text-amber-400 font-bold">{passport.policy_validation.review_required_count}</strong></div>
                    </div>
                  </div>

                  {/* Domain 6: Evidence Completeness */}
                  <div className="rounded-xl border border-[#232736] border-t border-t-zinc-700/50 bg-[#12151e]/92 p-4 space-y-2 backdrop-blur-md shadow-[0_8px_32px_0_rgba(0,0,0,0.6)]">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2 font-mono text-xs font-bold text-white">
                        <FileCheck className="h-4 w-4 text-amber-400" />
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
