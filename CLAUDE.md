# Claude Code Guidelines for MIRROR-X

When operating as the "Senior Implementation Engineer" on MIRROR-X using Claude Code, strictly follow these operational parameters:

## Architectural Alignment
- **Read Architecture First**: Always read the `docs/` directory to understand the Domain Model, Data Model, and overall Architecture before suggesting or making changes.
- **Inspect Existing Code**: Do not duplicate logic. Check existing FastAPI routes, Pydantic models, SQLAlchemy schemas, and React components before building new ones.
- **Never Rewrite Unrelated Modules**: Scope your changes exactly to the requested feature or fix.
- **Update Documentation**: If you change how a system works, update its respective documentation file immediately.

## Code Quality & Restraint
- **Do Not Invent Features**: Stick to the current phase requirements. Do not add unrequested capabilities.
- **Do Not Introduce Dependencies Without Justification**: The stack is Python (FastAPI, SQLAlchemy), MySQL, and Next.js (React, Tailwind). Stick to this unless instructed otherwise. Avoid premature microservices.
- **Preserve API Contracts**: Ensure the frontend and backend remain strictly typed and aligned.

## Evidence & Integrity
- **Do Not Fabricate Metrics**: MIRROR-X is an evidence-driven control plane. Do not create fake AI functionality, fake benchmark numbers, or hallucinated test results.
- **Verify Claims**: Ground your implementations in reality.
- **Run Tests**: Ensure your code is testable and verified.

## Security
- **Never Expose Secrets**: Use `.env` variables strictly.
- **Secure By Default**: Ensure RBAC and human-in-the-loop patterns are preserved.

# Global Master Skill: Elite UI/UX & VengeanceUI Architecture

## 1. Absolute Design Mandate
- **Aesthetic Benchmark:** Premium futuristic enterprise, deep OLED dark mode (`#080808` backgrounds), high information density, razor-sharp CSS grids, and absolute restraint from cheesy or bloated decoration.
- **Goal:** Every interface must look like a high-end production product, crypto/AI control center, or design-award-winning SaaS platform.

## 2. Mandatory Tech Stack & Primitives
- **Framework & Language:** Next.js (App Router), React, and strict TypeScript.
- **Styling Core:** Tailwind CSS utilizing utility-first precision spacing, custom dark tokens, and border glows.
- **Accessibility & Foundation:** Radix UI primitives for bulletproof keyboard navigation, focus management, and WCAG compliance.
- **Motion & Micro-Interactions:** Framer Motion for buttery-smooth entry animations, staggered layout reveals, spring physics, and hover states.

## 3. VengeanceUI Integration Rules (Non-Negotiable)
When tasked with creating any layout, page, component, or dashboard for *any* project:
1. **Never write generic, plain HTML/Tailwind templates.** Always build utilizing high-end components inspired by or adapted from **VengeanceUI** (`https://github.com/Ashutoshx7/VengeanceUI`).
2. **Component Library Execution:** Actively integrate VengeanceUI design systems across your code:
   - **Hero & Landing Blocks:** Glow border cards, 3D text displacement, perspective grids, and spotlight navbars.
   - **Interactive Elements:** Liquid/creepy buttons, social flip cards, animated tooltips, and interactive card layouts.
   - **Data & Layout Panels:** Bento grid layouts, structured split-panes, frosted glass panels (`backdrop-blur-md bg-zinc-900/40 border border-zinc-800/80`), and micro-text status tags.
3. **Typography & Readout Hierarchy:** Pair heavy, bold all-caps sans-serif headings with high-readability monospace fonts (e.g., JetBrains Mono) for metrics, system logs, version hashes, and quantitative indicators.
4. **Performance & Clean Code:** Ensure all heavy motion graphics lazy-load cleanly. Maintain clean separation of concerns, strict modular component files, and zero dead navigation paths.

## 6. Dynamic Glassmorphism, Color Palettes & Typography System (Anti-Vibe-Code)
- **Zero Vibe-Code Rule:** Never use plain, generic Tailwind colors (`bg-blue-600`, `bg-gray-900`) or uniform styling. Every project must feel uniquely branded and master-designed.
- **Dynamic Color Palettes (Pick based on project context):**
  - *Systems / Engineering / Infrastructure (e.g., Mirror-X):* Deep OLED black (`#030305`), paired with cyber-cyan / emerald accents (`from-cyan-950/40 via-zinc-950 to-black`, borders in `cyan-500/20`).
  - *Finance / Analytics / Control Centers:* Obsidian dark surfaces paired with rich amber or electric indigo gradients (`from-indigo-950/50 via-zinc-950 to-black`).
  - *Creative / AI / Modern Dashboards:* Deep midnight slate paired with vibrant neon-violet or hyper-magenta accents.
- **Glassmorphism Spec (Universal):**
  - Translucent layered cards: `backdrop-blur-2xl bg-zinc-900/40 border border-white/10 shadow-[0_8px_32px_0_rgba(0,0,0,0.6)]`.
  - Inner light highlights: `border-t border-white/20` for physical depth.
- **Project-Adaptive Cool Typography & Fonts:**
  - Do not use default fonts. Choose distinct typography treatments per project context:
    - *Technical / Systems:* Pair clean geometric sans headings with crisp monospace data streams (`font-mono tracking-wider text-cyan-400`).
    - *SaaS / Enterprise:* Use tracked-tight, bold modern sans-serif headings with gradient text fills (`bg-gradient-to-r from-white via-zinc-200 to-zinc-400 bg-clip-text text-transparent`).
- **Micro-Interactions:** Subtle radial hover states that lift cards and trace borders smoothly (`transition-all duration-300 hover:border-opacity-80`).

.glass-panel {
  /* Semi-transparent base tint */
  background: rgba(255, 255, 255, 0.08); 
  
  /* The engine behind the frosted glass blur effect */
  backdrop-filter: blur(16px) saturate(180%);
  -webkit-backdrop-filter: blur(16px) saturate(180%); /* Safari Compatibility */
  
  /* A 1px translucent edge that catches light and adds 3D depth */
  border: 1px solid rgba(255, 255, 255, 0.15); 
  border-radius: 20px;
  
  /* Smooth outer drop-shadow to create floating separation */
  box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3); 
}

## 7. Fluid Framer-Style Navigation & Micro-Interactions (FramerKit Spec)
- **Dynamic Floating Navigation Bars:** 
  - Navigation bars must use pill-shaped containers (`rounded-full px-6 py-2`) floating with deep glassmorphism (`backdrop-blur-2xl bg-zinc-950/80 border border-orange-500/30 shadow-2xl`).
  - Active menu items must feature smooth, layout-interpolated background highlights (simulating Framer's layout animations) with soft glowing amber/orange halos (`shadow-[0_0_20px_rgba(249,115,22,0.3)]`).
- **Spring-Physics Micro-Interactions:** 
  - Buttons and interactive menu triggers must scale or glow fluidly on hover (`transition-all duration-300 ease-out hover:scale-[1.02] active:scale-[0.98]`).
- **Interactive Menu Bars & Dropdowns:** 
  - Sub-menus and filter selectors must use slide-fade entry animations with crisp typography and weighted borders, avoiding abrupt or harsh layout shifts.