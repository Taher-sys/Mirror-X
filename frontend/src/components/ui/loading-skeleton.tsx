'use client';

import React from 'react';
import { cn } from '@/lib/utils';

export function LoadingSkeleton({ className }: { className?: string }) {
  return (
    <div
      className={cn(
        'animate-pulse rounded-2xl border-2 border-orange-500/35 border-t-2 border-white/30 bg-zinc-950/90 backdrop-blur-3xl shadow-[0_20px_50px_rgba(0,0,0,0.9)]',
        className
      )}
    />
  );
}

export function CommandCenterSkeleton() {
  return (
    <div className="space-y-6">
      {/* Top Telemetry Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[...Array(4)].map((_, i) => (
          <div
            key={i}
            className="h-28 rounded-2xl border-2 border-orange-500/35 border-t-2 border-white/30 bg-zinc-950/90 backdrop-blur-3xl shadow-[0_20px_50px_rgba(0,0,0,0.9)] animate-pulse p-4"
          >
            <div className="h-3 w-24 bg-orange-500/20 rounded mb-4" />
            <div className="h-8 w-20 bg-zinc-800 rounded" />
          </div>
        ))}
      </div>

      {/* Main Split Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          <div className="h-72 rounded-2xl border-2 border-orange-500/35 border-t-2 border-white/30 bg-zinc-950/90 backdrop-blur-3xl shadow-[0_20px_50px_rgba(0,0,0,0.9)] animate-pulse p-5">
            <div className="h-4 w-40 bg-zinc-800 rounded mb-5" />
            <div className="space-y-3">
              {[...Array(3)].map((_, j) => (
                <div key={j} className="h-12 bg-zinc-900/60 border border-white/5 rounded-xl" />
              ))}
            </div>
          </div>
          <div className="h-64 rounded-2xl border-2 border-orange-500/35 border-t-2 border-white/30 bg-zinc-950/90 backdrop-blur-3xl shadow-[0_20px_50px_rgba(0,0,0,0.9)] animate-pulse p-5">
            <div className="h-4 w-36 bg-zinc-800 rounded mb-5" />
            <div className="grid grid-cols-2 gap-3">
              {[...Array(4)].map((_, k) => (
                <div key={k} className="h-16 bg-zinc-900/60 border border-white/5 rounded-xl" />
              ))}
            </div>
          </div>
        </div>
        <div className="space-y-6">
          <div className="h-72 rounded-2xl border-2 border-orange-500/35 border-t-2 border-white/30 bg-zinc-950/90 backdrop-blur-3xl shadow-[0_20px_50px_rgba(0,0,0,0.9)] animate-pulse p-5">
            <div className="h-4 w-32 bg-zinc-800 rounded mb-5" />
            <div className="space-y-3">
              {[...Array(4)].map((_, m) => (
                <div key={m} className="h-10 bg-zinc-900/60 border border-white/5 rounded-xl" />
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
