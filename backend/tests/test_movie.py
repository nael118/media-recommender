from movie import Movie


def make_movie_data(release_date="2020-01-01", vote_count=100, genre_ids=None, overview="A perfectly reasonable overview of a movie, long enough to pass the filter."):
    return {
        "id": 1,
        "title": "Test Movie",
        "release_date": release_date,
        "vote_average": 7.5,
        "vote_count": vote_count,
        "genre_ids": genre_ids or [18],
        "overview": overview
    }


def make_keywords_data(names=None):
    names = names if names is not None else ["loneliness", "technology", "artificial intelligence"]
    return {"keywords": [{"name": name} for name in names]}


def test_valid_movie_is_accepted():
    movie = Movie.from_tmdb_result(make_movie_data(), make_keywords_data())
    assert movie is not None
    assert movie.title == "Test Movie"


def test_unreleased_movie_is_rejected():
    future_date = "2099-01-01"
    movie = Movie.from_tmdb_result(make_movie_data(release_date=future_date), make_keywords_data())
    assert movie is None


def test_movie_with_no_release_date_is_rejected():
    movie = Movie.from_tmdb_result(make_movie_data(release_date=""), make_keywords_data())
    assert movie is None


def test_low_vote_count_is_rejected():
    movie = Movie.from_tmdb_result(make_movie_data(vote_count=5), make_keywords_data())
    assert movie is None


def test_too_few_keywords_is_rejected():
    movie = Movie.from_tmdb_result(make_movie_data(), make_keywords_data(names=["one"]))
    assert movie is None


def test_stop_keywords_are_filtered_out():
    movie = Movie.from_tmdb_result(make_movie_data(), make_keywords_data(names=["loneliness", "technology", "aftercreditsstinger"]))
    assert movie is not None
    assert "aftercreditsstinger" not in movie.keywords
    assert "loneliness" in movie.keywords


def test_short_overview_is_rejected():
    movie = Movie.from_tmdb_result(make_movie_data(overview="Too short."), make_keywords_data())
    assert movie is None