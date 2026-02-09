# Contributing to Veridic

Thank you for your interest in contributing to Veridic! This document provides guidelines and instructions for contributing.

## Code of Conduct

By participating in this project, you agree to maintain a respectful and inclusive environment for all contributors.

## Getting Started

### Prerequisites

- **Rust** (1.75+) - For the MCP server
- **Python** (3.10+) - For the AI service
- **Docker** - For containerized deployment
- **protoc** (25.1+) - Protocol buffer compiler

### Development Setup

1. Clone the repository:
```bash
git clone https://github.com/khulnasoft/veridic.git
cd veridic
```

2. Run the setup command:
```bash
make setup
```

This will:
- Install Rust dependencies
- Set up Python virtual environment
- Generate protobuf files
- Build Docker images

## Development Workflow

### Branch Strategy

- `main` - Production-ready code
- `develop` - Integration branch
- `feature/*` - New features
- `fix/*` - Bug fixes
- `docs/*` - Documentation updates

### Making Changes

1. Create a feature branch:
```bash
git checkout -b feature/your-feature-name
```

2. Make your changes following our style guides

3. Run tests:
```bash
make test
```

4. Run validation:
```bash
make validate
```

5. Commit with meaningful messages:
```bash
git commit -m "feat: add new vulnerability detection pattern"
```

### Commit Message Format

We follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:

- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation changes
- `style:` - Code style changes (formatting, etc.)
- `refactor:` - Code refactoring
- `test:` - Adding or updating tests
- `chore:` - Maintenance tasks

## Code Style Guidelines

### Rust

- Follow [Rust API Guidelines](https://rust-lang.github.io/api-guidelines/)
- Run `cargo fmt` before committing
- Run `cargo clippy` and address warnings
- Use descriptive variable and function names

### Python

- Follow [PEP 8](https://peps.python.org/pep-0008/)
- Use type hints
- Run `black` for code formatting
- Run `pylint` or `flake8` for linting
- Document functions with docstrings

### TypeScript/JavaScript (if applicable)

- Follow the project's ESLint configuration
- Use TypeScript where possible
- Prefer `const` over `let`

## Testing

### Unit Tests

```bash
# Python tests
cd ai-service
pytest tests/

# Rust tests
cd mcp-server
cargo test
```

### Integration Tests

```bash
make test-phase1
```

### Validation

```bash
make validate
```

## Pull Request Process

1. Update documentation if needed
2. Add tests for new functionality
3. Ensure all tests pass
4. Update CHANGELOG.md
5. Request review from maintainers

### PR Checklist

- [ ] Code follows style guidelines
- [ ] Tests added/updated
- [ ] Documentation updated
- [ ] All tests passing
- [ ] No merge conflicts
- [ ] Appropriate labels added

## Reporting Issues

### Bug Reports

Include:
- Clear description
- Steps to reproduce
- Expected vs actual behavior
- Environment details (OS, versions)
- Logs if applicable

### Feature Requests

Include:
- Use case description
- Proposed solution
- Alternatives considered
- Impact assessment

## Questions?

- Open a GitHub issue
- Join our discussions
- Check existing documentation

## License

By contributing, you agree that your contributions will be licensed under the same license as the project.
