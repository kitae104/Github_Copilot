from pydantic import BaseModel


class NewPost(BaseModel):
    username: str
    content: str


class NewComment(BaseModel):
    username: str
    content: str


class LikeRequest(BaseModel):
    username: str
