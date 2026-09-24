# Instructions for Automated Agents

As an AI coding agent working on MIRROR-X, you must strictly adhere to the following rules:

1. **Read Architecture First**: Always consult `docs/architecture.md` and related documentation before writing code.
2. **Inspect Existing Code**: Always look for existing patterns, utilities, and components before creating new ones.
3. **Never Rewrite Unrelated Modules**: Keep PRs and commits focused. Do not touch code outside the immediate scope of your task.
4. **No Unjustified Dependencies**: Do not introduce new libraries, packages, or services without explicit architectural justification and user approval.
5. **Do Not Invent Features**: Only implement what is explicitly requested or documented in the spec.
6. **Do Not Fabricate Metrics**: MIRROR-X is an evidence-driven system. Never generate fake benchmark numbers, fake AI telemetry, or mock data that is presented as real.
7. **Never Expose Secrets**: Ensure all credentials, API keys, and sensitive configuration are strictly managed via environment variables and never hardcoded.
8. **Run Tests**: Verify your changes by running tests. Maintain the "testable" architectural principle.
9. **Verify Claims**: Base your analysis on real git diffs, ASTs, API schemas, and logs.
10. **Preserve API Contracts**: Ensure backwards compatibility or coordinate API changes systematically. Refer to `docs/api-contract.md`.
11. **Update Documentation**: When you make an architectural change, update the relevant files in the `docs/` folder to reflect reality.
