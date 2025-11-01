#!/usr/bin/env python3
"""Command-line interface for TPDB (Plex Poster Organizer)."""

from __future__ import annotations

import sys

import typer
from rich.console import Console

from tpdb.auth import (
    PlexAuthenticator,
    PlexConfigManager,
    PlexCredentials,
    validate_and_normalize_url,
    validate_token,
)
from tpdb.ui import PlexAuthUI

# Initialize Rich console
console = Console()

# Create the main Typer app
app = typer.Typer(
    name="tpdb",
    help="Reorganize ThePosterDB files to work with Kometa (formerly Plex Meta Manager)",
    no_args_is_help=False,
)


@app.command()
def login(
    test_only: bool = typer.Option(
        False, "--test", help="Test connection without saving credentials"
    ),
):
    """Interactive Plex authentication setup."""
    ui = PlexAuthUI(console)
    auth = PlexAuthenticator(timeout=30)
    config_manager = PlexConfigManager()

    # UI Layer
    ui.show_welcome_panel()
    plex_url = ui.prompt_url()

    # Validation Layer
    is_valid, plex_url, error = validate_and_normalize_url(plex_url)
    if not is_valid:
        ui.show_error(error)
        raise typer.Exit(code=1)

    # More UI
    plex_token = ui.prompt_token()

    # Validation
    is_valid, error = validate_token(plex_token)
    if not is_valid:
        ui.show_error(error)
        raise typer.Exit(code=1)

    # Business Logic Layer
    console.print()
    with ui.show_connecting_status():
        result = auth.connect(plex_url, plex_token)

    if not result.success:
        ui.show_error(f"Connection failed: {result.error_message}")
        raise typer.Exit(code=1)

    # Display results
    ui.show_server_info(result.server_info)
    ui.show_success("Successfully connected to Plex server!")

    # Save if requested
    if test_only:
        ui.show_info("\nTest mode - credentials not saved")
        return

    if ui.confirm_save():
        try:
            credentials = PlexCredentials(url=plex_url, token=plex_token)
            config_manager.save(credentials)
            ui.show_success(f"Credentials saved to {config_manager.config_path}")
        except IOError as e:
            ui.show_error(f"Failed to save: {e}")
            raise typer.Exit(code=1)
    else:
        ui.show_info("Credentials not saved")


@app.command()
def download(
    url: str = typer.Argument(..., help="URL of the poster to download"),
):
    """Download a poster from ThePosterDB."""
    from tpdb.main import download_poster

    console.print(f"[bold cyan]Downloading poster from:[/bold cyan] {url}")
    download_poster(url)
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
    libraries: list[str] | None = typer.Option(
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
    filter_str: str | None = typer.Option(
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
    download_url: str | None = typer.Option(
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

    from rapidfuzz import fuzz, process, utils

    from tpdb.main import (
        POSTER_DIR,
        LibraryData,
        Options,
        Posters,
        check_file,
        copy_posters,
        download_poster,
        find_posters,
        movie_poster,
        organize_movie_folder,
        organize_show_folder,
        process_zip_file,
        sync_movie_folder,
    )

    # Handle download (if specified, download first but continue processing)
    if download_url:
        download_poster(download_url)

    # Get Plex configuration using new architecture
    config_manager = PlexConfigManager()
    credentials = config_manager.load()

    if not credentials:
        # Display authentication panel using PlexAuthUI
        ui = PlexAuthUI(console)
        ui.show_credentials_needed_panel()

        plex_url = ui.prompt_url()
        plex_token = ui.prompt_token()

        if ui.confirm_save():
            try:
                credentials = PlexCredentials(url=plex_url, token=plex_token)
                config_manager.save(credentials)
                ui.show_success(f"Credentials saved to {config_manager.config_path}")
            except IOError as e:
                ui.show_error(f"Failed to save: {e}")
                ui.show_info("Continuing with unsaved credentials...")
        console.print()
    else:
        plex_url = credentials.url
        plex_token = credentials.token

    # Connect to Plex server with validation
    auth = PlexAuthenticator(timeout=30)
    ui = PlexAuthUI(console)

    with ui.show_connecting_status():
        result = auth.connect(plex_url, plex_token)

    if not result.success:
        ui.show_error(f"Connection failed: {result.error_message}")
        console.print(
            "\n[bold red]✗[/bold red] Failed to connect to Plex server. "
            "Run [bold]tpdb login[/bold] to reconfigure."
        )
        raise typer.Exit(code=1)

    ui.show_info(f"Connected to {result.server_info['name']}\n")
    plex = result.server

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
                    poster_data.media_folder_names[name].append(path)

            # Get poster root directories for the library
            poster_root_dirs = [
                os.path.join(POSTER_DIR, path)
                for path in os.listdir(POSTER_DIR)
                if fuzz.partial_ratio(selected_library.title, path) > 70
            ]
            find_posters(poster_root_dirs)

            if filter_str:
                folder_and_score = [
                    e
                    for e in process.extractBests(
                        filter_str,
                        poster_data.poster_folders,
                        scorer=fuzz.token_set_ratio,
                        score_cutoff=50,
                        processor=utils.default_process,
                    )
                ]
                if 100 in [s[1] for s in folder_and_score]:
                    poster_data.poster_folders = [
                        f[0] for f in folder_and_score if f[1] == 100
                    ]
                else:
                    poster_data.poster_folders = [f[0] for f in folder_and_score]
                console.print(
                    f"[bold]Filtered poster folders:[/bold]\n{poster_data.poster_folders}"
                )

            match selected_library.type:
                case "movie":
                    if unlinked:
                        movie_poster_folders = []
                        for folder in poster_data.poster_folders:
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
                                        *poster_data.media_folder_names.keys(),
                                    ]
                                )
                                and "Custom" not in movie
                            ):
                                unlinked_folders.add(movie)
                        if unlinked_folders and typer.confirm(
                            f"{len(unlinked_folders)} unlinked folders found. Start processing them?"
                        ):
                            for folder in unlinked_folders:
                                sync_movie_folder(folder)
                    elif action == "new":
                        movie_poster()
                        process_zip_file(selected_library)
                    elif action == "sync":
                        for folder in poster_data.poster_folders:
                            poster_exists = any(
                                os.path.isfile(os.path.join(folder, x))
                                for x in os.listdir(folder)
                            )
                            if poster_exists and (
                                replace_all
                                or typer.confirm(f'Process folder "{folder}"?')
                            ):
                                organize_movie_folder(folder)
                case "show":
                    if action == "new":
                        process_zip_file(selected_library)
                    elif action == "sync":
                        unorganized_poster_folders = [
                            folder
                            for folder in poster_data.poster_folders
                            if not check_file(folder, "poster")
                        ]
                        for folder in unorganized_poster_folders:
                            organize_show_folder(folder)

            # Move posters to media folders
            if copy:
                for folder in poster_data.poster_folders:
                    copy_posters(folder)
        else:
            console.print("[bold yellow]Library type not setup yet[/bold yellow]")


def main():
    """Main entry point for the CLI."""
    app()


if __name__ == "__main__":
    main()
