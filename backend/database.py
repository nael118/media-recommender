import sqlite3
import json

DB_PATH = "movies.db"


def get_connection():
    return sqlite3.connect(DB_PATH)


def create_table(conn):
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS movies (
            id INTEGER PRIMARY KEY,
            title TEXT NOT NULL,
            release_date TEXT,
            rating REAL,
            genres TEXT,
            keywords TEXT,
            overview TEXT,
            embedding TEXT
        )
    """)
    conn.commit()

def create_books_table(conn):
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS books (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            author TEXT,
            first_publish_year TEXT,
            subjects TEXT,
            description TEXT,
            embedding TEXT
        )
    """)
    conn.commit()

def create_liked_items_table(conn):
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS liked_items (
            id TEXT NOT NULL,
            media_type TEXT NOT NULL,
            title TEXT NOT NULL,
            PRIMARY KEY (id, media_type)
        )
    """)
    conn.commit()

def add_liked_item(conn, item_id, media_type, title):
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR IGNORE INTO liked_items (id, media_type, title)
        VALUES (?, ?, ?)
    """, (str(item_id), media_type, title))
    conn.commit()


def remove_liked_item(conn, item_id, media_type):
    cursor = conn.cursor()
    cursor.execute("""
        DELETE FROM liked_items WHERE id = ? AND media_type = ?
    """, (str(item_id), media_type))
    conn.commit()


def get_liked_items(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT id, media_type, title FROM liked_items")
    return cursor.fetchall()

def save_book(conn, work_key, book, embedding):
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR REPLACE INTO books
            (id, title, author, first_publish_year, subjects, description, embedding)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        work_key,
        book.title,
        book.author,
        str(book.first_publish_year),
        json.dumps(book.subjects),
        book.description,
        json.dumps(embedding.tolist())
    ))
    conn.commit()


def save_movie(conn, movie, embedding):
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR REPLACE INTO movies
            (id, title, release_date, rating, genres, keywords, overview, embedding)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        movie.tmdb_id,
        movie.title,
        movie.release_date,
        movie.rating,
        json.dumps(movie.genres),
        json.dumps(movie.keywords),
        movie.overview,
        json.dumps(embedding.tolist())
    ))
    conn.commit()


def get_movie_count(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM movies")
    return cursor.fetchone()[0]

def get_movie_by_title(conn, title):
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, embedding FROM movies WHERE title = ?", (title,))
    return cursor.fetchone()


def get_book_by_title(conn, title):
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, embedding FROM books WHERE title = ?", (title,))
    return cursor.fetchone()