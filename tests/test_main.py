from tpdb.main import normalize_name


def test_normalize_name():
    assert normalize_name("The Movie (2022)") == "the movie"
    assert normalize_name("The Movie. set by Me") == "the movie"
    assert normalize_name("The_Movie") == "themovie"
    assert normalize_name("The-Movie") == "themovie"
    assert normalize_name("The Movie!") == "the movie"
