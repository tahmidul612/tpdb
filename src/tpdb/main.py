#!/usr/bin/env python3
from __future__ import print_function, unicode_literals

import collections
import os
import re
import shutil
import string
import zipfile
from xmlrpc.client import Boolean

import pyrfc6266
import requests
import typer
from rich.console import Console
from rich.progress import Progress
from thefuzz import fuzz, process

# Initialize Rich console
console = Console()


# Helper functions for user prompts
def prompt_match_confirmation(
    source_name: str,
    match_name: str,
    match_score: int | float,
    media_type: str = "item",
) -> bool:
    """Display a nicely formatted match confirmation prompt.
    
    Args:
        source_name: The source file/folder name
        match_name: The matched media name
        match_score: The fuzzy match score (0-100)
        media_type: Type of media (movie, show, folder, etc.)
    
    Returns:
        bool: True if user confirms, False otherwise
    """
    # Determine score color
    if match_score >= 90:
        score_color = "green"
    elif match_score >= 70:
        score_color = "yellow"
    else:
        score_color = "red"
    
    console.print()
    console.print(f"[bold cyan]Match Found for {media_type.title()}[/bold cyan]")
    console.print(f"  Source:  [dim]{source_name}[/dim]")
    console.print(f"  Match:   [bold]{match_name}[/bold]")
    console.print(f"  Score:   [{score_color}]{match_score}/100[/{score_color}]")
    console.print()
    
    return typer.confirm("Proceed with this match?", default=True)


def prompt_collection_organization(source_name: str, best_match: str | None, score: int | float) -> bool:
    """Display prompt for organizing collection/set folders.
    
    Args:
        source_name: The collection/set name
        best_match: Best match found (if any)
        score: Match score
    
    Returns:
        bool: True if user wants to proceed
    """
    console.print()
    console.print("[bold cyan]Collection Detected[/bold cyan]")
    console.print(f"  File:    [dim]{source_name}[/dim]")
    
    if best_match:
        console.print(f"  Match:   [yellow]{best_match}[/yellow] (low score: {score})")
        console.print()
        console.print("[dim]This appears to be a collection/set with multiple movies.[/dim]")
        return typer.confirm("Unzip and organize movies individually?", default=True)
    else:
        console.print("  Match:   [red]No match found[/red]")
        console.print()
        console.print("[dim]This appears to be a collection/set with multiple movies.[/dim]")
        return typer.confirm("Unzip and organize movies individually?", default=True)


def prompt_poster_organization(
    file_name: str,
    match_name: str,
    match_score: int | float,
) -> str:
    """Display prompt for organizing individual poster files with match/force/skip options.
    
    Args:
        file_name: The poster file name
        match_name: The matched movie name
        match_score: The fuzzy match score (0-100)
    
    Returns:
        str: 'y' to use match, 'f' to force rename, 'n' to skip
    """
    # Determine score color
    if match_score >= 90:
        score_color = "green"
    elif match_score >= 70:
        score_color = "yellow"
    else:
        score_color = "red"
    
    console.print()
    console.print("[bold cyan]Poster Match[/bold cyan]")
    console.print(f"  File:    [dim]{file_name}[/dim]")
    console.print(f"  Match:   [bold]{match_name}[/bold]")
    console.print(f"  Score:   [{score_color}]{match_score:.0f}/100[/{score_color}]")
    console.print()
    console.print("[dim]Options: (y) use match, (f) force rename, (n) skip[/dim]")
    
    return typer.prompt("Choose", default="y").lower()


# Data classes
class LibraryData:
    """A data class to hold information about a Plex library.

    Attributes:
        title (str): The title of the library.
        type (str): The type of the library (e.g., 'movie', 'show').
        locations (list): A list of file paths for the library's content.
    """

    def __init__(self, title=None, type=None, locations=None):
        self.title = title
        self.type = type
        self.locations = locations


class Posters:
    """A data class to hold information about posters.

    Attributes:
        poster_folders (list): A list of paths to folders containing posters.
        poster_files (list): A list of paths to individual poster files.
        poster_zip_files (dict): A dictionary mapping zip file names to their paths.
        media_folder_names (collections.defaultdict): A dictionary mapping media folder names
            to a list of their root paths.
    """

    def __init__(
        self,
        poster_folders=None,
        poster_files=None,
        poster_zip_files=None,
        media_folder_names=None,
    ):
        self.poster_folders = poster_folders if poster_folders is not None else []
        self.poster_files = poster_files if poster_files is not None else []
        self.poster_zip_files = poster_zip_files if poster_zip_files is not None else {}
        self.media_folder_names = (
            media_folder_names
            if media_folder_names is not None
            else collections.defaultdict(list)
        )


class Options:
    """A data class to hold CLI options.

    This class is used to store command-line options that are injected
    by the CLI module. It's defined here to satisfy type checking.

    Attributes:
        force (bool): Process movie posters without matching to media folder.
        all (bool): Replace all poster files without prompting.
        copy (bool): Copy posters to media folders.
        unlinked (bool): Find and process unlinked posters.
        action (str): Action to perform ('new' or 'sync').
        filter (str | None): String filter for source poster folders.
    """

    def __init__(self):
        self.force: bool = False
        self.all: bool = False
        self.copy: bool = False
        self.unlinked: bool = False
        self.action: str = "new"
        self.filter: str | None = None


# Global static variables
PLEX_URL = ""
PLEX_TOKEN = ""
POSTER_DIR = "/data/Posters"

# Global variables (initialized by CLI)
# These are set dynamically by the CLI module before calling functions
poster_data: Posters = Posters()  # type: ignore[reportUnboundVariable]
opts: Options = Options()  # type: ignore[reportUnboundVariable]

################################# Start Plex Config #######################################


def update_config(config_path):
    """Updates the PlexAPI config file with the provided URL and token.

    Args:
        config_path (str): The path to the PlexAPI config file.

    Returns:
        bool: True if the file was updated, False otherwise.
    """
    updated = False
    with open(config_path, "r") as configfile:
        lines = configfile.readlines()

    with open(config_path, "w") as configfile:
        for line in lines:
            if line.startswith("server_baseurl"):
                configfile.write(f"server_baseurl = {PLEX_URL}\n")
                updated = True
            elif line.startswith("server_token"):
                configfile.write(f"server_token = {PLEX_TOKEN}\n")
                updated = True
            else:
                configfile.write(line)

    return updated


def download_poster(url):
    """Downloads a poster from a given URL.

    This function can handle URLs from 'theposterdb.com' for sets and individual
    posters, as well as direct API links or other URLs. It prompts the user
    to select a destination folder for the downloaded poster.

    Args:
        url (str): The URL of the poster to download.
    """
    from rich.prompt import Prompt

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
    }
    custom_filename = None
    filename = None
    if "theposterdb.com/set" in url:
        poster_id = url.split("/")[-1]
        download_url = f"https://theposterdb.com/set/download/{poster_id}"
    elif "theposterdb.com/poster" in url:
        poster_id = url.split("/")[-1]
        download_url = f"https://theposterdb.com/api/assets/{poster_id}"
    elif "theposterdb.com/api/assets" in url:
        download_url = url
    else:
        download_url = url
        custom_filename = Prompt.ask("Enter movie name for poster file (no ext)")
    if download_url:
        response = requests.get(download_url, headers=headers, stream=True)
    else:
        console.print("[bold red]Invalid URL[/bold red]")
        return
    if response.status_code == 200:
        filename = response.headers.get("content-disposition", None)
        if not custom_filename and filename:
            filename = pyrfc6266.parse_filename(filename)
        elif custom_filename and filename:
            filename = "".join(
                [
                    custom_filename,
                    os.path.splitext(pyrfc6266.parse_filename(filename))[1],
                ]
            )
        elif custom_filename:
            filename = "".join(
                [custom_filename, os.path.splitext(os.path.basename(url))[1]]
            )
        else:
            console.print(
                "[bold red]Could not find a filename, aborting download[/bold red]"
            )
            return
        console.print("[bold cyan]Select folder to save poster file[/bold cyan]")
        for i, dir in enumerate(os.listdir(POSTER_DIR), start=1):
            console.print(f"{i}: {dir}")
        dir_index = Prompt.ask("Enter folder number")
        save_dir = os.path.join(POSTER_DIR, os.listdir(POSTER_DIR)[int(dir_index) - 1])
        total_bytes = int(response.headers.get("content-length", 0)) or None

        with open(os.path.join(save_dir, filename), "wb") as file:
            with Progress() as progress:
                task = progress.add_task(
                    f"[cyan]Downloading {filename}...", total=total_bytes
                )
                for chunk in response.iter_content(chunk_size=4096):
                    file.write(chunk)
                    if total_bytes:
                        progress.update(task, advance=len(chunk))
        console.print(f"[bold green]File downloaded as '{filename}'[/bold green]")
    else:
        console.print("[bold red]Failed to download the file[/bold red]")


def organize_movie_folder(folder_dir):
    """Organizes a folder of movie posters.

    Renames poster files and creates a subfolder named after each movie,
    placing the renamed poster inside. Automatically organizes all posters that have an
    exact or strong fuzzy match to a media folder.

    Args:
        folder_dir (str): The path to the folder containing the movie posters.
    """
    global poster_data, opts
    for file in os.listdir(folder_dir):
        source_file = os.path.join(folder_dir, file)
        collection = False
        matched_media = []
        if os.path.isfile(source_file):
            if "Collection" not in file:
                matched_media = process.extractOne(
                    file,
                    poster_data.media_folder_names.keys(),
                    scorer=fuzz.token_sort_ratio,
                )
            else:
                collection = True
            user_in = ""
            if opts.force:
                user_in = "f"
            else:
                if matched_media:
                    user_in = prompt_poster_organization(
                        file, matched_media[0], matched_media[1]
                    )
                else:
                    user_in = None
            # Choosing option 'f' follows the force renaming logic for the movie folder/poster
            if opts.force or collection or (matched_media and user_in in ["y", "f"]):
                file_name = (
                    os.path.splitext(os.path.basename(file))[0]
                    if (opts.force or user_in == "f" or collection)
                    else matched_media[0]  # type: ignore[index]
                )
                file_extension = os.path.splitext(file)[1]
                new_folder = os.path.join(folder_dir, file_name)
                if os.path.isdir(new_folder):
                    shutil.rmtree(new_folder)
                os.mkdir(new_folder)
                destination_file = os.path.join(
                    new_folder, ("poster%s" % (file_extension))
                )
                os.rename(source_file, destination_file)


def organize_show_folder(folder_dir):
    """Organizes TV show posters in a given folder.

    This function renames TV show poster files to match the expected Plex
    naming convention (e.g., 'Season01.jpg', 'Season00.jpg' for specials).
    It handles season posters, special season posters, and the main show poster.

    Args:
        folder_dir (str): The directory path containing the TV show poster files.
    """
    global poster_data
    for file in os.listdir(folder_dir):
        source_file = os.path.join(folder_dir, file)
        if os.path.isfile(source_file):
            if "Season" in file:
                x = re.search(r"\b(?<=Season )\d+", file)
                if x:
                    season_number = str(x.group()).zfill(2)
                    file_extension = os.path.splitext(file)[1]
                    destination_file = os.path.join(
                        folder_dir, ("Season%s%s" % (season_number, file_extension))
                    )
                    os.rename(source_file, destination_file)
            elif "Specials" in file:
                season_number = "00"
                file_extension = os.path.splitext(file)[1]
                destination_file = os.path.join(
                    folder_dir, ("Season%s%s" % (season_number, file_extension))
                )
                os.rename(source_file, destination_file)
            else:
                file_extension = os.path.splitext(file)[1]
                destination_file = os.path.join(
                    folder_dir, ("poster%s" % (file_extension))
                )
                os.rename(source_file, destination_file)


def movie_poster():
    """Processes individual movie posters not in a collection folder.

    This function iterates through loose poster files and asks the user if they
    want to move them into a 'Custom' subfolder for organization. This is
    useful for preparing posters for use with Kometa or for manual review.
    """
    global poster_data
    for poster in poster_data.poster_files:
        if typer.confirm(
            f"Move poster file {os.path.basename(poster)} to Custom posters folder?"
        ):
            if "Custom" not in poster:
                source_dir = os.path.dirname(poster)
                destination_dir = os.path.join(source_dir, "Custom")
            else:
                destination_dir = os.path.dirname(poster)
            if not os.path.isdir(destination_dir):
                os.mkdir(destination_dir)
            shutil.move(poster, destination_dir)
            organize_movie_folder(destination_dir)
        else:
            console.print("[yellow]Skipped files[/yellow]")


def find_posters(poster_root_dirs):
    """Finds and categorizes posters from a list of root directories.

    This function scans the provided directories and categorizes the found items
    into three groups: zipped poster packs, folders containing posters, and
    individual poster files. It also renames zip files to a cleaner format.

    Args:
        poster_root_dirs (list): A list of directory paths to search for posters.
    """
    global poster_data
    for path1 in poster_root_dirs:
        for path2 in os.listdir(path1):
            file_path: str = os.path.join(path1, path2)
            if zipfile.is_zipfile(file_path):
                zip_file_path = file_path
                x = re.search(r"\b.+ set by (?:\S+)", os.path.splitext(path2)[0])
                if x:
                    new_zip_file_name = x.group() + os.path.splitext(path2)[1]
                else:
                    new_zip_file_name: str = (
                        path2.split(".", 1)[0].split("__", 1)[0]
                        + "."
                        + path2.split(".", 1)[1]
                    ).replace("_", " ")
                # new_zip_file_name = path2.replace('_', ' ')
                new_zip_file_path = os.path.join(path1, new_zip_file_name)
                if path2 != new_zip_file_name:
                    os.rename(zip_file_path, new_zip_file_path)
                poster_data.poster_zip_files[new_zip_file_name] = new_zip_file_path
            elif os.path.isdir(file_path):
                poster_data.poster_folders.append(file_path)
            elif os.path.isfile(file_path):
                poster_data.poster_files.append(file_path)
            else:
                continue


def copy_posters(poster_folder):
    """Copies posters from a poster folder to the corresponding Plex media folders.

    Creates hard links from the poster folder to each media folder location.

    Args:
        poster_folder (str): The path to the organized poster folder.
    """
    global poster_data, opts
    media_folders = poster_data.media_folder_names.get(os.path.basename(poster_folder))
    if media_folders:
        media_name = os.path.basename(poster_folder)
        poster_file_names = os.listdir(poster_folder)
        if opts.all or typer.confirm(
            f"Hardlink posters from [{poster_folder}] to [{media_folders}]?"
        ):
            replace_files = False
            for poster in poster_file_names:
                for media_root in media_folders:
                    orig_file = os.path.join(poster_folder, poster)
                    new_name = poster
                    if "Season00" in poster:
                        new_name = poster.replace("Season00", "season-specials-poster")
                    elif "Season" in poster:
                        new_name = (
                            poster.split(".")[0].lower()
                            + "-poster"
                            + "."
                            + poster.split(".")[1]
                        )
                    new_file = os.path.join(media_root, media_name, new_name)
                    if check_file(
                        os.path.dirname(new_file), os.path.splitext(new_name)[0]
                    ):
                        if os.path.isfile(new_file) and os.path.samefile(
                            orig_file, new_file
                        ):
                            continue
                        else:
                            if opts.all:
                                prompt_msg = f"Replace all poster files in {os.path.dirname(new_file)}?"
                            else:
                                prompt_msg = "Replace existing files?"
                            if replace_files or typer.confirm(prompt_msg):
                                replace_files = True
                                delete_file(
                                    os.path.dirname(new_file),
                                    os.path.splitext(new_name)[0],
                                    False,
                                )
                            else:
                                console.print(
                                    f"[yellow]Skipping folder {os.path.dirname(new_file)}[/yellow]"
                                )
                                continue
                    os.link(orig_file, new_file)


def normalize_name(name: str) -> str:
    """Normalizes a name for better fuzzy string matching.

    This function removes the file extension, year, 'set by' text, and all
    punctuation from a given string and converts it to lowercase. This helps
    in comparing poster names with media folder names more accurately.

    Args:
        name (str): The name to normalize.

    Returns:
        str: The normalized name.
    """
    name = os.path.splitext(name)[0]
    name = re.sub(r"\(\d{4}\)", "", name)  # remove (year)
    name = re.sub(r"\s+set by.*$", "", name, flags=re.IGNORECASE).strip()
    name = name.translate(str.maketrans("", "", string.punctuation)).lower()
    return name


def find_best_media_match(poster_zip_name: str, media_names: list):
    """Finds the best media match for a poster zip file.

    This function uses fuzzy string matching to find the best match between a
    poster zip file name and a list of media folder names. It normalizes both
    names before comparing them.

    Args:
        poster_zip_name (str): The name of the poster zip file.
        media_names (list): A list of media folder names to compare against.

    Returns:
        tuple: A tuple containing the best match and the matching score.
    """
    best_match = None
    best_score = 0
    norm_poster = normalize_name(poster_zip_name)
    for candidate in media_names:
        norm_candidate = normalize_name(candidate)
        score = fuzz.partial_token_sort_ratio(norm_poster, norm_candidate)
        if score > best_score:
            best_match, best_score = candidate, score
    return best_match, best_score


def organize_movie_collection_folder(folder_dir):
    """Organizes posters for movie collections.

    This function is designed to handle folders that contain posters for multiple
    movies, such as a collection or a set. It iterates through each poster file,
    tries to match it to a movie in the library, and then organizes it into a
    subfolder named after the movie. This is particularly useful for preparing
    movie collection posters for use with Kometa.

    Args:
        folder_dir (str): The directory containing the collection of posters.
    """
    global poster_data
    unmatched_files = []

    for file in os.listdir(folder_dir):
        source_file = os.path.join(folder_dir, file)
        if os.path.isfile(source_file):
            # Try to match this poster file to a movie in the library
            matched_media = process.extractOne(
                file,
                poster_data.media_folder_names.keys(),
                scorer=fuzz.token_sort_ratio,
                score_cutoff=60,
            )

            if matched_media:
                user_in = typer.prompt(
                    f"Matched poster file {file} to movie {matched_media[0]} [score: {matched_media[1]}], proceed? (y/n/f)",
                    default="y",
                ).lower()

                if user_in in ["y", "f"]:
                    # Determine folder name: use match name for 'y', original file name for 'f'
                    if user_in == "y":
                        folder_name = matched_media[0]
                    else:  # user_in == 'f'
                        folder_name = os.path.splitext(file)[0]

                    # Create a subfolder for this movie within the collection folder
                    movie_folder = os.path.join(folder_dir, folder_name)
                    if os.path.isdir(movie_folder):
                        shutil.rmtree(movie_folder)
                    os.mkdir(movie_folder)

                    file_extension = os.path.splitext(file)[1]
                    destination_file = os.path.join(
                        movie_folder, ("poster%s" % file_extension)
                    )
                    os.rename(source_file, destination_file)
                    console.print(
                        f"[green]Organized {file} into {folder_name} folder[/green]"
                    )
                else:
                    console.print(f"[yellow]Skipped {file}[/yellow]")
                    continue
            else:
                # No match found - ask if user wants to force rename
                if typer.confirm(
                    f"No match found for poster file {file}. Force rename?"
                ):
                    folder_name = os.path.splitext(file)[0]

                    # Create a subfolder within the collection folder
                    movie_folder = os.path.join(folder_dir, folder_name)
                    if os.path.isdir(movie_folder):
                        shutil.rmtree(movie_folder)
                    os.mkdir(movie_folder)

                    file_extension = os.path.splitext(file)[1]
                    destination_file = os.path.join(
                        movie_folder, ("poster%s" % file_extension)
                    )
                    os.rename(source_file, destination_file)
                    console.print(
                        f"[green]Organized {file} into {folder_name} folder[/green]"
                    )
                else:
                    unmatched_files.append(file)

    if unmatched_files:
        console.print(f"\n[yellow]Unmatched files in {folder_dir}:[/yellow]")
        for file in unmatched_files:
            console.print(f"  - {file}")
        console.print(
            "[yellow]These files were left in the collection folder for manual organization.[/yellow]"
        )


def process_zip_file(selected_library):
    """Processes zipped poster files.

    This function iterates through found zip files, matches them to media in the
    Plex library, and then extracts them. After extraction, it calls the
    appropriate organization function based on the library type (movie or show)
    and the quality of the match. It also handles archiving the zip file after
    processing.

    Args:
        selected_library (LibraryData): The Plex library to process posters for.
    """
    global poster_data
    for poster_zip in poster_data.poster_zip_files.keys():
        source_zip = poster_data.poster_zip_files.get(poster_zip)
        if not source_zip:
            continue
        destination_dir = ""
        unzip = ""
        if selected_library and selected_library.type == "show":
            best_match, best_score = find_best_media_match(
                poster_zip, list(poster_data.media_folder_names.keys())
            )
            if best_match:
                destination_dir = os.path.join(os.path.dirname(source_zip), best_match)
                unzip = (
                    "y"
                    if typer.confirm(
                        f"Matched zip file {os.path.basename(source_zip)} to show {best_match} [score: {best_score}], proceed?"
                    )
                    else "n"
                )
            else:
                console.print("[yellow]No matching media found[/yellow]")
                continue
        elif selected_library and selected_library.type == "movie":
            best_match, best_score = find_best_media_match(
                poster_zip, list(poster_data.media_folder_names.keys())
            )
            if (
                best_match and best_score > 70
            ):  # Only use direct match if score is high enough
                destination_dir = os.path.join(os.path.dirname(source_zip), best_match)
                unzip = (
                    "y"
                    if typer.confirm(
                        f"Matched zip file {os.path.basename(source_zip)} to movie {best_match} [score: {best_score}], proceed?"
                    )
                    else "n"
                )
            else:
                # For movie sets/collections, unzip with current name and organize individually
                destination_dir = os.path.join(
                    os.path.dirname(source_zip),
                    os.path.splitext(os.path.basename(source_zip))[0],
                )
                if best_match:
                    unzip = (
                        "y"
                        if typer.confirm(
                            f"Low match score ({best_score}) for {os.path.basename(source_zip)} to {best_match}. Unzip as collection and organize individually?"
                        )
                        else "n"
                    )
                else:
                    unzip = (
                        "y"
                        if typer.confirm(
                            f"No direct match found for {os.path.basename(source_zip)}. Unzip as collection and organize individually?"
                        )
                        else "n"
                    )
        if unzip == "y":
            with zipfile.ZipFile(source_zip, "r") as zip_ref:
                try:
                    if os.path.isdir(destination_dir):
                        shutil.rmtree(destination_dir)
                    zip_ref.extractall(destination_dir)
                except Exception as e:
                    console.print(
                        f"[bold red]Something went wrong extracting the zip: {e}[/bold red]"
                    )
                else:
                    if selected_library and selected_library.type == "show":
                        organize_show_folder(destination_dir)
                    elif selected_library and selected_library.type == "movie":
                        # Check if this was a direct match or a collection
                        best_match, best_score = find_best_media_match(
                            poster_zip, list(poster_data.media_folder_names.keys())
                        )
                        if best_match and best_score > 70:
                            # Direct match - use standard organization
                            organize_movie_folder(destination_dir)
                        else:
                            # Collection/set - organize individual movies within the collection
                            console.print(
                                f"\n[cyan]Processing collection folder: {os.path.basename(destination_dir)}[/cyan]"
                            )
                            organize_movie_collection_folder(destination_dir)
                    if typer.confirm("Move zip file to archive folder?"):
                        if os.path.isfile(
                            os.path.join(
                                POSTER_DIR, "Archives", os.path.basename(source_zip)
                            )
                        ):
                            os.remove(
                                os.path.join(
                                    POSTER_DIR, "Archives", os.path.basename(source_zip)
                                )
                            )
                        shutil.move(source_zip, os.path.join(POSTER_DIR, "Archives"))
        else:
            console.print("[yellow]Skipped files[/yellow]")


def sync_movie_folder(path):
    """Synchronizes a movie folder by matching it to the media library.

    This function is used to process folders that may be unlinked or incorrectly
    named. It attempts to find a match in the Plex library and, if successful,
    renames the folder to match the media. This is particularly useful for the
    '--unlinked' option.

    Args:
        path (str): The path to the movie folder to sync.
    """
    global poster_data
    if len(os.listdir(path)) > 1:
        console.print(f"[cyan]Organizing complex folder: {path}[/cyan]")
        organize_movie_folder(path)
    else:
        matched_media = process.extractOne(
            path,
            list(poster_data.media_folder_names.keys()),
            scorer=fuzz.token_sort_ratio,
            processor=lambda x: os.path.basename(x),
            score_cutoff=70,
        )

        if matched_media:
            if typer.confirm(
                f"Matched folder {os.path.basename(path)} to movie {matched_media[0]} [{matched_media[1]}], proceed?"
            ):
                new_path = os.path.join(os.path.dirname(path), matched_media[0])
                if os.path.isdir(new_path):
                    console.print(
                        f"[bold red]Error: Target directory {new_path} already exists. Skipping rename.[/bold red]"
                    )
                else:
                    os.rename(path, new_path)
                    console.print(
                        f"[green]Renamed {os.path.basename(path)} to {matched_media[0]}[/green]"
                    )
        else:
            console.print(
                f"[yellow]No match found for {os.path.basename(path)}[/yellow]"
            )


def check_file(directory, prefix):
    """Checks if a file with a given prefix exists in a directory.

    Args:
        directory (str): The directory to search in.
        prefix (str): The prefix of the file to look for (without extension).

    Returns:
        bool: True if a file with the prefix exists, False otherwise.
    """
    for s in os.listdir(directory):
        if os.path.splitext(s)[0] == prefix and os.path.isfile(
            os.path.join(directory, s)
        ):
            return True
    return False


def delete_file(directory, prefix, prompt: Boolean):
    """Deletes files in a directory with a specific prefix.

    Args:
        directory (str): The directory to delete files from.
        prefix (str): The prefix of the files to delete (without extension).
        prompt (bool): If True, ask for user confirmation before deleting.
    """
    for s in os.listdir(directory):
        file_path = os.path.join(directory, s)
        if os.path.splitext(s)[0] == prefix and os.path.isfile(file_path):
            if not prompt or typer.confirm(f"Delete {file_path}?"):
                os.remove(file_path)
