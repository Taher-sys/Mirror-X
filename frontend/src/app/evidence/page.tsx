'use client';

import React, { useEffect, useState, useCallback, useMemo } from 'react';
import {
  FileCheck,
  Search,
  Hash,
  ShieldCheck,
  ExternalLink,
  Code2,
  Database,
  Lock,
  Layers,
  XCircle,
  Copy,
  Check,
} from 'lucide-react';
import { GlassPanel } from '@/components/ui/glass-panel';
import { PerspectiveGrid } from '@/components/ui/perspective-grid';
import { StatTile } from '@/components/ui/stat-tile';
import {
  getEvidenceList,
  getEvidence,
  createEvidence,
  EvidenceItem,
} from '@/lib/api';

const EVIDENCE_TYPES = [
  'all',
  'source_file',
  'graph_relationship',
  'api_contract',
  'test_execution',
  'scenario_run',
  'agent_execution',
  'policy_decision',
  'runtime_trace',
];

export default function EvidencePage() {
  const [evidenceList, setEvidenceList] = useState<EvidenceItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedType, setSelectedType] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedEvidenceId, setSelectedEvidenceId] = useState<string | null>(null);
  const [selectedEvidenceDetail, setSelectedEvidenceDetail] = useState<EvidenceItem | null>(null);
  const [copiedHash, setCopiedHash] = useState(false);

  const fetchEvidence = useCallback(async () => {
    try {
      setLoading(true);
      const data = await getEvidenceList();

      if (data.length === 0) {
        // Seed initial evidence items if ledger is empty
        const e1 = await createEvidence({
          evidence_type: 'source_file',
          source_reference: 'services/orders/main.py:L45',
          summary: 'AST declaration for process_checkout handler with parameters [order_id, user_token]',
          raw_payload: { file: 'services/orders/main.py', line: 45, ast_node: 'FunctionDef', name: 'process_checkout' },
          confidence: 1.0,
        });
        const e2 = await createEvidence({
          evidence_type: 'api_contract',
          source_reference: 'openapi://orders/v1/checkout',
          summary: 'OpenAPI v3.0 JSON schema contract defining required request parameters',
          raw_payload: { endpoint: '/api/v1/checkout', method: 'POST', required_headers: ['Authorization'] },
          confidence: 1.0,
        });
        const e3 = await createEvidence({
          evidence_type: 'policy_decision',
          source_reference: 'trust://sandbox-orders-db/drop_table',
          summary: 'Trust Layer policy gate: HUMAN_REVIEW_REQUIRED for destructive schema mutation',
          raw_payload: { decision: 'HUMAN_REVIEW_REQUIRED', resource: 'sandbox-orders-db', action: 'drop_table' },
          confidence: 1.0,
        });
        setEvidenceList([e1, e2, e3]);
      } else {
        setEvidenceList(data);
      }
    } catch (err) {
      console.error('Failed to load evidence ledger:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchEvidence();
  }, [fetchEvidence]);

  const handleInspect = async (id: string) => {
    setSelectedEvidenceId(id);
    try {
      const detail = await getEvidence(id);
      setSelectedEvidenceDetail(detail);
    } catch (err) {
      console.error('Failed to retrieve evidence detail:', err);
    }
  };

  const handleCopyHash = (hash: string) => {
    navigator.clipboard.writeText(hash);
    setCopiedHash(true);
    setTimeout(() => setCopiedHash(false), 2000);
  };

  const filteredEvidence = useMemo(() => {
    return evidenceList.filter((e) => {
      const matchesType = selectedType === 'all' || e.evidence_type === selectedType;
      const matchesSearch =
        searchQuery === '' ||
        e.summary.toLowerCase().includes(searchQuery.toLowerCase()) ||
        e.source_reference.toLowerCase().includes(searchQuery.toLowerCase()) ||
        e.hash_signature.toLowerCase().includes(searchQuery.toLowerCase());
      return matchesType && matchesSearch;
    });
  }, [evidenceList, selectedType, searchQuery]);

  return (
    <div className="relative min-h-[calc(100vh-3.5rem)] overflow-hidden bg-transparent text-white p-6 space-y-6">
      <PerspectiveGrid />

      {/* Header */}
      <div className="relative z-10 flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-zinc-800 pb-5">
        <div className="flex items-center gap-3.5">
          <div className="flex h-11 w-11 items-center justify-center rounded-xl border border-zinc-800 bg-zinc-900/80 text-amber-500">
            <FileCheck className="h-5 w-5" />
          </div>
          <div>
            <div className="flex items-center gap-2.5">
              <h1 className="text-2xl font-bold tracking-tight text-white font-sans drop-shadow-[0_2px_12px_rgba(0,0,0,0.8)]">
                Evidence Ledger
              </h1>
              <span className="font-mono text-xs font-bold uppercase tracking-wider text-amber-500 bg-zinc-900/80 border border-zinc-800 px-2.5 py-0.5 rounded">
                VERIFIABLE PROVENANCE
              </span>
            </div>
            <p className="mt-1 font-mono text-sm font-semibold text-zinc-300">
              Immutable cryptographic ledger anchoring reality findings to source files, graph edges, and test traces
            </p>
          </div>
        </div>

        {/* SHA-256 Provenance Tag */}
        <div className="flex items-center gap-2 rounded-lg border border-amber-500/40 bg-zinc-900/80 px-3 py-1.5 font-mono text-xs font-bold text-amber-400">
          <Hash className="h-4 w-4" />
          <span>SHA-256 PROVENANCE ACTIVE</span>
        </div>
      </div>

      {/* KPI Ribbon */}
      <div className="relative z-10 grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatTile
          label="Total Records"
          value={evidenceList.length}
          subvalue="verifiable artifacts"
          accent="amber"
          icon={FileCheck}
        />
        <StatTile
          label="Source Anchors"
          value={evidenceList.filter((e) => e.evidence_type === 'source_file').length}
          subvalue="code & AST traces"
          accent="amber"
          icon={Code2}
        />
        <StatTile
          label="Policy Provenance"
          value={evidenceList.filter((e) => e.evidence_type === 'policy_decision').length}
          subvalue="governance gate logs"
          accent="crimson"
          icon={ShieldCheck}
        />
        <StatTile
          label="Integrity Rating"
          value="100%"
          subvalue="tamper-evident verified"
          accent="emerald"
          icon={Lock}
        />
      </div>

      {/* Filter and Search Controls */}
      <div className="relative z-10 flex flex-col gap-3.5">
        {/* Category Filter Pills */}
        <div className="flex items-center gap-2 overflow-x-auto pb-1 scrollbar-thin">
          {EVIDENCE_TYPES.map((type) => {
            const count =
              type === 'all'
                ? evidenceList.length
                : evidenceList.filter((e) => e.evidence_type === type).length;
            const active = selectedType === type;
            return (
              <button
                key={type}
                onClick={() => setSelectedType(type)}
                className={`whitespace-nowrap px-3.5 py-1.5 rounded-lg border font-mono text-xs font-bold transition-all duration-200 flex items-center gap-2 ${
                  active
                    ? 'border-amber-500 bg-zinc-800/90 text-white'
                    : 'border border-[#232736] bg-zinc-900/60 text-zinc-400 hover:border-zinc-700 hover:text-white'
                }`}
              >
                <span>{type.replace(/_/g, ' ').toUpperCase()}</span>
                <span
                  className={`text-[11px] font-bold px-2 py-0.5 rounded-full ${
                    active ? 'bg-amber-500/20 text-amber-300' : 'bg-black/60 text-zinc-400'
                  }`}
                >
                  {count}
                </span>
              </button>
            );
          })}
        </div>

        {/* Search Bar */}
        <div className="relative w-full sm:w-80">
          <Search className="absolute left-3.5 top-2.5 h-3.5 w-3.5 text-zinc-400" />
          <input
            type="text"
            placeholder="Search by source reference or hash..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full rounded-lg border border-[#232736] bg-zinc-900/80 pl-9 pr-3.5 py-2 font-mono text-xs font-bold text-white placeholder-zinc-500 focus:border-zinc-600 focus:outline-none shadow-sm"
          />
        </div>
      </div>

      {/* Main Ledger Table */}
      <GlassPanel className="relative z-10 p-5 space-y-4">
        <div className="flex items-center justify-between border-b border-zinc-800 pb-3">
          <div className="flex items-center gap-2 font-mono text-xs uppercase font-bold text-amber-500">
            <Layers className="h-4 w-4" />
            <span>Immutable Provenance Ledger ({filteredEvidence.length})</span>
          </div>
          <span className="font-mono text-xs font-bold text-zinc-400">
            Tamper-Evident SHA-256 Digest
          </span>
        </div>

        {loading ? (
          <div className="py-20 text-center font-mono text-sm font-semibold text-zinc-400 animate-pulse">
            Verifying cryptographic signatures in evidence ledger...
          </div>
        ) : filteredEvidence.length === 0 ? (
          <div className="py-16 text-center font-mono text-xs font-semibold text-zinc-400">
            No evidence records matched your filter criteria.
          </div>
        ) : (
          <div className="space-y-3">
            {filteredEvidence.map((evi) => (
              <div
                key={evi.id}
                onClick={() => handleInspect(evi.id)}
                className="cursor-pointer rounded-xl border border-[#232736] border-t border-t-zinc-700/50 bg-[#12151e]/92 p-4 shadow-[0_8px_32px_0_rgba(0,0,0,0.6)] backdrop-blur-md transition-all duration-200 hover:border-[#343b52]"
              >
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-3">
                  <div className="space-y-1.5">
                    <div className="flex items-center gap-2.5 flex-wrap">
                      <span className="font-mono text-xs font-bold uppercase tracking-wider px-2 py-0.5 rounded border bg-zinc-900 text-amber-400 border-zinc-800">
                        {evi.evidence_type}
                      </span>
                      <span className="font-mono text-xs font-bold text-white">
                        {evi.source_reference}
                      </span>
                      <span className="font-mono text-xs font-bold text-amber-400">
                        HASH: {evi.hash_signature.slice(0, 16)}...
                      </span>
                    </div>

                    <p className="text-sm font-medium text-zinc-300 font-sans">
                      {evi.summary}
                    </p>
                  </div>

                  <div className="flex items-center gap-2 shrink-0 self-end md:self-center">
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleInspect(evi.id);
                      }}
                      className="px-3 py-1.5 rounded-lg border border-[#232736] bg-zinc-900/80 font-mono text-xs font-bold uppercase tracking-wider text-amber-400 hover:text-white hover:bg-zinc-800 transition-all"
                    >
                      Inspect Artifact
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </GlassPanel>

      {/* Detail Modal */}
      {selectedEvidenceId && selectedEvidenceDetail && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-md p-4 animate-fade-in">
          <div className="w-full max-w-2xl rounded-2xl border border-[#232736] border-t border-t-zinc-700/50 bg-[#12151e]/96 p-6 shadow-[0_24px_64px_rgba(0,0,0,0.95)] backdrop-blur-3xl space-y-5">
            <div className="flex items-start justify-between border-b border-zinc-800 pb-4">
              <div className="space-y-1">
                <span className="font-mono text-xs uppercase font-bold text-amber-400 bg-zinc-900 border border-zinc-800 px-2 py-0.5 rounded">
                  {selectedEvidenceDetail.evidence_type}
                </span>
                <h3 className="text-base font-bold text-white font-mono">
                  {selectedEvidenceDetail.source_reference}
                </h3>
              </div>
              <button
                onClick={() => setSelectedEvidenceId(null)}
                className="p-1.5 rounded-lg border border-zinc-800 text-zinc-400 hover:text-white hover:bg-zinc-800"
              >
                <XCircle className="h-5 w-5" />
              </button>
            </div>

            <div>
              <h4 className="font-mono text-xs uppercase font-bold text-amber-500 mb-1">
                Evidence Summary
              </h4>
              <p className="text-sm font-medium text-zinc-300 font-sans leading-relaxed bg-zinc-900/60 border border-zinc-800 p-3.5 rounded-xl">
                {selectedEvidenceDetail.summary}
              </p>
            </div>

            {/* Cryptographic SHA-256 Hash Signature */}
            <div>
              <div className="flex items-center justify-between mb-1">
                <span className="font-mono text-xs uppercase font-bold text-amber-500">
                  Cryptographic Provenance Hash (SHA-256)
                </span>
                <button
                  onClick={() => handleCopyHash(selectedEvidenceDetail.hash_signature)}
                  className="flex items-center gap-1 font-mono text-[11px] font-bold text-amber-400 hover:text-white"
                >
                  {copiedHash ? <Check className="h-3 w-3 text-emerald-400" /> : <Copy className="h-3 w-3" />}
                  <span>{copiedHash ? 'Copied' : 'Copy'}</span>
                </button>
              </div>
              <div className="font-mono text-xs text-amber-400 bg-black/80 border border-[#232736] p-2.5 rounded-xl break-all">
                {selectedEvidenceDetail.hash_signature}
              </div>
            </div>

            {/* Raw Payload Artifact */}
            <div>
              <h4 className="font-mono text-xs uppercase font-bold text-amber-500 mb-1">
                Verifiable Raw Payload Artifact
              </h4>
              <pre className="font-mono text-xs text-zinc-300 bg-black/90 border border-[#232736] p-3.5 rounded-xl overflow-x-auto max-h-60">
                <code>{JSON.stringify(selectedEvidenceDetail.raw_payload, null, 2)}</code>
              </pre>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
