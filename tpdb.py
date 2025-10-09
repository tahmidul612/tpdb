#!/usr/bin/env python3
from __future__ import print_function, unicode_literals

import argparse
import collections
import os
import re
import shutil
import zipfile
from xmlrpc.client import Boolean

import pyrfc6266
import requests
from plexapi.server import CONFIG, PlexServer
from thefuzz import fuzz, process
from alive_progress import alive_bar

from pprint import pprint

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
    def __init__(self, posterFolders=[], posterFiles=[], posterZipFiles={}, mediaFolderNames=collections.defaultdict(list)):
        self.posterFolders = posterFolders
        self.posterFiles = posterFiles
        self.posterZipFiles = posterZipFiles
        self.mediaFolderNames = mediaFolderNames


# Global static variables
PLEX_URL = ''
PLEX_TOKEN = ''
POSTER_DIR = '/data/Posters'

################################# Start Plex Config #######################################


def update_config(config_path):
    """Updates the PlexAPI config file with the provided URL and token.

    Args:
        config_path (str): The path to the PlexAPI config file.

    Returns:
        bool: True if the file was updated, False otherwise.
    """
    updated = False
    with open(config_path, 'r') as configfile:
        lines = configfile.readlines()

    with open(config_path, 'w') as configfile:
        for line in lines:
            if line.startswith('server_baseurl'):
                configfile.write(f'server_baseurl = {PLEX_URL}\n')
                updated = True
            elif line.startswith('server_token'):
                configfile.write(f'server_token = {PLEX_TOKEN}\n')
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
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
    }
    customFilename = None
    filename = None
    if 'theposterdb.com/set' in url:
        posterID = url.split('/')[-1]
        downloadUrl = f'https://theposterdb.com/set/download/{posterID}'
    elif 'theposterdb.com/poster' in url:
        posterID = url.split('/')[-1]
        downloadUrl = f'https://theposterdb.com/api/assets/{posterID}'
    elif 'theposterdb.com/api/assets' in url:
        downloadUrl = url
    else:
        downloadUrl = url
        customFilename = input("Enter movie name for poster file (no ext): ")
    if downloadUrl:
        response = requests.get(downloadUrl, headers=headers, stream=True)
    else:
        print("Invalid URL")
        return
    if response.status_code == 200:
        filename = response.headers.get('content-disposition', None)
        if not customFilename and filename:
            filename = pyrfc6266.parse_filename(filename)
        elif customFilename and filename:
            filename = ''.join([customFilename, os.path.splitext(
                pyrfc6266.parse_filename(filename))[1]])
        elif customFilename:
            filename = ''.join(
                [customFilename, os.path.splitext(os.path.basename(url))[1]])
        else:
            print("Could not find a filename, aborting download")
            return
        print("Select folder to save poster file")
        for i, dir in enumerate(os.listdir(POSTER_DIR), start=1):
            print(f"{i}: {dir}")
        dirIndex = input("Enter folder number: ")
        saveDir = os.path.join(
            POSTER_DIR, os.listdir(POSTER_DIR)[int(dirIndex)-1])
        totalBytes = int(response.headers.get('content-length', 0)) or None  # Ensure totalBytes is set
        with open(os.path.join(saveDir, filename), 'wb') as file, alive_bar(totalBytes, title=filename, force_tty=True) as bar:
            for chunk in response.iter_content(chunk_size=4096):
                file.write(chunk)
                if totalBytes:
                    bar(len(chunk))
                else:
                    bar()  # update spinner
        print(f"File downloaded as '{filename}'")
    else:
        print("Failed to download the file")


def organizeMovieFolder(folderDir):
    """Organizes movie posters in a given folder.

    This function iterates through files in a directory, matches them to movies
    in the Plex library using fuzzy string matching, and then renames and moves
    them into a subfolder named after the movie. This is intended to be used
for individual movie posters.

    Args:
        folderDir (str): The directory path containing the movie poster files.
    """
    global poster_data
    for file in os.listdir(folderDir):
        sourceFile = os.path.join(folderDir, file)
        collection = False
        matchedMedia = []
        if os.path.isfile(sourceFile):
            if 'Collection' not in file:
                matchedMedia = process.extractOne(
                    file, poster_data.mediaFolderNames.keys(), scorer=fuzz.token_sort_ratio)
            else:
                collection = True
            user_in = ''
            if opts.force:
                user_in = 'f'
            else:
                user_in = input("Matched poster file %s to movie %s, proceed? (y/n/f):  " % (file, matchedMedia[0])) if matchedMedia else None
            # Choosing option 'f' follows the force renaming logic for the movie folder/poster
            if opts.force or collection or (matchedMedia and user_in in ['y', 'f']):
                fileName = os.path.splitext(os.path.basename(file))[
                    0] if (opts.force or user_in == 'f' or collection) else matchedMedia[0]
                fileExtension = os.path.splitext(file)[1]
                newFolder = os.path.join(folderDir, fileName)
                if os.path.isdir(newFolder):
                    shutil.rmtree(newFolder)
                os.mkdir(newFolder)
                destinationFile = os.path.join(
                    newFolder, ("poster%s" % (fileExtension)))
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
            if 'Season' in file:
                x = re.search(r"\b(?<=Season )\d+", file)
                if x:
                    seasonNumber = str(x.group()).zfill(2)
                    fileExtension = os.path.splitext(file)[1]
                    destinationFile = os.path.join(
                        folderDir, ("Season%s%s" % (seasonNumber, fileExtension)))
                    os.rename(sourceFile, destinationFile)
            elif 'Specials' in file:
                seasonNumber = "00"
                fileExtension = os.path.splitext(file)[1]
                destinationFile = os.path.join(
                    folderDir, ("Season%s%s" % (seasonNumber, fileExtension)))
                os.rename(sourceFile, destinationFile)
            else:
                fileExtension = os.path.splitext(file)[1]
                destinationFile = os.path.join(
                    folderDir, ("poster%s" % (fileExtension)))
                os.rename(sourceFile, destinationFile)


def moviePoster():
    """Processes individual movie posters not in a collection folder.

    This function iterates through loose poster files and asks the user if they
    want to move them into a 'Custom' subfolder for organization. This is
    useful for preparing posters for use with Kometa or for manual review.
    """
    global poster_data
    for poster in poster_data.posterFiles:
        organize = input(
            "Move poster file %s to Custom posters folder? (y/n):  " % os.path.basename(poster))
        if organize == 'y':
            if 'Custom' not in poster:
                sourceDir = os.path.dirname(poster)
                destinationDir = os.path.join(sourceDir, 'Custom')
            else:
                destinationDir = os.path.dirname(poster)
            if not os.path.isdir(destinationDir):
                os.mkdir(destinationDir)
            shutil.move(poster, destinationDir)
            organizeMovieFolder(destinationDir)
        else:
            print('Skipped files\n')


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
                x = re.search(r'\b.+ set by (?:\S+)',
                              os.path.splitext(path2)[0])
                if x:
                    newZipFileName = x.group()+os.path.splitext(path2)[1]
                else:
                    newZipFileName: str = (path2.split('.', 1)[0].split('__', 1)[
                        0]+'.'+path2.split('.', 1)[1]).replace('_', ' ')
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
    """Copies organized posters to the corresponding media folders.

    This function creates hard links from the organized poster folders to the
    actual media folders in the Plex library. This is useful for users who
    want to have the posters directly in their media folders for Plex to use.

    Args:
        posterFolder (str): The path to the organized poster folder.
    """
    global poster_data
    mediaFolders = poster_data.mediaFolderNames.get(
        os.path.basename(posterFolder))
    if mediaFolders:
        mediaName = os.path.basename(posterFolder)
        posterFileNames = os.listdir(posterFolder)
        if opts.all or input("Hardlink posters from [%s] to [%s]? (y/n): " % (posterFolder, mediaFolders)) == 'y':
            replaceFiles = False
            for poster in posterFileNames:
                for mediaRoot in mediaFolders:
                    orig_file = os.path.join(posterFolder, poster)
                    new_name = poster
                    if 'Season00' in poster:
                        new_name = poster.replace(
                            'Season00', 'season-specials-poster')
                    elif 'Season' in poster:
                        new_name = poster.split('.')[0].lower(
                        )+'-poster'+'.'+poster.split('.')[1]
                    new_file = os.path.join(mediaRoot, mediaName, new_name)
                    if check_file(os.path.dirname(new_file), os.path.splitext(new_name)[0]):
                        if os.path.isfile(new_file) and os.path.samefile(orig_file, new_file):
                            continue
                        else:
                            prompt = "Replace existing files? (y/n): "
                            if opts.all:
                                prompt = "Replace all poster files in %s? (y/n): " % os.path.dirname(
                                    new_file)
                            if replaceFiles or input(prompt) == 'y':
                                replaceFiles = True
                                delete_file(os.path.dirname(new_file),
                                            os.path.splitext(new_name)[0], False)
                            else:
                                print("Skipping folder %s" %
                                      os.path.dirname(new_file))
                                continue
                    os.link(orig_file, new_file)


import string

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
    name = re.sub(r'\(\d{4}\)', '', name)  # remove (year)
    name = re.sub(r'\s+set by.*$', '', name, flags=re.IGNORECASE).strip()
    name = name.translate(str.maketrans('', '', string.punctuation)).lower()
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
                file, poster_data.mediaFolderNames.keys(), scorer=fuzz.token_sort_ratio, score_cutoff=60)

            if matchedMedia:
                user_in = input("Matched poster file %s to movie %s [score: %d], proceed? (y/n/f):  "
                               % (file, matchedMedia[0], matchedMedia[1]))

                if user_in in ['y', 'f']:
                    # Determine folder name: use match name for 'y', original file name for 'f'
                    if user_in == 'y':
                        folderName = matchedMedia[0]
                    else:  # user_in == 'f'
                        folderName = os.path.splitext(file)[0]

                    # Create a subfolder for this movie within the collection folder
                    movieFolder = os.path.join(folderDir, folderName)
                    if os.path.isdir(movieFolder):
                        shutil.rmtree(movieFolder)
                    os.mkdir(movieFolder)

                    fileExtension = os.path.splitext(file)[1]
                    destinationFile = os.path.join(movieFolder, ("poster%s" % fileExtension))
                    os.rename(sourceFile, destinationFile)
                    print(f"Organized {file} into {folderName} folder")
                else:
                    print(f"Skipped {file}")
                    continue
            else:
                # No match found - ask if user wants to force rename
                user_in = input("No match found for poster file %s. Force rename? (y/n):  " % file)
                if user_in == 'y':
                    folderName = os.path.splitext(file)[0]

                    # Create a subfolder within the collection folder
                    movieFolder = os.path.join(folderDir, folderName)
                    if os.path.isdir(movieFolder):
                        shutil.rmtree(movieFolder)
                    os.mkdir(movieFolder)

                    fileExtension = os.path.splitext(file)[1]
                    destinationFile = os.path.join(movieFolder, ("poster%s" % fileExtension))
                    os.rename(sourceFile, destinationFile)
                    print(f"Organized {file} into {folderName} folder")
                else:
                    unmatched_files.append(file)

    if unmatched_files:
        print(f"\nUnmatched files in {folderDir}:")
        for file in unmatched_files:
            print(f"  - {file}")
        print("These files were left in the collection folder for manual organization.")

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
        destinationDir = ''
        unzip = ''
        if selectedLibrary and selectedLibrary.type == 'show':
            bestMatch, bestScore = findBestMediaMatch(posterZip, list(poster_data.mediaFolderNames.keys()))
            if bestMatch:
                destinationDir = os.path.join(os.path.dirname(sourceZip), bestMatch)
                unzip = input("Matched zip file %s to show %s [score: %d], proceed? (y/n):  "
                              % (os.path.basename(sourceZip), bestMatch, bestScore))
            else:
                print('No matching media found\n')
                continue
        elif selectedLibrary and selectedLibrary.type == 'movie':
            bestMatch, bestScore = findBestMediaMatch(posterZip, list(poster_data.mediaFolderNames.keys()))
            if bestMatch and bestScore > 70:  # Only use direct match if score is high enough
                destinationDir = os.path.join(os.path.dirname(sourceZip), bestMatch)
                unzip = input("Matched zip file %s to movie %s [score: %d], proceed? (y/n):  "
                              % (os.path.basename(sourceZip), bestMatch, bestScore))
            else:
                # For movie sets/collections, unzip with current name and organize individually
                destinationDir = os.path.join(os.path.dirname(sourceZip),
                                              os.path.splitext(os.path.basename(sourceZip))[0])
                if bestMatch:
                    unzip = input("Low match score (%d) for %s to %s. Unzip as collection and organize individually? (y/n):  "
                                  % (bestScore, os.path.basename(sourceZip), bestMatch))
                else:
                    unzip = input("No direct match found for %s. Unzip as collection and organize individually? (y/n):  "
                                  % os.path.basename(sourceZip))
        if unzip == 'y':
            with zipfile.ZipFile(sourceZip, 'r') as zip_ref:
                try:
                    if os.path.isdir(destinationDir):
                        shutil.rmtree(destinationDir)
                    zip_ref.extractall(destinationDir)
                except:
                    print("Something went wrong extracting the zip")
                else:
                    if selectedLibrary and selectedLibrary.type == 'show':
                        organizeShowFolder(destinationDir)
                    elif selectedLibrary and selectedLibrary.type == 'movie':
                        # Check if this was a direct match or a collection
                        bestMatch, bestScore = findBestMediaMatch(posterZip, list(poster_data.mediaFolderNames.keys()))
                        if bestMatch and bestScore > 70:
                            # Direct match - use standard organization
                            organizeMovieFolder(destinationDir)
                        else:
                            # Collection/set - organize individual movies within the collection
                            print(f"\nProcessing collection folder: {os.path.basename(destinationDir)}")
                            organizeMovieCollectionFolder(destinationDir)
                    moveZip = input(
                        "Move zip file to archive folder? (y/n):  ")
                    if (moveZip == 'y'):
                        if os.path.isfile(os.path.join(POSTER_DIR, 'Archives', os.path.basename(sourceZip))):
                            os.remove(os.path.join(
                                POSTER_DIR, 'Archives', os.path.basename(sourceZip)))
                        shutil.move(sourceZip, os.path.join(
                            POSTER_DIR, 'Archives'))
        else:
            print('Skipped files\n')

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
        print(f"Organizing complex folder: {path}")
        organizeMovieFolder(path)
    else:
        matchedMedia = process.extractOne(
            path, list(poster_data.mediaFolderNames.keys()),
            scorer=fuzz.token_sort_ratio, processor=lambda x: os.path.basename(x),
            score_cutoff=70)
        
        if matchedMedia:
            user_in = input("Matched folder %s to movie %s [%d], proceed? (y/n):  " %
                            (os.path.basename(path), matchedMedia[0], matchedMedia[1]))
            if user_in.lower() == 'y':
                newPath = os.path.join(os.path.dirname(path), matchedMedia[0])
                if os.path.isdir(newPath):
                    print(f"Error: Target directory {newPath} already exists. Skipping rename.")
                else:
                    os.rename(path, newPath)
                    print(f"Renamed {os.path.basename(path)} to {matchedMedia[0]}")
        else:
            print(f"No match found for {os.path.basename(path)}")


def check_file(directory, prefix):
    """Checks if a file with a given prefix exists in a directory.

    Args:
        directory (str): The directory to search in.
        prefix (str): The prefix of the file to look for (without extension).

    Returns:
        bool: True if a file with the prefix exists, False otherwise.
    """
    for s in os.listdir(directory):
        if os.path.splitext(s)[0] == prefix and os.path.isfile(os.path.join(directory, s)):
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
            if not prompt or input("Delete %s? (y/n): " % filePath) == 'y':
                os.remove(filePath)


if __name__ == '__main__':
    """
    Main execution block for the script.

    This script is designed to organize movie and TV show posters downloaded from
    The Poster DB (TPDb) for use with Plex and metadata managers like Kometa.
    It can process local poster files, sort them into media-specific folders,
    and handle zipped poster packs.

    The script connects to a Plex server to get a list of media for matching,
    and it can be configured via a config file or command-line arguments.
    """
    # Get config from file
    if CONFIG:
        if not PLEX_TOKEN:
            PLEX_TOKEN = CONFIG.data['auth'].get('server_token')
        if not PLEX_URL:
            PLEX_URL = CONFIG.data['auth'].get('server_baseurl')

    # Ask user for config
    if not PLEX_TOKEN or not PLEX_URL:
        if not PLEX_TOKEN:
            PLEX_TOKEN = input("Please enter your Plex auth token: ")
        if not PLEX_URL:
            PLEX_URL = input("Please enter your Plex URL: ")
        if input("Save config? (y/n): ") == 'y':
            config_directory = os.path.expanduser('~/.config/plexapi')
            os.makedirs(config_directory, exist_ok=True)
            config_file_path = os.path.join(config_directory, 'config.ini')

            if not os.path.exists(config_file_path):
                with open(config_file_path, 'w') as configfile:
                    configfile.write('[auth]\n')
                    configfile.write(f'server_baseurl = {PLEX_URL}\n')
                    configfile.write(f'server_token = {PLEX_TOKEN}\n')
            else:
                if update_config(config_file_path):
                    print("Config file updated.")
                else:
                    print("Config file already contains data, but server_baseurl and server_token were not found. Please update it manually.")

    plex = PlexServer(PLEX_URL, PLEX_TOKEN)
    allLibraries = []
    for library in plex.library.sections():
        if library.type not in ['artist', 'photo'] and library.locations:
            allLibraries.append(LibraryData(
                library.title, library.type, library.locations))

    # Define arguments
    parser = argparse.ArgumentParser(
        "Reorganize The Poster DB files to work with Kometa (formerly Plex Meta Manager)",
        formatter_class=argparse.RawTextHelpFormatter)
    libraryNames = [library.title for library in allLibraries]
    parser.add_argument('-l','--libraries', nargs='+',
                        choices=libraryNames, default=libraryNames, help='Name of the Plex libraries to process')
    parser.add_argument('--action', nargs='?',
                        choices=['sync', 'new'], default='new', help='Organize new posters or sync existing posters')
    parser.add_argument('-u', '--unlinked', action='store_true',
                        default=False, help='Find and process unlinked posters')
    parser.add_argument('-f', '--force', action='store_true', default=False,
                        help='Process movie posters without matching to a media folder')
    parser.add_argument('--filter', nargs='?', help='String filter for source poster folders')
    parser.add_argument('-a', '--all', action='store_true', default=False,
                        help='Replace all poster files in media folder without prompting')
    parser.add_argument('-c', '--copy', action='store_true',
                        default=False, help='Copy posters to media folders')
    parser.add_argument('-d', '--download', nargs='?',
                        help='Download a poster from a URL')
    opts = parser.parse_args()

    # Download poster
    if opts.download:
        downloadPoster(opts.download)

    # Process posters
    if opts.libraries:
        for library_name in opts.libraries:
            selectedLibrary = next((lib for lib in allLibraries if lib.title == library_name), None)
            if not selectedLibrary:
                print(f"Library '{library_name}' not found.")
                continue
            poster_data = Posters([], [], {}, collections.defaultdict(list))

            ####################################
            ### Organize and/or copy posters ###
            ####################################
            if selectedLibrary.type in ['movie', 'show']:
                # Get all media folders in the library
                for path in selectedLibrary.locations:
                    for name in os.listdir(path):
                        poster_data.mediaFolderNames[name].append(path)

                # Get poster root directories for the library
                posterRootDirs = [os.path.join(POSTER_DIR, path) for path in os.listdir(
                    POSTER_DIR) if fuzz.partial_ratio(selectedLibrary.title, path) > 70]
                findPosters(posterRootDirs)
                
                if opts.filter:
                    folder_and_score = [e for e in process.extractBests(
                        opts.filter, poster_data.posterFolders, scorer=fuzz.token_set_ratio, score_cutoff=50)]
                    if 100 in [s[1] for s in folder_and_score]:
                        poster_data.posterFolders = [f[0] for f in folder_and_score if f[1] == 100]
                    else:
                        poster_data.posterFolders = [f[0] for f in folder_and_score]
                    print(f'Filtered poster folders to search in:\n{poster_data.posterFolders}')

                match selectedLibrary.type:
                    case 'movie':
                        if opts.unlinked:
                            moviePosterFolders = []
                            for folder in poster_data.posterFolders:
                                moviePosterFolders.extend([os.path.join(folder, name) for name in os.listdir(folder)])
                            unlinkedFolders = set()
                            for movie in moviePosterFolders:
                                posterExists = False
                                if os.path.isfile(movie):
                                    unlinkedFolders.add(os.path.dirname(movie))
                                    continue
                                for path in os.listdir(movie):
                                    if os.path.isfile(os.path.join(movie, path)):
                                        posterExists = True
                                if posterExists and not any(m in os.path.basename(movie) for m in ['Collection', *poster_data.mediaFolderNames.keys()]) and 'Custom' not in movie:
                                    unlinkedFolders.add(movie)
                            if unlinkedFolders and input(f'{len(unlinkedFolders)} unlinked folders found. Start processing them? (y/n): ') == 'y':
                                for folder in unlinkedFolders:
                                    syncMovieFolder(folder)
                        elif opts.action == 'new':
                            moviePoster()
                            processZipFile(selectedLibrary)
                        elif opts.action == 'sync':
                            for folder in poster_data.posterFolders:
                                posterExists = any(os.path.isfile(os.path.join(folder, x)) for x in os.listdir(folder))
                                if posterExists and (opts.all or input("Process folder \"%s\"? (y/n):  " % folder) == 'y'):
                                    organizeMovieFolder(folder)
                    case 'show':
                        if opts.action == 'new':
                            processZipFile(selectedLibrary)
                        elif opts.action == 'sync':
                            unorganizedPosterFolders = [folder for folder in poster_data.posterFolders if not check_file(folder, "poster")]
                            for folder in unorganizedPosterFolders:
                                organizeShowFolder(folder)
                # Move posters to media folders
                if opts.copy:
                    for folder in poster_data.posterFolders:
                        copyPosters(folder)

            else:
                print("Library type not setup yet")
