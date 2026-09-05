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