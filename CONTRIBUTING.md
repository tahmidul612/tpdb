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
│   ├── matcher.py         # Fuzzy matching algorithms
│   ├── dupes.py           # Duplicate detection utility
│   ├── auth/              # Authentication package
│   │   ├── config.py      # Plex configuration management
│   │   ├── plex_auth.py   # Plex server connection logic
│   │   └── validators.py  # URL and token validation
│   └── ui/                # User interface package
│       └── prompts.py     # Rich console UI components
│
├── scripts/               # Development utilities
│   ├── analyze_naming.py  # Detects camelCase names
│   └── apply_snake_case.py # Applies snake_case conversions
│
├── tests/                 # Test suite (66 tests)
│   ├── test_matcher.py    # Matcher module tests
│   ├── test_auth_config.py # Config management tests
│   ├── test_auth_plex_auth.py # Plex authentication tests
│   ├── test_auth_validators.py # Validation tests
│   └── test_ui_prompts.py # UI prompts tests
│
├── assets/                # Demo and media files
│   ├── demo.gif           # Animated demo
│   └── demo.cast          # Asciinema recording
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
- **Key functions**:
  - `normalize_name()`: Strips years, punctuation, "set by" text
  - `find_best_media_match()`: Fuzzy matching using rapidfuzz
- **Thresholds**:
  - Library matching: 70%+ similarity
  - Media matching: Token-based ratio
  - Duplicate detection: 74%+ similarity
- **Design**: Pure functions with no global state - highly testable

#### Auth Package (`src/tpdb/auth/`)

Well-architected authentication module with separation of concerns:

- **`config.py`** - `PlexConfigManager` and `PlexCredentials` dataclass
  - Handles loading/saving Plex credentials from config files
  - Proper error handling with IOError for file operations
  - No side effects - fully testable

- **`plex_auth.py`** - `PlexAuthenticator` and `ConnectionResult` dataclass
  - Pure business logic for Plex server connections
  - No UI dependencies - perfect for testing
  - Comprehensive exception handling for all error types

- **`validators.py`** - Input validation functions
  - `validate_and_normalize_url()`: URL validation with scheme normalization
  - `validate_token()`: Token format validation
  - Returns tuple of (is_valid, value/error)

**Benefits:**
- 100% test coverage
- Pure functions with no side effects
- Easy to mock and test
- Proper type hints with dataclasses

#### UI Package (`src/tpdb/ui/`)

Presentation layer separated from business logic:

- **`prompts.py`** - `PlexAuthUI` class
  - All Rich console UI code isolated here
  - No business logic - only presentation
  - Methods for panels, prompts, status, messages
  - Dependency injection via console parameter

**Benefits:**
- Business logic can be tested without mocking Rich
- UI can be changed without affecting core logic
- Clear separation of concerns

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

## Development Workflow

### Creating a Feature Branch

Always create a new branch for your changes following the [branch naming convention](#branch-naming-convention):

```bash
# Sync with upstream first
git fetch upstream
git checkout main
git merge upstream/main

# Create your feature branch
git checkout -b feat/your-feature-name
# or
git checkout -b fix/bug-description
# or
git checkout -b docs/update-readme
```

### Making Changes

1. **Make your code changes** in the appropriate module
2. **Follow the code standards** outlined in this guide
3. **Add or update tests** for your changes
4. **Update documentation** if needed (README, docstrings, etc.)

### Testing Your Changes

Test thoroughly before committing:

```bash
# Run the full test suite
pytest

# Run tests with verbose output
pytest -v

# Run tests for a specific file
pytest tests/test_matcher.py

# Run a specific test function
pytest tests/test_matcher.py::test_normalize_name
```

**Manual testing:**

```bash
# Test the main CLI
tpdb --help

# Test with your Plex library (use a test library if possible)
tpdb -l "Test Movies" --action new

# Test download functionality
tpdb download "https://theposterdb.com/set/12345"

# Test duplicate detection
tpdb find-dupes /path/to/test/posters
```

### Committing Changes

We use **Conventional Commits** (see [Commit Conventions](#commit-conventions) below).

**Using commitizen (recommended):**

```bash
# Interactive commit prompt
cz commit
```

This guides you through:
1. Selecting commit type (feat, fix, docs, etc.)
2. Writing a short description
3. Optional longer description
4. Breaking changes (if any)

**Manual commits:**

```bash
# Format: <type>: <description>
git commit -m "feat: add support for custom poster directories"
git commit -m "fix: resolve fuzzy matching threshold issues"
git commit -m "docs: update installation instructions"
```

**Pushing your branch:**

```bash
# Push to your fork
git push origin your-branch-name

# If pre-push hooks fail, fix the issues and try again
```

## Code Standards

### Python Style Guide

TPDB follows PEP 8 with some project-specific conventions:

- **Line length**: 88 characters (Black-compatible)
- **Indentation**: 4 spaces (no tabs)
- **Line endings**: LF (Unix-style)
- **Quotes**: Double quotes for strings
- **Imports**: Organized and grouped (standard library, third-party, local)

### Naming Conventions

Follow these naming patterns consistently:

| Element | Convention | Example |
|---------|-----------|---------|
| Functions | snake_case | `find_best_media_match()` |
| Variables | snake_case | `best_match`, `poster_folders` |
| Classes | PascalCase | `LibraryData`, `Posters`, `Options` |
| Constants | UPPER_SNAKE_CASE | `POSTER_DIR`, `DEFAULT_THRESHOLD` |
| Private/internal | _leading_underscore | `_internal_helper()` |
| Module names | snake_case | `main.py`, `matcher.py` |

**Important**: The codebase has been refactored from camelCase to snake_case. Always use snake_case for new code.

### Documentation

**Docstrings** (Google style):

```python
def find_best_media_match(poster_name: str, media_items: list[str]) -> tuple[str, int]:
    """Find the best matching media item for a poster using fuzzy matching.

    Args:
        poster_name: The name of the poster to match.
        media_items: List of media item names to search.

    Returns:
        A tuple of (best_match_name, match_score) where match_score is 0-100.

    Raises:
        ValueError: If media_items is empty.
    """
    # Implementation
```

**Comments**:
- Add comments for complex logic or non-obvious code
- Avoid obvious comments that just repeat the code
- Use comments to explain *why*, not *what*

**Type hints**:
- Use type hints for all function signatures
- Import types from `typing` module when needed
- Use modern type syntax (e.g., `list[str]` instead of `List[str]` in Python 3.10+)

### Console Output Patterns

Use **rich markup** for consistent, beautiful terminal output:

```python
from rich.console import Console
console = Console()

# Success messages
console.print("[bold green]✓[/bold green] Operation completed successfully")

# Info messages
console.print("[bold cyan]Processing:[/bold cyan] Movie Library")

# Warnings
console.print("[yellow]⚠ Warning:[/yellow] Match score below threshold")

# Errors
console.print("[bold red]✗ Error:[/bold red] Library not found")

# Dimmed/secondary info
console.print(f"  Source: [dim]{file_name}[/dim]")
```

## Testing

### Running Tests

The project uses **pytest** as the testing framework:

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_matcher.py

# Run specific test function
pytest tests/test_matcher.py::test_normalize_name

# Run with coverage report
pytest --cov=src/tpdb --cov-report=html
```

### Writing Tests

When adding new functionality, include appropriate tests:

**Test file structure:**

```python
import pytest
from tpdb.matcher import normalize_name, find_best_media_match

def test_normalize_name():
    """Test name normalization removes years and punctuation."""
    assert normalize_name("The Matrix (1999)") == "the matrix"
    assert normalize_name("Movie: The Sequel") == "movie the sequel"

def test_find_best_media_match():
    """Test fuzzy matching finds correct media item."""
    media_items = ["The Dark Knight", "The Dark Knight Rises"]
    match, score = find_best_media_match("Dark Knight (2008)", media_items)
    assert match == "The Dark Knight"
    assert score > 80
```

**Testing guidelines:**

- One test file per module (e.g., `test_matcher.py` for `matcher.py`)
- Use descriptive test function names (`test_<what>_<condition>_<expected>`)
- Include docstrings explaining what the test validates
- Use pytest fixtures for common setup
- Test edge cases and error conditions
- Mock external dependencies (Plex API, file I/O)

**Current test coverage:**

✅ The project has excellent test coverage:
- **66 comprehensive tests** covering core functionality
- **auth package**: 100% coverage (config, plex_auth, validators)
- **ui package**: Full coverage (prompts)
- **matcher module**: Complete coverage (normalize_name, find_best_media_match)
- **Areas for improvement**: Additional tests for main.py and cli.py would be welcome

**Your contribution can help improve this!** Adding tests for main.py and cli.py integration would be valuable.

## Code Quality Tools

### Ruff (Linter & Formatter)

**Ruff** is an extremely fast Python linter and formatter that replaces multiple tools (flake8, black, isort, etc.).

**Configuration** is in `pyproject.toml`:

```toml
[tool.ruff]
line-length = 88
target-version = "py310"

[tool.ruff.format]
quote-style = "double"
indent-style = "space"
line-ending = "lf"
```

**Usage:**

```bash
# Check for linting issues
ruff check .

# Auto-fix issues
ruff check . --fix

# Format code
ruff format .

# Check and format in one command
ruff check . --fix && ruff format .
```

**Common linting errors:**

- **E501**: Line too long (max 88 characters)
- **F401**: Unused import
- **F841**: Unused variable
- **E711**: Comparison to None should use 'is'

Most issues can be auto-fixed with `ruff check . --fix`.

### Pre-commit Hooks

Pre-commit hooks run automatically before each commit to ensure code quality:

**Installed hooks:**

1. **uv-lock**: Updates lock file when `pyproject.toml` changes
2. **uv-export**: Exports `requirements.txt` from lock file
3. **trailing-whitespace**: Removes trailing whitespace
4. **check-illegal-windows-names**: Prevents Windows-incompatible filenames
5. **mixed-line-ending**: Ensures LF line endings
6. **ruff-check**: Lints Python code
7. **ruff-format**: Formats Python code
8. **mdformat**: Formats Markdown files
9. **commitizen**: Validates commit messages
10. **commitizen-branch**: Validates branch names (pre-push)
11. **detect-secrets**: Prevents committing secrets

**Manual runs:**

```bash
# Run all hooks on all files
pre-commit run --all-files

# Run specific hook
pre-commit run ruff-check --all-files

# Skip hooks (use sparingly!)
git commit --no-verify -m "feat: add feature"
```

## Commit Conventions

TPDB follows [Conventional Commits](https://www.conventionalcommits.org/) for clear, standardized commit messages.

### Commit Message Format

```text
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

### Commit Types

| Type | Description | Example |
|------|-------------|---------|
| `feat` | New features | `feat: add support for custom directories` |
| `fix` | Bug fixes | `fix: resolve memory leak in processor` |
| `docs` | Documentation only | `docs: update README installation section` |
| `style` | Code style/formatting | `style: apply ruff formatting` |
| `refactor` | Code restructuring | `refactor: simplify matching logic` |
| `test` | Test additions/changes | `test: add tests for normalize_name` |
| `chore` | Maintenance tasks | `chore: update dependencies` |
| `perf` | Performance improvements | `perf: optimize fuzzy matching` |
| `ci` | CI/CD changes | `ci: add GitHub Actions workflow` |

### Examples

**Good commit messages:**

```bash
feat: add support for custom poster directories
fix: resolve fuzzy matching threshold issues
docs: update contributing guide with code standards
refactor: extract user prompt helpers into functions
test: add comprehensive tests for matcher module
chore: bump rapidfuzz to version 3.0.0
```

**Bad commit messages:**

```bash
# Too vague
fix: fix bug

# Missing type
Add new feature

# Not descriptive
update code

# Wrong type
feat: fix typo in README  # Should be "docs:"
```

### Commit Body (Optional)

For complex changes, add a detailed body:

```text
feat: add support for custom poster directories

Users can now specify custom directories for poster storage
instead of using the default /data/Posters path. This adds
flexibility for users with different storage configurations.

- Add --poster-dir CLI option
- Update configuration to support custom paths
- Add validation for directory existence

Closes #42
```

### Breaking Changes

If your commit introduces breaking changes, mark it clearly:

```text
feat!: change default poster directory structure

BREAKING CHANGE: The default directory structure has changed.
Users will need to reorganize existing posters or update their
configuration to use the old structure.
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

### Branch Name Rules

- Use lowercase only
- Use hyphens to separate words (not underscores or spaces)
- Keep names short but descriptive
- Match the type to the primary work being done

## Pull Request Process

### Before Submitting

Complete this checklist before opening a PR:

- [ ] All tests pass locally (`pytest`)
- [ ] Code is linted and formatted (`ruff check . --fix && ruff format .`)
- [ ] Pre-commit hooks pass (`pre-commit run --all-files`)
- [ ] New tests added for new functionality
- [ ] Documentation updated (README, docstrings, etc.)
- [ ] Commit messages follow conventional commits
- [ ] Branch name follows conventional branch naming
- [ ] No merge conflicts with main branch

### PR Description Template

Use this template for your pull request description:

```markdown
## Description

Brief description of what this PR does and why.

## Type of Change

- [ ] Bug fix (non-breaking change fixing an issue)
- [ ] New feature (non-breaking change adding functionality)
- [ ] Breaking change (fix or feature causing existing functionality to change)
- [ ] Documentation update
- [ ] Code refactoring
- [ ] Performance improvement

## Changes Made

- Bullet point list of changes
- Another change
- And another

## Testing

Describe how you tested your changes:

- [ ] Ran test suite (`pytest`)
- [ ] Manually tested with Movies library
- [ ] Manually tested with TV Shows library
- [ ] Tested download functionality
- [ ] Tested duplicate detection

## Screenshots (if applicable)

Add screenshots or GIFs showing the changes in action.

## Related Issues

Closes #123
Related to #456

## Checklist

- [ ] My code follows the project's code standards
- [ ] I have performed a self-review of my code
- [ ] I have commented my code where necessary
- [ ] I have updated the documentation
- [ ] My changes generate no new warnings
- [ ] I have added tests that prove my fix/feature works
- [ ] New and existing tests pass locally
```

### Review Process

1. **Automated checks**: GitHub Actions (if configured) will run tests and linting
2. **Code review**: Maintainers will review your code
3. **Feedback**: Address any requested changes
4. **Approval**: Once approved, your PR will be merged
5. **Changelog**: Your changes will be included in the next release

**What reviewers look for:**

- Code quality and adherence to standards
- Test coverage for new functionality
- Clear commit messages and PR description
- No breaking changes (unless intentional and documented)
- Performance considerations
- Security implications

**Response time:**

- We aim to provide initial feedback within 1-2 weeks
- More complex PRs may take longer to review
- Feel free to ping maintainers if you haven't heard back

## Development Tips

### Debugging

**Enable verbose logging:**

Currently, TPDB doesn't have extensive logging. When debugging:

1. Add temporary `console.print()` statements
2. Use Python's debugger: `import pdb; pdb.set_trace()`
3. Check Plex server logs for API errors

**Common issues:**

- **Import errors**: Ensure you installed in editable mode (`pip install -e .`)
- **Plex connection**: Verify server URL and token in config file
- **File permissions**: Check write permissions to poster directory

### Working with Fuzzy Matching

The fuzzy matching logic is critical. When modifying:

- Test with various name formats (years, special characters, etc.)
- Maintain existing threshold values (70% for libraries, 74% for duplicates)
- Use `normalize_name()` before matching
- Test with both movie and TV show names

**Example test cases:**

```python
# These should match
"The Matrix (1999)" → "The Matrix"
"Movie: The Sequel" → "Movie The Sequel"
"Dark Knight, The" → "The Dark Knight"
```

### Development Scripts

The `scripts/` directory contains helpful utilities:

```bash
# Detect camelCase names in codebase
python scripts/analyze_naming.py

# Preview snake_case conversions
python scripts/apply_snake_case.py --dry-run

# Apply conversions interactively
python scripts/apply_snake_case.py --interactive
```

See `scripts/README.md` for detailed documentation.

### IDE Setup

**VS Code:**

Recommended extensions (from `.vscode/extensions.json`):
- Python
- Ruff
- GitLens

**PyCharm:**

1. Mark `src` as Sources Root
2. Enable Python 3.10+ support
3. Configure Ruff as external tool

## Getting Help

Need assistance? Here's how to get help:

- **Documentation**: Start with [README.md](README.md) for usage
- **Issues**: Search [existing issues](https://github.com/tahmidul612/tpdb/issues)
- **New issue**: Open an issue with details about your problem
- **Discussions**: Use GitHub Discussions for questions and ideas
- **Code review**: Request review from maintainers in your PR

**When asking for help, include:**

- Python version (`python --version`)
- Operating system
- TPDB version or commit hash
- Error messages (full stack trace)
- Steps to reproduce the issue

---

**Thank you for contributing to TPDB!** Your efforts help make poster management easier for Plex users worldwide. Every contribution, no matter how small, is valued and appreciated.

Happy coding! 🎨🎬
