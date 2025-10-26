# Copilot Instructions for TPDB (Plex Poster Organizer)

## Project Architecture

This is a Python utility for downloading, organizing, and syncing movie/TV show posters from ThePosterDB with Plex media libraries. The project has been refactored from monolithic scripts to a modern **src layout** with a clean separation of concerns:

### Package Structure

```
tpdb/
├── src/tpdb/           # Main package (installable)
│   ├── __init__.py     # Package initialization
│   ├── cli.py          # Command-line interface (typer-based)
│   ├── main.py         # Core business logic (~827 lines)
│   └── dupes.py        # Duplicate detection utility
├── scripts/            # Development utilities
│   ├── analyze_naming.py   # Detects camelCase names
│   └── apply_snake_case.py # Applies snake_case conversions
└── tests/              # Test suite
    └── test_main.py    # Tests for core functionality
```

### Key Components

- **`src/tpdb/cli.py`**: Typer-based CLI entry point (~290 lines)

  - Main command callback handles library processing
  - Subcommands: `download`, `find-dupes`
  - Injects global `opts` and `poster_data` into main module

- **`src/tpdb/main.py`**: Core poster processing logic (~827 lines)

  - All business logic and file operations
  - Helper functions for user prompts (rich formatting)
  - snake_case naming convention (converted from camelCase)

- **`src/tpdb/dupes.py`**: Standalone duplicate detection

  - Fuzzy matching for finding duplicate poster folders
  - Uses rich for formatted output

## Core Data Structures

### Key Classes

- **`LibraryData`**: Stores Plex library metadata (title, type, locations)
- **`Posters`**: Container for poster organization data with collections for folders, files, zip files, and media mappings
- **`Options`**: Configuration object holding CLI options (force, all, copy, unlinked, action, filter)

### Key Functions (All snake_case)

- `normalize_name()`: Name normalization for improved media matching (removes years, punctuation, "set by" text)
- `find_best_media_match()`: Fuzzy matching algorithm for associating poster files with media
- `download_poster()`: Downloads posters from ThePosterDB URLs with progress bars
- `process_zip_file()`: Extracts and organizes poster zip file collections
- `organize_movie_folder()` / `organize_show_folder()`: Media type-specific organization logic
- `copy_posters()`: Creates hard links from poster folders to Plex media directories
- `sync_movie_folder()`: Syncs existing movie poster folders
- `movie_poster()`: Processes individual movie posters
- `find_posters()`: Discovers poster files and folders

### Helper Functions for User Interaction

- `prompt_match_confirmation()`: Formatted prompt for match confirmation with score display
- `prompt_collection_organization()`: Prompt for organizing collection/set folders
- `prompt_poster_organization()`: Prompt with match/force/skip options for individual posters

These helpers use **rich markup** for colored, formatted console output.

### Global State Pattern

The application uses global variables injected by the CLI:

- `opts`: Global `Options` instance with CLI flags (force, all, copy, unlinked, action, filter)
- `poster_data`: Global `Posters` instance shared across functions
- `POSTER_DIR`: Default poster directory (`/data/Posters`)

The CLI module (`cli.py`) creates these objects and injects them into `main.py` via:

```python
import tpdb.main as main_module

main_module.opts = opts_obj
main_module.poster_data = poster_data
```

## Critical Workflows

### Fuzzy String Matching Pattern

The core matching logic uses `thefuzz` library with specific scoring thresholds:

```python
# Library matching: 70%+ similarity for directory discovery
poster_root_dirs = [
    os.path.join(POSTER_DIR, path)
    for path in os.listdir(POSTER_DIR)
    if fuzz.partial_ratio(selected_library.title, path) > 70
]

# Media matching: Uses token_set_ratio with normalize_name() preprocessing
def normalize_name(name: str) -> str:
    # Removes years, 'set by' text, punctuation, converts to lowercase
```

### User Interaction Pattern

The refactored codebase uses **typer** for prompts and **rich** for output:

```python
# Input prompts (typer)
if typer.confirm("Proceed with this match?", default=True):
    # ... process

# Console output (rich with markup)
console.print("[bold cyan]Processing library:[/bold cyan] Movies")
console.print(f"[bold green]✓[/bold green] Successfully processed {count} files")
```

**Helper functions** encapsulate common prompt patterns:

- `prompt_match_confirmation()` - Shows match with score and color-coded rating
- `prompt_collection_organization()` - Handles collection/set organization prompts
- `prompt_poster_organization()` - Offers match/force/skip options

### File Organization Conventions

- **TV Shows**: Season files renamed with zero-padded format (Season01, Season02, etc.)
- **Movies**: Individual posters renamed to standardized "poster" filename
- **Collections**: Multi-movie sets organized into subfolders by movie name
- **Archives**: Processed zip files moved to Archives subdirectory

### Plex Integration Pattern

Configuration stored in `~/.config/plexapi/config.ini`:

```ini
[auth]
server_baseurl = http://server:32400
server_token = your_token
```

## Expected Directory Structure

The tool expects a specific poster directory structure:

- Default poster root: `/data/Posters`
- Library-specific subdirectories (e.g., `/data/Posters/Movies`, `/data/Posters/TV Shows`)
- Downloads and zip files placed in library subdirectories
- Processed archives moved to `Archives/` subdirectory after extraction

## Development Practices

### Development Environment Setup

**Prerequisites**: Python 3.14+, Git, and uv package manager

**Setup workflow**:

```bash
# Clone and setup
git clone https://github.com/YOUR_USERNAME/tpdb.git
cd tpdb

# Install dependencies and dev tools
uv sync --group dev

# Setup pre-commit hooks
pre-commit install --hook-type commit-msg --hook-type pre-push
```

### Git Workflow Standards

Follow these conventions for commits, branches, and pull requests:

**Conventional Commits** (https://www.conventionalcommits.org/):

- `feat:` new features
- `fix:` bug fixes
- `refactor:` code changes that neither fix bugs nor add features
- `docs:` documentation only changes
- `style:` formatting, missing semicolons, etc (no code change)
- `test:` adding or correcting tests
- `chore:` updating build tasks, package manager configs, etc

**Conventional Branches** (https://conventional-branch.github.io/):

- `feat/description` - new features
- `fix/description` - bug fixes
- `refactor/description` - code refactoring
- `docs/description` - documentation updates
- `test/description` - test additions/fixes
- `chore/description` - maintenance tasks

**Pull Request Titles**: Use conventional commit syntax

- `feat: add support for custom poster directories`
- `fix: resolve fuzzy matching threshold issues`
- `refactor: improve normalize_name function performance`

### Testing

- Single test file: `tests/test_main.py` testing only `normalize_name()` function
- Run tests: `pytest` or `python -m pytest tests/`
- Very limited test coverage - most functionality untested

**Project-specific testing examples**:

```bash
# Test main functionality
tpdb --help
tpdb -l Movies --action new
tpdb -l "TV Shows" --action sync

# Test duplicates utility
tpdb find-dupes /path/to/test/posters

# Test download functionality
tpdb -d "https://theposterdb.com/set/12345"
```

### Development Scripts

The `scripts/` directory contains utilities for code maintenance:

- **`analyze_naming.py`**: Detects camelCase names that should be snake_case

  - Read-only analysis tool
  - Can be imported as a module
  - Filters out external library calls

- **`apply_snake_case.py`**: Automatically converts camelCase to snake_case

  - Imports detection logic from `analyze_naming.py`
  - Supports `--dry-run` and `--interactive` modes
  - Uses word-boundary regex for safe replacements

**Usage:**

```bash
# Analyze codebase
python scripts/analyze_naming.py

# Preview conversions
python scripts/apply_snake_case.py --dry-run

# Apply conversions interactively
python scripts/apply_snake_case.py --interactive
```

See `scripts/README.md` for detailed documentation.

### Duplicate Detection Utility

- `tpdb find-dupes` - Find duplicate posters (defaults to /data/Posters)
- `tpdb find-dupes /path/to/posters` - Find duplicates in specific directory
- Uses fuzzy matching with 74+ score threshold for duplicate detection

### File Processing Flow

1. Connect to Plex server and retrieve library information
1. Scan poster directories matching library names (70%+ similarity)
1. Process zip files by extracting and fuzzy-matching to media
1. Organize poster files into media-specific folder structure
1. Optionally create hard links to actual Plex media directories (`--copy` flag)

### Command Line Interface

The package is installed with a `tpdb` command-line entry point:

**Main commands:**

- `tpdb` - Run main poster organization (interactive mode by default)
- `tpdb download <URL>` - Download from ThePosterDB
- `tpdb find-dupes [directory]` - Find duplicate poster folders

**Main command options:**

- `-l, --libraries <names>` - Process specific Plex libraries (defaults to all)
- `--action <new|sync>` - Process new posters (default) or sync existing folders
- `-u, --unlinked` - Find and process orphaned poster folders
- `-f, --force` - Process movie posters without matching to media folder
- `--filter <string>` - Filter source poster folders by string match
- `-a, --all` - Replace all poster files without prompting
- `-c, --copy` - Create hard links to media folders
- `-d, --download <URL>` - Download from ThePosterDB (then continue processing)

**Example workflows:**

```bash
# Download and organize
tpdb -d "https://theposterdb.com/set/12345" -l Movies --action new

# Sync existing posters and copy to media
tpdb -l "TV Shows" --action sync --copy

# Find and fix unlinked posters
tpdb -l Movies --unlinked

# Find duplicates
tpdb find-dupes /data/Posters
```

### Dependencies

- **PlexAPI**: Plex server communication and library scanning
- **thefuzz**: Fuzzy string matching for media name association
- **requests**: HTTP downloads
- **pyrfc6266**: Content-Disposition header parsing for downloads
- **typer[all]**: Modern CLI framework (includes rich)
- **rich**: Terminal formatting and progress bars (replaced alive_progress)

### Development Dependencies

- **pytest**: Test framework
- **ruff**: Fast Python linter and formatter (replaced flake8/black)
- **pre-commit**: Git hooks for code quality
- **commitizen**: Conventional commits tooling
- **detect-secrets**: Prevent committing secrets

### Pre-commit Hook Configuration

The project uses extensive pre-commit hooks for quality control:

- **uv-lock & uv-export**: Automatically update dependency files when pyproject.toml changes
- **ruff-check & ruff-format**: Lint and format Python code
- **trailing-whitespace**: Remove trailing whitespace
- **mixed-line-ending**: Ensure LF line endings
- **mdformat**: Format Markdown files
- **commitizen**: Validate commit messages and branch names
- **detect-secrets**: Check for accidentally committed secrets

## Code Patterns to Follow

### Error Handling

Currently minimal - most functions assume successful operations. When adding error handling, follow the existing pattern of graceful degradation with user prompts.

### Interactive User Input

Uses **typer** for prompts (`typer.confirm()`, `typer.prompt()`) and **rich** for output (`console.print()` with markup). Maintain this pattern for new features requiring user confirmation.

### File Operations

Always use absolute paths. The codebase uses `os.path` operations - prefer `os.path.join()` for cross-platform compatibility.

### Naming Conventions

- **Functions**: snake_case (e.g., `find_best_media_match`, `organize_movie_folder`)
- **Variables**: snake_case (e.g., `best_match`, `poster_folders`)
- **Class names**: PascalCase (e.g., `LibraryData`, `Posters`, `Options`)
- **Helper functions**: Documented with Google-style docstrings including Args/Returns

### Console Output Patterns

Use rich markup for consistent, beautiful output:

```python
# Success messages
console.print("[bold green]✓[/bold green] Operation completed")

# Info messages
console.print("[bold cyan]Processing:[/bold cyan] Movie Library")

# Warnings
console.print("[yellow]Warning:[/yellow] Match score below threshold")

# Errors
console.print("[bold red]Error:[/bold red] Library not found")

# Dimmed/secondary info
console.print(f"  Source: [dim]{file_name}[/dim]")
```

### Important Development Notes

- **Target Python Version**: Requires Python 3.14+ (as specified in pyproject.toml)
- **Dependency Management**: Uses uv for fast package management and lock file generation
- **File Organization**: Always test with both movie and TV show libraries as they have different organization patterns
- **Interactive Nature**: Most functionality requires user input and confirmation prompts

When modifying fuzzy matching logic, always test with the `normalize_name()` function and maintain the existing threshold values that users depend on.
