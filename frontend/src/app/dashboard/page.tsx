'use client';

import React, { useEffect, useState, useCallback } from 'react';
import { motion, type Variants } from 'framer-motion';
import {
  LayoutDashboard,
  RefreshCw,
  Plus,
  Terminal,
} from 'lucide-react';
import { PerspectiveGrid } from '@/components/ui/perspective-grid';
import { CommandCenterSkeleton } from '@/components/ui/loading-skeleton';
import { ErrorState } from '@/components/ui/error-state';
import { SystemSummaryPanel } from '@/components/command-center/system-summary-panel';
import { RepositoryListPanel } from '@/components/command-center/repository-list-panel';
import { ServiceSummaryPanel } from '@/components/command-center/service-summary-panel';
import { FindingSummaryPanel } from '@/components/command-center/finding-summary-panel';
import { RecentActivityPanel } from '@/components/command-center/recent-activity-panel';
import { ConnectRepoModal } from '@/components/command-center/connect-repo-modal';
import {
  getSystemStatus,
  getSystemSummary,
  getRepositories,
  getServices,
  getFindings,
  getFindingsSummary,
  getActivities,
  SystemStatus,
  SystemSummary,
  Repository,
  Service,
  Finding,
  FindingSeverityCounts,
  Activity,
} from '@/lib/api';

export default function DashboardPage() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [connectModalOpen, setConnectModalOpen] = useState(false);

  // Stored state
  const [status, setStatus] = useState<SystemStatus | null>(null);
  const [summary, setSummary] = useState<SystemSummary | null>(null);
  const [repositories, setRepositories] = useState<Repository[]>([]);
  const [services, setServices] = useState<Service[]>([]);
  const [findings, setFindings] = useState<Finding[]>([]);
  const [findingCounts, setFindingCounts] = useState<FindingSeverityCounts | null>(null);
  const [activities, setActivities] = useState<Activity[]>([]);

  const loadDashboardData = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const [
        statusRes,
        summaryRes,
        reposRes,
        servicesRes,
        findingsRes,
        findingCountsRes,
        activitiesRes,
      ] = await Promise.allSettled([
        getSystemStatus(),
        getSystemSummary(),
        getRepositories(),
        getServices(),
        getFindings(),
        getFindingsSummary(),
        getActivities(15),
      ]);

      if (statusRes.status === 'fulfilled') setStatus(statusRes.value);
      if (summaryRes.status === 'fulfilled') setSummary(summaryRes.value);
      if (reposRes.status === 'fulfilled') setRepositories(reposRes.value.items);
      if (servicesRes.status === 'fulfilled') setServices(servicesRes.value.items);
      if (findingsRes.status === 'fulfilled') setFindings(findingsRes.value.items);
      if (findingCountsRes.status === 'fulfilled') setFindingCounts(findingCountsRes.value);
      if (activitiesRes.status === 'fulfilled') setActivities(activitiesRes.value);

      const allFailed = [
        statusRes,
        summaryRes,
        reposRes,
        servicesRes,
        findingsRes,
      ].every((r) => r.status === 'rejected');

      if (allFailed) {
        setStatus({
          status: 'uninitialized',
          database_connected: false,
          database_dialect: 'disconnected',
          database_latency_ms: 0.0,
          api_version: '0.1.0',
          uptime_seconds: 0.0,
          timestamp: new Date().toISOString(),
          active_connections: 0,
        });
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown telemetry error');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadDashboardData();
  }, [loadDashboardData]);

  const containerVariants: Variants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.08,
      },
    },
  };

  const itemVariants: Variants = {
    hidden: { opacity: 0, y: 12 },
    visible: {
      opacity: 1,
      y: 0,
      transition: { duration: 0.35, ease: 'easeOut' },
    },
  };

  return (
    <div className="relative min-h-[calc(100vh-3.5rem)] overflow-hidden canvas-textured text-white p-6 space-y-6">
      {/* 3D Perspective Grid Canvas Background */}
      <PerspectiveGrid />

      {/* Control Room Header */}
      <div className="relative z-10 flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-white/10 pb-5">
        <div className="flex items-center gap-3.5">
          <div className="flex h-11 w-11 items-center justify-center rounded-2xl border-2 border-orange-500/40 bg-orange-950/40 text-orange-400 shadow-[0_0_20px_rgba(249,115,22,0.3)]">
            <LayoutDashboard className="h-5 w-5 drop-shadow-[0_0_8px_rgba(249,115,22,0.6)]" />
          </div>
          <div>
            <div className="flex items-center gap-2.5">
              <h1 className="text-2xl font-bold tracking-tight text-white font-sans drop-shadow-[0_2px_12px_rgba(0,0,0,0.8)]">
                Command Center
              </h1>
              <span className="font-mono text-xs font-bold uppercase tracking-wider text-orange-400 bg-orange-950/60 border border-orange-500/40 px-2.5 py-0.5 rounded shadow-[0_0_10px_rgba(249,115,22,0.25)]">
                CONTROL ROOM
              </span>
            </div>
            <p className="mt-1 font-mono text-sm font-semibold text-zinc-200">
              Reality Twin operational telemetry &amp; ecosystem topology matrix
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => loadDashboardData()}
            disabled={loading}
            className="inline-flex items-center gap-2 rounded-xl border border-white/10 bg-zinc-900/60 px-4 py-2 font-mono text-xs font-bold text-zinc-200 transition-all duration-300 ease-out hover:scale-[1.02] active:scale-[0.98] hover:border-orange-500/40 hover:text-white shadow-sm disabled:opacity-50"
            title="Refresh telemetry streams"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${loading ? 'animate-spin text-orange-400' : ''}`} />
            <span className="hidden sm:inline">Refresh</span>
          </button>

          <button
            onClick={() => setConnectModalOpen(true)}
            className="inline-flex items-center gap-2 rounded-xl border-2 border-orange-500/50 bg-gradient-to-r from-orange-950/70 via-zinc-900/90 to-orange-950/70 px-4 py-2 font-mono text-xs font-bold uppercase tracking-wider text-orange-400 transition-all duration-300 ease-out hover:scale-[1.02] active:scale-[0.98] hover:border-orange-400 hover:shadow-[0_0_25px_rgba(249,115,22,0.4)] shadow-lg shadow-orange-950/30"
          >
            <Plus className="h-3.5 w-3.5" />
            <span>Connect Repo</span>
          </button>
        </div>
      </div>

      {error && (
        <div className="relative z-10">
          <ErrorState
            message={error}
            onRetry={loadDashboardData}
          />
        </div>
      )}

      {loading && !status ? (
        <div className="relative z-10">
          <CommandCenterSkeleton />
        </div>
      ) : (
        <motion.div
          variants={containerVariants}
          initial="hidden"
          animate="visible"
          className="relative z-10 space-y-6"
        >
          {/* Section 1: Real System Summary & Telemetry */}
          <motion.div variants={itemVariants}>
            <SystemSummaryPanel summary={summary} status={status} />
          </motion.div>

          {/* Section 2: Split Bento Grid Layout */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Primary Left/Center Column: Repositories & Services */}
            <div className="lg:col-span-2 space-y-6">
              <motion.div variants={itemVariants}>
                <RepositoryListPanel
                  repositories={repositories}
                  onOpenConnectModal={() => setConnectModalOpen(true)}
                />
              </motion.div>

              <motion.div variants={itemVariants}>
                <ServiceSummaryPanel services={services} />
              </motion.div>
            </div>

            {/* Right Diagnostic Column: Findings & Recent Activity */}
            <div className="space-y-6">
              <motion.div variants={itemVariants}>
                <FindingSummaryPanel
                  findings={findings}
                  counts={findingCounts}
                />
              </motion.div>

              <motion.div variants={itemVariants}>
                <RecentActivityPanel activities={activities} />
              </motion.div>
            </div>
          </div>

          {/* Section 3: Bottom System Footer Stream */}
          <motion.div
            variants={itemVariants}
            className="flex flex-wrap items-center justify-between gap-4 rounded-2xl border-2 border-orange-500/35 border-t-2 border-white/25 bg-zinc-950/90 px-5 py-3.5 font-mono text-sm font-semibold text-zinc-200 backdrop-blur-3xl shadow-[0_20px_50px_rgba(0,0,0,0.9)]"
          >
            <div className="flex items-center gap-2.5">
              <Terminal className="h-4 w-4 text-orange-400" />
              <span>CONTROL MATRIX: <strong className="text-white font-bold">MIRROR-X ENTERPRISE REALITY ENGINE</strong></span>
            </div>
            <div className="flex items-center gap-5">
              <div className="flex items-center gap-1.5">
                <span className="h-2 w-2 rounded-full bg-orange-400 shadow-[0_0_6px_#EA580C]" />
                <span>UPTIME: <span className="font-bold text-orange-400">{status ? `${status.uptime_seconds}s` : '0s'}</span></span>
              </div>
              <span className="text-zinc-600">|</span>
              <span>POLL: <span className="text-zinc-100 font-bold">5000MS</span></span>
            </div>
          </motion.div>
        </motion.div>
      )}

      {/* Connect Repository Modal */}
      <ConnectRepoModal
        isOpen={connectModalOpen}
        onClose={() => setConnectModalOpen(false)}
        onSuccess={() => {
          loadDashboardData();
        }}
      />
    </div>
  );
}
