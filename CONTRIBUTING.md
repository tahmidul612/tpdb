# Contributing to TPDB

Thank you for considering contributing to TPDB (Plex Poster Organizer)! This guide provides everything you need to get started with development, from setting up your environment to submitting pull requests.

We welcome all types of contributions: bug fixes, new features, documentation improvements, and more!

---

## Table of Contents

- [Contributing to TPDB](#contributing-to-tpdb)
  - [Table of Contents](#table-of-contents)
  - [Code of Conduct](#code-of-conduct)
  - [Getting Started](#getting-started)
    - [Prerequisites](#prerequisites)
    - [Development Environment Setup](#development-environment-setup)
  - [Project Architecture](#project-architecture)
    - [Package Structure](#package-structure)
    - [Key Components](#key-components)
    - [Data Flow](#data-flow)
  - [Development Workflow](#development-workflow)
    - [Creating a Feature Branch](#creating-a-feature-branch)
    - [Making Changes](#making-changes)
    - [Testing Your Changes](#testing-your-changes)
    - [Committing Changes](#committing-changes)
  - [Code Standards](#code-standards)
    - [Python Style Guide](#python-style-guide)
    - [Naming Conventions](#naming-conventions)
    - [Documentation](#documentation)
  - [Testing](#testing)
    - [Running Tests](#running-tests)
    - [Writing Tests](#writing-tests)
  - [Code Quality Tools](#code-quality-tools)
    - [Ruff (Linter &amp; Formatter)](#ruff-linter--formatter)
    - [Pre-commit Hooks](#pre-commit-hooks)
  - [Commit Conventions](#commit-conventions)
    - [Commit Message Format](#commit-message-format)
    - [Commit Types](#commit-types)
    - [Examples](#examples)
  - [Branch Naming Convention](#branch-naming-convention)
  - [Pull Request Process](#pull-request-process)
    - [Before Submitting](#before-submitting)
    - [PR Description Template](#pr-description-template)
    - [Review Process](#review-process)
  - [Development Tips](#development-tips)
  - [Getting Help](#getting-help)

## Code of Conduct

This project adheres to a code of conduct that all contributors are expected to follow. We are committed to providing a welcoming and inclusive experience for everyone.

### Our Standards

- **Be respectful**: Treat all contributors with respect and consideration
- **Be collaborative**: Work together to find the best solutions
- **Be patient**: Help newcomers get up to speed
- **Be constructive**: Provide helpful feedback and suggestions

## Getting Started

### Prerequisites

Ensure you have the following tools installed before starting development:

#### Required Tools

1. **Python 3.10 or higher**

   Check your version:

   ```bash
   python --version
   ```

   Installation:
   - **Windows**: Download from [python.org](https://www.python.org/downloads/)
   - **macOS**: `brew install python@3.10` or download from [python.org](https://www.python.org/downloads/)
   - **Linux**: `sudo apt install python3 python3-pip` (Debian/Ubuntu) or `sudo dnf install python3` (Fedora)

2. **Git**

   Check if installed:

   ```bash
   git --version
   ```

   Installation:
   - **Windows**: Download from [git-scm.com](https://git-scm.com/download/win)
   - **macOS**: `brew install git` or comes with Xcode Command Line Tools
   - **Linux**: `sudo apt install git` (Debian/Ubuntu)

3. **uv** (Python package manager - recommended)

   Installation:

   ```bash
   # macOS/Linux
   curl -LsSf https://astral.sh/uv/install.sh | sh

   # Windows (PowerShell)
   powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
   ```

   Verify installation:

   ```bash
   uv --version
   ```

### Development Environment Setup

Follow these steps to set up your local development environment:

#### 1. Fork and Clone

```bash
# Fork the repository on GitHub first, then clone your fork
git clone https://github.com/YOUR_USERNAME/tpdb.git
cd tpdb

# Add upstream remote to sync with the main repository
git remote add upstream https://github.com/tahmidul612/tpdb.git
```

#### 2. Install Dependencies

**Using uv (recommended):**

```bash
# Install all dependencies including dev tools
uv sync --group dev
```

**Using pip:**

```bash
# Create a virtual environment (optional but recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in editable mode with dev dependencies
pip install -e .[dev]
```

This installs:
- **Runtime dependencies**: PlexAPI, rapidfuzz, requests, typer, rich
- **Development tools**: pytest, ruff, pre-commit, commitizen, detect-secrets

#### 3. Set Up Pre-commit Hooks

Pre-commit hooks automatically check your code before each commit:

```bash
# Install the pre-commit framework
pre-commit install

# Install commit message validation
pre-commit install --hook-type commit-msg

# Install pre-push validation
pre-commit install --hook-type pre-push
```

**What the hooks do:**

- Update `uv.lock` and `requirements.txt` when dependencies change
- Remove trailing whitespace
- Ensure LF line endings
- Lint and format Python code with ruff
- Format Markdown files
- Validate commit messages (conventional commits)
- Validate branch names (conventional branches)
- Check for accidentally committed secrets

#### 4. Verify Setup

```bash
# Check that tpdb is installed
tpdb --help

# Run tests to ensure everything works
pytest

# Try running pre-commit manually
pre-commit run --all-files
```

If all commands succeed, your development environment is ready!

## Project Architecture

Understanding the project structure will help you navigate the codebase and make effective contributions.

### Package Structure

TPDB uses a modern **src layout** with clear separation of concerns:

```text
tpdb/
├── src/tpdb/              # Main package (installable)
│   ├── __init__.py        # Package initialization
│   ├── cli.py             # Command-line interface (~290 lines)
│   ├── main.py            # Core business logic (~827 lines)
│   ├── dupes.py           # Duplicate detection utility
│   └── matcher.py         # Fuzzy matching algorithms
│
├── scripts/               # Development utilities
│   ├── analyze_naming.py  # Detects camelCase names
│   └── apply_snake_case.py # Applies snake_case conversions
│
├── tests/                 # Test suite
│   └── test_main.py       # Unit tests
│
├── pyproject.toml         # Project metadata and dependencies
├── uv.lock                # Locked dependency versions
├── requirements.txt       # Exported requirements (generated)
└── .pre-commit-config.yaml # Pre-commit hook configuration
```

### Key Components

#### CLI Module (`src/tpdb/cli.py`)

- **Purpose**: Command-line interface entry point
- **Framework**: Typer-based for modern CLI experience
- **Responsibilities**:
  - Parse command-line arguments
  - Handle subcommands (`download`, `find-dupes`)
  - Initialize global state and inject into main module
  - Provide user-facing help text

**Key functions:**
- `main_callback()`: Main command handler with all options
- `download()`: Download posters from ThePosterDB
- `find_dupes()`: Invoke duplicate detection utility

#### Main Module (`src/tpdb/main.py`)

- **Purpose**: Core poster processing logic
- **Lines**: ~827 lines of business logic
- **Responsibilities**:
  - Connect to Plex server
  - Match posters to media using fuzzy matching
  - Organize files into folder structure
  - Handle ZIP extraction
  - Create hard links to media folders

**Key classes:**
- `LibraryData`: Stores Plex library metadata
- `Posters`: Container for poster organization data
- `Options`: Configuration from CLI options

**Key functions:**
- `normalize_name()`: Name normalization for matching
- `find_best_media_match()`: Fuzzy matching algorithm
- `download_poster()`: Download from ThePosterDB
- `process_zip_file()`: Extract and organize ZIP archives
- `organize_movie_folder()` / `organize_show_folder()`: Media-specific organization
- `copy_posters()`: Create hard links to media directories

**Helper functions for UX:**
- `prompt_match_confirmation()`: Formatted match confirmation with score
- `prompt_collection_organization()`: Collection folder prompt
- `prompt_poster_organization()`: Match/force/skip options

#### Matcher Module (`src/tpdb/matcher.py`)

- **Purpose**: Fuzzy string matching utilities
- **Library**: Uses `rapidfuzz` for fast matching
- **Thresholds**:
  - Library matching: 70%+ similarity
  - Media matching: Token-based ratio
  - Duplicate detection: 74%+ similarity

#### Dupes Module (`src/tpdb/dupes.py`)

- **Purpose**: Standalone duplicate detection
- **Features**: Fuzzy matching with formatted rich output
- **Usage**: Can be run directly or via CLI

### Data Flow

```
1. User runs tpdb command
   ↓
2. CLI parses options and creates Options object
   ↓
3. CLI connects to Plex server
   ↓
4. Main module receives Plex library data
   ↓
5. Discover poster directories (70%+ name similarity)
   ↓
6. Process ZIP files (extract, match, organize)
   ↓
7. Match individual posters to media (fuzzy matching)
   ↓
8. Prompt user for uncertain matches
   ↓
9. Organize into folder structure
   ↓
10. Optionally create hard links (--copy flag)
   ↓
11. Move processed ZIPs to Archives
```

### Global State Pattern

The application uses global variables injected by the CLI:

```python
# In cli.py
import tpdb.main as main_module
main_module.opts = opts_obj
main_module.poster_data = poster_data

# In main.py
opts: Options  # Global instance with CLI flags
poster_data: Posters  # Global data container
POSTER_DIR = "/data/Posters"  # Default directory
```

This pattern allows the main module's functions to access configuration without passing parameters everywhere.

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
