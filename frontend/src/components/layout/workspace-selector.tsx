'use client';

import React, { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ChevronDown, Building2, Plus } from 'lucide-react';
import { cn } from '@/lib/utils';

export function WorkspaceSelector() {
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  return (
    <div className="relative" ref={dropdownRef}>
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className={cn(
          'flex items-center gap-2.5 rounded-xl border-2 border-orange-500/35 border-t-2 border-white/25 bg-zinc-950/85 px-3.5 py-1.5 font-mono text-xs font-bold text-white shadow-[0_8px_20px_rgba(0,0,0,0.6)] backdrop-blur-2xl transition-all duration-300 ease-out hover:scale-[1.02] active:scale-[0.98] hover:border-orange-500/50 hover:shadow-[0_0_15px_rgba(249,115,22,0.25)] focus:outline-none'
        )}
      >
        <Building2 className="h-4 w-4 text-orange-400" aria-hidden="true" />
        <span className="font-bold tracking-tight text-white">Default Workspace</span>
        <ChevronDown
          className={cn(
            'h-3.5 w-3.5 text-zinc-300 transition-transform duration-200',
            isOpen ? 'rotate-180 text-orange-400' : ''
          )}
          aria-hidden="true"
        />
      </button>

      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, y: -8, scale: 0.96 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -8, scale: 0.96 }}
            transition={{ duration: 0.2, ease: [0.16, 1, 0.3, 1] }}
            className="absolute left-0 top-full z-50 mt-2 w-72 rounded-2xl border-2 border-orange-500/40 border-t-2 border-white/30 bg-zinc-950/95 p-4 shadow-[0_20px_50px_rgba(0,0,0,0.95)] backdrop-blur-3xl"
          >
            <div className="flex items-center justify-between pb-2.5 border-b border-white/10">
              <span className="font-mono text-[10px] font-bold uppercase tracking-wider text-orange-400">
                ACTIVE WORKSPACE
              </span>
              <span className="font-mono text-[10px] font-bold text-zinc-400">ONLINE</span>
            </div>

            <div className="py-3">
              <div className="flex items-center gap-2">
                <span className="h-2 w-2 rounded-full bg-orange-400 shadow-[0_0_6px_#EA580C]" />
                <p className="font-sans text-xs font-bold text-white tracking-tight">Production Topology Root</p>
              </div>
              <p className="mt-1.5 font-mono text-[11px] font-medium text-zinc-300 leading-relaxed">
                Single-tenant local control twin linked to active repository sources.
              </p>
            </div>

            <div className="pt-2.5 border-t border-white/10">
              <button
                type="button"
                className="w-full flex items-center justify-center gap-1.5 rounded-xl border border-orange-500/40 bg-orange-950/40 px-3 py-2 font-mono text-xs font-bold text-orange-400 transition-all duration-300 ease-out hover:scale-[1.02] active:scale-[0.98] hover:bg-orange-950/70 shadow-[0_0_12px_rgba(249,115,22,0.2)]"
              >
                <Plus className="h-3.5 w-3.5" />
                <span>Link Organization</span>
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
