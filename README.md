# Plex Poster Organizer & Utility

Plex Poster Organizer is a powerful Python utility designed to streamline the management of movie and TV show posters for your Plex media server. It helps you download, organize, and sync posters from The Poster DB (TPDb), preparing them for use with metadata managers like [Kometa](https://kometa.wiki/) (formerly Plex Meta Manager) or for direct use within your media library.

This tool is perfect for users who want to maintain a clean and organized poster collection, ensuring that their custom artwork is correctly named and structured for Plex and third-party tools.

## Table of Contents

- [Table of Contents](#table-of-contents)
- [Key Features](#key-features)
- [Installation](#installation)
- [Setup](#setup)
  - [Plex Configuration](#plex-configuration)
- [Usage](#usage)
  - [Command-Line Arguments](#command-line-arguments)
  - [Examples](#examples)
- [Finding Duplicates](#finding-duplicates)
- [Example Poster Directory Structure](#example-poster-directory-structure)

## Key Features

- **Download Posters**: Fetch posters directly from TPDb URLs, including sets and individual files.
- **Organize Media**: Automatically match posters to your Plex library and organize them into a clean, nested folder structure.
- **Handle Collections**: Process poster sets for movie collections, organizing each poster into a subfolder for the corresponding movie.
- **Sync with Plex**: Hardlink organized posters directly into your media folders for Plex to use.
- **Find Duplicates**: Identify and clean up potential duplicate poster folders.
- **Modern CLI**: Built with typer and rich for a beautiful, user-friendly command-line experience.

## Installation

To get started with the Plex Poster Organizer, follow these steps:

1. **Clone this repository:**

   ```console
   git clone https://github.com/tahmidul612/tpdb.git
   cd tpdb
   ```

2. **Install the package:**

   ```console
   pip install -e .
   ```

   Or if you're developing:

   ```console
   pip install -e .[dev]
   ```

## Setup

### Plex Configuration

The script needs to connect to your Plex server to fetch your library information for matching posters to media.

When you run `tpdb` for the first time, it will prompt you to enter your Plex URL and an authentication token.

- **Plex URL**: The address of your Plex server (e.g., `http://192.168.1.100:32400`).
- **Plex Token**: You can find your token by following [Plex's official guide](https://support.plex.tv/articles/204059436-finding-an-authentication-token-x-plex-token/).

If you choose to save the configuration, the script will create a `config.ini` file at `~/.config/plexapi/config.ini` with your credentials. This avoids the need to enter them every time you run the script.

## Usage

The main command-line tool is `tpdb`. It offers a range of options to customize its behavior.

### Command-Line Arguments

Here are the available command-line arguments for `tpdb`:

| Argument | Short | Description |
| :--- | :--- | :--- |
| `--libraries <names>` | `-l` | Specify the Plex libraries to process (e.g., `Movies`, `TV Shows`). Defaults to all. |
| `--action <type>` | | The action to perform. `new` (default) organizes new posters and zip files. `sync` organizes existing folders. |
| `--unlinked` | `-u` | Find and process poster folders that are not yet linked to a media item. |
| `--force` | `-f` | Force rename movie posters without matching them to a media folder. |
| `--filter <string>` | | Filter the source poster folders to process based on a string match. |
| `--all` | `-a` | Replace all poster files in a media folder without prompting for confirmation. |
| `--copy` | `-c` | Hardlink the organized posters to your media folders for Plex to use directly. |
| `--download <url>` | `-d` | Download a poster from a TPDb URL. |

### Available Commands

- `tpdb` - Main poster organization (with options above)
- `tpdb download <url>` - Download a poster from The Poster DB
- `tpdb find-dupes [directory]` - Find duplicate poster folders

### Examples

- **Download a poster set from TPDb:**

  ```console
  tpdb download "https://theposterdb.com/set/12345"
  ```

  Or using the `-d` flag:

  ```console
  tpdb -d "https://theposterdb.com/set/12345"
  ```

- **Organize new posters for your 'Movies' library:**
  This will process new zip files and loose poster files, matching them to your movies.

  ```console
  tpdb -l Movies --action new
  ```

- **Sync existing show posters and copy them to media folders:**
  This will organize existing TV show poster folders and then hardlink them to your TV show media directories.

  ```console
  tpdb -l "TV Shows" --action sync --copy
  ```

- **Find and fix unlinked movie posters:**
  This will scan for poster folders that don't match any movie in your library and prompt you to fix them.

  ```console
  tpdb -l Movies --unlinked
  ```

- **Find duplicate poster folders:**
  This will scan your poster directory for potential duplicates.

  ```console
  tpdb find-dupes /path/to/your/posters
  ```

## Finding Duplicates

The `find-dupes` command helps you identify potential duplicate poster folders within your collection. This is useful for cleaning up your poster directory.

- **To run the command:**

  ```console
  tpdb find-dupes /path/to/your/posters
  ```

  If you don't provide a path, it defaults to `/data/Posters`.

The command will scan the directory and print a list of potential duplicates based on name similarity, which you can then review and manage manually.

## Example Poster Directory Structure

Here is an example of what your poster directory might look like after being organized by this tool. This structure is ideal for use with Kometa.

```text
/data/Posters/
├── Movies/
│   ├── The Matrix (1999)/
│   │   ├── poster.jpg
│   ├── The Matrix Reloaded (2003)/
│   │   ├── poster.jpg
│   └── Movie Collection Name/
│       ├── Movie 1 in Collection/
│       │   ├── poster.jpg
│       └── Movie 2 in Collection/
│           ├── poster.jpg
├── TV Shows/
│   ├── Breaking Bad/
│   │   ├── poster.jpg
│   │   ├── Season01.jpg
│   │   ├── Season02.jpg
│   │   └── Season00.jpg  (Specials)
└── Archives/
    └── (Zipped files are moved here after processing)
```
