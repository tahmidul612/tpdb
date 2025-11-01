# TPDB - Plex Poster Organizer

<div align="center">

[![License](https://img.shields.io/github/license/tahmidul612/tpdb?style=for-the-badge&logo=opensourceinitiative&logoColor=white&color=blue)](LICENSE)
[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Version](https://img.shields.io/github/v/tag/tahmidul612/tpdb?style=for-the-badge&label=version&color=green)](https://github.com/tahmidul612/tpdb/tags)

<!-- [![GitHub Stars](https://img.shields.io/github/stars/tahmidul612/tpdb?style=for-the-badge&logo=github&color=yellow)](https://github.com/tahmidul612/tpdb/stargazers)
[![Issues](https://img.shields.io/github/issues/tahmidul612/tpdb?style=for-the-badge&logo=github&color=red)](https://github.com/tahmidul612/tpdb/issues)
[![Last Commit](https://img.shields.io/github/last-commit/tahmidul612/tpdb?style=for-the-badge&logo=git&logoColor=white&color=orange)](https://github.com/tahmidul612/tpdb/commits) -->

</div>

**TPDB** is a powerful Python utility that streamlines the management of movie and TV show posters for your Plex media server. Download, organize, and sync custom artwork from ThePosterDB with intelligent fuzzy matching and automated folder organization.

Perfect for Plex enthusiasts using metadata managers like [Kometa](https://kometa.wiki/) (formerly Plex Meta Manager) or managing posters directly in your media library.

---

<!-- Placeholder for demo GIF showing the tool in action -->
![Demo of TPDB organizing posters](docs/images/demo.gif)
*TPDB in action - downloading and organizing posters automatically*

## Table of Contents

- [TPDB - Plex Poster Organizer](#tpdb---plex-poster-organizer)
  - [Table of Contents](#table-of-contents)
  - [Why TPDB?](#why-tpdb)
  - [Key Features](#key-features)
  - [Installation](#installation)
    - [Prerequisites](#prerequisites)
    - [Quick Install](#quick-install)
  - [Configuration](#configuration)
    - [Plex Server Setup](#plex-server-setup)
  - [Quick Start](#quick-start)
  - [Usage](#usage)
    - [Main Command](#main-command)
    - [Download Command](#download-command)
    - [Duplicate Detection](#duplicate-detection)
    - [Command-Line Options](#command-line-options)
  - [Common Workflows](#common-workflows)
  - [Directory Structure](#directory-structure)
  - [How It Works](#how-it-works)
  - [Troubleshooting](#troubleshooting)
  - [Contributing](#contributing)
  - [License](#license)
  - [Acknowledgments](#acknowledgments)

## Why TPDB?

Managing custom posters for a large Plex library can be tedious and time-consuming. TPDB automates the entire workflow:

- **No more manual renaming** - Intelligent fuzzy matching automatically associates posters with your media
- **Batch processing** - Handle entire poster sets and collections at once
- **Kometa-ready** - Organized folder structure works seamlessly with Kometa's poster management
- **Interactive & Smart** - Confirms matches when uncertain, learns from your corrections
- **Beautiful CLI** - Modern interface with progress bars, colors, and clear prompts

## Key Features

### 🎨 Smart Poster Management

- **Fuzzy Matching**: Automatically matches posters to your Plex media using intelligent name normalization
- **Collection Handling**: Organizes movie collection posters into structured subfolders
- **TV Season Support**: Proper naming for TV show seasons with zero-padded formatting (Season01, Season02, etc.)

### 📥 Download & Extract

- **Direct Downloads**: Fetch posters and sets from ThePosterDB URLs
- **ZIP Processing**: Automatically extracts and organizes poster archives
- **Progress Tracking**: Beautiful progress bars for downloads and batch operations

### 🔄 Sync & Link

- **Hard Linking**: Create hard links from organized posters to your media folders
- **Sync Mode**: Update existing poster folders with new artwork
- **Unlinked Detection**: Find and fix orphaned poster folders

### 🔍 Duplicate Detection

- **Fuzzy Search**: Identify potential duplicate poster folders
- **Threshold-based**: Configurable similarity matching (74%+ by default)
- **Clean Output**: Color-coded results with similarity scores

### 💎 User Experience

- **Interactive Prompts**: Typer-based CLI with intuitive confirmation dialogs
- **Rich Formatting**: Color-coded output, formatted tables, and clear status messages
- **Flexible Filtering**: Process specific libraries, folders, or media types

## Installation

### Prerequisites

- **Python 3.10 or higher** - Check your version with `python --version`
- **Plex Media Server** - Running and accessible on your network
- **ThePosterDB Account** (optional) - For downloading premium content

### Quick Install

1. **Clone the repository:**

   ```bash
   git clone https://github.com/tahmidul612/tpdb.git
   cd tpdb
   ```

2. **Install using pip:**

   ```bash
   # For regular use
   pip install -e .

   # For development (includes testing and linting tools)
   pip install -e .[dev]
   ```

   Or using **uv** (recommended for faster installation):

   ```bash
   # Install uv first (if not already installed)
   curl -LsSf https://astral.sh/uv/install.sh | sh

   # Install dependencies
   uv sync

   # For development
   uv sync --group dev
   ```

3. **Verify installation:**

   ```bash
   tpdb --help
   ```

   You should see the TPDB help menu with available commands and options.

## Configuration

### Plex Server Setup

TPDB needs to connect to your Plex server to access library information for intelligent poster matching.

**First-time setup:**

When you run `tpdb` for the first time, you'll be prompted to enter:

1. **Plex Server URL**: Your server address (e.g., `http://192.168.1.100:32400`)
2. **Authentication Token**: Your Plex token ([how to find it](https://support.plex.tv/articles/204059436-finding-an-authentication-token-x-plex-token/))

**Saving configuration:**

If you choose to save these credentials, TPDB creates a configuration file at:

```
~/.config/plexapi/config.ini
```

This eliminates the need to re-enter credentials on subsequent runs.

**Manual configuration:**

You can also manually create the configuration file:

```ini
[auth]
server_baseurl = http://your-server:32400
server_token = your_plex_token_here
```

<!-- Placeholder for configuration screenshot -->
![Plex configuration prompt](docs/images/config-setup.png)
*First-time configuration - entering Plex server details*

## Quick Start

Get started with TPDB in just a few commands:

```bash
# Download a poster set from ThePosterDB
tpdb download "https://theposterdb.com/set/12345"

# Organize new posters for your Movies library
tpdb -l Movies --action new

# Sync existing TV show posters and link them to media folders
tpdb -l "TV Shows" --action sync --copy
```

<!-- Placeholder for quick start demo -->
![Quick start example](docs/images/quickstart.gif)
*Download, organize, and sync posters in minutes*

## Usage

### Main Command

The `tpdb` command processes posters for your Plex libraries with various options:

```bash
tpdb [OPTIONS]
```

**Basic examples:**

```bash
# Process all libraries interactively
tpdb

# Process specific library
tpdb -l Movies

# Process multiple libraries
tpdb -l Movies -l "TV Shows"

# Auto-replace all posters without prompting
tpdb -l Movies --all

# Create hard links to media folders
tpdb -l Movies --copy
```

### Download Command

Download posters directly from ThePosterDB:

```bash
# Using the download subcommand
tpdb download "https://theposterdb.com/set/12345"

# Using the -d flag (allows continued processing)
tpdb -d "https://theposterdb.com/set/12345" -l Movies --action new
```

The downloaded files are automatically saved to your poster directory and can be immediately organized.

### Duplicate Detection

Find and identify duplicate poster folders:

```bash
# Search default directory (/data/Posters)
tpdb find-dupes

# Search specific directory
tpdb find-dupes /path/to/your/posters
```

Output shows potential duplicates with similarity scores to help you clean up redundant folders.

### Command-Line Options

| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `--libraries <names>` | `-l` | Specify Plex libraries to process | All libraries |
| `--action <new\|sync>` | | Process new posters or sync existing folders | `new` |
| `--unlinked` | `-u` | Find and process unlinked poster folders | `false` |
| `--force` | `-f` | Force rename without matching to media | `false` |
| `--filter <string>` | | Filter source folders by string match | None |
| `--all` | `-a` | Replace all posters without prompting | `false` |
| `--copy` | `-c` | Hard link posters to media folders | `false` |
| `--download <url>` | `-d` | Download from ThePosterDB before processing | None |

**Action Modes:**

- **`new`** (default): Processes new poster files and ZIP archives, organizing them into the proper folder structure
- **`sync`**: Reorganizes existing poster folders, useful after manually adding files or updating naming conventions

## Common Workflows

### Workflow 1: Download and Organize New Poster Sets

Perfect for adding new poster collections to your library:

```bash
# Download a complete collection set
tpdb download "https://theposterdb.com/set/12345"

# Organize the downloaded set for your Movies library
tpdb -l Movies --action new

# Copy the organized posters to your media folders
tpdb -l Movies --copy
```

<!-- Placeholder for workflow screenshot -->
![Download and organize workflow](docs/images/workflow-download.png)
*Complete workflow from download to organization*

### Workflow 2: Sync Existing Posters

When you've manually added posters or want to reorganize:

```bash
# Reorganize existing TV show posters
tpdb -l "TV Shows" --action sync

# Sync and link to media folders
tpdb -l "TV Shows" --action sync --copy
```

### Workflow 3: Find and Fix Unlinked Posters

Clean up orphaned poster folders that don't match any media:

```bash
# Find unlinked posters in Movies library
tpdb -l Movies --unlinked

# The tool will prompt you to match or rename each unlinked folder
```

### Workflow 4: Clean Up Duplicates

Maintain a clean poster directory:

```bash
# Find duplicates in your poster directory
tpdb find-dupes /data/Posters

# Review the list and manually remove duplicates
# (TPDB identifies them but doesn't auto-delete for safety)
```

### Workflow 5: Batch Processing with Filters

Process specific poster folders:

```bash
# Only process folders matching "Marvel"
tpdb -l Movies --filter "Marvel"

# Force organize all matching folders without prompts
tpdb -l Movies --filter "Marvel" --all
```

## Directory Structure

TPDB organizes your posters into a clean, hierarchical structure optimized for Kometa and Plex:

### Default Structure

```text
/data/Posters/                          # Default poster root directory
├── Movies/                             # Movie library posters
│   ├── Custom/                         # Individual movie posters (catch-all)
│   │   ├── The Matrix (1999)/
│   │   │   └── poster.jpg
│   │   ├── Inception (2010)/
│   │   │   └── poster.jpg
│   │   └── Interstellar (2014)/
│   │       └── poster.jpg
│   │
│   ├── Marvel Cinematic Universe/     # Collection posters
│   │   ├── Iron Man (2008)/
│   │   │   └── poster.jpg
│   │   ├── The Avengers (2012)/
│   │   │   └── poster.jpg
│   │   └── Avengers Endgame (2019)/
│   │       └── poster.jpg
│   │
│   └── The Dark Knight Trilogy/       # Another collection
│       ├── Batman Begins (2005)/
│       │   └── poster.jpg
│       ├── The Dark Knight (2008)/
│       │   └── poster.jpg
│       └── The Dark Knight Rises (2012)/
│           └── poster.jpg
│
├── TV Shows/                           # TV series posters
│   ├── Breaking Bad/
│   │   ├── poster.jpg                 # Show poster
│   │   ├── Season01.jpg               # Season 1 poster
│   │   ├── Season02.jpg               # Season 2 poster
│   │   ├── Season03.jpg
│   │   ├── Season04.jpg
│   │   ├── Season05.jpg
│   │   └── Season00.jpg               # Specials
│   │
│   ├── Game of Thrones/
│   │   ├── poster.jpg
│   │   ├── Season01.jpg
│   │   ├── Season02.jpg
│   │   └── ...
│   │
│   └── The Office/
│       ├── poster.jpg
│       └── Season01.jpg
│
└── Archives/                           # Processed ZIP files
    ├── marvel-posters-set.zip
    ├── dc-collection.zip
    └── tv-shows-bundle.zip
```

### Key Structure Notes

- **Movies**: Organized into collection folders or "Custom" for standalone films
- **TV Shows**: Seasons use zero-padded naming (Season01, Season02, etc.)
- **Collections**: Each movie in a collection gets its own subfolder
- **Archives**: ZIP files are moved here after extraction to keep directories clean
- **Naming**: All poster files are renamed to `poster.jpg` for consistency

<!-- Placeholder for directory structure visualization -->
![Directory structure example](docs/images/structure-example.png)
*Clean, organized poster structure ready for Kometa*

## How It Works

TPDB uses intelligent fuzzy matching to automate poster organization:

### 1. Name Normalization

Before matching, TPDB normalizes media and poster names:

- Removes years, punctuation, and "set by" text
- Converts to lowercase for comparison
- Strips extra whitespace

**Example:** `"The Matrix (1999) set by UserXYZ"` → `"the matrix"`

### 2. Fuzzy Matching

Uses the `rapidfuzz` library with configurable thresholds:

- **Library matching**: 70%+ similarity for directory discovery
- **Media matching**: Token-based matching for poster-to-media association
- **Duplicate detection**: 74%+ similarity for finding duplicates

### 3. Interactive Confirmation

When matches are uncertain, TPDB prompts for confirmation:

- Shows match score with color coding (green for high confidence, yellow/red for lower)
- Offers options: Accept match, Force organization, or Skip
- Learns from your decisions to improve future matches

### 4. Organization

Once matched, TPDB:

- Creates proper folder structure
- Renames posters to standard format
- Organizes collections into subfolders
- Moves processed archives to Archives directory

### 5. Linking (Optional)

With the `--copy` flag, creates hard links:

- Links organized posters to actual media folders
- Plex can read posters directly from media directories
- No file duplication (hard links share disk space)

## Troubleshooting

### Common Issues

**Problem: "Cannot connect to Plex server"**

- Verify your Plex server is running and accessible
- Check the server URL in `~/.config/plexapi/config.ini`
- Ensure your authentication token is valid
- Try accessing Plex web interface from the same machine

**Problem: "Posters not matching to media"**

- Check that library names match between TPDB and Plex
- Use the `--filter` option to narrow down the search
- Try `--force` mode to organize without matching
- Verify poster file names are reasonably similar to media names

**Problem: "Permission denied when creating hard links"**

- Ensure you have write permissions to both poster and media directories
- Hard links require both directories to be on the same filesystem
- Consider using symbolic links instead (requires code modification)

**Problem: "Duplicates not detected"**

- Adjust the similarity threshold if needed (default is 74%)
- Check that folder names are similar enough for fuzzy matching
- Verify you're searching the correct directory

### Getting Help

- **Check existing issues**: [GitHub Issues](https://github.com/tahmidul612/tpdb/issues)
- **Open a new issue**: Provide details about your setup and error messages
- **Discussion forum**: Ask questions in GitHub Discussions
- **Logs**: Run with verbose output and include relevant error messages

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for:

- Development environment setup
- Coding standards and conventions
- Testing guidelines
- Pull request process
- Commit message format

## License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- **[ThePosterDB](https://theposterdb.com/)** - Excellent source for high-quality custom posters
- **[Kometa](https://kometa.wiki/)** - Powerful Plex metadata manager that inspired this tool
- **[PlexAPI](https://github.com/pkkid/python-plexapi)** - Python bindings for the Plex API
- **[Typer](https://typer.tiangolo.com/)** - Modern CLI framework
- **[Rich](https://rich.readthedocs.io/)** - Beautiful terminal formatting
- **[RapidFuzz](https://github.com/maxbachmann/RapidFuzz)** - Fast fuzzy string matching

---

**Made with ❤️ by [Tahmidul Islam](https://github.com/tahmidul612)**

Star ⭐ this repository if you find it helpful!
