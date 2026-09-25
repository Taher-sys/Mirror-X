'use client';

import React from 'react';
import { cn } from '@/lib/utils';

interface GlassPanelProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode;
  title?: string;
  subtitle?: string;
  badge?: React.ReactNode;
  action?: React.ReactNode;
  accentGlow?: 'amber' | 'orange' | 'crimson' | 'none';
  className?: string;
  headerClassName?: string;
}

/**
 * Heavy Glassmorphism Panel
 * Surface spec: bg-[#12151e]/90 backdrop-blur-md border border-[#232734] border-t border-zinc-700/40 rounded-lg
 * with inner top rim highlight: border-t border-zinc-700/40
 */
export function GlassPanel({
  children,
  title,
  subtitle,
  badge,
  action,
  accentGlow = 'none',
  className,
  headerClassName,
  ...props
}: GlassPanelProps) {
  const glowMap = {
    amber: 'before:absolute before:inset-x-0 before:top-0 before:h-px before:bg-amber-500/50',
    orange: 'before:absolute before:inset-x-0 before:top-0 before:h-px before:bg-amber-500/50',
    crimson: 'before:absolute before:inset-x-0 before:top-0 before:h-px before:bg-rose-500/50',
    none: '',
  };

  return (
    <div
      className={cn(
        'relative rounded-lg bg-[#12151e]/92 backdrop-blur-md border border-[#232736] border-t border-t-zinc-700/50',
        'shadow-[0_8px_32px_0_rgba(0,0,0,0.6)] transition-all duration-250 ease-out',
        'hover:border-[#343b52] hover:border-t-zinc-500/60 hover:shadow-[0_12px_40px_0_rgba(0,0,0,0.8)]',
        glowMap[accentGlow],
        className
      )}
      {...props}
    >
      {/* Corner micro-crosses for precision blueprint aesthetic */}
      <div className="pointer-events-none absolute top-2 left-2 h-1.5 w-1.5 border-t border-l border-zinc-700/60" />
      <div className="pointer-events-none absolute top-2 right-2 h-1.5 w-1.5 border-t border-r border-zinc-700/60" />
      <div className="pointer-events-none absolute bottom-2 left-2 h-1.5 w-1.5 border-b border-l border-zinc-700/60" />
      <div className="pointer-events-none absolute bottom-2 right-2 h-1.5 w-1.5 border-b border-r border-zinc-700/60" />

      {(title || action || badge) && (
        <div
          className={cn(
            'flex items-center justify-between border-b border-zinc-800/80 px-5 py-3.5',
            headerClassName
          )}
        >
          <div className="flex items-center gap-2.5">
            <div>
              <div className="flex items-center gap-2">
                <h3 className="font-mono text-sm font-bold uppercase tracking-wider text-white">
                  {title}
                </h3>
                {badge}
              </div>
              {subtitle && (
                <p className="mt-0.5 text-sm font-medium text-zinc-300">
                  {subtitle}
                </p>
              )}
            </div>
          </div>
          {action && <div className="flex items-center gap-2">{action}</div>}
        </div>
      )}

      <div className="p-5">{children}</div>
    </div>
  );
}