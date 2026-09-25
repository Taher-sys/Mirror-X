'use client';

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
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
} from 'lucide-react';
import { cn } from '@/lib/utils';

const navigation = [
  { name: 'Dashboard', href: '/dashboard', icon: LayoutDashboard },
  { name: 'Reality Graph', href: '/graph', icon: GitBranch },
  { name: 'Context', href: '/context', icon: Layers },
  { name: 'Changes', href: '/changes', icon: GitCompare },
  { name: 'Scenarios', href: '/scenarios', icon: FlaskConical },
  { name: 'Agents', href: '/agents', icon: Bot },
  { name: 'Policies', href: '/policies', icon: Shield },
  { name: 'Evidence', href: '/evidence', icon: FileCheck },
  { name: 'Releases', href: '/releases', icon: Rocket },
  { name: 'Runtime', href: '/runtime', icon: Cpu },
  { name: 'Edge', href: '/edge', icon: HardDrive },
  { name: 'Settings', href: '/settings', icon: Settings },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="relative z-20 m-3 my-3 flex h-[calc(100vh-1.5rem)] w-64 flex-col rounded-2xl border border-[#232736] border-t border-t-zinc-700/50 bg-[#12151e]/92 backdrop-blur-md shadow-[0_8px_32px_0_rgba(0,0,0,0.6)] overflow-hidden shrink-0">
      {/* Brand Header */}
      <div className="flex h-16 items-center justify-between border-b border-zinc-800/80 px-5">
        <div className="flex items-center gap-2.5">
          <div className="flex h-8 w-8 items-center justify-center rounded-xl border border-zinc-700/70 bg-zinc-900/80 text-amber-500">
            <span className="font-mono text-xs font-black">X</span>
          </div>
          <span className="font-sans text-base font-bold tracking-tight text-white">
            MIRROR-X
          </span>
        </div>

        {/* Live System Indicator */}
        <div className="flex items-center gap-1.5 rounded-full border border-zinc-800 bg-zinc-900/80 px-2.5 py-0.5 font-mono text-[11px] font-bold text-emerald-400">
          <div className="h-1.5 w-1.5 rounded-full bg-emerald-500 animate-pulse" />
          <span>LIVE</span>
        </div>
      </div>

      {/* Navigation Matrix */}
      <nav className="flex-1 space-y-1 overflow-y-auto px-3 py-4 scrollbar-none">
        <div className="px-3 pb-2 pt-1 font-mono text-[11px] font-bold uppercase tracking-wider text-zinc-500">
          CORE CONSOLES
        </div>
        {navigation.map((item) => {
          const isActive = pathname === item.href;
          return (
            <Link
              key={item.name}
              href={item.href}
              className={cn(
                'group relative flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-mono transition-colors duration-150',
                isActive
                  ? 'bg-zinc-800/80 border border-zinc-700/70 border-l-2 border-l-amber-500 text-white font-bold'
                  : 'text-zinc-300 hover:text-white hover:bg-zinc-800/40 border border-transparent'
              )}
            >
              <item.icon
                className={cn(
                  'h-4 w-4 shrink-0 transition-colors',
                  isActive ? 'text-amber-500' : 'text-zinc-400 group-hover:text-zinc-200'
                )}
                aria-hidden="true"
              />
              <span className={cn('tracking-tight font-semibold', isActive ? 'text-white font-bold' : 'text-zinc-300')}>
                {item.name}
              </span>
            </Link>
          );
        })}
      </nav>

      {/* Bottom Node Signature */}
      <div className="border-t border-zinc-800/80 p-3.5">
        <div className="rounded-lg border border-zinc-800/80 bg-zinc-900/50 p-2.5 font-mono text-xs">
          <div className="flex items-center justify-between text-zinc-300">
            <span className="font-bold text-zinc-400">REALITY TWIN</span>
            <span className="font-mono font-bold text-amber-500">v1.0.0</span>
          </div>
          <div className="mt-1 flex items-center gap-1.5 text-xs font-bold text-zinc-400">
            <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" />
            <span className="font-mono text-zinc-300">NODE // CLUSTER-01</span>
          </div>
        </div>
      </div>
    </aside>
  );
}