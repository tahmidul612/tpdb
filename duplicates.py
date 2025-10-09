#!/usr/bin/env python3
import os
from os.path import basename
from typing import List
from thefuzz import fuzz, process
import argparse
import logging
# Suppress empty string warnings from thefuzz
logging.getLogger("thefuzz").setLevel(logging.ERROR)

# List of OS/garbage directories to ignore
IGNORE_DIR = ['__MACOSX']

def main():
    """
    Finds and prints potential duplicate poster directories.

    This script scans a directory for subdirectories that might be duplicates
    based on their names. It uses fuzzy string matching to identify potential
    duplicates at the same directory depth level. This is useful for cleaning
    up a poster directory and finding redundant entries.
    """
    parser = argparse.ArgumentParser(
        "Find duplicate posters", formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('dir', default='/data/Posters', nargs='?',
                        help="The root directory to search for duplicate posters.")
    opts = parser.parse_args()
    
    dir_list = subdirs(opts.dir)
    if not dir_list or len(dir_list) < 2:
        print(f'There must be >=2 subdirectories in {opts.dir} to find duplicates.')
        exit(1)

    max_depth = max(dir_list, key=lambda x: x[1])[1]

    for depth in range(0, max_depth + 1):
        print(f'Checking for duplicates at level {depth}...')
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
                    score_cutoff=74
                )
            except Exception:
                continue

            if result:
                # Find the full path of the matched directory
                original_match_path = next((p for p in match_list if basename(p) == result[0]), None)
                if original_match_path:
                    out = (d, original_match_path, result[1])
                    print(f'\t- Potential duplicate: {out[0]}  <-->  {out[1]} (Score: {out[2]})')
                    found_duplicates = True

            match_list.append(d) # Add it back for the next iteration

        if not found_duplicates:
            print(f'\t- No duplicates found at level {depth}.')


def subdirs(directory: str) -> list[tuple[str, int]]:
    """
    Recursively finds all subdirectories and their depth.

    Args:
        directory (str): The path to the directory to scan.

    Returns:
        List[tuple[str, int]]: A list of tuples, where each tuple contains
                               the directory path and its depth level.
    """
    dir_list = []
    if not os.path.isdir(directory):
        print(f'Error: Directory {directory} does not exist.')
        exit(1)

    for d in os.walk(directory):
        if basename(d[0]) not in IGNORE_DIR:
            # Calculate depth based on the number of path separators
            depth = d[0].count(os.path.sep) - directory.count(os.path.sep)
            dir_list.append((d[0], depth))

    return dir_list


if __name__ == '__main__':
    main()