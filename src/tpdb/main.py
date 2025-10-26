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
        posterFolders (list): A list of paths to folders containing posters.
        posterFiles (list): A list of paths to individual poster files.
        posterZipFiles (dict): A dictionary mapping zip file names to their paths.
        mediaFolderNames (collections.defaultdict): A dictionary mapping media folder names
            to a list of their root paths.
    """

    def __init__(
        self,
        posterFolders=None,
        posterFiles=None,
        posterZipFiles=None,
        mediaFolderNames=None,
    ):
        self.posterFolders = posterFolders if posterFolders is not None else []
        self.posterFiles = posterFiles if posterFiles is not None else []
        self.posterZipFiles = posterZipFiles if posterZipFiles is not None else {}
        self.mediaFolderNames = (
            mediaFolderNames
            if mediaFolderNames is not None
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


def downloadPoster(url):
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
    customFilename = None
    filename = None
    if "theposterdb.com/set" in url:
        posterID = url.split("/")[-1]
        downloadUrl = f"https://theposterdb.com/set/download/{posterID}"
    elif "theposterdb.com/poster" in url:
        posterID = url.split("/")[-1]
        downloadUrl = f"https://theposterdb.com/api/assets/{posterID}"
    elif "theposterdb.com/api/assets" in url:
        downloadUrl = url
    else:
        downloadUrl = url
        customFilename = Prompt.ask("Enter movie name for poster file (no ext)")
    if downloadUrl:
        response = requests.get(downloadUrl, headers=headers, stream=True)
    else:
        console.print("[bold red]Invalid URL[/bold red]")
        return
    if response.status_code == 200:
        filename = response.headers.get("content-disposition", None)
        if not customFilename and filename:
            filename = pyrfc6266.parse_filename(filename)
        elif customFilename and filename:
            filename = "".join(
                [
                    customFilename,
                    os.path.splitext(pyrfc6266.parse_filename(filename))[1],
                ]
            )
        elif customFilename:
            filename = "".join(
                [customFilename, os.path.splitext(os.path.basename(url))[1]]
            )
        else:
            console.print(
                "[bold red]Could not find a filename, aborting download[/bold red]"
            )
            return
        console.print("[bold cyan]Select folder to save poster file[/bold cyan]")
        for i, dir in enumerate(os.listdir(POSTER_DIR), start=1):
            console.print(f"{i}: {dir}")
        dirIndex = Prompt.ask("Enter folder number")
        saveDir = os.path.join(POSTER_DIR, os.listdir(POSTER_DIR)[int(dirIndex) - 1])
        totalBytes = int(response.headers.get("content-length", 0)) or None

        with open(os.path.join(saveDir, filename), "wb") as file:
            with Progress() as progress:
                task = progress.add_task(
                    f"[cyan]Downloading {filename}...", total=totalBytes
                )
                for chunk in response.iter_content(chunk_size=4096):
                    file.write(chunk)
                    if totalBytes:
                        progress.update(task, advance=len(chunk))
        console.print(f"[bold green]File downloaded as '{filename}'[/bold green]")
    else:
        console.print("[bold red]Failed to download the file[/bold red]")


def organizeMovieFolder(folderDir):
    """Organizes a folder of movie posters.

    Renames poster files and creates a subfolder named after each movie,
    placing the renamed poster inside. Automatically organizes all posters that have an
    exact or strong fuzzy match to a media folder.

    Args:
        folderDir (str): The path to the folder containing the movie posters.
    """
    global poster_data, opts
    for file in os.listdir(folderDir):
        sourceFile = os.path.join(folderDir, file)
        collection = False
        matchedMedia = []
        if os.path.isfile(sourceFile):
            if "Collection" not in file:
                matchedMedia = process.extractOne(
                    file,
                    poster_data.mediaFolderNames.keys(),
                    scorer=fuzz.token_sort_ratio,
                )
            else:
                collection = True
            user_in = ""
            if opts.force:
                user_in = "f"
            else:
                if matchedMedia:
                    user_in = typer.prompt(
                        f"Matched poster file {file} to movie {matchedMedia[0]}, proceed? (y/n/f)",
                        default="y",
                    ).lower()
                else:
                    user_in = None
            # Choosing option 'f' follows the force renaming logic for the movie folder/poster
            if opts.force or collection or (matchedMedia and user_in in ["y", "f"]):
                fileName = (
                    os.path.splitext(os.path.basename(file))[0]
                    if (opts.force or user_in == "f" or collection)
                    else matchedMedia[0]  # type: ignore[index]
                )
                fileExtension = os.path.splitext(file)[1]
                newFolder = os.path.join(folderDir, fileName)
                if os.path.isdir(newFolder):
                    shutil.rmtree(newFolder)
                os.mkdir(newFolder)
                destinationFile = os.path.join(
                    newFolder, ("poster%s" % (fileExtension))
                )
                os.rename(sourceFile, destinationFile)


def organizeShowFolder(folderDir):
    """Organizes TV show posters in a given folder.

    This function renames TV show poster files to match the expected Plex
    naming convention (e.g., 'Season01.jpg', 'Season00.jpg' for specials).
    It handles season posters, special season posters, and the main show poster.

    Args:
        folderDir (str): The directory path containing the TV show poster files.
    """
    global poster_data
    for file in os.listdir(folderDir):
        sourceFile = os.path.join(folderDir, file)
        if os.path.isfile(sourceFile):
            if "Season" in file:
                x = re.search(r"\b(?<=Season )\d+", file)
                if x:
                    seasonNumber = str(x.group()).zfill(2)
                    fileExtension = os.path.splitext(file)[1]
                    destinationFile = os.path.join(
                        folderDir, ("Season%s%s" % (seasonNumber, fileExtension))
                    )
                    os.rename(sourceFile, destinationFile)
            elif "Specials" in file:
                seasonNumber = "00"
                fileExtension = os.path.splitext(file)[1]
                destinationFile = os.path.join(
                    folderDir, ("Season%s%s" % (seasonNumber, fileExtension))
                )
                os.rename(sourceFile, destinationFile)
            else:
                fileExtension = os.path.splitext(file)[1]
                destinationFile = os.path.join(
                    folderDir, ("poster%s" % (fileExtension))
                )
                os.rename(sourceFile, destinationFile)


def moviePoster():
    """Processes individual movie posters not in a collection folder.

    This function iterates through loose poster files and asks the user if they
    want to move them into a 'Custom' subfolder for organization. This is
    useful for preparing posters for use with Kometa or for manual review.
    """
    global poster_data
    for poster in poster_data.posterFiles:
        if typer.confirm(
            f"Move poster file {os.path.basename(poster)} to Custom posters folder?"
        ):
            if "Custom" not in poster:
                sourceDir = os.path.dirname(poster)
                destinationDir = os.path.join(sourceDir, "Custom")
            else:
                destinationDir = os.path.dirname(poster)
            if not os.path.isdir(destinationDir):
                os.mkdir(destinationDir)
            shutil.move(poster, destinationDir)
            organizeMovieFolder(destinationDir)
        else:
            console.print("[yellow]Skipped files[/yellow]")


def findPosters(posterRootDirs):
    """Finds and categorizes posters from a list of root directories.

    This function scans the provided directories and categorizes the found items
    into three groups: zipped poster packs, folders containing posters, and
    individual poster files. It also renames zip files to a cleaner format.

    Args:
        posterRootDirs (list): A list of directory paths to search for posters.
    """
    global poster_data
    for path1 in posterRootDirs:
        for path2 in os.listdir(path1):
            filePath: str = os.path.join(path1, path2)
            if zipfile.is_zipfile(filePath):
                zipFilePath = filePath
                x = re.search(r"\b.+ set by (?:\S+)", os.path.splitext(path2)[0])
                if x:
                    newZipFileName = x.group() + os.path.splitext(path2)[1]
                else:
                    newZipFileName: str = (
                        path2.split(".", 1)[0].split("__", 1)[0]
                        + "."
                        + path2.split(".", 1)[1]
                    ).replace("_", " ")
                # newZipFileName = path2.replace('_', ' ')
                newZipFilePath = os.path.join(path1, newZipFileName)
                if path2 != newZipFileName:
                    os.rename(zipFilePath, newZipFilePath)
                poster_data.posterZipFiles[newZipFileName] = newZipFilePath
            elif os.path.isdir(filePath):
                poster_data.posterFolders.append(filePath)
            elif os.path.isfile(filePath):
                poster_data.posterFiles.append(filePath)
            else:
                continue


def copyPosters(posterFolder):
    """Copies posters from a poster folder to the corresponding Plex media folders.

    Creates hard links from the poster folder to each media folder location.

    Args:
        posterFolder (str): The path to the organized poster folder.
    """
    global poster_data, opts
    mediaFolders = poster_data.mediaFolderNames.get(os.path.basename(posterFolder))
    if mediaFolders:
        mediaName = os.path.basename(posterFolder)
        posterFileNames = os.listdir(posterFolder)
        if opts.all or typer.confirm(
            f"Hardlink posters from [{posterFolder}] to [{mediaFolders}]?"
        ):
            replaceFiles = False
            for poster in posterFileNames:
                for mediaRoot in mediaFolders:
                    orig_file = os.path.join(posterFolder, poster)
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
                    new_file = os.path.join(mediaRoot, mediaName, new_name)
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
                            if replaceFiles or typer.confirm(prompt_msg):
                                replaceFiles = True
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


def findBestMediaMatch(poster_zip_name: str, media_names: list):
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
    bestMatch = None
    bestScore = 0
    normPoster = normalize_name(poster_zip_name)
    for candidate in media_names:
        normCandidate = normalize_name(candidate)
        score = fuzz.partial_token_sort_ratio(normPoster, normCandidate)
        if score > bestScore:
            bestMatch, bestScore = candidate, score
    return bestMatch, bestScore


def organizeMovieCollectionFolder(folderDir):
    """Organizes posters for movie collections.

    This function is designed to handle folders that contain posters for multiple
    movies, such as a collection or a set. It iterates through each poster file,
    tries to match it to a movie in the library, and then organizes it into a
    subfolder named after the movie. This is particularly useful for preparing
    movie collection posters for use with Kometa.

    Args:
        folderDir (str): The directory containing the collection of posters.
    """
    global poster_data
    unmatched_files = []

    for file in os.listdir(folderDir):
        sourceFile = os.path.join(folderDir, file)
        if os.path.isfile(sourceFile):
            # Try to match this poster file to a movie in the library
            matchedMedia = process.extractOne(
                file,
                poster_data.mediaFolderNames.keys(),
                scorer=fuzz.token_sort_ratio,
                score_cutoff=60,
            )

            if matchedMedia:
                user_in = typer.prompt(
                    f"Matched poster file {file} to movie {matchedMedia[0]} [score: {matchedMedia[1]}], proceed? (y/n/f)",
                    default="y",
                ).lower()

                if user_in in ["y", "f"]:
                    # Determine folder name: use match name for 'y', original file name for 'f'
                    if user_in == "y":
                        folderName = matchedMedia[0]
                    else:  # user_in == 'f'
                        folderName = os.path.splitext(file)[0]

                    # Create a subfolder for this movie within the collection folder
                    movieFolder = os.path.join(folderDir, folderName)
                    if os.path.isdir(movieFolder):
                        shutil.rmtree(movieFolder)
                    os.mkdir(movieFolder)

                    fileExtension = os.path.splitext(file)[1]
                    destinationFile = os.path.join(
                        movieFolder, ("poster%s" % fileExtension)
                    )
                    os.rename(sourceFile, destinationFile)
                    console.print(
                        f"[green]Organized {file} into {folderName} folder[/green]"
                    )
                else:
                    console.print(f"[yellow]Skipped {file}[/yellow]")
                    continue
            else:
                # No match found - ask if user wants to force rename
                if typer.confirm(
                    f"No match found for poster file {file}. Force rename?"
                ):
                    folderName = os.path.splitext(file)[0]

                    # Create a subfolder within the collection folder
                    movieFolder = os.path.join(folderDir, folderName)
                    if os.path.isdir(movieFolder):
                        shutil.rmtree(movieFolder)
                    os.mkdir(movieFolder)

                    fileExtension = os.path.splitext(file)[1]
                    destinationFile = os.path.join(
                        movieFolder, ("poster%s" % fileExtension)
                    )
                    os.rename(sourceFile, destinationFile)
                    console.print(
                        f"[green]Organized {file} into {folderName} folder[/green]"
                    )
                else:
                    unmatched_files.append(file)

    if unmatched_files:
        console.print(f"\n[yellow]Unmatched files in {folderDir}:[/yellow]")
        for file in unmatched_files:
            console.print(f"  - {file}")
        console.print(
            "[yellow]These files were left in the collection folder for manual organization.[/yellow]"
        )


def processZipFile(selectedLibrary):
    """Processes zipped poster files.

    This function iterates through found zip files, matches them to media in the
    Plex library, and then extracts them. After extraction, it calls the
    appropriate organization function based on the library type (movie or show)
    and the quality of the match. It also handles archiving the zip file after
    processing.

    Args:
        selectedLibrary (LibraryData): The Plex library to process posters for.
    """
    global poster_data
    for posterZip in poster_data.posterZipFiles.keys():
        sourceZip = poster_data.posterZipFiles.get(posterZip)
        if not sourceZip:
            continue
        destinationDir = ""
        unzip = ""
        if selectedLibrary and selectedLibrary.type == "show":
            bestMatch, bestScore = findBestMediaMatch(
                posterZip, list(poster_data.mediaFolderNames.keys())
            )
            if bestMatch:
                destinationDir = os.path.join(os.path.dirname(sourceZip), bestMatch)
                unzip = (
                    "y"
                    if typer.confirm(
                        f"Matched zip file {os.path.basename(sourceZip)} to show {bestMatch} [score: {bestScore}], proceed?"
                    )
                    else "n"
                )
            else:
                console.print("[yellow]No matching media found[/yellow]")
                continue
        elif selectedLibrary and selectedLibrary.type == "movie":
            bestMatch, bestScore = findBestMediaMatch(
                posterZip, list(poster_data.mediaFolderNames.keys())
            )
            if (
                bestMatch and bestScore > 70
            ):  # Only use direct match if score is high enough
                destinationDir = os.path.join(os.path.dirname(sourceZip), bestMatch)
                unzip = (
                    "y"
                    if typer.confirm(
                        f"Matched zip file {os.path.basename(sourceZip)} to movie {bestMatch} [score: {bestScore}], proceed?"
                    )
                    else "n"
                )
            else:
                # For movie sets/collections, unzip with current name and organize individually
                destinationDir = os.path.join(
                    os.path.dirname(sourceZip),
                    os.path.splitext(os.path.basename(sourceZip))[0],
                )
                if bestMatch:
                    unzip = (
                        "y"
                        if typer.confirm(
                            f"Low match score ({bestScore}) for {os.path.basename(sourceZip)} to {bestMatch}. Unzip as collection and organize individually?"
                        )
                        else "n"
                    )
                else:
                    unzip = (
                        "y"
                        if typer.confirm(
                            f"No direct match found for {os.path.basename(sourceZip)}. Unzip as collection and organize individually?"
                        )
                        else "n"
                    )
        if unzip == "y":
            with zipfile.ZipFile(sourceZip, "r") as zip_ref:
                try:
                    if os.path.isdir(destinationDir):
                        shutil.rmtree(destinationDir)
                    zip_ref.extractall(destinationDir)
                except Exception as e:
                    console.print(
                        f"[bold red]Something went wrong extracting the zip: {e}[/bold red]"
                    )
                else:
                    if selectedLibrary and selectedLibrary.type == "show":
                        organizeShowFolder(destinationDir)
                    elif selectedLibrary and selectedLibrary.type == "movie":
                        # Check if this was a direct match or a collection
                        bestMatch, bestScore = findBestMediaMatch(
                            posterZip, list(poster_data.mediaFolderNames.keys())
                        )
                        if bestMatch and bestScore > 70:
                            # Direct match - use standard organization
                            organizeMovieFolder(destinationDir)
                        else:
                            # Collection/set - organize individual movies within the collection
                            console.print(
                                f"\n[cyan]Processing collection folder: {os.path.basename(destinationDir)}[/cyan]"
                            )
                            organizeMovieCollectionFolder(destinationDir)
                    if typer.confirm("Move zip file to archive folder?"):
                        if os.path.isfile(
                            os.path.join(
                                POSTER_DIR, "Archives", os.path.basename(sourceZip)
                            )
                        ):
                            os.remove(
                                os.path.join(
                                    POSTER_DIR, "Archives", os.path.basename(sourceZip)
                                )
                            )
                        shutil.move(sourceZip, os.path.join(POSTER_DIR, "Archives"))
        else:
            console.print("[yellow]Skipped files[/yellow]")


def syncMovieFolder(path):
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
        organizeMovieFolder(path)
    else:
        matchedMedia = process.extractOne(
            path,
            list(poster_data.mediaFolderNames.keys()),
            scorer=fuzz.token_sort_ratio,
            processor=lambda x: os.path.basename(x),
            score_cutoff=70,
        )

        if matchedMedia:
            if typer.confirm(
                f"Matched folder {os.path.basename(path)} to movie {matchedMedia[0]} [{matchedMedia[1]}], proceed?"
            ):
                newPath = os.path.join(os.path.dirname(path), matchedMedia[0])
                if os.path.isdir(newPath):
                    console.print(
                        f"[bold red]Error: Target directory {newPath} already exists. Skipping rename.[/bold red]"
                    )
                else:
                    os.rename(path, newPath)
                    console.print(
                        f"[green]Renamed {os.path.basename(path)} to {matchedMedia[0]}[/green]"
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
        filePath = os.path.join(directory, s)
        if os.path.splitext(s)[0] == prefix and os.path.isfile(filePath):
            if not prompt or typer.confirm(f"Delete {filePath}?"):
                os.remove(filePath)
