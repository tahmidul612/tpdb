# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is the Plex Poster Organizer (TPDB), a Python utility for organizing movie and TV show posters from The Poster DB and matching them with Plex media libraries. The tool downloads, extracts, organizes and links poster files to media folders in a Plex server setup.

## Commands

### Main Application

- `python tpdb.py` - Run the main poster organizer (interactive mode)
- `python tpdb.py --download <URL>` - Download a poster from a URL
- `python tpdb.py --action new` - Organize new posters
- `python tpdb.py --action sync` - Sync existing posters
- `python tpdb.py -l <library1> <library2>` - Process specific Plex libraries
- `python tpdb.py --force` - Process movie posters without matching to media folder
- `python tpdb.py --copy` - Copy posters to media folders (creates hard links)
- `python tpdb.py --all` - Replace all poster files without prompting
- `python tpdb.py --unlinked` - Find and process unlinked posters
- `python tpdb.py --filter <string>` - Filter source poster folders by string

### Duplicate Detection

- `python duplicates.py` - Find duplicate posters (defaults to /data/Posters)
- `python duplicates.py /path/to/posters` - Find duplicates in specific directory

### Testing

- `pytest` - Run tests (single test file exists: tests/test_main.py)
- `python -m pytest tests/` - Alternative test runner command

### Install Requirements

- `pip install -r requirements.txt` - Install required packages

## Architecture

### Core Components

- **tpdb.py**: Main application script containing all poster processing logic
- **duplicates.py**: Standalone utility for detecting duplicate poster folders using fuzzy string matching
- **tests/test_main.py**: Test file for the normalize_name function

### Key Classes and Functions

- `LibraryData`: Stores Plex library information (title, type, locations)
- `Posters`: Container for poster file organization data (folders, files, zip files, media folder mappings)
- `normalize_name()`: Name normalization function for improved media matching (removes years, punctuation, set info)
- `findBestMediaMatch()`: Fuzzy matching algorithm for associating poster files with media
- `downloadPoster()`: Downloads posters from The Poster DB URLs
- `processZipFile()`: Extracts and organizes poster zip file collections
- `organizeMovieFolder()` / `organizeShowFolder()`: Organize posters for movies vs TV shows
- `copyPosters()`: Creates hard links from poster folders to Plex media directories

### Configuration

The application requires Plex server configuration:

- Server URL and auth token stored in `~/.config/plexapi/config.ini`
- Default poster directory: `/data/Posters`
- Supports interactive config setup on first run

### Media Processing Flow

1. Connects to Plex server and retrieves library information
2. Scans poster directories matching library names (70%+ similarity)
3. Processes zip files by extracting and matching to media using fuzzy string matching
4. Organizes individual poster files into media-specific folders
5. Optionally creates hard links from organized posters to actual Plex media directories

### Dependencies

- **PlexAPI**: Plex server communication
- **thefuzz**: Fuzzy string matching for media name matching
- **requests**: HTTP downloads
- **pyrfc6266**: Content-Disposition header parsing
- **alive_progress**: Download progress bars
