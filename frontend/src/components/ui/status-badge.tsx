'use client';

import React from 'react';
import { cn } from '@/lib/utils';

export type StatusVariant =
  | 'healthy'
  | 'degraded'
  | 'critical'
  | 'uninitialized'
  | 'offline'
  | 'info'
  | 'synced';

interface StatusBadgeProps {
  status: StatusVariant | string;
  label?: string;
  size?: 'sm' | 'md';
  pulse?: boolean;
  className?: string;
}

const statusConfigs: Record<
  string,
  { label: string; text: string; bg: string; border: string; dot: string; pulseColor: string }
> = {
  healthy: {
    label: 'HEALTHY',
    text: 'text-emerald-400',
    bg: 'bg-emerald-950/40',
    border: 'border-emerald-800/60',
    dot: 'bg-emerald-400',
    pulseColor: 'bg-emerald-400',
  },
  synced: {
    label: 'SYNCED',
    text: 'text-emerald-400',
    bg: 'bg-emerald-950/40',
    border: 'border-emerald-800/60',
    dot: 'bg-emerald-400',
    pulseColor: 'bg-emerald-400',
  },
  degraded: {
    label: 'DEGRADED',
    text: 'text-amber-400',
    bg: 'bg-amber-950/40',
    border: 'border-amber-800/60',
    dot: 'bg-amber-400',
    pulseColor: 'bg-amber-400',
  },
  critical: {
    label: 'CRITICAL',
    text: 'text-rose-400',
    bg: 'bg-rose-950/40',
    border: 'border-rose-800/60',
    dot: 'bg-rose-400',
    pulseColor: 'bg-rose-400',
  },
  uninitialized: {
    label: 'UNINITIALIZED',
    text: 'text-amber-400',
    bg: 'bg-amber-950/40',
    border: 'border-amber-800/60',
    dot: 'bg-amber-400',
    pulseColor: 'bg-amber-400',
  },
  offline: {
    label: 'STANDBY',
    text: 'text-zinc-400',
    bg: 'bg-zinc-900/60',
    border: 'border-zinc-700/60',
    dot: 'bg-zinc-500',
    pulseColor: 'bg-zinc-500',
  },
  info: {
    label: 'INFO',
    text: 'text-amber-400',
    bg: 'bg-amber-950/40',
    border: 'border-amber-800/60',
    dot: 'bg-amber-400',
    pulseColor: 'bg-amber-400',
  },
};

export function StatusBadge({
  status,
  label,
  size = 'sm',
  pulse = true,
  className,
}: StatusBadgeProps) {
  const normalizedKey = (status || 'offline').toLowerCase();
  const config =
    statusConfigs[normalizedKey] || {
      label: status?.toUpperCase() || 'UNKNOWN',
      text: 'text-zinc-400',
      bg: 'bg-zinc-900/60',
      border: 'border-zinc-700/60',
      dot: 'bg-zinc-500',
      pulseColor: 'bg-zinc-500',
    };

  const displayText = label || config.label;

  return (
    <span
      className={cn(
        'inline-flex items-center gap-1.5 font-mono font-bold tracking-wider uppercase rounded-full border shadow-sm',
        config.bg,
        config.border,
        config.text,
        size === 'sm' ? 'px-2 py-0.5 text-[10px]' : 'px-2.5 py-1 text-xs',
        className
      )}
    >
      <span className="relative flex h-1.5 w-1.5">
        {pulse && (
          <span
            className={cn(
              'animate-ping absolute inline-flex h-full w-full rounded-full opacity-75',
              config.pulseColor
            )}
          />
        )}
        <span className={cn('relative inline-flex rounded-full h-1.5 w-1.5', config.dot)} />
      </span>
      {displayText}
    </span>
  );
}
