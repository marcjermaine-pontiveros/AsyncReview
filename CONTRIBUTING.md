# Contributing to AsyncReview

## Development Setup

```bash
# Backend
uv pip install -e ".[dev]"

# Frontend
cd web && bun install
```

## Code Style

**Python:** ruff + mypy (config in pyproject.toml)
```bash
ruff check .
mypy cr/
```

**TypeScript:** Follow existing patterns.

## Testing

```bash
# Backend
uv run pytest tests/ -v

# Frontend
cd web && bun test
```

## Pull Requests

1. Fork and create a feature branch
2. Add tests for new features
3. Ensure all tests pass
4. Submit PR with clear description
