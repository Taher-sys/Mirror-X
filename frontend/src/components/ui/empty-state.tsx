'use client';

import React from 'react';
import { LucideIcon } from 'lucide-react';
import { cn } from '@/lib/utils';

interface EmptyStateProps {
  icon: LucideIcon;
  title: string;
  description: string;
  action?: React.ReactNode;
  className?: string;
}

export function EmptyState({
  icon: Icon,
  title,
  description,
  action,
  className,
}: EmptyStateProps) {
  return (
    <div
      className={cn(
        'flex flex-col items-center justify-center rounded-lg border border-dashed border-zinc-800 bg-zinc-950/40 p-8 text-center backdrop-blur-sm',
        className
      )}
    >
      <div className="flex h-12 w-12 items-center justify-center rounded-xl border border-zinc-800 bg-zinc-900/60 text-zinc-500 shadow-inner">
        <Icon className="h-6 w-6 stroke-[1.5]" />
      </div>
      <h4 className="mt-3 font-mono text-sm font-semibold uppercase tracking-wider text-zinc-200">
        {title}
      </h4>
      <p className="mt-1.5 max-w-sm text-sm text-zinc-300 font-sans leading-relaxed">
        {description}
      </p>
      {action && <div className="mt-4">{action}</div>}
    </div>
  );
}
