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
│   ├── cli/              # CLI commands (Typer)
│   │   ├── app.py        # Main CLI application
│   │   └── output.py     # Output formatting
│   ├── agent/            # Agent and learning loop
│   │   ├── runner.py     # LLM interaction
│   │   ├── session.py    # Session management
│   │   ├── progression.py # Lesson advancement
│   │   ├── evaluation.py # Competency assessment
│   │   ├── context.py    # Context compression
│   │   ├── instructions.md # Agent behavior
│   │   └── registry.py   # Tool registry
│   ├── skills/           # Deterministic capabilities
│   │   ├── courses.py    # Course CRUD
│   │   ├── artifacts.py  # File management
│   │   ├── uploads.py    # Upload handling
│   │   └── workspace.py  # Workspace checks
│   ├── gateway/          # LLM provider integration
│   │   ├── provider.py   # API calls
│   │   └── config.py     # Configuration
│   ├── state/            # State management
│   │   └── manager.py    # State persistence
│   ├── persistence/      # SQLite database
│   ├── validation.py     # Input validation
│   ├── path_utils.py     # Path safety
│   └── main.py           # Entry point
├── tests/                # Test suite
│   ├── test_validation.py
│   ├── test_path_utils.py
│   ├── test_skills_courses.py
│   ├── test_skills_artifacts.py
│   └── test_skills_uploads.py
├── courses/              # Course workspaces
├── pyproject.toml        # Package config
└── roadmap.md            # Development roadmap
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
python -m pytest tests/ -v
```

To run a specific test file:
```bash
python -m pytest tests/test_validation.py -v
```

## Reporting Issues

- Use GitHub Issues for bug reports
- Include steps to reproduce
- Include expected vs actual behavior

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
