# Contributing to Sensei

Thank you for your interest in contributing to Sensei! This document provides guidelines and instructions for contributing.

## Development Setup

1. Clone the repository
2. Install dependencies:
   ```bash
   uv sync
   ```
3. Run the application:
   ```bash
   sensei --help
   ```

## Project Structure

```
sensei/
├── src/sensei/
│   ├── cli/          # CLI commands (Typer)
│   ├── agent/        # Agent runner and skill registry
│   ├── skills/       # Deterministic capabilities
│   ├── gateway/      # LLM provider integration
│   ├── state/        # State management (legacy)
│   └── persistence/  # SQLite database layer
├── courses/          # Course workspaces
└── tests/            # Test files
```

## Code Style

- Follow PEP 8 for Python code
- Use type hints for all function signatures
- Write docstrings for public functions
- Keep functions focused and small

## Making Changes

1. Create a feature branch from `main`
2. Make your changes with clear commits
3. Add tests for new functionality
4. Update documentation if needed
5. Submit a pull request

## Testing

Run tests before submitting:
```bash
python -m pytest
```

## Reporting Issues

- Use GitHub Issues for bug reports
- Include steps to reproduce
- Include expected vs actual behavior

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
