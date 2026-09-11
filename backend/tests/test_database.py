import sqlite3
import database


def get_test_connection():
    return sqlite3.connect(":memory:")


def test_add_and_get_liked_items():
    conn = get_test_connection()
    database.create_liked_items_table(conn)

    database.add_liked_item(conn, 123, "movie", "Her")
    items = database.get_liked_items(conn)

    assert items == [("123", "movie", "Her")]


def test_add_liked_item_ignores_duplicates():
    conn = get_test_connection()
    database.create_liked_items_table(conn)

    database.add_liked_item(conn, 123, "movie", "Her")
    database.add_liked_item(conn, 123, "movie", "Her")

    items = database.get_liked_items(conn)
    assert len(items) == 1


def test_remove_liked_item():
    conn = get_test_connection()
    database.create_liked_items_table(conn)

    database.add_liked_item(conn, 123, "movie", "Her")
    database.remove_liked_item(conn, 123, "movie")

    assert database.get_liked_items(conn) == []


def test_seen_items_same_id_different_media_type_are_distinct():
    conn = get_test_connection()
    database.create_seen_items_table(conn)

    database.add_seen_item(conn, "1", "movie", "Movie Called 1")
    database.add_seen_item(conn, "1", "book", "Book Called 1")

    items = database.get_seen_items(conn)
    assert len(items) == 2