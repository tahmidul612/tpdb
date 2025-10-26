#!/usr/bin/env python3
"""Command-line interface for TPDB (Plex Poster Organizer)."""

from __future__ import annotations

import os
from typing import Optional

import typer
from rich.console import Console
from rich.progress import track

from tpdb.main import (
    CONFIG,
    POSTER_DIR,
    LibraryData,
    Posters,
    copyPosters,
    downloadPoster,
    findPosters,
    moviePoster,
    organizeMovieFolder,
    organizeShowFolder,
    processZipFile,
    syncMovieFolder,
    update_config,
    check_file,
)

# Initialize Rich console
console = Console()

# Create the main Typer app
app = typer.Typer(
    name="tpdb",
    help="Reorganize The Poster DB files to work with Kometa (formerly Plex Meta Manager)",
    no_args_is_help=True,
)


def get_plex_server():
    """Get Plex server instance with configuration."""
    from plexapi.server import PlexServer
    
    plex_url = ""
    plex_token = ""
    
    # Get config from file
    if CONFIG:
        plex_token = CONFIG.data["auth"].get("server_token", "")
        plex_url = CONFIG.data["auth"].get("server_baseurl", "")
    
    # Ask user for config if not found
    if not plex_token or not plex_url:
        if not plex_token:
            plex_token = typer.prompt("Please enter your Plex auth token")
        if not plex_url:
            plex_url = typer.prompt("Please enter your Plex URL")
        
        if typer.confirm("Save config?"):
            config_directory = os.path.expanduser("~/.config/plexapi")
            os.makedirs(config_directory, exist_ok=True)
            config_file_path = os.path.join(config_directory, "config.ini")
            
            if not os.path.exists(config_file_path):
                with open(config_file_path, "w") as configfile:
                    configfile.write("[auth]\n")
                    configfile.write(f"server_baseurl = {plex_url}\n")
                    configfile.write(f"server_token = {plex_token}\n")
            else:
                if update_config(config_file_path):
                    console.print("[bold green]Config file updated.[/bold green]")
                else:
                    console.print(
                        "[bold yellow]Config file already contains data, but server_baseurl and "
                        "server_token were not found. Please update it manually.[/bold yellow]"
                    )
    
    return PlexServer(plex_url, plex_token)


def get_libraries(plex):
    """Get all eligible Plex libraries."""
    all_libraries = []
    for library in plex.library.sections():
        if library.type not in ["artist", "photo"] and library.locations:
            all_libraries.append(
                LibraryData(library.title, library.type, library.locations)
            )
    return all_libraries


@app.command()
def download(
    url: str = typer.Argument(..., help="URL of the poster to download"),
):
    """Download a poster from The Poster DB."""
    console.print(f"[bold cyan]Downloading poster from:[/bold cyan] {url}")
    downloadPoster(url)
    console.print("[bold green]Download complete![/bold green]")


@app.command()
def sync(
    libraries: Optional[list[str]] = typer.Option(
        None,
        "-l",
        "--libraries",
        help="Name of the Plex libraries to process (defaults to all)",
    ),
    copy: bool = typer.Option(
        False, "-c", "--copy", help="Copy posters to media folders"
    ),
    filter_str: Optional[str] = typer.Option(
        None, "--filter", help="String filter for source poster folders"
    ),
    replace_all: bool = typer.Option(
        False,
        "-a",
        "--all",
        help="Replace all poster files in media folder without prompting",
    ),
):
    """Organize existing posters by syncing them with media folders."""
    from thefuzz import fuzz, process
    import collections
    
    plex = get_plex_server()
    all_libraries = get_libraries(plex)
    
    if not libraries:
        libraries = [lib.title for lib in all_libraries]
    
    for library_name in track(libraries, description="Processing libraries..."):
        selected_library = next(
            (lib for lib in all_libraries if lib.title == library_name), None
        )
        if not selected_library:
            console.print(f"[bold red]Library '{library_name}' not found.[/bold red]")
            continue
        
        console.print(f"\n[bold cyan]Processing library:[/bold cyan] {library_name}")
        poster_data = Posters([], [], {}, collections.defaultdict(list))
        
        if selected_library.type in ["movie", "show"]:
            # Get all media folders in the library
            for path in selected_library.locations:
                for name in os.listdir(path):
                    poster_data.mediaFolderNames[name].append(path)
            
            # Get poster root directories for the library
            poster_root_dirs = [
                os.path.join(POSTER_DIR, path)
                for path in os.listdir(POSTER_DIR)
                if fuzz.partial_ratio(selected_library.title, path) > 70
            ]
            findPosters(poster_root_dirs)
            
            if filter_str:
                folder_and_score = [
                    e
                    for e in process.extractBests(
                        filter_str,
                        poster_data.posterFolders,
                        scorer=fuzz.token_set_ratio,
                        score_cutoff=50,
                    )
                ]
                if 100 in [s[1] for s in folder_and_score]:
                    poster_data.posterFolders = [
                        f[0] for f in folder_and_score if f[1] == 100
                    ]
                else:
                    poster_data.posterFolders = [f[0] for f in folder_and_score]
                console.print(
                    f"[bold cyan]Filtered poster folders:[/bold cyan]\n{poster_data.posterFolders}"
                )
            
            match selected_library.type:
                case "movie":
                    for folder in poster_data.posterFolders:
                        poster_exists = any(
                            os.path.isfile(os.path.join(folder, x))
                            for x in os.listdir(folder)
                        )
                        if poster_exists and (
                            replace_all
                            or typer.confirm(f'Process folder "{folder}"?')
                        ):
                            organizeMovieFolder(folder)
                case "show":
                    unorganized_poster_folders = [
                        folder
                        for folder in poster_data.posterFolders
                        if not check_file(folder, "poster")
                    ]
                    for folder in unorganized_poster_folders:
                        organizeShowFolder(folder)
            
            # Move posters to media folders
            if copy:
                for folder in poster_data.posterFolders:
                    copyPosters(folder)
        else:
            console.print("[bold yellow]Library type not setup yet[/bold yellow]")


@app.command()
def new(
    libraries: Optional[list[str]] = typer.Option(
        None,
        "-l",
        "--libraries",
        help="Name of the Plex libraries to process (defaults to all)",
    ),
    copy: bool = typer.Option(
        False, "-c", "--copy", help="Copy posters to media folders"
    ),
    force: bool = typer.Option(
        False,
        "-f",
        "--force",
        help="Process movie posters without matching to a media folder",
    ),
    filter_str: Optional[str] = typer.Option(
        None, "--filter", help="String filter for source poster folders"
    ),
    replace_all: bool = typer.Option(
        False,
        "-a",
        "--all",
        help="Replace all poster files in media folder without prompting",
    ),
):
    """Process new posters and zip files (default action)."""
    from thefuzz import fuzz, process
    import collections
    
    plex = get_plex_server()
    all_libraries = get_libraries(plex)
    
    if not libraries:
        libraries = [lib.title for lib in all_libraries]
    
    for library_name in track(libraries, description="Processing libraries..."):
        selected_library = next(
            (lib for lib in all_libraries if lib.title == library_name), None
        )
        if not selected_library:
            console.print(f"[bold red]Library '{library_name}' not found.[/bold red]")
            continue
        
        console.print(f"\n[bold cyan]Processing library:[/bold cyan] {library_name}")
        poster_data = Posters([], [], {}, collections.defaultdict(list))
        
        if selected_library.type in ["movie", "show"]:
            # Get all media folders in the library
            for path in selected_library.locations:
                for name in os.listdir(path):
                    poster_data.mediaFolderNames[name].append(path)
            
            # Get poster root directories for the library
            poster_root_dirs = [
                os.path.join(POSTER_DIR, path)
                for path in os.listdir(POSTER_DIR)
                if fuzz.partial_ratio(selected_library.title, path) > 70
            ]
            findPosters(poster_root_dirs)
            
            if filter_str:
                folder_and_score = [
                    e
                    for e in process.extractBests(
                        filter_str,
                        poster_data.posterFolders,
                        scorer=fuzz.token_set_ratio,
                        score_cutoff=50,
                    )
                ]
                if 100 in [s[1] for s in folder_and_score]:
                    poster_data.posterFolders = [
                        f[0] for f in folder_and_score if f[1] == 100
                    ]
                else:
                    poster_data.posterFolders = [f[0] for f in folder_and_score]
                console.print(
                    f"[bold cyan]Filtered poster folders:[/bold cyan]\n{poster_data.posterFolders}"
                )
            
            match selected_library.type:
                case "movie":
                    moviePoster()
                    processZipFile(selected_library)
                case "show":
                    processZipFile(selected_library)
            
            # Move posters to media folders
            if copy:
                for folder in poster_data.posterFolders:
                    copyPosters(folder)
        else:
            console.print("[bold yellow]Library type not setup yet[/bold yellow]")


@app.command()
def unlinked(
    libraries: Optional[list[str]] = typer.Option(
        None,
        "-l",
        "--libraries",
        help="Name of the Plex libraries to process (defaults to all)",
    ),
    filter_str: Optional[str] = typer.Option(
        None, "--filter", help="String filter for source poster folders"
    ),
):
    """Find and process unlinked posters."""
    from thefuzz import fuzz, process
    import collections
    
    plex = get_plex_server()
    all_libraries = get_libraries(plex)
    
    if not libraries:
        libraries = [lib.title for lib in all_libraries]
    
    for library_name in track(libraries, description="Processing libraries..."):
        selected_library = next(
            (lib for lib in all_libraries if lib.title == library_name), None
        )
        if not selected_library:
            console.print(f"[bold red]Library '{library_name}' not found.[/bold red]")
            continue
        
        console.print(f"\n[bold cyan]Processing library:[/bold cyan] {library_name}")
        poster_data = Posters([], [], {}, collections.defaultdict(list))
        
        if selected_library.type == "movie":
            # Get all media folders in the library
            for path in selected_library.locations:
                for name in os.listdir(path):
                    poster_data.mediaFolderNames[name].append(path)
            
            # Get poster root directories for the library
            poster_root_dirs = [
                os.path.join(POSTER_DIR, path)
                for path in os.listdir(POSTER_DIR)
                if fuzz.partial_ratio(selected_library.title, path) > 70
            ]
            findPosters(poster_root_dirs)
            
            if filter_str:
                folder_and_score = [
                    e
                    for e in process.extractBests(
                        filter_str,
                        poster_data.posterFolders,
                        scorer=fuzz.token_set_ratio,
                        score_cutoff=50,
                    )
                ]
                if 100 in [s[1] for s in folder_and_score]:
                    poster_data.posterFolders = [
                        f[0] for f in folder_and_score if f[1] == 100
                    ]
                else:
                    poster_data.posterFolders = [f[0] for f in folder_and_score]
                console.print(
                    f"[bold cyan]Filtered poster folders:[/bold cyan]\n{poster_data.posterFolders}"
                )
            
            movie_poster_folders = []
            for folder in poster_data.posterFolders:
                movie_poster_folders.extend(
                    [os.path.join(folder, name) for name in os.listdir(folder)]
                )
            unlinked_folders = set()
            for movie in movie_poster_folders:
                poster_exists = False
                if os.path.isfile(movie):
                    unlinked_folders.add(os.path.dirname(movie))
                    continue
                for path in os.listdir(movie):
                    if os.path.isfile(os.path.join(movie, path)):
                        poster_exists = True
                if (
                    poster_exists
                    and not any(
                        m in os.path.basename(movie)
                        for m in [
                            "Collection",
                            *poster_data.mediaFolderNames.keys(),
                        ]
                    )
                    and "Custom" not in movie
                ):
                    unlinked_folders.add(movie)
            
            if unlinked_folders:
                console.print(
                    f"[bold yellow]{len(unlinked_folders)} unlinked folders found.[/bold yellow]"
                )
                if typer.confirm("Start processing them?"):
                    for folder in track(
                        unlinked_folders, description="Processing unlinked folders..."
                    ):
                        syncMovieFolder(folder)
            else:
                console.print("[bold green]No unlinked folders found.[/bold green]")
        else:
            console.print(
                "[bold yellow]Unlinked command only supports movie libraries.[/bold yellow]"
            )


@app.command(name="find-dupes")
def find_dupes(
    directory: str = typer.Argument(
        "/data/Posters",
        help="The root directory to search for duplicate posters",
    ),
):
    """Find duplicate posters using fuzzy matching."""
    from tpdb.dupes import subdirs
    from thefuzz import fuzz, process
    from os.path import basename
    
    dir_list = subdirs(directory)
    if not dir_list or len(dir_list) < 2:
        console.print(
            f"[bold red]There must be >=2 subdirectories in {directory} to find duplicates.[/bold red]"
        )
        raise typer.Exit(1)
    
    max_depth = max(dir_list, key=lambda x: x[1])[1]
    
    for depth in range(0, max_depth + 1):
        console.print(f"[bold cyan]Checking for duplicates at level {depth}...[/bold cyan]")
        # Get all directories at the current depth
        current_level_dirs = [d[0] for d in dir_list if d[1] == depth]
        
        # Create a temporary list for matching
        match_list = list(current_level_dirs)
        
        found_duplicates = False
        for d in current_level_dirs:
            match_list.remove(d)
            if not match_list:
                continue
            
            try:
                # Find the best match for the current directory in the rest of the list
                result = process.extractOne(
                    basename(d),
                    [basename(x) for x in match_list],
                    scorer=fuzz.token_set_ratio,
                    score_cutoff=74,
                )
            except Exception:
                continue
            
            if result:
                # Find the full path of the matched directory
                original_match_path = next(
                    (p for p in match_list if basename(p) == result[0]), None
                )
                if original_match_path:
                    console.print(
                        f"\t- [bold yellow]Potential duplicate:[/bold yellow] {d}  <-->  {original_match_path} (Score: {result[1]})"
                    )
                    found_duplicates = True
            
            match_list.append(d)  # Add it back for the next iteration
        
        if not found_duplicates:
            console.print(f"\t- [bold green]No duplicates found at level {depth}.[/bold green]")


def main():
    """Main entry point for the CLI."""
    app()


if __name__ == "__main__":
    main()
