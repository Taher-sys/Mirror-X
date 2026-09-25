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
          'flex items-center gap-2.5 rounded-lg border border-[#232736] border-t border-t-zinc-700/50 bg-[#12151e]/92 px-3 py-1.5 font-mono text-xs font-bold text-white shadow-sm transition-all duration-150 hover:border-zinc-700 focus:outline-none'
        )}
      >
        <Building2 className="h-4 w-4 text-amber-500" aria-hidden="true" />
        <span className="font-bold tracking-tight text-white">Default Workspace</span>
        <ChevronDown
          className={cn(
            'h-3.5 w-3.5 text-zinc-400 transition-transform duration-200',
            isOpen ? 'rotate-180 text-amber-500' : ''
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
            transition={{ duration: 0.15, ease: [0.16, 1, 0.3, 1] }}
            className="absolute left-0 top-full z-50 mt-2 w-72 rounded-lg border border-[#232736] border-t border-t-zinc-700/50 bg-[#12151e]/96 p-4 shadow-[0_20px_50px_rgba(0,0,0,0.95)] backdrop-blur-md"
          >
            <div className="flex items-center justify-between pb-2.5 border-b border-zinc-800/80">
              <span className="font-mono text-[10px] font-bold uppercase tracking-wider text-zinc-400">
                ACTIVE WORKSPACE
              </span>
              <span className="font-mono text-[10px] font-bold text-emerald-400">ONLINE</span>
            </div>

            <div className="py-3">
              <div className="flex items-center gap-2">
                <span className="h-2 w-2 rounded-full bg-emerald-500" />
                <p className="font-sans text-xs font-bold text-white tracking-tight">Production Topology Root</p>
              </div>
              <p className="mt-1.5 font-mono text-[11px] font-medium text-zinc-400 leading-relaxed">
                Single-tenant local control twin linked to active repository sources.
              </p>
            </div>

            <div className="pt-2.5 border-t border-zinc-800/80">
              <button
                type="button"
                className="w-full flex items-center justify-center gap-1.5 rounded-lg border border-zinc-700 bg-zinc-800/80 px-3 py-1.5 font-mono text-xs font-bold text-zinc-200 hover:bg-zinc-700 hover:text-white transition-colors"
              >
                <Plus className="h-3.5 w-3.5 text-amber-500" />
                <span>Link Organization</span>
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
