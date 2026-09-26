'use client';

import React from 'react';
import { cn } from '@/lib/utils';
import { LucideIcon } from 'lucide-react';

interface StatTileProps {
  label: string;
  value: string | number;
  subvalue?: string;
  icon?: LucideIcon;
  trend?: 'up' | 'down' | 'neutral';
  accent?: 'amber' | 'orange' | 'crimson' | 'emerald' | 'cyan' | 'none';
  className?: string;
}

export function StatTile({
  label,
  value,
  subvalue,
  icon: Icon,
  accent = 'amber',
  className,
}: StatTileProps) {
  const accentConfigs = {
    amber: {
      border: 'hover:border-amber-500/60',
      glow: 'hover:shadow-[0_20px_45px_-5px_rgba(245,158,11,0.35)]',
      valueColor: 'text-white',
      dot: 'bg-amber-500 shadow-[0_0_8px_rgba(245,158,11,0.8)]',
      iconColor: 'text-amber-500',
      bar: 'bg-amber-500/40',
    },
    orange: {
      border: 'hover:border-amber-500/60',
      glow: 'hover:shadow-[0_20px_45px_-5px_rgba(245,158,11,0.35)]',
      valueColor: 'text-white',
      dot: 'bg-amber-500 shadow-[0_0_8px_rgba(245,158,11,0.8)]',
      iconColor: 'text-amber-500',
      bar: 'bg-amber-500/40',
    },
    crimson: {
      border: 'hover:border-rose-500/60',
      glow: 'hover:shadow-[0_20px_45px_-5px_rgba(244,63,94,0.35)]',
      valueColor: 'text-white',
      dot: 'bg-rose-500 shadow-[0_0_8px_rgba(244,63,94,0.8)]',
      iconColor: 'text-rose-400',
      bar: 'bg-rose-500/40',
    },
    emerald: {
      border: 'hover:border-emerald-500/60',
      glow: 'hover:shadow-[0_20px_45px_-5px_rgba(16,185,129,0.35)]',
      valueColor: 'text-white',
      dot: 'bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.8)]',
      iconColor: 'text-emerald-400',
      bar: 'bg-emerald-500/40',
    },
    cyan: {
      border: 'hover:border-cyan-500/60',
      glow: 'hover:shadow-[0_20px_45px_-5px_rgba(6,182,212,0.35)]',
      valueColor: 'text-white',
      dot: 'bg-cyan-500 shadow-[0_0_8px_rgba(6,182,212,0.8)]',
      iconColor: 'text-cyan-400',
      bar: 'bg-cyan-500/40',
    },
    none: {
      border: 'hover:border-zinc-500/60',
      glow: 'hover:shadow-[0_20px_45px_-5px_rgba(255,255,255,0.15)]',
      valueColor: 'text-zinc-100',
      dot: 'bg-zinc-600',
      iconColor: 'text-zinc-400',
      bar: 'bg-zinc-700/30',
    },
  };

  const currentAccent = accentConfigs[accent as keyof typeof accentConfigs] || accentConfigs.amber;

  return (
    <div
      className={cn(
        'relative rounded-lg bg-[#12151e]/92 backdrop-blur-md border border-[#232736] border-t border-t-zinc-700/50',
        'shadow-[0_8px_32px_0_rgba(0,0,0,0.6)] transition-all duration-300 ease-out cursor-pointer group',
        'hover:-translate-y-2.5 hover:scale-[1.02] hover:border-t-zinc-400',
        currentAccent.border,
        currentAccent.glow,
        className
      )}
    >
      {/* Top accent highlight rim */}
      <div className={cn('absolute top-0 left-3 right-3 h-[2px] opacity-0 group-hover:opacity-100 transition-opacity duration-300 rounded-full', currentAccent.bar)} />

      <div className="flex items-center justify-between p-4 pb-2">
        <div className="flex items-center gap-2">
          <div className={cn('h-2 w-2 rounded-full transition-transform duration-300 group-hover:scale-125', currentAccent.dot)} />
          <span className="font-mono text-xs font-bold uppercase tracking-wider text-zinc-400 group-hover:text-zinc-200 transition-colors">
            {label}
          </span>
        </div>
        {Icon && <Icon className={cn('h-4 w-4 transition-transform duration-300 group-hover:scale-110', currentAccent.iconColor)} />}
      </div>

      <div className="flex items-baseline gap-2 p-4 pt-1">
        <span className={cn('font-mono text-2xl font-bold tracking-wider', currentAccent.valueColor)}>
          {value}
        </span>
        {subvalue && (
          <span className="font-mono text-xs font-medium text-zinc-400 truncate group-hover:text-zinc-300 transition-colors">
            {subvalue}
          </span>
        )}
      </div>
    </div>
  );
}