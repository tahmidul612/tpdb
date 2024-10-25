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
from tqdm.auto import tqdm

from pprint import pprint

# Data classes
class LibraryData:
    def __init__(self, title=None, type=None, locations=None):
        self.title = title
        self.type = type
        self.locations = locations


class Posters:
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
################################## End Plex Config #######################################


def downloadPoster(url):
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

        # Download with progress bar: https://stackoverflow.com/a/61575758
        with tqdm.wrapattr(open(os.path.join(saveDir, filename), 'wb'), "write", miniters=1, total=int(response.headers.get('content-length', 0)), desc=filename) as file:
            for chunk in response.iter_content(chunk_size=4096):
                file.write(chunk)
        print(f"File downloaded as '{filename}'")
    else:
        print("Failed to download the file")


def organizeMovieFolder(folderDir):
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


def processZipFile():
    global poster_data
    for posterZip in poster_data.posterZipFiles.keys():
        sourceZip = poster_data.posterZipFiles.get(posterZip)
        destinationDir = ''
        unzip = ''
        if selectedLibrary and selectedLibrary.type == 'show':
            matchedMedia = process.extractOne(
                posterZip, poster_data.mediaFolderNames.keys(), scorer=fuzz.token_sort_ratio)
            if matchedMedia:
                destinationDir = os.path.join(os.path.dirname(
                    poster_data.posterZipFiles.get(posterZip)), matchedMedia[0])
                unzip = input("Matched zip file %s to show %s [score: %d], proceed? (y/n):  " %
                              (os.path.basename(sourceZip), matchedMedia[0], matchedMedia[1]))
            else:
                print('No matching media found\n')
                continue
        elif selectedLibrary and selectedLibrary.type == 'movie':
            destinationDir = os.path.join(os.path.dirname(
                sourceZip), os.path.splitext(os.path.basename(sourceZip))[0])
            unzip = input("Unzip file %s? (y/n):  " %
                          (os.path.basename(sourceZip)))
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
                        organizeMovieFolder(destinationDir)
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
    global poster_data
    if len(os.listdir(path)) > 1:
        print(path)
        organizeMovieFolder(path)
    else:
        matchedMedia = process.extractOne(
            path, poster_data.mediaFolderNames.keys(), scorer=fuzz.token_sort_ratio, processor=lambda x: os.path.basename(x), score_cutoff=70)
        
        user_in = input("Matched folder %s to movie %s [%d], proceed? (y/n/f):  " %
                        (os.path.basename(path), matchedMedia[0], matchedMedia[1])) if matchedMedia else None
        # Choosing option 'f' follows the force renaming logic for the movie folder/poster
        # if opts.force or (matchedMedia and user_in in ['y', 'f']):
        #     fileName = os.path.splitext(os.path.basename(file))[
        #         0] if (opts.force or user_in == 'f' or collection) else matchedMedia[0]
        #     fileExtension = os.path.splitext(file)[1]
        #     newFolder = os.path.join(folderDir, fileName)
        #     if os.path.isdir(newFolder):
        #         shutil.rmtree(newFolder)
        #     os.mkdir(newFolder)
        #     destinationFile = os.path.join(
        #         newFolder, ("poster%s" % (fileExtension)))
        #     os.rename(sourceFile, destinationFile)

def check_file(dir, prefix):
    for s in os.listdir(dir):
        if os.path.splitext(s)[0] == prefix and os.path.isfile(os.path.join(dir, s)):
            return True
    return False


def delete_file(dir, prefix, prompt: Boolean):
    for s in os.listdir(dir):
        filePath = os.path.join(dir, s)
        if os.path.splitext(s)[0] == prefix and os.path.isfile(filePath):
            if not prompt or input("Delete %s? (y/n): " % filePath) == 'y':
                os.remove(filePath)


if __name__ == '__main__':
    # Define arguments
    parser = argparse.ArgumentParser(
        "Reorganize The Poster DB files to work with Plex Meta Manager", formatter_class=argparse.RawTextHelpFormatter)
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
        for library in opts.libraries:
            selectedLibrary = LibraryData()
            for lib in allLibraries:
                if lib.title == library:
                    selectedLibrary = lib
                    break
            else:
                selectedLibrary = None
                break
            global poster_data
            poster_data = Posters([], [], {}, collections.defaultdict(list))

            ####################################
            ### Organize and/or copy posters ###
            ####################################
            if selectedLibrary.type in ['movie', 'show']:
                # Get all media folders in the library
                # mediaPaths["NAME OF THE MEDIA FOLDER",...]
                for path in selectedLibrary.locations:
                    for name in os.listdir(path):
                        poster_data.mediaFolderNames[name].append(path)

                # Get poster root directories for the library
                posterRootDirs = [os.path.join(POSTER_DIR, path) for path in os.listdir(
                    POSTER_DIR) if fuzz.partial_ratio(selectedLibrary.title, path) > 70]
                findPosters(posterRootDirs)
                
                if opts.filter:
                    poster_data.posterFolders = [e[0] for e in process.extractBests(
                        opts.filter, poster_data.posterFolders, scorer=fuzz.partial_token_set_ratio, score_cutoff=80)]
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
                                if posterExists:
                                    if not any(m in os.path.basename(movie) for m in ['Collection', *poster_data.mediaFolderNames.keys()]) and 'Custom' not in movie:
                                        unlinkedFolders.add(movie)
                            # print(*unlinkedFolders, sep='\n\n')
                            if input(f'{len(unlinkedFolders)} unlinked folders found. Start processing them? (y/n): ') == 'y':
                                for folder in unlinkedFolders:
                                    syncMovieFolder(folder)
                        elif opts.action == 'new':
                            moviePoster()
                            processZipFile()
                        elif opts.action == 'sync':
                            for folder in poster_data.posterFolders:
                                posterExists = False
                                for path in os.listdir(folder):
                                    if os.path.isfile(os.path.join(folder, path)):
                                        posterExists = True
                                if posterExists and (opts.all or input("Process folder \"%s\"? (y/n):  " % folder) == 'y'):
                                    organizeMovieFolder(folder)
                    case 'show':
                        if opts.action == 'new':
                            processZipFile()
                        elif opts.action == 'sync':
                            unorganizedPosterFolders = []
                            for folder in poster_data.posterFolders:
                                if not check_file(folder, "poster"):
                                    unorganizedPosterFolders.append(folder)
                            for folder in unorganizedPosterFolders:
                                organizeShowFolder(folder)
                # Move posters to media folders
                if opts.copy:
                    for folder in poster_data.posterFolders:
                        copyPosters(folder)

            else:
                print("Library type not setup yet")
