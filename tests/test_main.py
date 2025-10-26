import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from tpdb import normalize_name


def test_normalize_name():
    assert normalize_name("The Movie (2022)") == "the movie"
    assert normalize_name("The Movie. set by Me") == "the movie"
    assert normalize_name("The_Movie") == "themovie"
    assert normalize_name("The-Movie") == "themovie"
    assert normalize_name("The Movie!") == "the movie"
