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
 * Elite Glassmorphism Panel - Obsidian Black & Electric Orange
 * Heavy, thick glassmorphism cards using: backdrop-blur-3xl bg-zinc-950/80 border-2 border-orange-500/35
 * shadow-[0_20px_50px_rgba(0,0,0,0.9)] with strong inner top rim highlight (border-t-2 border-white/25)
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
    amber: 'before:absolute before:inset-x-0 before:top-0 before:h-px before:bg-gradient-to-r before:from-transparent before:via-amber-400/60 before:to-transparent',
    orange: 'before:absolute before:inset-x-0 before:top-0 before:h-px before:bg-gradient-to-r before:from-transparent before:via-orange-500/60 before:to-transparent',
    crimson: 'before:absolute before:inset-x-0 before:top-0 before:h-px before:bg-gradient-to-r before:from-transparent before:via-rose-500/60 before:to-transparent',
    none: '',
  };

  return (
    <div
      className={cn(
        // Elite Heavy Glassmorphism Spec
        'relative rounded-2xl border-2 border-orange-500/35 border-t-2 border-white/30 bg-zinc-950/90 backdrop-blur-3xl',
        'shadow-[0_20px_50px_rgba(0,0,0,0.9)] transition-all duration-300',
        // Micro-Interactions: hover lift & border illumination
        'hover:-translate-y-0.5 hover:border-orange-500/50 hover:border-t-white/40 hover:shadow-[0_25px_60px_0_rgba(0,0,0,0.95)]',
        glowMap[accentGlow],
        className
      )}
      {...props}
    >
      {/* Corner micro-crosses for precision blueprint aesthetic */}
      <div className="pointer-events-none absolute top-2 left-2 h-1.5 w-1.5 border-t border-l border-white/30" />
      <div className="pointer-events-none absolute top-2 right-2 h-1.5 w-1.5 border-t border-r border-white/30" />
      <div className="pointer-events-none absolute bottom-2 left-2 h-1.5 w-1.5 border-b border-l border-white/30" />
      <div className="pointer-events-none absolute bottom-2 right-2 h-1.5 w-1.5 border-b border-r border-white/30" />

      {(title || action || badge) && (
        <div
          className={cn(
            'flex items-center justify-between border-b border-white/10 px-5 py-3.5',
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
                <p className="mt-0.5 text-xs font-medium text-zinc-200">
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