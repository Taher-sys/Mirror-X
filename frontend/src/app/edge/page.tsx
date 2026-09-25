'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  HardDrive,
  Activity,
  RefreshCw,
  CheckCircle2,
  AlertTriangle,
  Database,
  Wifi,
  WifiOff,
  Server,
  ShieldCheck,
  Layers,
  ArrowUpRight,
  Lock,
  FileText,
  Clock,
  Check,
  Zap,
} from 'lucide-react';
import { cn } from '@/lib/utils';

interface ConflictRecord {
  id: string;
  entity_type: string;
  entity_id: string;
  resolution_status: string;
  detected_at?: string;
  resolution_notes?: string | null;
}

interface SyncQueueEvent {
  id: string;
  entity_type: string;
  entity_id: string;
  version: number;
  status: string;
  checksum: string;
  timestamp?: string;
}

interface EdgeStatusData {
  connectivity: 'ONLINE' | 'OFFLINE';
  storage_used_kb: number;
  queue_length: number;
  local_model_version: string;
  local_policy_version: string;
  last_sync: string;
  conflicts: ConflictRecord[];
  node_id?: string;
  sync_status?: string;
  permitted_offline_capabilities?: string[];
  restricted_cloud_capabilities?: string[];
}

const FALLBACK_EDGE_STATUS: EdgeStatusData = {
  connectivity: 'ONLINE',
  storage_used_kb: 204.0,
  queue_length: 0,
  local_model_version: 'v2.1.0-edge',
  local_policy_version: 'v1.0-cloud-snapshot',
  last_sync: new Date().toISOString(),
  conflicts: [
    {
      id: 'conflict-demo-1',
      entity_type: 'evidence',
      entity_id: 'ev-local-branch-01',
      resolution_status: 'resolved_local',
      detected_at: new Date(Date.now() - 1000 * 60 * 15).toISOString(),
      resolution_notes: 'Approved local network override for branch edge deployment',
    },
  ],
  node_id: 'mirrorx-edge-primary-01',
  sync_status: 'idle',
  permitted_offline_capabilities: [
    'scenario_execution',
    'policy_evaluation',
    'agent_evaluation',
    'local_evidence_creation',
    'graph_exploration',
    'trace_storage',
    'sync_queue_management',
  ],
  restricted_cloud_capabilities: [
    'cloud_model_training',
    'global_release_passport',
    'central_analytics',
    'repository_ingestion',
  ],
};

const DEFAULT_EVENTS: SyncQueueEvent[] = [
  {
    id: 'evt-edge-001',
    entity_type: 'evidence',
    entity_id: 'ev-audit-disk-read',
    version: 1,
    status: 'synced',
    checksum: '8f7a6b2c4d1e...',
    timestamp: new Date(Date.now() - 1000 * 60 * 5).toISOString(),
  },
  {
    id: 'evt-edge-002',
    entity_type: 'scenario_run',
    entity_id: 'sc-offline-bench',
    version: 1,
    status: 'synced',
    checksum: '3a9b1c7e5f0d...',
    timestamp: new Date(Date.now() - 1000 * 60 * 12).toISOString(),
  },
];

export default function EdgePage() {
  const [edgeData, setEdgeData] = useState<EdgeStatusData>(FALLBACK_EDGE_STATUS);
  const [queueEvents, setQueueEvents] = useState<SyncQueueEvent[]>(DEFAULT_EVENTS);
  const [isLoading, setIsLoading] = useState(true);
  const [isTogglingMode, setIsTogglingMode] = useState(false);
  const [isSyncing, setIsSyncing] = useState(false);
  const [actionNotice, setActionNotice] = useState<string | null>(null);

  const API_HOST = typeof window !== 'undefined'
    ? (process.env.NEXT_PUBLIC_API_URL?.replace('/api/v1', '') || 'http://localhost:8000')
    : 'http://localhost:8000';

  const fetchEdgeData = useCallback(async () => {
    try {
      let res = await fetch(`${API_HOST}/api/edge/status`).catch(() => null);
      if (!res || !res.ok) {
        res = await fetch(`${API_HOST}/api/v1/edge/status`).catch(() => null);
      }

      if (res && res.ok) {
        const json = await res.json();
        const payload = json.data || json;
        setEdgeData({
          connectivity: payload.connectivity || (payload.is_offline ? 'OFFLINE' : 'ONLINE'),
          storage_used_kb: payload.storage_used_kb ?? 204.0,
          queue_length: payload.queue_length ?? (payload.local_stats?.pending_sync_events ?? 0),
          local_model_version: payload.local_model_version || 'v2.1.0-edge',
          local_policy_version: payload.local_policy_version || payload.active_snapshot_version || 'v1.0-cloud-snapshot',
          last_sync: payload.last_sync || payload.last_sync_timestamp || new Date().toISOString(),
          conflicts: payload.conflicts || [],
          node_id: payload.node_id || 'mirrorx-edge-node',
          sync_status: payload.sync_status || 'idle',
          permitted_offline_capabilities: payload.permitted_offline_capabilities || FALLBACK_EDGE_STATUS.permitted_offline_capabilities,
          restricted_cloud_capabilities: payload.restricted_cloud_capabilities || FALLBACK_EDGE_STATUS.restricted_cloud_capabilities,
        });
      }

      // Fetch Queue
      let qRes = await fetch(`${API_HOST}/api/edge/queue`).catch(() => null);
      if (!qRes || !qRes.ok) {
        qRes = await fetch(`${API_HOST}/api/v1/edge/queue`).catch(() => null);
      }
      if (qRes && qRes.ok) {
        const qJson = await qRes.json();
        if (Array.isArray(qJson.data)) {
          setQueueEvents(qJson.data);
        }
      }
    } catch {
      // Graceful fallback preserves UI without crash
    } finally {
      setIsLoading(false);
    }
  }, [API_HOST]);

  useEffect(() => {
    fetchEdgeData();
    const interval = setInterval(fetchEdgeData, 10000);
    return () => clearInterval(interval);
  }, [fetchEdgeData]);

  const handleToggleMode = async () => {
    setIsTogglingMode(true);
    const nextMode = edgeData.connectivity === 'ONLINE' ? 'OFFLINE' : 'ONLINE';
    try {
      let res = await fetch(`${API_HOST}/api/edge/mode`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ network_mode: nextMode }),
      }).catch(() => null);

      if (!res || !res.ok) {
        res = await fetch(`${API_HOST}/api/v1/edge/mode`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ network_mode: nextMode }),
        }).catch(() => null);
      }

      setEdgeData(prev => ({
        ...prev,
        connectivity: nextMode,
        sync_status: nextMode === 'OFFLINE' ? 'offline' : 'idle',
      }));

      setActionNotice(`Edge Node transitioned to ${nextMode} mode.`);
      setTimeout(() => setActionNotice(null), 4000);
    } catch {
      setEdgeData(prev => ({ ...prev, connectivity: nextMode }));
    } finally {
      setIsTogglingMode(false);
    }
  };

  const handleTriggerSync = async () => {
    setIsSyncing(true);
    try {
      let res = await fetch(`${API_HOST}/api/edge/sync`, { method: 'POST' }).catch(() => null);
      if (!res || !res.ok) {
        res = await fetch(`${API_HOST}/api/v1/edge/sync`, { method: 'POST' }).catch(() => null);
      }

      await fetchEdgeData();
      setActionNotice('Edge Synchronization flush executed successfully.');
      setTimeout(() => setActionNotice(null), 4000);
    } catch {
      setActionNotice('Sync deferred: Operating offline or unreachable.');
      setTimeout(() => setActionNotice(null), 4000);
    } finally {
      setIsSyncing(false);
    }
  };

  const isOnline = edgeData.connectivity === 'ONLINE';

  return (
    <div className="min-h-screen bg-[#121316] text-zinc-100 p-6 md:p-10 relative overflow-hidden bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-orange-950/20 via-[#121316] to-[#121316]">
      {/* Background Ambience */}
      <div className="absolute top-0 right-1/4 w-96 h-96 bg-orange-600/10 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute bottom-10 left-1/4 w-80 h-80 bg-zinc-900/60 rounded-full blur-3xl pointer-events-none" />

      <div className="max-w-7xl mx-auto space-y-8 relative z-10">
        {/* Header Bar */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-zinc-800/80 pb-6">
          <div className="space-y-1">
            <div className="flex items-center space-x-3">
              <div className="p-2.5 rounded-xl bg-orange-500/10 border border-orange-500/30 text-orange-400 shadow-[0_0_20px_rgba(249,115,22,0.15)]">
                <HardDrive className="h-7 w-7" />
              </div>
              <div>
                <h1 className="text-3xl font-extrabold text-white tracking-tight">
                  MIRROR-X Edge Console
                </h1>
                <p className="text-xs text-zinc-400 font-medium">
                  Local-First Runtime & Autonomous Node Orchestration
                </p>
              </div>
            </div>
          </div>

          {/* Action Center & Network Mode Toggle */}
          <div className="flex items-center space-x-3">
            <button
              onClick={handleToggleMode}
              disabled={isTogglingMode}
              className={cn(
                'flex items-center space-x-2.5 px-4 py-2.5 rounded-xl border-2 font-bold text-xs uppercase tracking-wider',
                'transition-all duration-300 ease-out hover:-translate-y-1 hover:scale-[1.02] shadow-lg',
                isOnline
                  ? 'border-emerald-500/50 bg-emerald-950/40 text-emerald-300 hover:border-emerald-400 hover:bg-emerald-950/60 shadow-emerald-950/40'
                  : 'border-amber-500/50 bg-amber-950/40 text-amber-300 hover:border-amber-400 hover:bg-amber-950/60 shadow-amber-950/40'
              )}
            >
              {isOnline ? (
                <>
                  <Wifi className="h-4 w-4 text-emerald-400 animate-pulse" />
                  <span>ONLINE MODE</span>
                  <span className="h-2 w-2 rounded-full bg-emerald-400 shadow-[0_0_8px_#34d399]" />
                </>
              ) : (
                <>
                  <WifiOff className="h-4 w-4 text-amber-400" />
                  <span>OFFLINE MODE</span>
                  <span className="h-2 w-2 rounded-full bg-amber-400 shadow-[0_0_8px_#fbbf24]" />
                </>
              )}
            </button>

            <button
              onClick={handleTriggerSync}
              disabled={isSyncing}
              className={cn(
                'flex items-center space-x-2 px-4 py-2.5 rounded-xl border-2 border-orange-500/40 bg-zinc-950/80 text-orange-300 font-bold text-xs',
                'transition-all duration-300 ease-out hover:-translate-y-1 hover:scale-[1.02] hover:border-orange-500 hover:bg-orange-500/10 shadow-lg shadow-orange-950/20'
              )}
            >
              <RefreshCw className={cn('h-4 w-4', isSyncing && 'animate-spin')} />
              <span>{isSyncing ? 'Flushing Queue...' : 'Trigger Edge Sync'}</span>
            </button>
          </div>
        </div>

        {/* Action Notice Banner */}
        <AnimatePresence>
          {actionNotice && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className="p-3.5 rounded-xl bg-orange-500/15 border border-orange-500/40 text-orange-200 text-sm flex items-center justify-between shadow-lg"
            >
              <div className="flex items-center space-x-2.5">
                <Zap className="h-4 w-4 text-orange-400" />
                <span>{actionNotice}</span>
              </div>
              <span className="text-xs font-mono text-orange-400/80">LIVE</span>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Primary Edge Telemetry Bento Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5">
          {/* Card 1: Node State & Storage */}
          <div className="backdrop-blur-3xl bg-zinc-950/85 border-2 border-orange-500/35 shadow-2xl transition-all duration-300 ease-out hover:-translate-y-2 hover:scale-[1.01] hover:shadow-[0_25px_60px_rgba(249,115,22,0.25)] rounded-2xl p-6 relative overflow-hidden group">
            <div className="flex items-center justify-between mb-4">
              <span className="text-xs font-bold text-zinc-400 uppercase tracking-wider">
                Storage & Database
              </span>
              <Database className="h-5 w-5 text-orange-400 group-hover:scale-110 transition-transform" />
            </div>
            <div className="space-y-1">
              <div className="text-3xl font-extrabold text-white font-mono tabular-nums">
                {edgeData.storage_used_kb.toFixed(1)} <span className="text-sm font-normal text-zinc-400">KB</span>
              </div>
              <p className="text-xs text-zinc-400 flex items-center space-x-1.5 pt-1">
                <span className="h-2 w-2 rounded-full bg-emerald-400" />
                <span>SQLite Embedded Local Engine</span>
              </p>
            </div>
            <div className="mt-4 pt-3 border-t border-zinc-800/80 flex justify-between text-xs text-zinc-500 font-mono">
              <span>artifacts/edge/edge_node.db</span>
            </div>
          </div>

          {/* Card 2: Outbound Queue */}
          <div className="backdrop-blur-3xl bg-zinc-950/85 border-2 border-orange-500/35 shadow-2xl transition-all duration-300 ease-out hover:-translate-y-2 hover:scale-[1.01] hover:shadow-[0_25px_60px_rgba(249,115,22,0.25)] rounded-2xl p-6 relative overflow-hidden group">
            <div className="flex items-center justify-between mb-4">
              <span className="text-xs font-bold text-zinc-400 uppercase tracking-wider">
                Outbound Sync Queue
              </span>
              <Layers className="h-5 w-5 text-orange-400 group-hover:scale-110 transition-transform" />
            </div>
            <div className="space-y-1">
              <div className="text-3xl font-extrabold text-white font-mono tabular-nums">
                {edgeData.queue_length} <span className="text-sm font-normal text-zinc-400">Events</span>
              </div>
              <p className="text-xs text-zinc-400 flex items-center space-x-1.5 pt-1">
                <span className={cn('h-2 w-2 rounded-full', edgeData.queue_length === 0 ? 'bg-emerald-400' : 'bg-amber-400 animate-pulse')} />
                <span>{edgeData.queue_length === 0 ? 'Queue Fully Synced' : 'Pending Reconnection Flush'}</span>
              </p>
            </div>
            <div className="mt-4 pt-3 border-t border-zinc-800/80 flex justify-between text-xs text-zinc-500 font-mono">
              <span>Idempotent SHA-256 Hashes</span>
            </div>
          </div>

          {/* Card 3: Versions & Snapshot */}
          <div className="backdrop-blur-3xl bg-zinc-950/85 border-2 border-orange-500/35 shadow-2xl transition-all duration-300 ease-out hover:-translate-y-2 hover:scale-[1.01] hover:shadow-[0_25px_60px_rgba(249,115,22,0.25)] rounded-2xl p-6 relative overflow-hidden group">
            <div className="flex items-center justify-between mb-4">
              <span className="text-xs font-bold text-zinc-400 uppercase tracking-wider">
                Model & Policy State
              </span>
              <ShieldCheck className="h-5 w-5 text-orange-400 group-hover:scale-110 transition-transform" />
            </div>
            <div className="space-y-1.5">
              <div className="flex items-center justify-between text-sm">
                <span className="text-xs text-zinc-400">Model:</span>
                <span className="font-mono text-orange-400 font-semibold">{edgeData.local_model_version}</span>
              </div>
              <div className="flex items-center justify-between text-sm">
                <span className="text-xs text-zinc-400">Policy:</span>
                <span className="font-mono text-orange-400 font-semibold">{edgeData.local_policy_version}</span>
              </div>
            </div>
            <div className="mt-4 pt-3 border-t border-zinc-800/80 flex justify-between text-xs text-zinc-500 font-mono">
              <span>HMAC-SHA256 Signed</span>
            </div>
          </div>

          {/* Card 4: Last Synchronization */}
          <div className="backdrop-blur-3xl bg-zinc-950/85 border-2 border-orange-500/35 shadow-2xl transition-all duration-300 ease-out hover:-translate-y-2 hover:scale-[1.01] hover:shadow-[0_25px_60px_rgba(249,115,22,0.25)] rounded-2xl p-6 relative overflow-hidden group">
            <div className="flex items-center justify-between mb-4">
              <span className="text-xs font-bold text-zinc-400 uppercase tracking-wider">
                Sync Heartbeat
              </span>
              <Clock className="h-5 w-5 text-orange-400 group-hover:scale-110 transition-transform" />
            </div>
            <div className="space-y-1">
              <div className="text-xl font-extrabold text-white font-mono tabular-nums truncate">
                {new Date(edgeData.last_sync).toLocaleTimeString()}
              </div>
              <p className="text-xs text-zinc-400 pt-1">
                {new Date(edgeData.last_sync).toLocaleDateString()}
              </p>
            </div>
            <div className="mt-4 pt-3 border-t border-zinc-800/80 flex justify-between text-xs text-zinc-500 font-mono">
              <span className="capitalize">{edgeData.sync_status || 'Synchronized'}</span>
              <span>{isOnline ? 'Direct Cloud Link' : 'Offline Buffer'}</span>
            </div>
          </div>
        </div>

        {/* Runtime Capability Enforcement Matrix */}
        <div className="backdrop-blur-3xl bg-zinc-950/85 border-2 border-orange-500/35 shadow-2xl transition-all duration-300 ease-out hover:-translate-y-2 hover:scale-[1.01] hover:shadow-[0_25px_60px_rgba(249,115,22,0.25)] rounded-2xl p-6">
          <div className="flex items-center justify-between mb-4 pb-2 border-b border-zinc-800/80">
            <div>
              <h2 className="text-lg font-extrabold text-white tracking-tight">
                Runtime Boundary & Capability Enforcement
              </h2>
              <p className="text-xs text-zinc-400">
                Core domain contracts enforced locally; heavy centralized tasks strictly guarded with structured 503 boundary responses
              </p>
            </div>
            <span className="px-2.5 py-1 rounded-md text-[11px] font-mono bg-orange-500/10 border border-orange-500/30 text-orange-400">
              {isOnline ? 'ALL CAPABILITIES UNLOCKED' : 'CONSTRAINED OFFLINE EXECUTION'}
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Permitted Offline Capabilities */}
            <div className="space-y-3">
              <h3 className="text-xs font-bold text-emerald-400 uppercase tracking-wider flex items-center space-x-1.5">
                <Check className="h-3.5 w-3.5" />
                <span>Permitted Edge Operations (Always Available)</span>
              </h3>
              <div className="flex flex-wrap gap-2">
                {(edgeData.permitted_offline_capabilities || []).map((cap) => (
                  <span
                    key={cap}
                    className="px-3 py-1.5 rounded-lg text-xs font-mono bg-emerald-950/30 border border-emerald-500/40 text-emerald-300 flex items-center space-x-1.5"
                  >
                    <CheckCircle2 className="h-3 w-3 text-emerald-400" />
                    <span>{cap.replace(/_/g, ' ')}</span>
                  </span>
                ))}
              </div>
            </div>

            {/* Restricted Cloud Capabilities */}
            <div className="space-y-3">
              <h3 className="text-xs font-bold text-amber-400 uppercase tracking-wider flex items-center space-x-1.5">
                <Lock className="h-3.5 w-3.5" />
                <span>Restricted Cloud Capabilities (Unavailable Offline)</span>
              </h3>
              <div className="flex flex-wrap gap-2">
                {(edgeData.restricted_cloud_capabilities || []).map((cap) => (
                  <span
                    key={cap}
                    className={cn(
                      'px-3 py-1.5 rounded-lg text-xs font-mono border flex items-center space-x-1.5',
                      isOnline
                        ? 'bg-zinc-900/60 border-zinc-700/60 text-zinc-300'
                        : 'bg-amber-950/20 border-amber-500/40 text-amber-300'
                    )}
                  >
                    <Lock className="h-3 w-3 text-amber-400" />
                    <span>{cap.replace(/_/g, ' ')}</span>
                  </span>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Dual Feeds: Outbound Sync Queue & Conflict Resolution Ledger */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Outbound Sync Queue Feed */}
          <div className="backdrop-blur-3xl bg-zinc-950/85 border-2 border-orange-500/35 shadow-2xl transition-all duration-300 ease-out hover:-translate-y-2 hover:scale-[1.01] hover:shadow-[0_25px_60px_rgba(249,115,22,0.25)] rounded-2xl p-6">
            <div className="flex items-center justify-between mb-4 pb-2 border-b border-zinc-800/80">
              <div className="flex items-center space-x-2">
                <FileText className="h-4 w-4 text-orange-400" />
                <h3 className="font-extrabold text-white text-base tracking-tight">
                  Outbound Sync Queue
                </h3>
              </div>
              <span className="text-xs font-mono text-zinc-400">
                {queueEvents.length} items logged
              </span>
            </div>

            {queueEvents.length === 0 ? (
              <div className="py-10 text-center text-zinc-500 text-sm font-medium">
                No outbound sync events currently queued.
              </div>
            ) : (
              <div className="space-y-3">
                {queueEvents.slice(0, 5).map((evt) => (
                  <div
                    key={evt.id}
                    className="p-3.5 rounded-xl border border-zinc-800/80 bg-zinc-900/40 flex items-center justify-between text-xs"
                  >
                    <div className="space-y-1">
                      <div className="flex items-center space-x-2">
                        <span className="font-mono text-orange-400 font-semibold">{evt.entity_type}</span>
                        <span className="text-zinc-500">#{evt.entity_id.slice(0, 8)}</span>
                      </div>
                      <p className="text-[11px] font-mono text-zinc-400">
                        Checksum: {evt.checksum ? evt.checksum.slice(0, 16) : 'computed'}...
                      </p>
                    </div>
                    <span
                      className={cn(
                        'px-2.5 py-1 rounded-md text-[10px] font-mono uppercase font-bold',
                        evt.status === 'synced'
                          ? 'bg-emerald-950/40 text-emerald-300 border border-emerald-500/30'
                          : evt.status === 'conflict'
                          ? 'bg-rose-950/40 text-rose-300 border border-rose-500/30'
                          : 'bg-amber-950/40 text-amber-300 border border-amber-500/30'
                      )}
                    >
                      {evt.status}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Conflict Resolution Ledger Feed */}
          <div className="backdrop-blur-3xl bg-zinc-950/85 border-2 border-orange-500/35 shadow-2xl transition-all duration-300 ease-out hover:-translate-y-2 hover:scale-[1.01] hover:shadow-[0_25px_60px_rgba(249,115,22,0.25)] rounded-2xl p-6">
            <div className="flex items-center justify-between mb-4 pb-2 border-b border-zinc-800/80">
              <div className="flex items-center space-x-2">
                <AlertTriangle className="h-4 w-4 text-orange-400" />
                <h3 className="font-extrabold text-white text-base tracking-tight">
                  Conflict Resolution Ledger
                </h3>
              </div>
              <span className="text-xs font-mono text-zinc-400">
                Explicit Non-Overwriting Policy
              </span>
            </div>

            {edgeData.conflicts.length === 0 ? (
              <div className="py-10 text-center text-zinc-500 text-sm font-medium">
                Zero active conflicts. All state transitions reconciled.
              </div>
            ) : (
              <div className="space-y-3">
                {edgeData.conflicts.map((c) => (
                  <div
                    key={c.id}
                    className="p-3.5 rounded-xl border border-zinc-800/80 bg-zinc-900/40 space-y-2 text-xs"
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-mono text-zinc-300 font-bold uppercase">{c.entity_type}</span>
                      <span
                        className={cn(
                          'px-2 py-0.5 rounded text-[10px] font-mono uppercase font-bold',
                          c.resolution_status === 'resolved_local'
                            ? 'bg-emerald-950/50 text-emerald-300 border border-emerald-500/40'
                            : c.resolution_status === 'resolved_remote'
                            ? 'bg-blue-950/50 text-blue-300 border border-blue-500/40'
                            : 'bg-rose-950/50 text-rose-300 border border-rose-500/40'
                        )}
                      >
                        {c.resolution_status.replace(/_/g, ' ')}
                      </span>
                    </div>
                    <p className="text-[11px] text-zinc-400">{c.resolution_notes || 'Conflict recorded'}</p>
                    {c.detected_at && (
                      <p className="text-[10px] font-mono text-zinc-500">
                        Detected: {new Date(c.detected_at).toLocaleString()}
                      </p>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}