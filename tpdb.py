#!/usr/bin/env python3
from __future__ import print_function, unicode_literals

import argparse
import os
import re
import shutil
import zipfile

from plexapi.server import PlexServer
from thefuzz import fuzz, process


class LibraryData:
    def __init__(self, title, type, locations):
        self.title = title
        self.type = type
        self.locations = locations


PLEX_URL = ''
PLEX_TOKEN = ''

# Environmental Variables
PLEX_URL = os.getenv('PLEX_URL', PLEX_URL)
PLEX_TOKEN = os.getenv('PLEX_TOKEN', PLEX_TOKEN)
plex = PlexServer(PLEX_URL, PLEX_TOKEN)
allLibraries = []
for library in plex.library.sections():
    if library.type not in ['artist', 'photo']:
        allLibraries.append(LibraryData(
            library.title, library.type, library.locations))
# sections = [library for library in plex.library.sections() if library.type not in ['artist','photo']]
# print(libraries)
POSTER_DIR = '/data/Posters'
posterZipFiles = {}
posterFolders = []
posterFiles = []
mediaFolderNames = []

def organizeMovieFolder(folderDir):
    for file in os.listdir(folderDir):
        sourceFile = os.path.join(folderDir, file)
        collection = False
        matchedMedia = []
        if os.path.isfile(sourceFile):
            if 'Collection' not in file:
                matchedMedia = process.extractOne(file, mediaFolderNames, scorer=fuzz.token_sort_ratio)
            else:
                collection = True
            if opts.force or collection or (matchedMedia and input("Matched poster file %s to movie %s, proceed? (y/n):  " % (file, matchedMedia[0])) == 'y'):
                fileName = os.path.splitext(os.path.basename(file))[0] if opts.force or collection else matchedMedia[0]
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
    for poster in posterFiles:
        organize = input("Move poster file %s to Custom posters folder? (y/n):  " % os.path.basename(poster))
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
    for path1 in posterRootDirs:
        for path2 in os.listdir(path1):
            filePath = os.path.join(path1, path2)
            if zipfile.is_zipfile(filePath):
                zipFilePath = filePath
                newZipFileName = path2.replace('_', ' ')
                newZipFilePath = os.path.join(path1, newZipFileName)
                if path2 != newZipFileName:
                    os.rename(zipFilePath, newZipFilePath)
                posterZipFiles[newZipFileName] = newZipFilePath
            elif os.path.isdir(filePath):
                posterFolders.append(filePath)
            elif os.path.isfile(filePath):
                posterFiles.append(filePath)
            else:
                continue


def processZipFile():
    for posterZip in posterZipFiles.keys():
        sourceZip = posterZipFiles.get(posterZip)
        destinationDir = ''
        unzip = ''
        if selectedLibrary.type == 'show':
            matchedMedia = process.extractOne(
                posterZip, mediaFolderNames, scorer=fuzz.token_sort_ratio)
            if matchedMedia:
                destinationDir = os.path.join(os.path.dirname(
                    posterZipFiles.get(posterZip)), matchedMedia[0])
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
                    print(sourceZip)
                    print(destinationDir)
                    moveZip = input(
                        "Move zip file to archive folder? (y/n):  ")
                    if(moveZip == 'y'):
                        shutil.move(sourceZip, os.path.join(
                            POSTER_DIR, 'Archives'))
        else:
            print('Skipped files\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        "Reorganize The Poster DB files to work with Plex Meta Manager", formatter_class=argparse.RawTextHelpFormatter)
    libraryNames = [library.title for library in allLibraries]
    # print(libraryNames)
    parser.add_argument('--libraries', nargs='+',
                        choices=libraryNames, default=libraryNames)
    parser.add_argument('--action', nargs='?',
                        choices=['sync', 'new'], default='new')
    parser.add_argument('-f', '--force', action='store_true')
    opts = parser.parse_args()

    if opts.libraries:
        for library in opts.libraries:
            selectedLibrary = LibraryData
            for lib in allLibraries:
                if lib.title == library:
                    selectedLibrary = lib
                    break
            else:
                selectedLibrary = None
                break
            #############################
            ### Process movie posters ###
            #############################
            if selectedLibrary.type == 'movie':
                # Get all media folders in the library
                # mediaPaths["NAME OF THE MEDIA FOLDER",...]
                for path in selectedLibrary.locations:
                    mediaFolderNames.extend(os.listdir(path))

                # Get poster root directories for the library
                posterRootDirs = [os.path.join(POSTER_DIR, path) for path in os.listdir(
                    POSTER_DIR) if fuzz.partial_ratio(selectedLibrary.title, path) > 70]
                findPosters(posterRootDirs)
                if opts.action == 'new':
                    moviePoster()
                    processZipFile()
                elif opts.action == 'sync':
                    for folder in posterFolders:
                        posterExists = False
                        for path in os.listdir(folder):
                            if os.path.isfile(os.path.join(folder, path)):
                                posterExists = True
                        if posterExists and input("Process folder \"%s\"? (y/n):  " % folder) == 'y':
                            organizeMovieFolder(folder)
            ############################
            ### Process show posters ###
            ############################
            elif selectedLibrary.type == 'show':
                # Get all media folders in the library
                # mediaPaths["NAME OF THE MEDIA FOLDER",...]
                mediaFolderNames = []
                for path in selectedLibrary.locations:
                    mediaFolderNames.extend(os.listdir(path))

                # Get poster root directories for the library
                posterRootDirs = [os.path.join(POSTER_DIR, path) for path in os.listdir(
                    POSTER_DIR) if fuzz.partial_ratio(selectedLibrary.title, path) > 70]
                findPosters(posterRootDirs)
                if opts.action == 'new':
                    processZipFile()
                # elif opts.action == 'sync':
                #     matchFolder = process.extractOne(media, posterFolders.keys(), scorer=fuzz.token_sort_ratio, score_cutoff=70)
                #     if matchFolder:
                #         organizeShowFolder(posterFolders.get(matchFolder[0]))
            else:
                print("Library type not setup yet")
