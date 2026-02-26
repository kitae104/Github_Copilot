import os
import sqlite3

BASE_DIR = os.path.dirname(__file__)
DB_PATH = os.path.join(BASE_DIR, "sns_api.db")


def init_db():
    # 애플리케이션 시작 시 DB를 항상 초기화(기존 파일 삭제)
    if os.path.exists(DB_PATH):
        try:
            os.remove(DB_PATH)
        except OSError:
            pass

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute(
        """
        CREATE TABLE posts (
            id TEXT PRIMARY KEY,
            username TEXT NOT NULL,
            content TEXT NOT NULL,
            createdAt TEXT NOT NULL,
            updatedAt TEXT,
            likes INTEGER DEFAULT 0,
            commentsCount INTEGER DEFAULT 0
        )
        """
    )

    c.execute(
        """
        CREATE TABLE comments (
            id TEXT PRIMARY KEY,
            postId TEXT NOT NULL,
            username TEXT NOT NULL,
            content TEXT NOT NULL,
            createdAt TEXT NOT NULL,
            updatedAt TEXT
        )
        """
    )

    c.execute(
        """
        CREATE TABLE likes (
            postId TEXT NOT NULL,
            username TEXT NOT NULL,
            PRIMARY KEY(postId, username)
        )
        """
    )

    conn.commit()
    conn.close()


def get_conn():
    return sqlite3.connect(DB_PATH, check_same_thread=False)
