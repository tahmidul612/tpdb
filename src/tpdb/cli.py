#!/usr/bin/env python3
"""Command-line interface for TPDB (Plex Poster Organizer)."""

from __future__ import annotations

import sys
from typing import Optional

import typer
from rich.console import Console

# Initialize Rich console
console = Console()

# Create the main Typer app
app = typer.Typer(
    name="tpdb",
    help="Reorganize ThePosterDB files to work with Kometa (formerly Plex Meta Manager)",
    no_args_is_help=False,
)


@app.command()
def download(
    url: str = typer.Argument(..., help="URL of the poster to download"),
):
    """Download a poster from ThePosterDB."""
    from tpdb.main import downloadPoster

    console.print(f"[bold cyan]Downloading poster from:[/bold cyan] {url}")
    downloadPoster(url)
    console.print("[bold green]Download complete![/bold green]")


@app.command(name="find-dupes")
def find_dupes(
    directory: str = typer.Argument(
        "/data/Posters",
        help="The root directory to search for duplicate posters",
    ),
):
    """Find duplicate posters using fuzzy matching."""
    # Import and run the duplicates main function
    sys.argv = ["find-dupes", directory]
    from tpdb.dupes import main as dupes_main

    dupes_main()


@app.callback(invoke_without_command=True)
def main_callback(
    ctx: typer.Context,
    libraries: Optional[list[str]] = typer.Option(
        None,
        "-l",
        "--libraries",
        help="Name of the Plex libraries to process (defaults to all)",
    ),
    action: str = typer.Option(
        "new",
        "--action",
        help="Organize new posters or sync existing posters",
    ),
    unlinked: bool = typer.Option(
        False, "-u", "--unlinked", help="Find and process unlinked posters"
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
    copy: bool = typer.Option(
        False, "-c", "--copy", help="Copy posters to media folders"
    ),
    download_url: Optional[str] = typer.Option(
        None, "-d", "--download", help="Download a poster from a URL"
    ),
):
    """Process posters for Plex libraries."""
    # If a subcommand was invoked, don't run the main logic
    if ctx.invoked_subcommand is not None:
        return

    # Import here to avoid circular imports and to delay loading
    import collections
    import os
    from thefuzz import fuzz, process
    from plexapi.server import CONFIG, PlexServer
    from tpdb.main import (
        POSTER_DIR,
        LibraryData,
        Posters,
        update_config,
        findPosters,
        moviePoster,
        organizeMovieFolder,
        organizeShowFolder,
        processZipFile,
        syncMovieFolder,
        copyPosters,
        check_file,
        downloadPoster,
    )

    # Handle download (if specified, download first but continue processing)
    if download_url:
        downloadPoster(download_url)

    # Get Plex configuration
    plex_url = ""
    plex_token = ""

    if CONFIG:
        plex_token = CONFIG.data["auth"].get("server_token", "")
        plex_url = CONFIG.data["auth"].get("server_baseurl", "")

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

    plex = PlexServer(plex_url, plex_token)
    all_libraries = []
    for library in plex.library.sections():
        if library.type not in ["artist", "photo"] and library.locations:
            all_libraries.append(
                LibraryData(library.title, library.type, library.locations)
            )

    # Set library names
    if not libraries:
        libraries = [lib.title for lib in all_libraries]

    # Process each library
    for library_name in libraries:
        selected_library = next(
            (lib for lib in all_libraries if lib.title == library_name), None
        )
        if not selected_library:
            console.print(f"[bold red]Library '{library_name}' not found.[/bold red]")
            continue

        console.print(f"\n[bold cyan]Processing library:[/bold cyan] {library_name}")
        poster_data = Posters([], [], {}, collections.defaultdict(list))

        # This is a workaround for the global variable issue
        # We need to inject the options and poster_data into the module
        import tpdb.main as main_module

        # Create opts object using the Options class from main
        from tpdb.main import Options

        opts_obj = Options()
        opts_obj.force = force
        opts_obj.all = replace_all
        opts_obj.copy = copy
        opts_obj.unlinked = unlinked
        opts_obj.action = action
        opts_obj.filter = filter_str

        main_module.opts = opts_obj
        main_module.poster_data = poster_data

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
                    f"[bold]Filtered poster folders:[/bold]\n{poster_data.posterFolders}"
                )

            match selected_library.type:
                case "movie":
                    if unlinked:
                        movie_poster_folders = []
                        for folder in poster_data.posterFolders:
                            movie_poster_folders.extend(
                                [
                                    os.path.join(folder, name)
                                    for name in os.listdir(folder)
                                ]
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
                        if unlinked_folders and typer.confirm(
                            f"{len(unlinked_folders)} unlinked folders found. Start processing them?"
                        ):
                            for folder in unlinked_folders:
                                syncMovieFolder(folder)
                    elif action == "new":
                        moviePoster()
                        processZipFile(selected_library)
                    elif action == "sync":
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
                    if action == "new":
                        processZipFile(selected_library)
                    elif action == "sync":
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


def main():
    """Main entry point for the CLI."""
    app()


if __name__ == "__main__":
    main()
