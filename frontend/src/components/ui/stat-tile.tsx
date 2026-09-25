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
  accent?: 'amber' | 'orange' | 'crimson' | 'emerald' | 'none';
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
      border: 'border-orange-500/35',
      glow: 'shadow-[0_0_20px_rgba(249,115,22,0.3)]',
      valueColor: 'text-orange-400 drop-shadow-[0_0_8px_rgba(234,88,12,0.4)]',
      dot: 'bg-orange-400',
      bar: 'bg-orange-500/30',
    },
    orange: {
      border: 'border-orange-500/40',
      glow: 'shadow-[0_0_20px_rgba(249,115,22,0.35)]',
      valueColor: 'text-orange-400 drop-shadow-[0_0_8px_rgba(234,88,12,0.5)]',
      dot: 'bg-orange-400',
      bar: 'bg-orange-500/35',
    },
    crimson: {
      border: 'border-rose-500/35',
      glow: 'shadow-[0_0_20px_rgba(244,63,94,0.3)]',
      valueColor: 'text-rose-400 drop-shadow-[0_0_8px_rgba(244,63,94,0.3)]',
      dot: 'bg-rose-400',
      bar: 'bg-rose-500/30',
    },
    emerald: {
      border: 'border-emerald-500/35',
      glow: 'shadow-[0_0_20px_rgba(16,185,129,0.3)]',
      valueColor: 'text-emerald-400 drop-shadow-[0_0_8px_rgba(16,185,129,0.4)]',
      dot: 'bg-emerald-400',
      bar: 'bg-emerald-500/30',
    },
    none: {
      border: 'border-orange-500/30',
      glow: '',
      valueColor: 'text-zinc-100',
      dot: 'bg-orange-400',
      bar: 'bg-orange-500/20',
    },
  };

  const currentAccent = accentConfigs[accent as keyof typeof accentConfigs] || accentConfigs.amber;

  return (
    <div
      className={cn(
        'relative rounded-2xl border-2 border-orange-500/35 border-t-2 border-white/25 bg-zinc-950/90 backdrop-blur-3xl',
        'shadow-[0_20px_50px_rgba(0,0,0,0.9)] transition-all duration-300 ease-out',
        'hover:-translate-y-2.5 hover:scale-[1.015] hover:border-orange-500/60 hover:border-t-white/40 hover:shadow-[0_20px_45px_-5px_rgba(249,115,22,0.3)]',
        currentAccent.border,
        className
      )}
    >
      {/* Top accent line */}
      <div className={cn('absolute top-0 left-4 right-4 h-[2px] opacity-80', currentAccent.bar)} />

      <div className="flex items-center justify-between p-4">
        <div className="flex items-center gap-2">
          <div className={cn('h-2 w-2 rounded-full', currentAccent.dot)} />
          <span className="font-mono text-xs font-bold uppercase tracking-wider text-orange-400">
            {label}
          </span>
        </div>
        {Icon && <Icon className="h-4 w-4 text-orange-400" />}
      </div>

      <div className="mt-1 flex items-baseline gap-2 p-4 pt-0">
        <span className={cn('font-mono text-2xl font-bold tracking-wider', currentAccent.valueColor)}>
          {value}
        </span>
        {subvalue && (
          <span className="font-mono text-xs font-semibold text-zinc-300 truncate">
            {subvalue}
          </span>
        )}
      </div>
    </div>
  );
}