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
        'flex flex-col items-center justify-center rounded-2xl border-2 border-orange-500/35 border-t-2 border-white/25 bg-zinc-950/90 p-8 text-center backdrop-blur-3xl shadow-[0_20px_50px_rgba(0,0,0,0.9)] transition-all duration-300 ease-out',
        'hover:-translate-y-2.5 hover:scale-[1.015] hover:border-orange-500/60 hover:border-t-white/40 hover:shadow-[0_20px_45px_-5px_rgba(249,115,22,0.3)]',
        className
      )}
    >
      <div className="flex h-14 w-14 items-center justify-center rounded-2xl border-2 border-orange-500/40 bg-orange-950/40 text-orange-400 shadow-[0_0_20px_rgba(249,115,22,0.3)]">
        <Icon className="h-7 w-7 drop-shadow-[0_0_8px_rgba(249,115,22,0.6)]" />
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
