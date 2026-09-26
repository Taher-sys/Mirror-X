'use client';

import { useEffect, useRef } from 'react';

export default function TopographicBackground() {
  const svgRef = useRef<SVGSVGElement>(null);

  useEffect(() => {
    const svg = svgRef.current;
    if (!svg) return;

    const updateBackground = (e: MouseEvent) => {
      const x = e.clientX;
      const y = e.clientY;

      // Set CSS variable for mouse position
      svg.style.setProperty('--mouse-x', `${x}px`);
      svg.style.setProperty('--mouse-y', `${y}px`);
    };

    // Initial position (center)
    svg.style.setProperty('--mouse-x', `${window.innerWidth / 2}px`);
    svg.style.setProperty('--mouse-y', `${window.innerHeight / 2}px`);

    // Add mouse move listener
    window.addEventListener('mousemove', updateBackground);

    return () => {
      window.removeEventListener('mousemove', updateBackground);
    };
  }, []);

  return (
    <svg
      ref={svgRef}
      className="fixed inset-0 pointer-events-none z-0"
      aria-hidden="true"
    >
      <defs>
        <radialGradient id="mouseGlow" gradientUnits="userSpaceOnUse">
          <stop offset="0%" stopColor="rgba(249, 115, 22, 0.08)" />
          <stop offset="80%" stopColor="transparent" />
        </radialGradient>
      </defs>

      {/* Background fill */}
      <rect width="100%" height="100%" fill="none" />

      {/* Topographic contour lines */}
      <g stroke="url(#mouseGlow)" stroke-width="1.2" fill="none">
        {/* Organic contour lines - simplified representation */}
        <path
          d="M-100 200 Q0 -50 100 200 T300 200 T500 200 T700 200 T900 200 T1100 200"
          strokeOpacity="0.13"
        />
        <path
          d="M-100 250 Q0 0 100 250 T300 250 T500 250 T700 250 T900 250 T1100 250"
          strokeOpacity="0.15"
        />
        <path
          d="M-100 300 Q0 50 100 300 T300 300 T500 300 T700 300 T900 300 T1100 300"
          strokeOpacity="0.18"
        />
      </g>

      {/* Ambient radial vignette - darkening at edges */}
      <rect width="100%" height="100%" fill="black" fill-opacity="0.4" />
    </svg>
  );
}