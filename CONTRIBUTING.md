# Contributing to MIRROR-X

Thank you for your interest in contributing to MIRROR-X! As an AI engineering control plane operating in mission-critical environments, MIRROR-X adheres to strict architectural, security, and code quality standards.

---

## 1. Core Engineering Principles

1. **Evidence-Driven**: Every finding, metric, or calculation must be backed by verifiable data. Never fabricate benchmark metrics or mock data presented as real.
2. **Read Architecture First**: Always consult [Architecture](docs/architecture.md) and related specifications before writing code.
3. **No Unjustified Dependencies**: Never introduce external packages or services without explicit architectural justification.
4. **Zero Implicit Trust**: Code must follow the [Security Model](docs/security-model.md) and [Threat Model](docs/threat-model.md).
5. **Preserve API Contracts**: All endpoint modifications must maintain backwards compatibility or be coordinated via [API Contract](docs/api-contract.md).
6. **Strict Sandbox Isolation**: Production mutations are strictly prohibited; destructive operations must require human review.

---

## 2. Development Setup

### Backend Setup
```bash
cd backend
python -m venv venv

# Activate virtual environment
# Windows:
.\venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run migrations
alembic upgrade head

# Start local server
uvicorn app.main:app --reload
```

---

## 3. Code Standards & Linting

We enforce strict linting, formatting, and type consistency:

### Linting & Formatting with Ruff
```bash
# Run linter
ruff check .

# Fix auto-fixable lint issues
ruff check --fix .

# Verify formatting
ruff format --check .

# Auto-format files
ruff format .
```

### Running Tests
All tests must pass before submitting any change:
```bash
# Run complete test suite
pytest -v

# Run with test coverage
pytest --cov=app --cov-report=term-missing
```

---

## 4. Security Rules for Contributors

- **Never Expose Secrets**: Never commit API keys, private certificates, or passwords. All sensitive parameters must be configured via environment variables.
- **Path Traversal Guards**: Any file-handling logic must validate paths using `app.core.security.is_safe_relative_path`.
- **Payload Bound Checks**: Ingestion or upload endpoints must enforce strict file count and payload size limits.
- **No Subprocess Invocations**: Untrusted code or user-provided files must never be passed to `subprocess.Popen`, `os.system`, or shell commands.
- **Trace Context**: When adding new domain engines or asynchronous workflows, instrument the operation using `@trace_span("domain.operation")`.

---

## 5. Pull Request Guidelines

1. **Focused Scope**: Keep PRs scoped to a single feature or bug fix. Do not touch unrelated files or refactor unaffected modules.
2. **Test Coverage**: Every new feature or fix must include automated tests in `backend/tests/`.
3. **Documentation**: Update the relevant markdown files in `docs/` whenever making architectural or schema changes.
4. **CI Passes**: Verify that GitHub Actions (`ci.yml` and `security.yml`) pass cleanly on your branch.
