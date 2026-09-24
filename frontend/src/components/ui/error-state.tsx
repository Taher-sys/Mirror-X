'use client';

import React from 'react';
import { AlertCircle, RefreshCw } from 'lucide-react';

interface ErrorStateProps {
  title?: string;
  message?: string;
  onRetry?: () => void;
}

export function ErrorState({
  title = 'Telemetry Synchronization Failure',
  message = 'Unable to establish connection to the backend telemetry daemon. Verify the service is online.',
  onRetry,
}: ErrorStateProps) {
  return (
    <div className="rounded-xl border border-rose-900/60 bg-rose-950/20 p-6 backdrop-blur-md">
      <div className="flex items-start gap-4">
        <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg border border-rose-800/80 bg-rose-950/60 text-rose-400">
          <AlertCircle className="h-5 w-5" />
        </div>
        <div className="flex-1">
          <h3 className="font-mono text-sm font-semibold tracking-wide uppercase text-rose-300">
            {title}
          </h3>
          <p className="mt-1 text-sm font-medium text-rose-200/80 font-sans">
            {message}
          </p>
          {onRetry && (
            <button
              onClick={onRetry}
              className="mt-3 inline-flex items-center gap-2 rounded-lg border border-rose-700/60 bg-rose-900/40 px-3 py-1.5 font-mono text-sm font-bold text-rose-200 transition-colors hover:bg-rose-800/50"
            >
              <RefreshCw className="h-3.5 w-3.5" />
              <span>Retry Telemetry Fetch</span>
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
