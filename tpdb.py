#!/usr/bin/env python3
from __future__ import print_function, unicode_literals

import argparse
import glob
import os
import re
import shutil
from xmlrpc.client import Boolean
import zipfile
import collections
import requests

from plexapi.server import PlexServer
from plexapi.server import CONFIG
from thefuzz import fuzz, process


class LibraryData:
    def __init__(self, title, type, locations):
        self.title = title
        self.type = type
        self.locations = locations


class Posters:
    def __init__(self, posterFolders=[], posterFiles=[], posterZipFiles={}, mediaFolderNames=collections.defaultdict(list)):
        self.posterFolders = posterFolders
        self.posterFiles = posterFiles
        self.posterZipFiles = posterZipFiles
        self.mediaFolderNames = mediaFolderNames


PLEX_URL = ''
PLEX_TOKEN = ''


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

# Environmental Variables
# PLEX_URL = os.getenv('PLEX_URL', PLEX_URL)
# PLEX_TOKEN = os.getenv('PLEX_TOKEN', PLEX_TOKEN)


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
    if library.type not in ['artist', 'photo']:
        allLibraries.append(LibraryData(
            library.title, library.type, library.locations))
POSTER_DIR = '/data/Posters'

def downloadPoster(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
    }

    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        filename = response.headers.get('content-disposition', None)
        if filename:
            filename = filename.split('filename=')[1].strip('"')
        else:
            filename = os.path.basename(url)

        with open(filename, 'wb') as file:
            file.write(response.content)
        print(f"File downloaded as '{filename}'")
    else:
        print("Failed to download the file")


def organizeMovieFolder(folderDir):
    for file in os.listdir(folderDir):
        sourceFile = os.path.join(folderDir, file)
        collection = False
        matchedMedia = []
        if os.path.isfile(sourceFile):
            if 'Collection' not in file:
                matchedMedia = process.extractOne(
                    file, poster.mediaFolderNames.keys(), scorer=fuzz.token_sort_ratio)
            else:
                collection = True
            if opts.force or collection or (matchedMedia and input("Matched poster file %s to movie %s, proceed? (y/n):  " % (file, matchedMedia[0])) == 'y'):
                fileName = os.path.splitext(os.path.basename(file))[
                    0] if opts.force or collection else matchedMedia[0]
                fileExtension = os.path.splitext(file)[1]
                newFolder = os.path.join(folderDir, fileName)
                if os.path.isdir(newFolder):
                    shutil.rmtree(newFolder)
                os.mkdir(newFolder)
                destinationFile = os.path.join(
                    newFolder, ("poster%s" % (fileExtension)))
                os.rename(sourceFile, destinationFile)


def organizeShowFolder(folderDir):
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
    global poster
    for poster in poster.posterFiles:
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
    global poster
    for path1 in posterRootDirs:
        for path2 in os.listdir(path1):
            filePath: str = os.path.join(path1, path2)
            if zipfile.is_zipfile(filePath):
                zipFilePath = filePath
                newZipFileName: str = (path2.split('.', 1)[0].split('__', 1)[
                    0]+'.'+path2.split('.', 1)[1]).replace('_', ' ')
                # newZipFileName = path2.replace('_', ' ')
                newZipFilePath = os.path.join(path1, newZipFileName)
                if path2 != newZipFileName:
                    os.rename(zipFilePath, newZipFilePath)
                poster.posterZipFiles[newZipFileName] = newZipFilePath
            elif os.path.isdir(filePath):
                poster.posterFolders.append(filePath)
            elif os.path.isfile(filePath):
                poster.posterFiles.append(filePath)
            else:
                continue


def movePosters(posterFolder):
    global poster
    mediaFolders = poster.mediaFolderNames.get(os.path.basename(posterFolder))
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
    global poster
    for posterZip in poster.posterZipFiles.keys():
        sourceZip = poster.posterZipFiles.get(posterZip)
        destinationDir = ''
        unzip = ''
        if selectedLibrary.type == 'show':
            matchedMedia = process.extractOne(
                posterZip, poster.mediaFolderNames.keys(), scorer=fuzz.token_sort_ratio)
            if matchedMedia:
                destinationDir = os.path.join(os.path.dirname(
                    poster.posterZipFiles.get(posterZip)), matchedMedia[0])
                unzip = input("Matched zip file %s to show %s, proceed? (y/n):  " %
                              (os.path.basename(sourceZip), matchedMedia[0]))
            else:
                print('No matching media found\n')
                continue
        elif selectedLibrary.type == 'movie':
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
                    if selectedLibrary.type == 'show':
                        organizeShowFolder(destinationDir)
                    elif selectedLibrary.type == 'movie':
                        organizeMovieFolder(destinationDir)
                    moveZip = input(
                        "Move zip file to archive folder? (y/n):  ")
                    if (moveZip == 'y'):
                        shutil.move(sourceZip, os.path.join(
                            POSTER_DIR, 'Archives'))
        else:
            print('Skipped files\n')


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
    parser.add_argument('--libraries', nargs='+',
                        choices=libraryNames, default=libraryNames)
    parser.add_argument('--action', nargs='?',
                        choices=['sync', 'new'], default='new')
    parser.add_argument('-f', '--force', action='store_true')
    parser.add_argument('-a', '--all', action='store_true')
    parser.add_argument('--server', nargs='?',
                        choices=['plex', 'emby', 'all'], default='plex')
    parser.add_argument('-d', '--download', nargs='?')
    opts = parser.parse_args()

    # Download poster
    if opts.download:
        downloadPoster(opts.download)

    # Process posters
    elif opts.libraries:
        for library in opts.libraries:
            selectedLibrary = LibraryData
            for lib in allLibraries:
                if lib.title == library:
                    selectedLibrary = lib
                    break
            else:
                selectedLibrary = None
                break
            global poster
            poster = Posters()


            #################################
            ### Copy posters to media dir ###
            #################################
            if opts.server == 'emby' and (selectedLibrary.type == 'movie' or selectedLibrary.type == 'show'):
                for path in selectedLibrary.locations:
                    for name in os.listdir(path):
                        poster.mediaFolderNames[name].append(path)
                posterRootDirs = [os.path.join(POSTER_DIR, path) for path in os.listdir(
                    POSTER_DIR) if fuzz.partial_ratio(selectedLibrary.title, path) > 70]
                poster.posterFolders = []
                if selectedLibrary.type == 'movie':
                    for folder in posterRootDirs:
                        allPaths = glob.glob(os.path.join(
                            glob.escape(folder), '*', '*'))
                        poster.posterFolders.extend(
                            filter(lambda f: os.path.isdir(f), allPaths))
                elif selectedLibrary.type == 'show':
                    for folder in posterRootDirs:
                        allPaths = glob.glob(
                            os.path.join(glob.escape(folder), '*'))
                        poster.posterFolders.extend(
                            filter(lambda f: os.path.isdir(f), allPaths))
                for folder in poster.posterFolders:
                    movePosters(folder)

            #############################
            ### Process movie posters ###
            #############################
            elif selectedLibrary.type == 'movie':
                # Get all media folders in the library
                # mediaPaths["NAME OF THE MEDIA FOLDER",...]
                for path in selectedLibrary.locations:
                    for name in os.listdir(path):
                        poster.mediaFolderNames[name].append(path)

                # Get poster root directories for the library
                posterRootDirs = [os.path.join(POSTER_DIR, path) for path in os.listdir(
                    POSTER_DIR) if fuzz.partial_ratio(selectedLibrary.title, path) > 70]
                findPosters(posterRootDirs)
                if opts.action == 'new':
                    moviePoster()
                    processZipFile()
                elif opts.action == 'sync':
                    for folder in poster.posterFolders:
                        posterExists = False
                        for path in os.listdir(folder):
                            if os.path.isfile(os.path.join(folder, path)):
                                posterExists = True
                        if posterExists and input("Process folder \"%s\"? (y/n):  " % folder) == 'y':
                            organizeMovieFolder(folder)
                if opts.server == 'all':
                    for folder in poster.posterFolders:
                        movePosters(folder)
            ############################
            ### Process show posters ###
            ############################
            elif selectedLibrary.type == 'show':
                # Get all media folders in the library
                # mediaPaths["NAME OF THE MEDIA FOLDER",...]
                for path in selectedLibrary.locations:
                    for name in os.listdir(path):
                        poster.mediaFolderNames[name].append(path)

                # Get poster root directories for the library
                posterRootDirs = [os.path.join(POSTER_DIR, path) for path in os.listdir(
                    POSTER_DIR) if fuzz.partial_ratio(selectedLibrary.title, path) > 70]
                findPosters(posterRootDirs)
                if opts.action == 'new':
                    processZipFile()
                elif opts.action == 'sync':
                    unorganizedPosterFolders = []
                    for folder in poster.posterFolders:
                        if not check_file(folder, "poster"):
                            unorganizedPosterFolders.append(folder)
                    for folder in unorganizedPosterFolders:
                        organizeShowFolder(folder)
                if opts.server == 'all':
                    for folder in poster.posterFolders:
                        movePosters(folder)
            else:
                print("Library type not setup yet")
