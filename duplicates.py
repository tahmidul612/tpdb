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
    parser = argparse.ArgumentParser(
        "Find duplicate posters", formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('dir', default='/data/Posters', nargs='?')
    opts = parser.parse_args()
    
    dir_list = subdirs(opts.dir)
    if not dir_list or len(dir_list) < 2:
        print(f'There must be >=2 subdirectories in {opts.dir}')
        exit(1)
    max_depth = max(dir_list, key= lambda x: x[1])[1]
    new_list = []
    for depth in range(0, max_depth):
        print(f'Duplicates at level {depth}')
        new_list = [d[0] for d in dir_list if d[1] == depth]
        for _ in range(0, len(new_list)):
            d = new_list.pop(0)
            try:
                result = process.extractOne(basename(d), new_list, lambda x: str(basename(
                    x)).strip('Collection') , score_cutoff=74, scorer=fuzz.token_set_ratio)
            except Exception as _:
                continue
            if result:
                out = (d , *result)
                print(f'\t{out}')
            new_list.append(d)


def subdirs(dir) -> List[tuple[str, int]]:
    dir_list = []
    if not os.path.isdir(dir):
        print(f'Directory {dir} does not exist')
        exit(1)
    for d in os.walk(dir):
        if basename(d[0]) not in IGNORE_DIR:
            dir_list.append((d[0], d[0][len(dir)+len(os.path.sep):].count(os.path.sep)))
    return dir_list


if __name__ == '__main__':
    main()