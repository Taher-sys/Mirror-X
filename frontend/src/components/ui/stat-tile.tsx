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
      valueColor: 'text-white',
      dot: 'bg-amber-500',
      iconColor: 'text-amber-500',
    },
    orange: {
      valueColor: 'text-white',
      dot: 'bg-amber-500',
      iconColor: 'text-amber-500',
    },
    crimson: {
      valueColor: 'text-white',
      dot: 'bg-rose-500',
      iconColor: 'text-rose-400',
    },
    emerald: {
      valueColor: 'text-white',
      dot: 'bg-emerald-500',
      iconColor: 'text-emerald-400',
    },
    cyan: {
      valueColor: 'text-white',
      dot: 'bg-cyan-500',
      iconColor: 'text-cyan-400',
    },
    none: {
      valueColor: 'text-zinc-100',
      dot: 'bg-zinc-600',
      iconColor: 'text-zinc-400',
    },
  };

  const currentAccent = accentConfigs[accent as keyof typeof accentConfigs] || accentConfigs.amber;

  return (
    <div
      className={cn(
        'relative rounded-lg bg-[#12151e]/92 backdrop-blur-md border border-[#232736] border-t border-t-zinc-700/50',
        'shadow-[0_8px_32px_0_rgba(0,0,0,0.6)] transition-all duration-250 ease-out',
        'hover:border-[#343b52] hover:border-t-zinc-500/60 hover:shadow-[0_12px_40px_0_rgba(0,0,0,0.8)]',
        className
      )}
    >
      <div className="flex items-center justify-between p-4 pb-2">
        <div className="flex items-center gap-2">
          <div className={cn('h-2 w-2 rounded-full', currentAccent.dot)} />
          <span className="font-mono text-xs font-bold uppercase tracking-wider text-zinc-400">
            {label}
          </span>
        </div>
        {Icon && <Icon className={cn('h-4 w-4', currentAccent.iconColor)} />}
      </div>

      <div className="flex items-baseline gap-2 p-4 pt-1">
        <span className={cn('font-mono text-2xl font-bold tracking-wider', currentAccent.valueColor)}>
          {value}
        </span>
        {subvalue && (
          <span className="font-mono text-xs font-medium text-zinc-400 truncate">
            {subvalue}
          </span>
        )}
      </div>
    </div>
  );
}