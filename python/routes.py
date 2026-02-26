import uuid
import sqlite3
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse

from db import get_conn
from schemas import NewPost, NewComment, LikeRequest
from utils import iso_now, row_to_post, row_to_comment

router = APIRouter(prefix="/api")


@router.get("/posts")
def list_posts():
    conn = get_conn()
    c = conn.cursor()
    c.execute(
        "SELECT id,username,content,createdAt,updatedAt,likes,commentsCount FROM posts ORDER BY createdAt DESC"
    )
    rows = c.fetchall()
    conn.close()
    return [row_to_post(r) for r in rows]


@router.post("/posts", status_code=status.HTTP_201_CREATED)
def create_post(payload: NewPost):
    id_ = str(uuid.uuid4())
    now = iso_now()
    conn = get_conn()
    c = conn.cursor()
    c.execute(
        "INSERT INTO posts (id,username,content,createdAt,likes,commentsCount) VALUES (?,?,?,?,?,?)",
        (id_, payload.username, payload.content, now, 0, 0),
    )
    conn.commit()
    conn.close()
    return {
        "id": id_,
        "username": payload.username,
        "content": payload.content,
        "createdAt": now,
        "updatedAt": None,
        "likes": 0,
        "commentsCount": 0,
    }


@router.get("/posts/{postId}")
def get_post(postId: str):
    conn = get_conn()
    c = conn.cursor()
    c.execute(
        "SELECT id,username,content,createdAt,updatedAt,likes,commentsCount FROM posts WHERE id=?",
        (postId,),
    )
    row = c.fetchone()
    conn.close()
    if not row:
        raise HTTPException(
            status_code=404, detail={"code": 404, "message": "Not found"}
        )
    return row_to_post(row)


@router.patch("/posts/{postId}")
def update_post(postId: str, payload: NewPost):
    now = iso_now()
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT id FROM posts WHERE id=?", (postId,))
    if not c.fetchone():
        conn.close()
        raise HTTPException(
            status_code=404, detail={"code": 404, "message": "Not found"}
        )
    c.execute(
        "UPDATE posts SET username=?, content=?, updatedAt=? WHERE id=?",
        (payload.username, payload.content, now, postId),
    )
    conn.commit()
    c.execute(
        "SELECT id,username,content,createdAt,updatedAt,likes,commentsCount FROM posts WHERE id= ?",
        (postId,),
    )
    row = c.fetchone()
    conn.close()
    return row_to_post(row)


@router.delete("/posts/{postId}", status_code=status.HTTP_204_NO_CONTENT)
def delete_post(postId: str):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT id FROM posts WHERE id=?", (postId,))
    if not c.fetchone():
        conn.close()
        raise HTTPException(
            status_code=404, detail={"code": 404, "message": "Not found"}
        )
    c.execute("DELETE FROM posts WHERE id=?", (postId,))
    c.execute("DELETE FROM comments WHERE postId=?", (postId,))
    c.execute("DELETE FROM likes WHERE postId=?", (postId,))
    conn.commit()
    conn.close()
    return JSONResponse(status_code=status.HTTP_204_NO_CONTENT, content=None)


@router.get("/posts/{postId}/comments")
def list_comments(postId: str):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT id FROM posts WHERE id= ?", (postId,))
    if not c.fetchone():
        conn.close()
        raise HTTPException(
            status_code=404, detail={"code": 404, "message": "Not found"}
        )
    c.execute(
        "SELECT id,postId,username,content,createdAt,updatedAt FROM comments WHERE postId=? ORDER BY createdAt ASC",
        (postId,),
    )
    rows = c.fetchall()
    conn.close()
    return [row_to_comment(r) for r in rows]


@router.post("/posts/{postId}/comments", status_code=status.HTTP_201_CREATED)
def create_comment(postId: str, payload: NewComment):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT id FROM posts WHERE id= ?", (postId,))
    if not c.fetchone():
        conn.close()
        raise HTTPException(
            status_code=404, detail={"code": 404, "message": "Not found"}
        )
    id_ = str(uuid.uuid4())
    now = iso_now()
    c.execute(
        "INSERT INTO comments (id,postId,username,content,createdAt) VALUES (?,?,?,?,?)",
        (id_, postId, payload.username, payload.content, now),
    )
    c.execute(
        "UPDATE posts SET commentsCount = commentsCount + 1 WHERE id=?", (postId,)
    )
    conn.commit()
    conn.close()
    return {
        "id": id_,
        "postId": postId,
        "username": payload.username,
        "content": payload.content,
        "createdAt": now,
        "updatedAt": None,
    }


@router.get("/posts/{postId}/comments/{commentId}")
def get_comment(postId: str, commentId: str):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT id FROM posts WHERE id= ?", (postId,))
    if not c.fetchone():
        conn.close()
        raise HTTPException(
            status_code=404, detail={"code": 404, "message": "Not found"}
        )
    c.execute(
        "SELECT id,postId,username,content,createdAt,updatedAt FROM comments WHERE id=? AND postId=?",
        (commentId, postId),
    )
    row = c.fetchone()
    conn.close()
    if not row:
        raise HTTPException(
            status_code=404, detail={"code": 404, "message": "Not found"}
        )
    return row_to_comment(row)


@router.patch("/posts/{postId}/comments/{commentId}")
def update_comment(postId: str, commentId: str, payload: NewComment):
    now = iso_now()
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT id FROM comments WHERE id=? AND postId=?", (commentId, postId))
    if not c.fetchone():
        conn.close()
        raise HTTPException(
            status_code=404, detail={"code": 404, "message": "Not found"}
        )
    c.execute(
        "UPDATE comments SET username=?, content=?, updatedAt=? WHERE id=? AND postId=?",
        (payload.username, payload.content, now, commentId, postId),
    )
    conn.commit()
    c.execute(
        "SELECT id,postId,username,content,createdAt,updatedAt FROM comments WHERE id=? AND postId=?",
        (commentId, postId),
    )
    row = c.fetchone()
    conn.close()
    return row_to_comment(row)


@router.delete(
    "/posts/{postId}/comments/{commentId}", status_code=status.HTTP_204_NO_CONTENT
)
def delete_comment(postId: str, commentId: str):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT id FROM comments WHERE id=? AND postId=?", (commentId, postId))
    if not c.fetchone():
        conn.close()
        raise HTTPException(
            status_code=404, detail={"code": 404, "message": "Not found"}
        )
    c.execute("DELETE FROM comments WHERE id=? AND postId=?", (commentId, postId))
    c.execute(
        "UPDATE posts SET commentsCount = commentsCount - 1 WHERE id=?", (postId,)
    )
    conn.commit()
    conn.close()
    return JSONResponse(status_code=status.HTTP_204_NO_CONTENT, content=None)


@router.post("/posts/{postId}/likes", status_code=status.HTTP_201_CREATED)
def like_post(postId: str, payload: LikeRequest):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT id FROM posts WHERE id= ?", (postId,))
    if not c.fetchone():
        conn.close()
        raise HTTPException(
            status_code=404, detail={"code": 404, "message": "Not found"}
        )
    try:
        c.execute(
            "INSERT INTO likes (postId, username) VALUES (?,?)",
            (postId, payload.username),
        )
    except sqlite3.IntegrityError:
        conn.close()
        raise HTTPException(
            status_code=400, detail={"code": 400, "message": "Bad request"}
        )
    c.execute("UPDATE posts SET likes = likes + 1 WHERE id=?", (postId,))
    c.execute("SELECT likes FROM posts WHERE id=?", (postId,))
    total = c.fetchone()[0]
    conn.commit()
    conn.close()
    return {"postId": postId, "username": payload.username, "totalLikes": total}


@router.delete("/posts/{postId}/likes", status_code=status.HTTP_204_NO_CONTENT)
def unlike_post(postId: str, payload: LikeRequest):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT id FROM posts WHERE id= ?", (postId,))
    if not c.fetchone():
        conn.close()
        raise HTTPException(
            status_code=404, detail={"code": 404, "message": "Not found"}
        )
    c.execute(
        "SELECT username FROM likes WHERE postId=? AND username= ?",
        (postId, payload.username),
    )
    if not c.fetchone():
        conn.close()
        raise HTTPException(
            status_code=400, detail={"code": 400, "message": "Bad request"}
        )
    c.execute(
        "DELETE FROM likes WHERE postId=? AND username= ?", (postId, payload.username)
    )
    c.execute("UPDATE posts SET likes = likes - 1 WHERE id=?", (postId,))
    conn.commit()
    conn.close()
    return JSONResponse(status_code=status.HTTP_204_NO_CONTENT, content=None)
