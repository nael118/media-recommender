from book import Book


def make_search_result(title="Test Book", authors=None, year=1990):
    return {
        "title": title,
        "author_name": authors or ["Test Author"],
        "first_publish_year": year,
        "key": "/works/OL1W"
    }


def make_work_details(subjects=None, description="A perfectly reasonable description of a book."):
    subjects = subjects if subjects is not None else ["Fiction", "Drama", "Loneliness"]
    return {
        "subjects": subjects,
        "description": description
    }


def test_valid_book_is_accepted():
    book = Book.from_openlibrary_result(make_search_result(), make_work_details())
    assert book is not None
    assert book.title == "Test Book"


def test_too_few_subjects_is_rejected():
    book = Book.from_openlibrary_result(make_search_result(), make_work_details(subjects=["Fiction"]))
    assert book is None


def test_missing_description_is_rejected():
    book = Book.from_openlibrary_result(make_search_result(), make_work_details(description=""))
    assert book is None


def test_dict_shaped_description_is_unwrapped():
    work_details = make_work_details()
    work_details["description"] = {"value": "A description wrapped in a dict, as Open Library sometimes returns.", "type": "/type/text"}
    book = Book.from_openlibrary_result(make_search_result(), work_details)
    assert book is not None
    assert "wrapped in a dict" in book.description


def test_multilanguage_description_keeps_only_first_block():
    work_details = make_work_details(description="English paragraph here.\r\n\r\nParrafo en espanol aqui.")
    book = Book.from_openlibrary_result(make_search_result(), work_details)
    assert book is not None
    assert "English paragraph" in book.description
    assert "espanol" not in book.description