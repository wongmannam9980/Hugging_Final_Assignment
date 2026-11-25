from math_tools import count_albums

def test_count_albums_deduplicates_within_inclusive_range():
    assert count_albums.invoke({
        "albums": [
            {"title": "Alpha", "year": 1990},
            {"title": "Beta", "year": 2000},
            {"title": "Beta", "year": 2000},
            {"title": "Gamma", "year": 2005},
        ],
        "start_year": 1990,
        "end_year": 2000,
    }) == 2
