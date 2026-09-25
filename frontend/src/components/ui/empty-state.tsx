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
        'flex flex-col items-center justify-center rounded-lg bg-[#12151e]/92 backdrop-blur-md border border-[#232736] border-t border-t-zinc-700/50 p-8 text-center',
        'shadow-[0_8px_32px_0_rgba(0,0,0,0.6)] transition-all duration-250 ease-out',
        'hover:border-[#343b52] hover:border-t-zinc-500/60 hover:shadow-[0_12px_40px_0_rgba(0,0,0,0.8)]',
        className
      )}
    >
      <div className="flex h-14 w-14 items-center justify-center rounded-xl border border-zinc-800 bg-zinc-900/80 text-amber-500 shadow-inner">
        <Icon className="h-7 w-7" />
      </div>
      <h3 className="mt-4 font-mono text-base font-bold uppercase tracking-wider text-white">
        {title}
      </h3>
      <p className="mt-2 max-w-md text-sm font-medium text-zinc-200 font-sans leading-relaxed">
        {description}
      </p>
      {action && <div className="mt-5">{action}</div>}
    </div>
  );
}
