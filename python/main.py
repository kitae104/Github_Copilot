from app import create_app

app = create_app()

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
import os
import sqlite3
import uuid
from datetime import datetime
import yaml

from fastapi import FastAPI, APIRouter, HTTPException, status, Request
from fastapi.responses import JSONResponse, PlainTextResponse, HTMLResponse
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel


# 파일 경로
BASE_DIR = os.path.dirname(__file__)
DB_PATH = os.path.join(BASE_DIR, "sns_api.db")
OPENAPI_YAML = os.path.abspath(os.path.join(BASE_DIR, "..", "openapi.yaml"))


def load_openapi_schema():
    with open(OPENAPI_YAML, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


app = FastAPI(docs_url=None, redoc_url=None, openapi_url="/openapi.json")

# CORS: 모든 출처 허용
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup_db():
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


def iso_now():
    return datetime.utcnow().isoformat() + "Z"


# Pydantic 모델 (요청/응답 스키마와 호환되도록 최소한으로 정의)
class NewPost(BaseModel):
    username: str
    content: str


class NewComment(BaseModel):
    username: str
    content: str


class LikeRequest(BaseModel):
    username: str


router = APIRouter(prefix="/api")


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


# 게시물 목록
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


# 게시물 생성
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


# 단일 게시물 조회
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


# 게시물 업데이트
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
        "SELECT id,username,content,createdAt,updatedAt,likes,commentsCount FROM posts WHERE id=?",
        (postId,),
    )
    row = c.fetchone()
    conn.close()
    return row_to_post(row)


# 게시물 삭제
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


# 댓글 목록
@router.get("/posts/{postId}/comments")
def list_comments(postId: str):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT id FROM posts WHERE id=?", (postId,))
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


# 댓글 생성
@router.post("/posts/{postId}/comments", status_code=status.HTTP_201_CREATED)
def create_comment(postId: str, payload: NewComment):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT id FROM posts WHERE id=?", (postId,))
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


# 특정 댓글 조회
@router.get("/posts/{postId}/comments/{commentId}")
def get_comment(postId: str, commentId: str):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT id FROM posts WHERE id=?", (postId,))
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


# 댓글 업데이트
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


# 댓글 삭제
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


# 좋아요 추가
@router.post("/posts/{postId}/likes", status_code=status.HTTP_201_CREATED)
def like_post(postId: str, payload: LikeRequest):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT id FROM posts WHERE id=?", (postId,))
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
        # 이미 좋아요가 존재하면 400
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


# 좋아요 취소
@router.delete("/posts/{postId}/likes", status_code=status.HTTP_204_NO_CONTENT)
def unlike_post(postId: str, payload: LikeRequest):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT id FROM posts WHERE id=?", (postId,))
    if not c.fetchone():
        conn.close()
        raise HTTPException(
            status_code=404, detail={"code": 404, "message": "Not found"}
        )
    c.execute(
        "SELECT username FROM likes WHERE postId=? AND username=?",
        (postId, payload.username),
    )
    if not c.fetchone():
        conn.close()
        raise HTTPException(
            status_code=400, detail={"code": 400, "message": "Bad request"}
        )
    c.execute(
        "DELETE FROM likes WHERE postId=? AND username=?", (postId, payload.username)
    )
    c.execute("UPDATE posts SET likes = likes - 1 WHERE id=?", (postId,))
    conn.commit()
    conn.close()
    return JSONResponse(status_code=status.HTTP_204_NO_CONTENT, content=None)


app.include_router(router)


# OpenAPI 및 Swagger UI 제공 (루트에 Swagger UI 렌더링)
_openapi_schema = None


@app.get("/openapi.yaml", response_class=PlainTextResponse)
def openapi_yaml():
    with open(OPENAPI_YAML, "r", encoding="utf-8") as f:
        return f.read()


@app.get("/", response_class=HTMLResponse)
def root_swagger():
    return get_swagger_ui_html(openapi_url="/openapi.json", title="API Docs")


def custom_openapi():
    global _openapi_schema
    if _openapi_schema is not None:
        return _openapi_schema
    _openapi_schema = load_openapi_schema()
    return _openapi_schema


app.openapi = custom_openapi


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
