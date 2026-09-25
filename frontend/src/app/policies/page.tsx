'use client';

import React, { useEffect, useState, useCallback } from 'react';
import {
  Shield,
  ShieldAlert,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Play,
  RotateCcw,
  Layers,
  Lock,
  FileCheck,
  Check,
  ExternalLink,
} from 'lucide-react';
import { GlassPanel } from '@/components/ui/glass-panel';
import { PerspectiveGrid } from '@/components/ui/perspective-grid';
import { StatTile } from '@/components/ui/stat-tile';
import { StatusBadge } from '@/components/ui/status-badge';
import {
  getTrustPolicies,
  getTrustPermissions,
  getTrustResources,
  evaluateTrustPolicy,
  getPolicyDecisions,
  reviewPolicyDecision,
  TrustPolicy,
  PermissionItem,
  TrustResourceItem,
  PolicyDecisionItem,
} from '@/lib/api';

export default function PoliciesPage() {
  const [policies, setPolicies] = useState<TrustPolicy[]>([]);
  const [permissions, setPermissions] = useState<PermissionItem[]>([]);
  const [resources, setResources] = useState<TrustResourceItem[]>([]);
  const [decisions, setDecisions] = useState<PolicyDecisionItem[]>([]);
  const [loading, setLoading] = useState(true);

  // Simulator state
  const [principal, setPrincipal] = useState('autonomous_agent');
  const [resource, setResource] = useState('sandbox-orders-db');
  const [action, setAction] = useState('drop_table');
  const [simulating, setSimulating] = useState(false);
  const [simResult, setSimResult] = useState<{
    result: string;
    reason: string;
    matched_policies: string[];
    evidence?: Record<string, unknown> | null;
  } | null>(null);

  const fetchTrustData = useCallback(async () => {
    try {
      setLoading(true);
      const [polList, permList, resList, decList] = await Promise.all([
        getTrustPolicies(),
        getTrustPermissions(),
        getTrustResources(),
        getPolicyDecisions(),
      ]);
      setPolicies(polList);
      setPermissions(permList);
      setResources(resList);
      setDecisions(decList);
    } catch (err) {
      console.error('Failed to load Trust Layer:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchTrustData();
  }, [fetchTrustData]);

  const handleSimulate = async () => {
    try {
      setSimulating(true);
      const res = await evaluateTrustPolicy({
        principal_name: principal,
        resource_name: resource,
        action_name: action,
        is_sandbox: true,
      });
      setSimResult(res);
      // Refresh decisions
      const updatedDecs = await getPolicyDecisions();
      setDecisions(updatedDecs);
    } catch (err) {
      console.error('Evaluation failed:', err);
    } finally {
      setSimulating(false);
    }
  };

  const handleReview = async (id: string, reviewStatus: 'approved' | 'rejected') => {
    try {
      await reviewPolicyDecision(id, reviewStatus, 'security_admin@mirror-x.internal');
      setDecisions((prev) =>
        prev.map((d) => (d.id === id ? { ...d, review_status: reviewStatus } : d))
      );
    } catch (err) {
      console.error('Review update failed:', err);
    }
  };

  const blockedCount = decisions.filter((d) => d.result === 'DENY').length;
  const reviewRequiredCount = decisions.filter((d) => d.result === 'HUMAN_REVIEW_REQUIRED').length;
  const allowCount = decisions.filter((d) => d.result === 'ALLOW').length;

  return (
    <div className="relative min-h-[calc(100vh-3.5rem)] overflow-hidden canvas-textured text-white p-6 space-y-6">
      <PerspectiveGrid />

      {/* Header */}
      <div className="relative z-10 flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-zinc-800 pb-5">
        <div className="flex items-center gap-3.5">
          <div className="flex h-11 w-11 items-center justify-center rounded-xl border border-zinc-800 bg-zinc-900/80 text-amber-500">
            <Shield className="h-5 w-5" />
          </div>
          <div>
            <div className="flex items-center gap-2.5">
              <h1 className="text-2xl font-bold tracking-tight text-white font-sans drop-shadow-[0_2px_12px_rgba(0,0,0,0.8)]">
                Trust Layer: Policy &amp; Permissions
              </h1>
              <span className="font-mono text-xs font-bold uppercase tracking-wider text-amber-500 bg-zinc-900/80 border border-zinc-800 px-2.5 py-0.5 rounded">
                SANDBOX GOVERNANCE GATE
              </span>
            </div>
            <p className="mt-1 font-mono text-sm font-semibold text-zinc-300">
              Strict policy enforcement, human-in-the-loop review requirements, and sandbox isolation
            </p>
          </div>
        </div>

        {/* Security Isolation Indicator */}
        <div className="flex items-center gap-2 rounded-lg border border-amber-500/40 bg-zinc-900/80 px-3 py-1.5 font-mono text-xs font-bold text-amber-400">
          <Lock className="h-4 w-4" />
          <span>PRODUCTION ACTIONS PROHIBITED</span>
        </div>
      </div>

      {/* KPI Ribbon */}
      <div className="relative z-10 grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatTile
          label="Active Policies"
          value={policies.length}
          subvalue="governance rules"
          accent="amber"
          icon={Shield}
        />
        <StatTile
          label="Allowed Operations"
          value={allowCount}
          subvalue="nominal sandbox actions"
          accent="emerald"
          icon={CheckCircle2}
        />
        <StatTile
          label="Review Required"
          value={reviewRequiredCount}
          subvalue="sensitive / destructive gates"
          accent="amber"
          icon={AlertTriangle}
        />
        <StatTile
          label="Blocked Actions"
          value={blockedCount}
          subvalue="policy denials"
          accent="crimson"
          icon={XCircle}
        />
      </div>

      {/* Policy Simulator Interactive Card */}
      <GlassPanel className="relative z-10 p-5 space-y-4">
        <div className="flex items-center justify-between border-b border-zinc-800 pb-3">
          <div className="flex items-center gap-2 font-mono text-xs uppercase font-bold text-amber-500">
            <Play className="h-4 w-4" />
            <span>Interactive Policy Decision Simulator</span>
          </div>
          <span className="font-mono text-xs font-bold text-zinc-400">
            100% Mock / Sandbox Isolation
          </span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-4 gap-3.5 items-end">
          <div>
            <label className="block font-mono text-xs uppercase font-bold text-zinc-400 mb-1">
              Principal Identity
            </label>
            <select
              value={principal}
              onChange={(e) => setPrincipal(e.target.value)}
              className="w-full rounded-lg border border-[#232736] bg-zinc-900/80 px-3.5 py-2 font-mono text-xs font-bold text-white focus:border-zinc-600 focus:outline-none"
            >
              <option value="autonomous_agent">autonomous_agent (AI)</option>
              <option value="developer">developer (Human)</option>
              <option value="ci_pipeline">ci_pipeline (System)</option>
            </select>
          </div>

          <div>
            <label className="block font-mono text-xs uppercase font-bold text-zinc-400 mb-1">
              Target Resource
            </label>
            <select
              value={resource}
              onChange={(e) => setResource(e.target.value)}
              className="w-full rounded-lg border border-[#232736] bg-zinc-900/80 px-3.5 py-2 font-mono text-xs font-bold text-white focus:border-zinc-600 focus:outline-none"
            >
              {resources.map((r) => (
                <option key={r.name} value={r.name}>
                  {r.name} ({r.classification})
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block font-mono text-xs uppercase font-bold text-zinc-400 mb-1">
              Action Name
            </label>
            <select
              value={action}
              onChange={(e) => setAction(e.target.value)}
              className="w-full rounded-lg border border-[#232736] bg-zinc-900/80 px-3.5 py-2 font-mono text-xs font-bold text-white focus:border-zinc-600 focus:outline-none"
            >
              <option value="read">read (Safe inspection)</option>
              <option value="write">write (Sandbox mutation)</option>
              <option value="drop_table">drop_table (Destructive action)</option>
              <option value="schema_alter">schema_alter (Schema alteration)</option>
              <option value="delete">delete (Data removal)</option>
            </select>
          </div>

          <button
            onClick={handleSimulate}
            disabled={simulating}
            className="w-full inline-flex items-center justify-center gap-2 rounded-lg bg-amber-500 hover:bg-amber-600 px-4 py-2 font-mono text-xs font-extrabold uppercase tracking-wider text-black transition-all shadow-md active:scale-95 disabled:opacity-50"
          >
            {simulating ? (
              <RotateCcw className="h-4 w-4 animate-spin text-black" />
            ) : (
              <Play className="h-4 w-4 fill-current" />
            )}
            <span>Evaluate Policy Gate</span>
          </button>
        </div>

        {simResult && (
          <div className="mt-3 rounded-xl border border-[#232736] border-t border-t-zinc-700/50 bg-[#12151e]/92 p-4 space-y-2 backdrop-blur-md shadow-[0_8px_32px_0_rgba(0,0,0,0.6)]">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="font-mono text-xs font-bold text-zinc-400">Decision:</span>
                <span
                  className={`font-mono text-xs font-bold uppercase px-2.5 py-0.5 rounded-lg border ${
                    simResult.result === 'ALLOW'
                      ? 'bg-emerald-950/60 text-emerald-400 border-emerald-500/40'
                      : simResult.result === 'DENY'
                      ? 'bg-rose-950/60 text-rose-400 border-rose-500/40'
                      : 'bg-amber-950/60 text-amber-400 border-amber-500/40'
                  }`}
                >
                  {simResult.result}
                </span>
              </div>
              {simResult.evidence && (
                <div className="flex items-center gap-1.5 font-mono text-xs font-bold text-amber-400">
                  <FileCheck className="h-4 w-4" />
                  <span>Evidence Created ({String(simResult.evidence.hash_signature).slice(0, 10)}...)</span>
                </div>
              )}
            </div>
            <p className="text-sm font-medium text-zinc-300 font-sans">
              {simResult.reason}
            </p>
          </div>
        )}
      </GlassPanel>

      {/* Dual Pane: Governance Matrix (Left) & Policy Decisions Audit Trail (Right) */}
      <div className="relative z-10 grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Left Column: Governance Policies & Permissions */}
        <div className="lg:col-span-6 space-y-4">
          <GlassPanel className="p-5 space-y-4">
            <div className="flex items-center justify-between border-b border-zinc-800 pb-3">
              <div className="flex items-center gap-2 font-mono text-xs uppercase font-bold text-amber-500">
                <ShieldAlert className="h-4 w-4" />
                <span>Governance Policies ({policies.length})</span>
              </div>
              <span className="font-mono text-xs font-bold text-amber-500">MANDATORY ENFORCEMENT</span>
            </div>

            <div className="space-y-2.5">
              {policies.map((p, idx) => (
                <div
                  key={idx}
                  className="rounded-xl border border-[#232736] border-t border-t-zinc-700/50 bg-[#12151e]/92 p-4 space-y-1.5 backdrop-blur-md shadow-[0_8px_32px_0_rgba(0,0,0,0.6)]"
                >
                  <div className="flex items-center justify-between">
                    <span className="font-mono text-sm font-bold text-white">{p.name}</span>
                    <span className="font-mono text-[10px] font-bold uppercase tracking-wider text-amber-400 bg-zinc-900 border border-zinc-800 px-2 py-0.5 rounded">
                      {p.enforcement_level}
                    </span>
                  </div>
                  <p className="text-xs font-medium text-zinc-300 font-sans">
                    {p.description}
                  </p>
                </div>
              ))}
            </div>
          </GlassPanel>

          {/* Permissions Matrix */}
          <GlassPanel className="p-5 space-y-4">
            <div className="flex items-center justify-between border-b border-zinc-800 pb-3">
              <div className="flex items-center gap-2 font-mono text-xs uppercase font-bold text-amber-500">
                <Layers className="h-4 w-4" />
                <span>Agent Permissions &amp; Resource Bindings</span>
              </div>
            </div>

            <div className="space-y-2">
              {permissions.map((perm, idx) => (
                <div
                  key={idx}
                  className="flex items-center justify-between p-3 rounded-xl border border-[#232736] bg-zinc-900/40 font-mono text-xs"
                >
                  <div className="space-y-0.5">
                    <div className="text-white font-bold">{perm.name}</div>
                    <div className="text-zinc-400">
                      Role: <strong className="text-amber-400">{perm.principal_role}</strong> → Action: <strong className="text-white">{perm.action_name}</strong> on <strong className="text-amber-400">{perm.resource_type}</strong>
                    </div>
                  </div>
                  <span className={`font-bold px-2 py-0.5 rounded border ${perm.effect === 'ALLOW' ? 'text-emerald-400 border-emerald-500/30 bg-emerald-950/40' : 'text-rose-400 border-rose-500/30 bg-rose-950/40'}`}>
                    {perm.effect}
                  </span>
                </div>
              ))}
            </div>
          </GlassPanel>
        </div>

        {/* Right Column: Policy Decision Audit Trail */}
        <div className="lg:col-span-6 space-y-4">
          <GlassPanel className="p-5 space-y-4">
            <div className="flex items-center justify-between border-b border-zinc-800 pb-3">
              <div className="flex items-center gap-2 font-mono text-xs uppercase font-bold text-amber-500">
                <FileCheck className="h-4 w-4" />
                <span>Policy Decision Audit Trail ({decisions.length})</span>
              </div>
              <span className="font-mono text-xs font-bold text-zinc-400">Live Provenance Log</span>
            </div>

            {decisions.length === 0 ? (
              <div className="py-16 text-center font-mono text-xs font-semibold text-zinc-400">
                No policy decisions logged yet. Use the simulator above to evaluate actions.
              </div>
            ) : (
              <div className="space-y-3 max-h-[700px] overflow-y-auto pr-1 scrollbar-thin">
                {decisions.map((dec) => {
                  const isReviewRequired = dec.result === 'HUMAN_REVIEW_REQUIRED';
                  const isApproved = dec.review_status === 'approved';

                  return (
                    <div
                      key={dec.id}
                      className="rounded-xl border border-[#232736] border-t border-t-zinc-700/50 bg-[#12151e]/92 p-4 space-y-2 backdrop-blur-md shadow-[0_8px_32px_0_rgba(0,0,0,0.6)]"
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <span
                            className={`font-mono text-xs font-bold uppercase px-2 py-0.5 rounded border ${
                              dec.result === 'ALLOW'
                                ? 'bg-emerald-950/60 text-emerald-400 border-emerald-500/40'
                                : dec.result === 'DENY'
                                ? 'bg-rose-950/60 text-rose-400 border-rose-500/40'
                                : 'bg-amber-950/60 text-amber-400 border-amber-500/40'
                            }`}
                          >
                            {dec.result}
                          </span>
                          <span className="font-mono text-xs font-bold text-white">
                            {dec.action_name} on {dec.resource_name}
                          </span>
                        </div>

                        {dec.evidence_id && (
                          <span className="font-mono text-[10px] font-bold text-amber-400 flex items-center gap-1">
                            <FileCheck className="h-3 w-3" /> EVI RECORD
                          </span>
                        )}
                      </div>

                      <p className="text-xs font-medium text-zinc-300 font-sans">
                        {dec.reason}
                      </p>

                      <div className="flex items-center justify-between font-mono text-[11px] text-zinc-400 pt-1 border-t border-zinc-800">
                        <span>Principal: <strong className="text-white font-bold">{dec.principal_name}</strong></span>

                        {isReviewRequired && (
                          <div className="flex items-center gap-2">
                            {isApproved ? (
                              <span className="text-emerald-400 font-bold uppercase flex items-center gap-1">
                                <Check className="h-3.5 w-3.5" /> Approved
                              </span>
                            ) : (
                              <button
                                onClick={() => handleReview(dec.id, 'approved')}
                                className="px-3 py-1 rounded-lg bg-amber-500 hover:bg-amber-600 font-mono text-xs font-extrabold uppercase tracking-wider text-black transition-all shadow-sm active:scale-95"
                              >
                                Sign Off (Approve)
                              </button>
                            )}
                          </div>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </GlassPanel>
        </div>
      </div>
    </div>
  );
}
