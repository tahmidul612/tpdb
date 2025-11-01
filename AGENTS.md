# AGENTS.md

This file provides guidance to AI coding agents like Claude Code (claude.ai/code), Cursor AI, Codex, Gemini CLI, GitHub Copilot, and other AI coding assistants when working with code in this repository.

## Essential Commands

### Development Setup

```bash
# Install dependencies (recommended)
uv sync --group dev

# Install pre-commit hooks
pre-commit install --hook-type commit-msg --hook-type pre-push
```

### Testing

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_matcher.py

# Run specific test function
pytest tests/test_matcher.py::test_normalize_name

# Run with verbose output
pytest -v
```

### Code Quality

```bash
# Lint and auto-fix issues
ruff check . --fix

# Format code
ruff format .

# Run both
ruff check . --fix && ruff format .

# Run all pre-commit hooks
pre-commit run --all-files
```

### Running the Application

```bash
# Main command help
tpdb --help

# Process specific library
tpdb -l Movies --action new

# Download and organize
tpdb -d "https://theposterdb.com/set/12345" -l Movies

# Sync existing posters with hard links
tpdb -l "TV Shows" --action sync --copy

# Find duplicates
tpdb find-dupes /data/Posters
```

## Architecture Overview

### Global State Pattern

The application uses **global variables** that are injected by the CLI module into the main module. This is critical to understand:

```python
# In cli.py - injection happens here
import tpdb.main as main_module

opts_obj = Options()
opts_obj.force = force
opts_obj.all = replace_all
# ... set other options
main_module.opts = opts_obj
main_module.poster_data = poster_data

# In main.py - globals are declared
opts: Options = Options()  # Injected by CLI
poster_data: Posters = Posters()  # Injected by CLI
POSTER_DIR = "/data/Posters"  # Static default
```

**Why this matters:** Functions in `main.py` access `opts` and `poster_data` directly without parameters. When adding new features, either:

1. Use the existing globals if modifying `main.py`
1. Pass data explicitly if creating new modules (preferred for testability)

### Module Responsibilities

#### `src/tpdb/cli.py` (~290 lines)

- Entry point for all commands
- Parses CLI arguments using Typer
- Connects to Plex server and retrieves library metadata
- **Injects** `opts` and `poster_data` into `main.py` before calling functions
- Handles control flow for library processing

#### `src/tpdb/main.py` (~827 lines)

- Core business logic for poster organization
- All file operations (rename, move, extract, link)
- Fuzzy matching coordination (delegates to `matcher.py`)
- User interaction prompts (using rich markup)
- **Depends on injected globals** (`opts`, `poster_data`)

#### `src/tpdb/matcher.py` (~60 lines)

- **Pure functions** - no global state
- `normalize_name()`: Strips years, punctuation, "set by" text
- `find_best_media_match()`: Fuzzy matching using rapidfuzz
- Highly testable (see `tests/test_matcher.py`)

#### `src/tpdb/auth/` package

**Well-architected authentication module with separation of concerns:**

- `config.py` - `PlexConfigManager` and `PlexCredentials` dataclass
  - Handles loading/saving Plex credentials from config files
  - Proper error handling with IOError for file operations
  - No side effects - fully testable
- `plex_auth.py` - `PlexAuthenticator` and `ConnectionResult` dataclass
  - Pure business logic for Plex server connections
  - No UI dependencies - perfect for testing
  - Comprehensive exception handling for all error types
- `validators.py` - Input validation functions
  - `validate_and_normalize_url()` - URL validation with scheme normalization
  - `validate_token()` - Token format validation
  - Returns tuple of (is_valid, value/error)

**Benefits:**

- 100% test coverage (66 tests)
- Pure functions with no side effects
- Easy to mock and test
- Proper type hints with dataclasses

#### `src/tpdb/ui/` package

**Presentation layer separated from business logic:**

- `prompts.py` - `PlexAuthUI` class
  - All Rich console UI code isolated here
  - No business logic - only presentation
  - Methods for panels, prompts, status, messages
  - Dependency injection via console parameter

**Benefits:**

- Business logic can be tested without mocking Rich
- UI can be changed without affecting core logic
- Clear separation of concerns

#### `src/tpdb/dupes.py`

- Standalone duplicate detection utility
- Can be run via CLI or directly
- Uses fuzzy matching with 74+ similarity threshold

### Data Flow

1. **CLI** receives command → parses options → creates `Options` object
1. **CLI** connects to Plex → retrieves library data → creates `LibraryData` objects
1. **CLI** creates `Posters` container and **injects** into `main.py`
1. **main.py** scans poster directories (70%+ name similarity to library)
1. **main.py** processes ZIP files → extracts → fuzzy matches to media
1. **main.py** prompts user for uncertain matches (using helper functions)
1. **main.py** organizes into folder structure (movies/shows have different logic)
1. **main.py** optionally creates hard links to media folders (`--copy` flag)
1. **main.py** archives processed ZIPs to `Archives/` subdirectory

### Fuzzy Matching Thresholds

These values are **critical** - don't change without extensive testing:

- **Library directory matching**: 70%+ (`fuzz.partial_ratio`)
  - Used to find poster directories like "Movies" vs "Movie Posters"
- **Media name matching**: token-based ratio (`fuzz.token_sort_ratio`)
  - Used after `normalize_name()` preprocessing
  - No hard cutoff - prompts user for confirmation
- **Duplicate detection**: 74%+ (`fuzz.token_set_ratio`)
  - Used in `dupes.py` to find similar folder names

### Directory Structure Expectations

```text
/data/Posters/                    # POSTER_DIR constant
├── Movies/                       # Library-specific (70%+ match to Plex library name)
│   ├── Custom/                   # Individual movie posters
│   │   └── Movie Name (Year)/
│   │       └── poster.jpg
│   ├── Collection Name/          # Multi-movie collections
│   │   ├── Movie 1/
│   │   │   └── poster.jpg
│   │   └── Movie 2/
│   │       └── poster.jpg
│   └── Archives/                 # Processed ZIP files moved here
├── TV Shows/
│   └── Show Name/
│       ├── poster.jpg            # Main show poster
│       ├── Season01.jpg          # Zero-padded seasons
│       ├── Season02.jpg
│       └── Season00.jpg          # Specials
```

## Code Standards

### Naming Conventions

**Critical:** This project was **refactored from camelCase to snake_case**. Always use snake_case:

```python
# Functions and variables
def find_best_media_match():  # ✓ Correct
def findBestMediaMatch():     # ✗ Wrong (old style)

best_match = "..."            # ✓ Correct
bestMatch = "..."             # ✗ Wrong (old style)

# Classes
class LibraryData:            # ✓ Correct (PascalCase)

# Constants
POSTER_DIR = "/data/Posters"  # ✓ Correct (UPPER_SNAKE_CASE)
```

### Rich Console Output

Use **rich markup** for all user-facing output:

```python
from rich.console import Console

console = Console()

# Success
console.print("[bold green]✓[/bold green] Successfully processed")

# Info
console.print("[bold cyan]Processing:[/bold cyan] Movies")

# Warning
console.print("[yellow]⚠ Warning:[/yellow] Low match score")

# Error
console.print("[bold red]✗ Error:[/bold red] Failed to process")

# Dimmed/secondary
console.print(f"  Source: [dim]{file_name}[/dim]")
```

### User Prompts Pattern

Use helper functions for consistent prompts:

```python
# Match confirmation with colored score
if prompt_match_confirmation(source_name, match_name, score, "movie"):
    # proceed with match

# Collection organization
if prompt_collection_organization(source_name, best_match, score):
    # unzip and organize

# Poster organization with match/force/skip options
user_choice = prompt_poster_organization(file_name, match_name, score)
if user_choice == "y":
    # use match
elif user_choice == "f":
    # force rename
else:
    # skip
```

### File Organization Functions

Different logic for movies vs TV shows:

```python
# Movies: Creates subfolder for each movie, renames to "poster.ext"
organize_movie_folder(folder_dir)

# Movie collections: Multiple movies in one folder
organize_movie_collection_folder(folder_dir)

# TV Shows: Renames seasons to SeasonXX.ext format
organize_show_folder(folder_dir)

# Sync existing folders to media library
sync_movie_folder(path)
```

## Testing Guidelines

### Current Test Coverage

✅ **Excellent coverage for auth and ui modules** - 66 comprehensive tests:

**Fully Tested:**

- `auth/config.py` - PlexConfigManager and PlexCredentials (12 tests)
- `auth/plex_auth.py` - PlexAuthenticator and ConnectionResult (14 tests)
- `auth/validators.py` - URL and token validation (13 tests)
- `ui/prompts.py` - PlexAuthUI class (15 tests)
- `matcher.py` - normalize_name() and find_best_media_match() (12 tests)

**Benefits of new test architecture:**

- Pure functions are easy to test without mocking
- Business logic separated from UI enables isolated testing
- Mock PlexServer for connection tests (no real network calls)
- Parametrized tests for comprehensive edge case coverage
- Test file operations with temporary directories
- Proper exception handling verification

⚠️ **Still needs coverage:**

- Most of `main.py` (poster organization logic)
- Integration tests for `cli.py` commands

### Writing Tests

Follow the existing pattern in `tests/test_matcher.py`:

```python
import pytest
from tpdb.matcher import normalize_name


@pytest.mark.parametrize(
    "input_name,expected",
    [
        ("Movie (2022)", "movie"),
        ("Movie. set by Creator", "movie"),
        # ... more test cases
    ],
)
def test_normalize_name(input_name, expected):
    """Test normalize_name with various inputs."""
    assert normalize_name(input_name) == expected
```

**Test naming:** `test_<function>_<scenario>` (e.g., `test_find_best_media_match_successful`)

## Commit & Branch Conventions

### Conventional Commits

Required by pre-commit hooks:

```bash
feat: add support for custom poster directories
fix: resolve fuzzy matching threshold issues
docs: update README installation instructions
refactor: simplify matching logic in matcher.py
test: add tests for organize_movie_folder
chore: update dependencies to latest versions
```

Use `cz commit` for interactive prompt.

### Conventional Branches

```bash
git checkout -b feat/custom-directories
git checkout -b fix/memory-leak
git checkout -b docs/update-contributing
git checkout -b refactor/simplify-matching
git checkout -b test/add-main-tests
```

## Important Implementation Details

### Hard Linking (`--copy` flag)

Creates hard links (not copies) from organized posters to media folders:

```python
os.link(orig_file, new_file)  # Same inode, no space duplication
```

**Limitations:**

- Both directories must be on same filesystem
- Requires write permissions to both locations
- Season renaming: `Season01.jpg` → `season01-poster.jpg`
- Specials: `Season00.jpg` → `season-specials-poster.jpg`

### ZIP File Processing

1. Renames ZIP to clean format (removes underscores, extracts "set by" text)
1. Fuzzy matches ZIP name to media library
1. For shows: Extracts to matched show name folder
1. For movies with high match (>70): Extracts to matched movie folder
1. For movies with low match: Treats as collection, organizes individually
1. Archives ZIP to `Archives/` subdirectory after processing

### Plex Configuration

Stored in `~/.config/plexapi/config.ini`:

```ini
[auth]
server_baseurl = http://server:32400
server_token = your_token_here
```

First run prompts for credentials and optionally saves them.

## Common Pitfalls

1. **Don't bypass global injection** - Functions in `main.py` expect `opts` and `poster_data` to be set by CLI
1. **Don't change fuzzy thresholds** without understanding impact - users depend on these values
1. **Don't use print()** - Always use `console.print()` with rich markup
1. **Don't forget pre-commit hooks** - Run `pre-commit install` after clone
1. **Don't use camelCase** - Project was refactored to snake_case
1. **Test with both library types** - Movies and TV shows have different organization logic

## Development Scripts

Located in `scripts/`:

```bash
# Detect camelCase names (analysis only)
python scripts/analyze_naming.py

# Preview snake_case conversions
python scripts/apply_snake_case.py --dry-run

# Apply conversions interactively
python scripts/apply_snake_case.py --interactive
```

See `scripts/README.md` for details.

## Dependencies

### Core Runtime

- **plexapi**: Plex server communication
- **rapidfuzz**: Fast fuzzy string matching (replaced thefuzz)
- **requests**: HTTP downloads from ThePosterDB
- **typer[all]**: Modern CLI framework (includes rich)
- **rich**: Terminal formatting and progress bars
- **pyrfc6266**: Parse Content-Disposition headers

### Development Tools

- **pytest**: Testing framework
- **ruff**: Linter and formatter (replaced black/flake8)
- **pre-commit**: Git hooks for quality control
- **commitizen**: Conventional commits enforcement
- **detect-secrets**: Prevent committing sensitive data

## References

For detailed information, see:

- `README.md` - User-facing documentation and usage examples
- `CONTRIBUTING.md` - Full development guide with setup instructions
- `.github/copilot-instructions.md` - Additional architecture details
- `pyproject.toml` - Dependencies and tool configuration
