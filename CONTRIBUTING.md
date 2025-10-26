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

1. **Python 3.10 or higher** (as specified in pyproject.toml)

   - **Windows**: Download from [python.org](https://www.python.org/downloads/)
   - **macOS**: Use Homebrew: `brew install python@3.10` or download from [python.org](https://www.python.org/downloads/)
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

This installs all runtime dependencies (PlexAPI, thefuzz, requests, typer, rich, etc.) and development tools (commitizen, ruff, pre-commit, pytest).

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

   # Test the main CLI
   tpdb --help

   # Test download command
   tpdb download "https://theposterdb.com/set/12345"

   # Test find-dupes command
   tpdb find-dupes /path/to/posters
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

The project has been refactored to use a **modern src layout**:

- **`src/tpdb/cli.py`**: Typer-based command-line interface (~290 lines)

  - Entry point for the `tpdb` command
  - Handles command parsing and option processing
  - Injects configuration into main module

- **`src/tpdb/main.py`**: Core poster processing logic (~827 lines)

  - All business logic and file operations
  - Helper functions for formatted user prompts
  - Uses snake_case naming convention

- **`src/tpdb/dupes.py`**: Duplicate detection utility

  - Standalone tool for finding duplicate poster folders
  - Uses rich for formatted output

- **`scripts/`**: Development utilities

  - `analyze_naming.py`: Detects camelCase naming
  - `apply_snake_case.py`: Automated naming conversions

- **Global state**: The application uses global variables injected by the CLI module

- **Fuzzy matching**: Core feature using `thefuzz` library with specific thresholds

- **User interaction**: Uses typer for prompts and rich for formatted console output

### Important Patterns

- **Name normalization**: The `normalize_name()` function is critical for matching
- **Interactive prompts**: Uses typer for user input, rich for formatted output
- **Helper functions**: `prompt_match_confirmation()`, `prompt_collection_organization()`, `prompt_poster_organization()` provide consistent UX
- **File organization**: Specific naming conventions for TV shows vs movies
- **Threshold values**: 70%+ similarity for library matching, 74+ for duplicates
- **Console output**: Uses rich markup for color-coded, formatted messages

### Testing Your Changes

When working on poster organization features:

```bash
# Test with different library types
tpdb -l Movies --action new
tpdb -l "TV Shows" --action sync

# Test duplicate detection
tpdb find-dupes /path/to/test/posters

# Test download functionality
tpdb download "https://theposterdb.com/set/12345"

# Or use the -d flag with main command
tpdb -d "https://theposterdb.com/set/12345" -l Movies
```

### Code Quality Standards

The refactored codebase follows Python best practices:

- **Naming**: Functions and variables use snake_case, classes use PascalCase
- **Type hints**: Used throughout for better IDE support and type checking
- **Docstrings**: Google-style docstrings with Args/Returns sections
- **Console output**: Rich markup for colored, formatted messages
- **Error handling**: Graceful degradation with informative user prompts

### Development Scripts

Use the scripts in `scripts/` directory for code maintenance:

```bash
# Analyze naming conventions
python scripts/analyze_naming.py

# Preview naming conversions (dry-run)
python scripts/apply_snake_case.py --dry-run

# Apply conversions interactively
python scripts/apply_snake_case.py --interactive
```

See `scripts/README.md` for detailed documentation on these utilities.

## Getting Help

- **Issues**: Check [GitHub Issues](https://github.com/tahmidul612/tpdb/issues)
- **Questions**: Open a discussion or create an issue
- **Documentation**: Refer to README.md for usage examples

**Thank you for contributing to TPDB!** Your contributions help improve poster organization for Plex users everywhere.
