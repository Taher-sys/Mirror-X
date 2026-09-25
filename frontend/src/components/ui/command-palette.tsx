'use client';

import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import {
  Search,
  LayoutDashboard,
  GitBranch,
  Layers,
  GitCompare,
  FlaskConical,
  Bot,
  Shield,
  FileCheck,
  Rocket,
  Cpu,
  HardDrive,
  Settings,
  Plus,
  Activity,
  AlertTriangle,
  Command,
  CornerDownLeft,
} from 'lucide-react';
import { cn } from '@/lib/utils';

interface CommandItem {
  id: string;
  category: 'Navigation' | 'Actions' | 'Entities';
  title: string;
  subtitle?: string;
  icon: React.ElementType;
  shortcut?: string;
  action: () => void;
}

interface CommandPaletteProps {
  isOpen: boolean;
  onClose: () => void;
  onOpenConnectModal?: () => void;
}

export function CommandPalette({
  isOpen,
  onClose,
  onOpenConnectModal,
}: CommandPaletteProps) {
  const [query, setQuery] = useState('');
  const [selectedIndex, setSelectedIndex] = useState(0);
  const router = useRouter();

  const commands: CommandItem[] = [
    {
      id: 'nav-dashboard',
      category: 'Navigation',
      title: 'Command Center',
      subtitle: 'Overview & system status',
      icon: LayoutDashboard,
      shortcut: 'G D',
      action: () => router.push('/dashboard'),
    },
    {
      id: 'nav-graph',
      category: 'Navigation',
      title: 'Reality Graph',
      subtitle: 'Explore architecture topology',
      icon: GitBranch,
      shortcut: 'G R',
      action: () => router.push('/graph'),
    },
    {
      id: 'nav-context',
      category: 'Navigation',
      title: 'Context Explorer',
      subtitle: 'Inspect code, schemas, and findings',
      icon: Layers,
      shortcut: 'G C',
      action: () => router.push('/context'),
    },
    {
      id: 'nav-changes',
      category: 'Navigation',
      title: 'Change Twin',
      subtitle: 'Simulate git diff impacts',
      icon: GitCompare,
      shortcut: 'G T',
      action: () => router.push('/changes'),
    },
    {
      id: 'nav-scenarios',
      category: 'Navigation',
      title: 'Scenario Lab',
      subtitle: 'Synthetic test scenarios',
      icon: FlaskConical,
      action: () => router.push('/scenarios'),
    },
    {
      id: 'nav-agents',
      category: 'Navigation',
      title: 'Agent Behavior Lab',
      subtitle: 'AI agent runtime traces',
      icon: Bot,
      action: () => router.push('/agents'),
    },
    {
      id: 'nav-policies',
      category: 'Navigation',
      title: 'Policies & Governance',
      subtitle: 'Security and behavioral constraints',
      icon: Shield,
      action: () => router.push('/policies'),
    },
    {
      id: 'nav-evidence',
      category: 'Navigation',
      title: 'Evidence Ledger',
      subtitle: 'Immutable audit verification',
      icon: FileCheck,
      action: () => router.push('/evidence'),
    },
    {
      id: 'nav-releases',
      category: 'Navigation',
      title: 'Release Passport',
      subtitle: 'Release validation gateway',
      icon: Rocket,
      action: () => router.push('/releases'),
    },
    {
      id: 'nav-runtime',
      category: 'Navigation',
      title: 'AI Runtime Console',
      subtitle: 'Model telemetry and tokens',
      icon: Cpu,
      action: () => router.push('/runtime'),
    },
    {
      id: 'nav-edge',
      category: 'Navigation',
      title: 'Edge Console',
      subtitle: 'Local-first execution nodes',
      icon: HardDrive,
      action: () => router.push('/edge'),
    },
    {
      id: 'nav-settings',
      category: 'Navigation',
      title: 'Settings',
      subtitle: 'System configuration',
      icon: Settings,
      action: () => router.push('/settings'),
    },
    {
      id: 'act-connect-repo',
      category: 'Actions',
      title: 'Connect Repository',
      subtitle: 'Ingest Git repository into Reality Graph',
      icon: Plus,
      shortcut: 'C R',
      action: () => {
        if (onOpenConnectModal) onOpenConnectModal();
      },
    },
    {
      id: 'act-view-findings',
      category: 'Actions',
      title: 'Filter Critical Findings',
      subtitle: 'Focus on high-severity drift findings',
      icon: AlertTriangle,
      action: () => router.push('/context?filter=critical'),
    },
    {
      id: 'act-refresh-telemetry',
      category: 'Actions',
      title: 'Refresh System Telemetry',
      subtitle: 'Re-poll database status and health',
      icon: Activity,
      action: () => window.location.reload(),
    },
  ];

  const filtered = commands.filter(
    (cmd) =>
      cmd.title.toLowerCase().includes(query.toLowerCase()) ||
      cmd.subtitle?.toLowerCase().includes(query.toLowerCase()) ||
      cmd.category.toLowerCase().includes(query.toLowerCase())
  );

  useEffect(() => {
    setSelectedIndex(0);
  }, [query]);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault();
        if (isOpen) {
          onClose();
        } else {
          // Open handled by parent or state
        }
      }

      if (!isOpen) return;

      if (e.key === 'Escape') {
        e.preventDefault();
        onClose();
      } else if (e.key === 'ArrowDown') {
        e.preventDefault();
        setSelectedIndex((prev) => (prev + 1) % Math.max(1, filtered.length));
      } else if (e.key === 'ArrowUp') {
        e.preventDefault();
        setSelectedIndex((prev) =>
          prev === 0 ? Math.max(0, filtered.length - 1) : prev - 1
        );
      } else if (e.key === 'Enter') {
        e.preventDefault();
        if (filtered[selectedIndex]) {
          filtered[selectedIndex].action();
          onClose();
        }
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, filtered, selectedIndex, onClose]);

  if (!isOpen) return null;

  return (
    <div
      role="dialog"
      aria-modal="true"
      className="fixed inset-0 z-50 flex items-start justify-center pt-24 px-4 bg-[rgba(20,21,26,0.8)] backdrop-blur-md animate-in fade-in duration-150"
      onClick={onClose}
    >
      <div
        className="w-full max-w-2xl overflow-hidden rounded-xl border border-[#232736] border-t border-t-zinc-700/50 bg-[#12151e]/96 shadow-[0_24px_64px_rgba(0,0,0,0.95)] backdrop-blur-md"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Search Input Bar */}
        <div className="flex items-center border-b border-zinc-800/80 px-4 py-3.5">
          <Search className="h-4 w-4 text-zinc-400 mr-3" />
          <input
            type="text"
            placeholder="Type a command, module, or search query..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            className="flex-1 bg-transparent text-sm font-medium text-white placeholder-zinc-500 outline-none font-sans"
            autoFocus
          />
          <div className="flex items-center gap-1.5 font-mono text-[10px] font-bold text-zinc-400">
            <kbd className="rounded border border-zinc-700 bg-zinc-800 px-2 py-0.5 text-zinc-300">ESC</kbd>
            <span>to close</span>
          </div>
        </div>

        {/* Results List */}
        <div className="max-h-[380px] overflow-y-auto p-2.5 space-y-1">
          {filtered.length === 0 ? (
            <div className="py-8 text-center text-sm text-zinc-400 font-mono font-bold">
              No matching commands or entities found for &quot;{query}&quot;
            </div>
          ) : (
            filtered.map((item, idx) => {
              const isSelected = idx === selectedIndex;
              const Icon = item.icon;
              return (
                <button
                  key={item.id}
                  onClick={() => {
                    item.action();
                    onClose();
                  }}
                  onMouseEnter={() => setSelectedIndex(idx)}
                  className={cn(
                    'w-full flex items-center justify-between rounded-lg px-3 py-2.5 text-left transition-colors duration-150',
                    isSelected
                      ? 'bg-zinc-800/90 text-white border border-zinc-700/80'
                      : 'text-zinc-300 hover:bg-zinc-800/40 hover:text-white border border-transparent'
                  )}
                >
                  <div className="flex items-center gap-3">
                    <div
                      className={cn(
                        'flex h-8 w-8 items-center justify-center rounded-lg border',
                        isSelected
                          ? 'border-zinc-700 bg-zinc-800 text-amber-500'
                          : 'border-zinc-800 bg-zinc-900 text-zinc-400'
                      )}
                    >
                      <Icon className="h-4 w-4" />
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-semibold text-white tracking-tight">
                          {item.title}
                        </span>
                        <span className="font-mono text-[10px] font-bold uppercase tracking-wider text-zinc-400">
                          [{item.category}]
                        </span>
                      </div>
                      {item.subtitle && (
                        <p className="text-[11px] font-medium text-zinc-400 truncate">
                          {item.subtitle}
                        </p>
                      )}
                    </div>
                  </div>

                  <div className="flex items-center gap-2">
                    {item.shortcut && (
                      <kbd className="hidden sm:inline-block font-mono text-[10px] font-medium text-zinc-300 border border-zinc-700 bg-zinc-800 px-2 py-0.5 rounded">
                        {item.shortcut}
                      </kbd>
                    )}
                    {isSelected && (
                      <CornerDownLeft className="h-3.5 w-3.5 text-amber-500" />
                    )}
                  </div>
                </button>
              );
            })
          )}
        </div>

        {/* Footer info bar */}
        <div className="flex items-center justify-between border-t border-[#232736] bg-zinc-950/80 px-4 py-2.5 font-mono text-[11px] font-bold text-zinc-300">
          <div className="flex items-center gap-2">
            <Command className="h-3.5 w-3.5 text-amber-500" />
            <span>MIRROR-X Control Pallet</span>
          </div>
          <div className="flex items-center gap-3">
            <span>↑↓ Navigate</span>
            <span>↵ Select</span>
          </div>
        </div>
      </div>
    </div>
  );
}
