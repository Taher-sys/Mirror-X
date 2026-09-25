'use client';

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { motion } from 'framer-motion';
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
    <aside className="relative z-20 m-3 my-3 flex h-[calc(100vh-1.5rem)] w-64 flex-col rounded-2xl border-2 border-orange-500/35 border-t-2 border-white/25 bg-zinc-950/90 backdrop-blur-3xl shadow-[0_20px_50px_rgba(0,0,0,0.9)] transition-all duration-300 ease-out hover:-translate-y-2.5 hover:scale-[1.015] hover:border-orange-500/60 hover:border-t-white/40 hover:shadow-[0_20px_45px_-5px_rgba(249,115,22,0.3)] overflow-hidden shrink-0">
      {/* Brand Header */}
      <div className="flex h-16 items-center justify-between border-b border-white/10 px-5">
        <div className="flex items-center gap-2.5">
          <div className="flex h-8 w-8 items-center justify-center rounded-xl border-2 border-orange-500/50 bg-orange-950/60 text-orange-400 shadow-[0_0_16px_rgba(249,115,22,0.4)]">
            <span className="font-mono text-xs font-black">X</span>
          </div>
          <span className="font-sans text-base font-bold tracking-tight text-white drop-shadow-[0_2px_10px_rgba(0,0,0,0.8)]">
            MIRROR-X
          </span>
        </div>

        {/* Live System Indicator */}
        <div className="flex items-center gap-1.5 rounded-full border border-orange-500/40 bg-orange-950/50 px-2.5 py-0.5 font-mono text-[11px] font-bold text-orange-400 shadow-[0_0_12px_rgba(249,115,22,0.25)]">
          <div className="h-1.5 w-1.5 rounded-full bg-orange-400 animate-amber-pulse shadow-[0_0_8px_#EA580C]" />
          <span>LIVE</span>
        </div>
      </div>

      {/* Navigation Matrix */}
      <nav className="flex-1 space-y-1.5 overflow-y-auto px-3.5 py-4 scrollbar-none">
        <div className="px-3 pb-2 pt-1 font-mono text-xs font-bold uppercase tracking-wider text-orange-400">
          CORE CONSOLES
        </div>
        {navigation.map((item) => {
          const isActive = pathname === item.href;
          return (
            <Link
              key={item.name}
              href={item.href}
              className={cn(
                'group relative flex items-center gap-3 rounded-xl px-3.5 py-2.5 text-sm font-mono transition-all duration-300 ease-out hover:scale-[1.02] active:scale-[0.98]',
                isActive ? 'text-white' : 'text-zinc-300 hover:text-white'
              )}
            >
              {isActive && (
                <motion.div
                  layoutId="activeNavHighlight"
                  className="absolute inset-0 rounded-xl border border-orange-500/60 bg-gradient-to-r from-orange-500/25 via-amber-500/15 to-orange-500/10 shadow-[0_0_20px_rgba(249,115,22,0.35)] -z-10"
                  transition={{ type: 'spring', stiffness: 380, damping: 30 }}
                />
              )}
              <item.icon
                className={cn(
                  'h-4 w-4 transition-colors shrink-0',
                  isActive
                    ? 'text-orange-400 drop-shadow-[0_0_10px_rgba(249,115,22,0.6)]'
                    : 'text-zinc-400 group-hover:text-zinc-200'
                )}
                aria-hidden="true"
              />
              <span className={cn('tracking-tight font-semibold', isActive ? 'text-white font-bold' : 'text-zinc-200')}>
                {item.name}
              </span>
            </Link>
          );
        })}
      </nav>

      {/* Bottom Node Signature */}
      <div className="border-t border-white/10 p-3.5">
        <div className="rounded-xl border border-white/10 bg-zinc-900/50 p-2.5 font-mono text-xs">
          <div className="flex items-center justify-between text-zinc-200">
            <span className="font-bold">REALITY TWIN</span>
            <span className="font-mono font-bold text-orange-400">v0.1.0</span>
          </div>
          <div className="mt-1 flex items-center gap-1.5 text-xs text-zinc-300 font-bold">
            <span className="h-1.5 w-1.5 rounded-full bg-orange-400 shadow-[0_0_6px_#EA580C]" />
            <span className="font-mono font-bold text-orange-400">NODE // CLUSTER-01</span>
          </div>
        </div>
      </div>
    </aside>
  );
}