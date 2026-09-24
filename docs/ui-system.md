# UI System

MIRROR-X demands a futuristic enterprise control interface that prioritizes information density and operational clarity. 

## 1. Visual Direction
- **Theme**: Deep OLED dark theme (true blacks `#000000` to deep grays `#0A0A0C`).
- **Surfaces**: Frosted glass panels (`backdrop-blur`) to create depth without clutter.
- **Accents**: Restrained, single-color status glows (e.g., electric cyan `#00F0FF`, emerald `#00FF66`, or alert crimson `#FF003C`) exclusively for active data streams, node states, or alerts.
- **Layout**: High-density split-pane layouts featuring structural data grids, node-graph topology lines, and real-time telemetry metrics.

## 2. Typography
- **Headings**: Strict, heavy, geometric sans-serif (e.g., Inter, Roboto, or a custom geometric font).
- **Data/Code**: High-readability monospace fonts (e.g., JetBrains Mono, Fira Code) for system logs, hashes, and quantitative metrics.
- **Accessibility**: Strict WCAG-compliant contrast ratios. Legibility over decoration.

## 3. Primary Pages
1. **Command Center**: The primary dashboard summarizing system health, active findings, and recent changes.
2. **Reality Graph**: An interactive, real-time node-link visualization (Three.js/React Flow) mapping out the ecosystem topology.
3. **Context Explorer**: Deep dive into specific nodes (Services, Agents, Tables) to view their explicit context and metadata.
4. **Change Twin**: A dual-pane view analyzing a proposed change (Git diff) against the Reality Graph to show direct and indirect impact.
5. **Scenario Lab**: Interface for generating and running synthetic scenarios against APIs and agents.
6. **Agent Behavior Lab**: Telemetry and trace viewer for agent runs, tool calls, and performance comparisons.
7. **Policy & Permissions**: Management grid for RBAC, rules, and governance policies.
8. **Evidence Ledger**: Immutable audit log tying findings to source evidence.
9. **Release Passport**: A gateway view summarizing all evidence, tests, and policies for a specific release candidate prior to human approval.
10. **AI Runtime**: Dashboard monitoring active models, context windows, and token usage.
11. **Edge Console**: (Future) Management for local-first execution nodes.
12. **Settings**: System configuration, integrations, and user management.
