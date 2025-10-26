#!/usr/bin/env python3
"""Fuzzy matching and name processing utilities for TPDB.

This module contains pure Python logic for matching poster names to media
files using fuzzy string matching. It is decoupled from CLI/UI presentation
layers to improve testability and maintainability.
"""

import os
import re
import string

from rapidfuzz import fuzz


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
        # Use token_set_ratio as a good replacement for partial_token_sort_ratio
        score = fuzz.token_set_ratio(norm_poster, norm_candidate)
        if score > best_score:
            best_match, best_score = candidate, score
    return best_match, best_score
