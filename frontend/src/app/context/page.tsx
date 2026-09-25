'use client';

import React, { useEffect, useState, useMemo } from 'react';
import Link from 'next/link';
import {
  AlertTriangle,
  CheckCircle2,
  ChevronRight,
  Code2,
  FileText,
  Filter,
  Layers,
  RefreshCw,
  Search,
  ShieldAlert,
  XCircle,
  Database,
  ExternalLink,
} from 'lucide-react';
import { GlassPanel } from '@/components/ui/glass-panel';
import { PerspectiveGrid } from '@/components/ui/perspective-grid';
import { StatTile } from '@/components/ui/stat-tile';
import { StatusBadge } from '@/components/ui/status-badge';
import {
  analyzeContext,
  getContextFindings,
  getContextFindingDetail,
  updateFindingStatus,
  getContextStatistics,
  Finding,
  FindingDetailResponse,
  ContextStatistics,
} from '@/lib/api';

const DISCREPANCY_TABS = [
  { id: 'all', label: 'All Drift' },
  { id: 'endpoint_mismatch', label: 'Endpoint Mismatch' },
  { id: 'schema_mismatch', label: 'Schema Mismatch' },
  { id: 'naming_mismatch', label: 'Naming Drift' },
  { id: 'documentation_drift', label: 'Doc Drift' },
  { id: 'missing_documentation', label: 'Missing Docs' },
  { id: 'stale_references', label: 'Stale Refs' },
  { id: 'contradictory_declarations', label: 'Contradictions' },
];

const SEVERITY_OPTIONS = ['all', 'critical', 'high', 'medium', 'low'];

export default function ContextPage() {
  const [findings, setFindings] = useState<Finding[]>([]);
  const [stats, setStats] = useState<ContextStatistics | null>(null);
  const [loading, setLoading] = useState(true);
  const [scanning, setScanning] = useState(false);
  const [selectedType, setSelectedType] = useState('all');
  const [selectedSeverity, setSelectedSeverity] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedFindingId, setSelectedFindingId] = useState<string | null>(null);
  const [detailData, setDetailData] = useState<FindingDetailResponse | null>(null);
  const [loadingDetail, setLoadingDetail] = useState(false);

  const fetchData = async () => {
    try {
      setLoading(true);
      const [findingsData, statsData] = await Promise.all([
        getContextFindings(),
        getContextStatistics().catch(() => null),
      ]);
      setFindings(Array.isArray(findingsData) ? findingsData : []);
      setStats(statsData);
    } catch (err) {
      console.error('Failed to load context findings:', err);
      setFindings([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleRunScan = async () => {
    try {
      setScanning(true);
      await analyzeContext();
      await fetchData();
    } catch (err) {
      console.error('Scan execution failed:', err);
    } finally {
      setScanning(false);
    }
  };

  const handleOpenDetail = async (id: string) => {
    setSelectedFindingId(id);
    setLoadingDetail(true);
    try {
      const data = await getContextFindingDetail(id);
      setDetailData(data);
    } catch (err) {
      console.error('Failed to fetch finding detail:', err);
    } finally {
      setLoadingDetail(false);
    }
  };

  const handleStatusChange = async (id: string, newStatus: string) => {
    try {
      const updated = await updateFindingStatus(id, newStatus);
      setFindings((prev) => (Array.isArray(prev) ? prev.map((f) => (f.id === id ? updated : f)) : []));
      if (detailData && detailData.finding.id === id) {
        setDetailData({ ...detailData, finding: updated });
      }
      const newStats = await getContextStatistics().catch(() => null);
      if (newStats) setStats(newStats);
    } catch (err) {
      console.error('Failed to update status:', err);
    }
  };

  const filteredFindings = useMemo(() => {
    const list = Array.isArray(findings) ? findings : [];
    return list.filter((f) => {
      const matchesType = selectedType === 'all' || f.finding_type === selectedType;
      const matchesSeverity = selectedSeverity === 'all' || f.severity.toLowerCase() === selectedSeverity;
      const matchesSearch =
        searchQuery === '' ||
        f.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
        f.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
        f.finding_type.toLowerCase().includes(searchQuery.toLowerCase());
      return matchesType && matchesSeverity && matchesSearch;
    });
  }, [findings, selectedType, selectedSeverity, searchQuery]);

  return (
    <div className="relative min-h-[calc(100vh-3.5rem)] overflow-hidden canvas-textured text-white p-6 space-y-6">
      <PerspectiveGrid />

      {/* Header */}
      <div className="relative z-10 flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-zinc-800 pb-5">
        <div className="flex items-center gap-3.5">
          <div className="flex h-11 w-11 items-center justify-center rounded-xl border border-zinc-800 bg-zinc-900/80 text-amber-500">
            <ShieldAlert className="h-5 w-5" />
          </div>
          <div>
            <div className="flex items-center gap-2.5">
              <h1 className="text-2xl font-bold tracking-tight text-white font-sans drop-shadow-[0_2px_12px_rgba(0,0,0,0.8)]">
                Context Engine
              </h1>
              <span className="font-mono text-xs font-bold uppercase tracking-wider text-amber-500 bg-zinc-900/80 border border-zinc-800 px-2.5 py-0.5 rounded">
                DRIFT MATRIX
              </span>
            </div>
            <p className="mt-1 font-mono text-sm font-semibold text-zinc-300">
              Deterministic discrepancy detectors contrasting code, API contracts, database schemas, and documentation
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={handleRunScan}
            disabled={scanning}
            className="inline-flex items-center gap-2 rounded-lg bg-amber-500 hover:bg-amber-600 px-4 py-2 font-mono text-xs font-extrabold uppercase tracking-wider text-black transition-all shadow-md active:scale-95 disabled:opacity-50"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${scanning ? 'animate-spin text-black' : ''}`} />
            <span>{scanning ? 'Analyzing Reality...' : 'Run Deep Scan'}</span>
          </button>
        </div>
      </div>

      {/* Telemetry Summary Bento */}
      <div className="relative z-10 grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatTile
          label="Total Discrepancies"
          value={stats ? stats.total_findings : findings.length}
          subvalue="across reality graph"
          accent="amber"
          icon={Layers}
        />
        <StatTile
          label="Critical / High Drifts"
          value={stats ? (stats.findings_by_severity.critical || 0) + (stats.findings_by_severity.high || 0) : 0}
          subvalue="immediate attention"
          accent="crimson"
          icon={AlertTriangle}
        />
        <StatTile
          label="Open Issues"
          value={stats ? stats.findings_by_status.open || 0 : findings.filter((f) => f.status === 'open').length}
          subvalue="unresolved discrepancies"
          accent="amber"
          icon={XCircle}
        />
        <StatTile
          label="Resolution Rate"
          value={stats ? `${(stats.resolution_rate * 100).toFixed(0)}%` : '0%'}
          subvalue="resolved findings"
          accent="amber"
          icon={CheckCircle2}
        />
      </div>

      {/* Filter and Category Controls */}
      <div className="relative z-10 flex flex-col gap-3.5">
        {/* Category Pills */}
        <div className="flex items-center gap-2 overflow-x-auto pb-1 scrollbar-thin">
          {DISCREPANCY_TABS.map((tab) => {
            const count =
              tab.id === 'all'
                ? findings.length
                : findings.filter((f) => f.finding_type === tab.id).length;
            const active = selectedType === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setSelectedType(tab.id)}
                className={`whitespace-nowrap px-3.5 py-1.5 rounded-lg border font-mono text-xs font-bold transition-all duration-200 flex items-center gap-2 ${
                  active
                    ? 'border-amber-500 bg-zinc-800/90 text-white'
                    : 'border border-[#232736] bg-zinc-900/60 text-zinc-400 hover:border-zinc-700 hover:text-white'
                }`}
              >
                <span>{tab.label}</span>
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

        {/* Severity Filters & Search Bar */}
        <div className="flex flex-col sm:flex-row items-center justify-between gap-3">
          <div className="flex items-center gap-1.5 w-full sm:w-auto flex-wrap">
            <span className="font-mono text-xs text-zinc-400 uppercase tracking-wider mr-1 flex items-center gap-1 font-bold">
              <Filter className="h-3.5 w-3.5 text-zinc-400" /> Severity:
            </span>
            {SEVERITY_OPTIONS.map((sev) => {
              const active = selectedSeverity === sev;
              return (
                <button
                  key={sev}
                  onClick={() => setSelectedSeverity(sev)}
                  className={`px-3 py-1 rounded-lg border font-mono text-xs font-bold uppercase tracking-wider transition-all duration-200 ${
                    active
                      ? 'border-amber-500 bg-zinc-800/90 text-white'
                      : 'border border-[#232736] bg-zinc-900/40 text-zinc-400 hover:border-zinc-700 hover:text-white'
                  }`}
                >
                  {sev}
                </button>
              );
            })}
          </div>

          <div className="relative w-full sm:w-72">
            <Search className="absolute left-3.5 top-2.5 h-3.5 w-3.5 text-zinc-400" />
            <input
              type="text"
              placeholder="Search findings or evidence..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full rounded-lg border border-[#232736] bg-zinc-900/80 pl-9 pr-3.5 py-2 font-mono text-xs font-bold text-white placeholder-zinc-500 focus:border-zinc-600 focus:outline-none shadow-sm"
            />
          </div>
        </div>
      </div>

      {/* Main Findings Matrix */}
      <div className="relative z-10">
        {loading ? (
          <div className="py-20 text-center font-mono text-sm font-semibold text-zinc-400 animate-pulse">
            Analyzing reality graph telemetry...
          </div>
        ) : filteredFindings.length === 0 ? (
          <GlassPanel className="py-16 text-center">
            <div className="flex flex-col items-center justify-center p-6">
              <div className="flex h-12 w-12 items-center justify-center rounded-xl border border-zinc-800 bg-zinc-900/80 text-emerald-400 mb-3">
                <CheckCircle2 className="h-6 w-6 stroke-[1.5]" />
              </div>
              <h4 className="font-mono text-sm font-bold uppercase tracking-wider text-zinc-200">
                No Discrepancies Found
              </h4>
              <p className="mt-1.5 max-w-sm text-sm font-medium text-zinc-400 font-sans leading-relaxed">
                Zero discrepancies match the current filter criteria. If you have not ingested repositories yet, trigger a sync to extract reality graph telemetry.
              </p>
              <div className="mt-4 flex gap-3">
                <button
                  onClick={handleRunScan}
                  className="inline-flex items-center gap-2 rounded-lg bg-amber-500 hover:bg-amber-600 px-4 py-2 font-mono text-xs font-extrabold uppercase tracking-wider text-black transition-all shadow-md active:scale-95"
                >
                  <RefreshCw className="h-3.5 w-3.5" />
                  <span>Execute Scan</span>
                </button>
                <Link
                  href="/dashboard"
                  className="inline-flex items-center gap-2 rounded-lg border border-zinc-800 bg-zinc-900/80 px-4 py-2 font-mono text-xs font-bold text-zinc-300 hover:text-white transition-all"
                >
                  <span>Go to Command Center</span>
                </Link>
              </div>
            </div>
          </GlassPanel>
        ) : (
          <div className="grid grid-cols-1 gap-3">
            {filteredFindings.map((finding) => {
              const evidence = finding.evidence_payload || {};
              const sev = finding.severity.toLowerCase();

              return (
                <div
                  key={finding.id}
                  onClick={() => handleOpenDetail(finding.id)}
                  className="cursor-pointer rounded-xl border border-[#232736] border-t border-t-zinc-700/50 bg-[#12151e]/92 p-4.5 shadow-[0_8px_32px_0_rgba(0,0,0,0.6)] backdrop-blur-md transition-all duration-200 hover:border-[#343b52]"
                >
                  <div className="flex flex-col md:flex-row md:items-center justify-between gap-3">
                    <div className="space-y-1.5">
                      <div className="flex items-center gap-2.5 flex-wrap">
                        <span
                          className={`font-mono text-xs font-bold uppercase tracking-wider px-2 py-0.5 rounded border ${
                            sev === 'critical'
                              ? 'bg-rose-950/60 text-rose-400 border-rose-500/50'
                              : sev === 'high'
                              ? 'bg-amber-950/60 text-amber-400 border-amber-500/50'
                              : 'bg-zinc-900 text-zinc-300 border-zinc-800'
                          }`}
                        >
                          {finding.severity}
                        </span>
                        <span className="font-mono text-xs font-bold text-amber-400 bg-zinc-900 border border-zinc-800 px-2 py-0.5 rounded-lg">
                          {finding.finding_type}
                        </span>
                        <span className="font-mono text-xs font-bold text-amber-400">
                          {Math.round(finding.confidence * 100)}% EVIDENCE CONFIDENCE
                        </span>
                        <StatusBadge
                          status={finding.status === 'resolved' ? 'healthy' : finding.status === 'dismissed' ? 'offline' : 'critical'}
                          label={finding.status.toUpperCase()}
                        />
                      </div>

                      <h3 className="font-mono text-sm font-bold text-white tracking-wide">
                        {finding.title}
                      </h3>
                      <p className="text-sm font-medium text-zinc-300 line-clamp-2 font-sans">
                        {finding.description}
                      </p>
                    </div>

                    <div className="flex items-center gap-3 shrink-0 self-end md:self-center">
                      {Boolean(evidence.file_path) && (
                        <div className="flex items-center gap-1.5 font-mono text-xs font-bold text-zinc-300 bg-zinc-900/80 border border-zinc-800 px-2.5 py-1 rounded-lg">
                          <Code2 className="h-3 w-3 text-amber-500" />
                          <span className="max-w-[200px] truncate">{String(evidence.file_path)}</span>
                          {Boolean(evidence.line_number) && <span className="text-amber-400">:L{String(evidence.line_number)}</span>}
                        </div>
                      )}
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleOpenDetail(finding.id);
                        }}
                        className="flex items-center gap-1 text-xs font-mono font-bold text-amber-400 hover:text-amber-300 transition-colors"
                      >
                        <span>Inspect</span>
                        <ChevronRight className="h-3.5 w-3.5" />
                      </button>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Evidence Inspector Drawer / Modal */}
      {selectedFindingId && (
        <div className="fixed inset-0 z-50 flex items-center justify-end bg-black/80 backdrop-blur-md p-4 sm:p-6 animate-fade-in">
          <div className="w-full max-w-2xl h-full max-h-[90vh] flex flex-col rounded-2xl border border-[#232736] border-t border-t-zinc-700/50 bg-[#12151e]/96 p-6 shadow-[0_24px_64px_rgba(0,0,0,0.95)] backdrop-blur-3xl overflow-y-auto space-y-6">
            {loadingDetail || !detailData ? (
              <div className="py-20 text-center font-mono text-sm font-bold text-zinc-400 animate-pulse">
                Fetching evidence payload and graph telemetry...
              </div>
            ) : (
              <>
                {/* Header */}
                <div className="flex items-start justify-between border-b border-zinc-800 pb-4">
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-xs uppercase font-bold text-amber-400 bg-zinc-900 border border-zinc-800 px-2 py-0.5 rounded-lg">
                        {detailData.finding.finding_type}
                      </span>
                      <span className="font-mono text-xs font-bold text-amber-400">
                        {Math.round(detailData.finding.confidence * 100)}% CONFIDENCE
                      </span>
                    </div>
                    <h2 className="text-base font-bold text-white font-mono">
                      {detailData.finding.title}
                    </h2>
                  </div>
                  <button
                    onClick={() => setSelectedFindingId(null)}
                    className="p-1.5 rounded-lg border border-zinc-800 text-zinc-400 hover:text-white hover:bg-zinc-800"
                  >
                    <XCircle className="h-5 w-5" />
                  </button>
                </div>

                {/* Description */}
                <div>
                  <h4 className="font-mono text-xs font-bold uppercase tracking-wider text-amber-500 mb-1.5">
                    Analytical Conclusion
                  </h4>
                  <p className="text-sm font-medium text-zinc-300 font-sans leading-relaxed bg-zinc-900/60 border border-zinc-800 p-3.5 rounded-xl">
                    {detailData.finding.description}
                  </p>
                </div>

                {/* Expected vs Actual Diff Card */}
                {detailData.finding.evidence_payload && (
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    <div className="rounded-xl border border-zinc-800 bg-zinc-900/40 p-3">
                      <div className="flex items-center gap-1.5 font-mono text-xs uppercase font-bold text-amber-500 mb-1">
                        <CheckCircle2 className="h-3 w-3" /> Expected Architectural State
                      </div>
                      <div className="font-mono text-xs text-zinc-300 break-all bg-black/60 p-2.5 rounded-lg border border-zinc-800">
                        {JSON.stringify(detailData.finding.evidence_payload.expected ?? 'N/A', null, 2)}
                      </div>
                    </div>

                    <div className="rounded-xl border border-rose-500/30 bg-rose-950/20 p-3">
                      <div className="flex items-center gap-1.5 font-mono text-xs uppercase font-bold text-rose-400 mb-1">
                        <AlertTriangle className="h-3 w-3" /> Observed Reality Drift
                      </div>
                      <div className="font-mono text-xs text-zinc-300 break-all bg-black/60 p-2.5 rounded-lg border border-rose-900/40">
                        {JSON.stringify(detailData.finding.evidence_payload.actual ?? 'N/A', null, 2)}
                      </div>
                    </div>
                  </div>
                )}

                {/* Code Snippet / File Origin */}
                {Boolean(detailData.finding.evidence_payload?.file_path) && (
                  <div>
                    <div className="flex items-center justify-between mb-1.5">
                      <span className="font-mono text-xs uppercase tracking-wider text-amber-500 flex items-center gap-1.5 font-bold">
                        <FileText className="h-3.5 w-3.5 text-amber-500" /> Evidence Source
                      </span>
                      <span className="font-mono text-xs text-amber-400 font-semibold">
                        {String(detailData.finding.evidence_payload?.file_path)}
                        {Boolean(detailData.finding.evidence_payload?.line_number) &&
                          `:L${String(detailData.finding.evidence_payload?.line_number)}`}
                      </span>
                    </div>

                    {Boolean(detailData.finding.evidence_payload?.code_snippet) && (
                      <pre className="font-mono text-xs text-zinc-300 bg-black/90 border border-[#232736] p-3.5 rounded-xl overflow-x-auto">
                        <code>{String(detailData.finding.evidence_payload?.code_snippet)}</code>
                      </pre>
                    )}
                  </div>
                )}

                {/* Related Reality Graph Entities */}
                {detailData.related_nodes && detailData.related_nodes.length > 0 && (
                  <div>
                    <h4 className="font-mono text-xs uppercase tracking-wider text-amber-500 mb-2 flex items-center gap-1.5 font-bold">
                      <Database className="h-3.5 w-3.5 text-amber-500" /> Linked Reality Graph Nodes
                    </h4>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                      {detailData.related_nodes.map((n) => (
                        <Link
                          key={n.id}
                          href="/graph"
                          className="flex items-center justify-between p-2.5 rounded-xl border border-zinc-800 bg-zinc-900/50 hover:border-zinc-700 transition-all"
                        >
                          <div className="space-y-0.5 truncate">
                            <div className="font-mono text-xs text-white font-bold truncate">
                              {n.name}
                            </div>
                            <div className="font-mono text-[10px] uppercase font-bold text-amber-400">
                              {n.node_type}
                            </div>
                          </div>
                          <ExternalLink className="h-3.5 w-3.5 text-zinc-400 shrink-0 ml-2" />
                        </Link>
                      ))}
                    </div>
                  </div>
                )}

                {/* Status Switcher Actions */}
                <div className="border-t border-zinc-800 pt-4 flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-xs font-semibold text-zinc-300">Current Status:</span>
                    <span className="font-mono text-xs uppercase font-bold text-amber-400 px-2 py-0.5 rounded bg-zinc-900 border border-zinc-800">
                      {detailData.finding.status}
                    </span>
                  </div>

                  <div className="flex items-center gap-2">
                    {detailData.finding.status !== 'resolved' && (
                      <button
                        onClick={() => handleStatusChange(detailData.finding.id, 'resolved')}
                        className="px-3.5 py-1.5 rounded-lg bg-amber-500 hover:bg-amber-600 font-mono text-xs font-extrabold uppercase tracking-wider text-black transition-all shadow-sm active:scale-95"
                      >
                        Mark Resolved
                      </button>
                    )}
                    {detailData.finding.status !== 'dismissed' && (
                      <button
                        onClick={() => handleStatusChange(detailData.finding.id, 'dismissed')}
                        className="px-3.5 py-1.5 rounded-lg border border-zinc-800 bg-zinc-900 font-mono text-xs font-bold uppercase tracking-wider text-zinc-300 hover:text-white transition-all"
                      >
                        Dismiss
                      </button>
                    )}
                    {detailData.finding.status !== 'open' && (
                      <button
                        onClick={() => handleStatusChange(detailData.finding.id, 'open')}
                        className="px-3.5 py-1.5 rounded-lg border border-zinc-800 bg-zinc-900 font-mono text-xs font-bold uppercase tracking-wider text-amber-400 hover:text-white transition-all"
                      >
                        Reopen
                      </button>
                    )}
                  </div>
                </div>
              </>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
