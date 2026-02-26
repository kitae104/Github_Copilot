import uuid
from datetime import datetime


def iso_now():
    return datetime.utcnow().isoformat() + "Z"


def row_to_post(row):
    return {
        "id": row[0],
        "username": row[1],
        "content": row[2],
        "createdAt": row[3],
        "updatedAt": row[4],
        "likes": row[5],
        "commentsCount": row[6],
    }


def row_to_comment(row):
    return {
        "id": row[0],
        "postId": row[1],
        "username": row[2],
        "content": row[3],
        "createdAt": row[4],
        "updatedAt": row[5],
    }
