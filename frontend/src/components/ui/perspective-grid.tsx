'use client';

import React from 'react';

/**
 * 3D Perspective Grid background inspired by VengeanceUI control rooms.
 * Creates an elite depth field without visual noise or excessive decoration.
 */
export function PerspectiveGrid() {
  return (
    <div
      aria-hidden="true"
      className="pointer-events-none fixed inset-0 z-0 overflow-hidden select-none"
    >
      {/* Pure Smoked Onyx base without muddy orange radial glow */}

      {/* 3D Horizon Grid Floor */}
      <div
        className="absolute inset-x-0 bottom-0 h-[650px] origin-bottom overflow-hidden [perspective:1000px] opacity-40"
      >
        <div
          className="absolute inset-0 w-full h-[220%] [transform:rotateX(70deg)] [transform-origin:50%_100%]"
          style={{
            backgroundImage: `
              linear-gradient(to right, rgba(245, 158, 11, 0.08) 1px, transparent 1px),
              linear-gradient(to bottom, rgba(245, 158, 11, 0.08) 1px, transparent 1px)
            `,
            backgroundSize: '40px 40px',
            maskImage:
              'radial-gradient(ellipse 85% 60% at 50% 100%, #000 50%, transparent 100%)',
            WebkitMaskImage:
              'radial-gradient(ellipse 85% 60% at 50% 100%, #000 50%, transparent 100%)',
          }}
        />
      </div>

      {/* Top Ambient Amber Horizon Line */}
      <div className="absolute top-0 inset-x-0 h-px bg-gradient-to-r from-transparent via-amber-500/25 to-transparent" />
    </div>
  );
}
