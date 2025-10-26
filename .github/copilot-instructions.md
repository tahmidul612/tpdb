# Copilot Instructions for TPDB (Plex Poster Organizer)

## Project Architecture

This is a Python utility for downloading, organizing, and syncing movie/TV show posters from The Poster DB with Plex media libraries. The codebase follows a monolithic script pattern with two main components:

- **`tpdb.py`**: Main application (~739 lines) handling all poster processing workflows
- **`duplicates.py`**: Standalone utility for detecting duplicate poster folders using fuzzy matching

## Core Data Structures

### Key Classes

- `LibraryData`: Stores Plex library metadata (title, type, locations)
- `Posters`: Container for poster organization data with collections for folders, files, zip files, and media mappings

### Key Functions

- `normalize_name()`: Name normalization for improved media matching (removes years, punctuation, "set by" text)
- `findBestMediaMatch()`: Fuzzy matching algorithm for associating poster files with media
- `downloadPoster()`: Downloads posters from The Poster DB URLs with progress bars
- `processZipFile()`: Extracts and organizes poster zip file collections
- `organizeMovieFolder()` / `organizeShowFolder()`: Media type-specific organization logic
- `copyPosters()`: Creates hard links from poster folders to Plex media directories

### Global State Pattern

The application uses global variables extensively:

- `poster_data`: Global `Posters` instance shared across functions
- `POSTER_DIR`: Default poster directory (`/data/Posters`)
- `PLEX_URL`/`PLEX_TOKEN`: Plex server configuration

## Critical Workflows

### Fuzzy String Matching Pattern

The core matching logic uses `thefuzz` library with specific scoring thresholds:

```python
# Library matching: 70%+ similarity for directory discovery
posterRootDirs = [path for path in os.listdir(POSTER_DIR)
                 if fuzz.partial_ratio(selectedLibrary.title, path) > 70]

# Media matching: Uses token_set_ratio with normalize_name() preprocessing
def normalize_name(name: str) -> str:
    # Removes years, 'set by' text, punctuation, converts to lowercase
```

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

### Duplicate Detection Utility

- `python duplicates.py` - Find duplicate posters (defaults to /data/Posters)
- `python duplicates.py /path/to/posters` - Find duplicates in specific directory
- Uses fuzzy matching with 74+ score threshold for duplicate detection

### File Processing Flow

1. Connect to Plex server and retrieve library information
1. Scan poster directories matching library names (70%+ similarity)
1. Process zip files by extracting and fuzzy-matching to media
1. Organize poster files into media-specific folder structure
1. Optionally create hard links to actual Plex media directories (`--copy` flag)

### Command Line Interface

Key workflow commands:

- `python tpdb.py` - Run in interactive mode (prompts for user decisions)
- `python tpdb.py --download <URL>` - Download from The Poster DB
- `python tpdb.py --action new` - Process new posters/zips (default)
- `python tpdb.py --action sync` - Organize existing poster folders
- `python tpdb.py --copy` - Create hard links to media folders
- `python tpdb.py --unlinked` - Find orphaned poster folders
- `python tpdb.py --force` - Process movie posters without matching to media folder
- `python tpdb.py --all` - Replace all poster files without prompting
- `python tpdb.py --filter <string>` - Filter source poster folders by string match
- `python tpdb.py -l <library1> <library2>` - Process specific Plex libraries

### Dependencies

- **PlexAPI**: Plex server communication and library scanning
- **thefuzz**: Fuzzy string matching for media name association
- **requests**: HTTP downloads with progress bars (`alive_progress`)
- **pyrfc6266**: Content-Disposition header parsing for downloads

## Code Patterns to Follow

### Error Handling

Currently minimal - most functions assume successful operations. When adding error handling, follow the existing pattern of graceful degradation with user prompts.

### Interactive User Input

Heavy use of `input()` prompts for user decisions. Maintain this pattern for new features requiring user confirmation.

### File Operations

Always use absolute paths. The codebase mixes `os.path` and string operations - prefer `os.path.join()` for cross-platform compatibility.

### Naming Conventions

- Functions use camelCase (e.g., `findBestMediaMatch`, `organizeMovieFolder`)
- Variables use camelCase or snake_case inconsistently
- Class names use PascalCase

When modifying fuzzy matching logic, always test with the `normalize_name()` function and maintain the existing threshold values that users depend on.
