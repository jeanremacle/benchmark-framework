# Directives — benchmark-framework

## *Last updated by PM layer: 2026-02-19*

### Priorities

1. This repo is stable at v0.1.0 — no active development
2. If a Claude Code session is opened here, verify `make lint && make test` pass clean
3. No new features until notebook-processor Phase 3b is complete and tested end-to-end

### Decisions

- Phase 1 is complete. No changes planned until the notebook-processor consumes the benchmark bridge in Phase 4.
- Pyenv patch (Python 3.13.9) has been applied.

### Constraints

- Run `uv run mypy src/` and `uv run pytest -v` after any change before journaling
- Do not bump version without PM approval
- Never write files outside the repo root
- Never write files into `../project-management/`

### Answers to Blockers

*No blockers raised yet.*
