'use client';

import React, { useState } from 'react';
import { X, GitFork, Loader2 } from 'lucide-react';
import { createRepository } from '@/lib/api';

interface ConnectRepoModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

export function ConnectRepoModal({
  isOpen,
  onClose,
  onSuccess,
}: ConnectRepoModalProps) {
  const [name, setName] = useState('Mirror-X');
  const [url, setUrl] = useState('https://github.com/Taher-sys/Mirror-X');
  const [branch, setBranch] = useState('main');
  const [language, setLanguage] = useState('TypeScript');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      // In local mode, if no project exists yet, fetch or use a bootstrap project ID
      // Or create through API
      await createRepository({
        name,
        url,
        default_branch: branch,
        language,
        project_id: '00000000-0000-0000-0000-000000000001', // Fallback/default bootstrap ID
      });
      onSuccess();
      onClose();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to connect repository';
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      role="dialog"
      aria-modal="true"
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-[#14151a]/80 backdrop-blur-md animate-in fade-in"
      onClick={onClose}
    >
      <div
        className="w-full max-w-lg rounded-2xl border-2 border-orange-500/40 border-t-2 border-white/30 bg-zinc-950/95 p-6 shadow-[0_24px_64px_rgba(0,0,0,0.95)] backdrop-blur-3xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between border-b border-white/10 pb-4">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl border-2 border-orange-500/40 bg-orange-950/50 text-orange-400 shadow-[0_0_12px_rgba(249,115,22,0.25)]">
              <GitFork className="h-4 w-4" />
            </div>
            <div>
              <h3 className="font-mono text-sm font-bold tracking-wide uppercase text-white">
                Connect Git Repository
              </h3>
              <p className="text-xs font-bold text-zinc-300 font-sans">
                Register source repository for Reality Graph ingestion
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="rounded-xl p-1 text-zinc-400 hover:bg-zinc-900 hover:text-white transition-colors"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="mt-5 space-y-4">
          {error && (
            <div className="rounded-xl border border-rose-500/40 bg-rose-950/40 p-3 text-xs text-rose-300 font-mono font-bold">
              {error}
            </div>
          )}

          <div>
            <label className="block font-mono text-[11px] font-bold uppercase tracking-wider text-orange-400 mb-1.5">
              Repository Name
            </label>
            <input
              type="text"
              required
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g. Mirror-X"
              className="w-full rounded-xl border-2 border-orange-500/30 bg-zinc-950/90 px-3.5 py-2 font-mono text-xs font-bold text-white placeholder-zinc-500 focus:border-orange-500/60 focus:outline-none transition-colors"
            />
          </div>

          <div>
            <label className="block font-mono text-[11px] font-bold uppercase tracking-wider text-orange-400 mb-1.5">
              Git Remote URL
            </label>
            <input
              type="url"
              required
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="https://github.com/..."
              className="w-full rounded-xl border-2 border-orange-500/30 bg-zinc-950/90 px-3.5 py-2 font-mono text-xs font-bold text-white placeholder-zinc-500 focus:border-orange-500/60 focus:outline-none transition-colors"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block font-mono text-[11px] font-bold uppercase tracking-wider text-orange-400 mb-1.5">
                Default Branch
              </label>
              <input
                type="text"
                required
                value={branch}
                onChange={(e) => setBranch(e.target.value)}
                placeholder="main"
                className="w-full rounded-xl border-2 border-orange-500/30 bg-zinc-950/90 px-3.5 py-2 font-mono text-xs font-bold text-white placeholder-zinc-500 focus:border-orange-500/60 focus:outline-none transition-colors"
              />
            </div>
            <div>
              <label className="block font-mono text-[11px] font-bold uppercase tracking-wider text-orange-400 mb-1.5">
                Primary Language
              </label>
              <input
                type="text"
                value={language}
                onChange={(e) => setLanguage(e.target.value)}
                placeholder="TypeScript"
                className="w-full rounded-xl border-2 border-orange-500/30 bg-zinc-950/90 px-3.5 py-2 font-mono text-xs font-bold text-white placeholder-zinc-500 focus:border-orange-500/60 focus:outline-none transition-colors"
              />
            </div>
          </div>

          <div className="mt-6 flex items-center justify-end gap-3 pt-3 border-t border-white/10">
            <button
              type="button"
              onClick={onClose}
              className="rounded-xl border border-white/10 px-4 py-2 font-mono text-xs font-bold text-zinc-300 hover:bg-zinc-900 hover:text-white transition-all duration-300 ease-out hover:scale-[1.02] active:scale-[0.98]"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="inline-flex items-center gap-2 rounded-xl border-2 border-orange-500/50 bg-gradient-to-r from-orange-950/70 via-zinc-900/90 to-orange-950/70 px-4 py-2 font-mono text-xs font-bold uppercase tracking-wider text-orange-400 transition-all duration-300 ease-out hover:scale-[1.02] active:scale-[0.98] hover:border-orange-400 hover:shadow-[0_0_20px_rgba(249,115,22,0.4)] shadow-lg disabled:opacity-50"
            >
              {loading && <Loader2 className="h-3.5 w-3.5 animate-spin text-orange-400" />}
              <span>Register Repository</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
