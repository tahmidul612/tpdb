# Contributing to TPDB (Plex Poster Organizer)

Thank you for your interest in contributing to TPDB! This guide will help you get started with the development workflow, tools, and best practices.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Setting Up Your Development Environment](#setting-up-your-development-environment)
- [Development Workflow](#development-workflow)
- [Code Quality Tools](#code-quality-tools)
- [Commit Guidelines](#commit-guidelines)
- [Branch Naming Convention](#branch-naming-convention)
- [Testing](#testing)
- [Pull Request Process](#pull-request-process)

## Prerequisites

Before you begin, ensure you have the following tools installed:

### Required Tools

1. **Python 3.14 or higher** (as specified in pyproject.toml)

   - **Windows**: Download from [python.org](https://www.python.org/downloads/)
   - **macOS**: Use Homebrew: `brew install python@3.14` or download from [python.org](https://www.python.org/downloads/)
   - **Linux**: Usually pre-installed. If not: `sudo apt install python3 python3-pip` (Debian/Ubuntu)

1. **Git**

   - **Windows**: Download from [git-scm.com](https://git-scm.com/download/win)
   - **macOS**: `brew install git` or comes with Xcode Command Line Tools
   - **Linux**: `sudo apt install git` (Debian/Ubuntu)

1. **uv** (Python package manager)

   - **Windows**: `powershell -c "irm https://astral.sh/uv/install.ps1 | iex"`
   - **macOS/Linux**: `curl -LsSf https://astral.sh/uv/install.sh | sh`

## Setting Up Your Development Environment

### 1. Fork and Clone the Repository

```bash
# Fork the repository on GitHub, then clone your fork
git clone https://github.com/YOUR_USERNAME/tpdb.git
cd tpdb
```

### 2. Install Development Dependencies

```bash
# Install the package in editable mode with dev dependencies
uv sync --group dev
```

This installs all runtime dependencies (PlexAPI, thefuzz, requests, etc.) and development tools (commitizen, ruff, pre-commit).

### 3. Set Up Pre-commit Hooks

```bash
# Install pre-commit hooks
pre-commit install

# Install commit message and pre-push hooks
pre-commit install --hook-type commit-msg
pre-commit install --hook-type pre-push
```

The pre-commit hooks will:

- Update `uv.lock` and `requirements.txt` when dependencies change
- Check for trailing whitespace and line endings
- Run `ruff` for linting and formatting
- Format Markdown files
- Validate commit messages and branch names
- Check for secrets

## Development Workflow

### Making Changes

1. **Create a new branch** following the [branch naming convention](#branch-naming-convention):

   ```bash
   git checkout -b feat/your-feature-name
   # or
   git checkout -b fix/your-bug-fix
   ```

1. **Make your changes** to the codebase

1. **Test your changes**:

   ```bash
   # Run tests
   pytest

   # Test the main script
   python tpdb.py --help

   # Test duplicates utility
   python duplicates.py --help
   ```

1. **Check code quality**:

   ```bash
   # Run linter and formatter
   ruff check . --fix
   ruff format .
   ```

1. **Commit your changes**:

   ```bash
   # Using commitizen (recommended)
   cz commit

   # Or manually with conventional commit message
   git commit -m "feat: add support for custom poster directories"
   ```

1. **Push your branch**:

   ```bash
   git push origin feat/your-feature-name
   ```

## Code Quality Tools

This project uses several tools to maintain code quality:

### Ruff

Ruff handles both linting and formatting Python code. Configuration is in `pyproject.toml`:

- Line length: 88 characters (Black-compatible)
- Target: Python 3.10+
- LF line endings

**Usage**:

```bash
# Lint and auto-fix issues
ruff check . --fix

# Format code
ruff format .
```

### Pre-commit

Pre-commit runs automated checks before commits:

- **uv-lock & uv-export**: Keep dependencies synchronized
- **ruff**: Lint and format Python code
- **trailing-whitespace**: Remove trailing whitespace
- **mixed-line-ending**: Ensure LF line endings
- **mdformat**: Format Markdown files
- **commitizen**: Validate commit messages and branch names
- **detect-secrets**: Check for accidentally committed secrets

## Commit Guidelines

This project follows [Conventional Commits](https://www.conventionalcommits.org/).

### Commit Message Format

```text
<type>[optional scope]: <description>

[optional body]
```

### Commit Types

- **feat**: New features
- **fix**: Bug fixes
- **refactor**: Code changes that neither fix bugs nor add features
- **docs**: Documentation only changes
- **style**: Formatting, no code change
- **test**: Adding or correcting tests
- **chore**: Maintenance tasks (dependency updates, build tasks, etc.)

### Commit Examples

```bash
feat: add support for custom poster directories
fix: resolve fuzzy matching threshold issues
refactor: improve normalize_name function performance
docs: update README with new installation steps
chore: update dependencies to latest versions
```

### Using Commitizen

Use the interactive prompt for guided commit creation:

```bash
cz commit
```

## Branch Naming Convention

Follow [Conventional Branch](https://conventional-branch.github.io/) naming:

### Format

```text
<type>/<description>
```

### Branch Examples

```bash
git checkout -b feat/add-custom-directories
git checkout -b fix/memory-leak-in-processor
git checkout -b docs/update-contributing-guide
git checkout -b refactor/simplify-matching-logic
```

## Testing

The project uses `pytest` for testing.

### Running Tests

```bash
# Run all tests
pytest

# Run tests with verbose output
pytest -v

# Run specific test
pytest tests/test_main.py
```

### Current Test Coverage

Currently, the project has minimal test coverage:

- Only `normalize_name()` function is tested in `tests/test_main.py`
- Most functionality is untested

When contributing new features, please add appropriate tests.

## Pull Request Process

1. **Ensure all checks pass**:

   - Pre-commit hooks run successfully
   - All tests pass
   - Code follows project conventions

1. **Write a clear PR description**:

   - Explain what changes you made and why
   - Reference any related issues (e.g., "Fixes #123")
   - Include examples if you've changed command-line behavior

1. **Follow conventional commits**:

   - PR titles should follow conventional commit format
   - Example: `feat: add support for custom poster directories`

1. **Test your changes**:

   - Run the main script with different options
   - Test the duplicates utility
   - Ensure existing functionality still works

1. **Update documentation** if needed:

   - Update README.md for new features
   - Update command-line help text
   - Add examples for new functionality

## Project-Specific Notes

### Understanding the Codebase

- **`tpdb.py`**: Main application (~739 lines) with monolithic structure
- **`duplicates.py`**: Standalone utility for finding duplicate posters
- **Global state**: The application uses global variables extensively
- **Fuzzy matching**: Core feature using `thefuzz` library with specific thresholds

### Important Patterns

- **Name normalization**: The `normalize_name()` function is critical for matching
- **Interactive prompts**: Heavy use of `input()` for user decisions
- **File organization**: Specific naming conventions for TV shows vs movies
- **Threshold values**: 70%+ similarity for library matching, 74+ for duplicates

### Testing Your Changes

When working on poster organization features:

```bash
# Test with different library types
python tpdb.py -l Movies --action new
python tpdb.py -l "TV Shows" --action sync

# Test duplicate detection
python duplicates.py /path/to/test/posters

# Test download functionality
python tpdb.py --download "https://theposterdb.com/set/12345"
```

## Getting Help

- **Issues**: Check [GitHub Issues](https://github.com/tahmidul612/tpdb/issues)
- **Questions**: Open a discussion or create an issue
- **Documentation**: Refer to README.md for usage examples

**Thank you for contributing to TPDB!** Your contributions help improve poster organization for Plex users everywhere.
