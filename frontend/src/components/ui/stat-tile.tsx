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
  accent?: 'amber' | 'orange' | 'crimson' | 'cyan' | 'emerald' | 'none';
  className?: string;
}

export function StatTile({
  label,
  value,
  subvalue,
  icon: Icon,
  accent = 'none',
  className,
}: StatTileProps) {
  // Accent color configurations for glass panels
  const accentConfigs = {
    amber: {
      border: 'border-orange-500/35',
      glow: 'shadow-[0_0_20px_rgba(249,115,22,0.3)]',
      valueColor: 'text-orange-400 drop-shadow-[0_0_8px_rgba(234,88,12,0.4)]',
      dot: 'bg-orange-400',
      bar: 'bg-orange-500/20',
    },
    orange: {
      border: 'border-orange-500/35',
      glow: 'shadow-[0_0_20px_rgba(249,115,22,0.3)]',
      valueColor: 'text-orange-400 drop-shadow-[0_0_8px_rgba(234,88,12,0.4)]',
      dot: 'bg-orange-400',
      bar: 'bg-orange-500/20',
    },
    crimson: {
      border: 'border-rose-500/35',
      glow: 'shadow-[0_0_20px_rgba(244,63,94,0.3)]',
      valueColor: 'text-rose-400 drop-shadow-[0_0_8px_rgba(244,63,94,0.3)]',
      dot: 'bg-rose-400',
      bar: 'bg-rose-500/20',
    },
    cyan: {
      border: 'border-cyan-500/35',
      glow: 'shadow-[0_0_20px_rgba(6,182,212,0.3)]',
      valueColor: 'text-cyan-400 drop-shadow-[0_0_8px_rgba(6,182,212,0.4)]',
      dot: 'bg-cyan-400',
      bar: 'bg-cyan-500/20',
    },
    emerald: {
      border: 'border-emerald-500/35',
      glow: 'shadow-[0_0_20px_rgba(16,185,129,0.3)]',
      valueColor: 'text-emerald-400 drop-shadow-[0_0_8px_rgba(16,185,129,0.4)]',
      dot: 'bg-emerald-400',
      bar: 'bg-emerald-500/20',
    },
    none: {
      border: 'border-white/10',
      glow: '',
      valueColor: 'text-zinc-100',
      dot: 'bg-zinc-600',
      bar: 'bg-zinc-900/20',
    },
  };

  const currentAccent = accentConfigs[accent] || accentConfigs.none;

  return (
    <div
      className={cn(
        // Elite Heavy Glassmorphism Panel
        'relative rounded-2xl border-2 border-orange-500/35 border-t-2 border-white/30 bg-zinc-950/90 backdrop-blur-3xl',
        'shadow-[0_20px_50px_rgba(0,0,0,0.9)] transition-all duration-300',
        // Micro-Interactions
        'hover:-translate-y-0.5 hover:border-orange-500/50 hover:border-t-white/40 hover:shadow-[0_25px_60px_0_rgba(0,0,0,0.95)]',
        // Accent-specific styles
        currentAccent.border,
        currentAccent.glow,
        className
      )}
    >
      {/* Top accent line */}
      <div className={cn('absolute top-0 left-4 right-4 h-[2px] opacity-75', currentAccent.bar)} />

      <div className="flex items-center justify-between p-4">
        <div className="flex items-center gap-2">
          <div className={cn('h-2 w-2 rounded-full', currentAccent.dot)} />
          <span className="font-mono text-xs font-bold uppercase tracking-wider text-orange-400">
            {label}
          </span>
        </div>
        {Icon && <Icon className="h-4 w-4 text-orange-400/90" />}
      </div>

      <div className="mt-1 flex items-baseline gap-2 p-4 pt-0">
        <span className={cn('font-mono text-2xl font-bold tracking-wider', currentAccent.valueColor)}>
          {value}
        </span>
        {subvalue && (
          <span className="font-mono text-xs font-bold text-zinc-200 truncate">
            {subvalue}
          </span>
        )}
      </div>
    </div>
  );
}