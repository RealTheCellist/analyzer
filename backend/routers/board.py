import sqlite3
import os
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, field_validator

router = APIRouter()

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'board.db')


def _get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _init_db():
    with _get_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS posts (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                category  TEXT    NOT NULL,
                title     TEXT    NOT NULL,
                content   TEXT    NOT NULL,
                created_at TEXT   NOT NULL
            )
        """)
        conn.commit()


_init_db()

VALID_CATEGORIES = {'버그제보', '기능제안', '기타'}


class PostCreate(BaseModel):
    category: str
    title: str
    content: str

    @field_validator('category')
    @classmethod
    def check_category(cls, v: str) -> str:
        if v not in VALID_CATEGORIES:
            raise ValueError(f'category는 {VALID_CATEGORIES} 중 하나여야 합니다')
        return v

    @field_validator('title')
    @classmethod
    def check_title(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError('제목을 입력해주세요')
        if len(v) > 100:
            raise ValueError('제목은 100자 이내로 작성해주세요')
        return v

    @field_validator('content')
    @classmethod
    def check_content(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError('내용을 입력해주세요')
        if len(v) > 2000:
            raise ValueError('내용은 2000자 이내로 작성해주세요')
        return v


def _row_to_dict(row: sqlite3.Row) -> dict:
    return {
        'id': row['id'],
        'category': row['category'],
        'title': row['title'],
        'content': row['content'],
        'created_at': row['created_at'],
    }


@router.get('/posts')
def list_posts(page: int = 1, limit: int = Query(default=20, ge=1, le=100)):
    if page < 1:
        page = 1
    offset = (page - 1) * limit
    with _get_conn() as conn:
        total = conn.execute('SELECT COUNT(*) FROM posts').fetchone()[0]
        rows = conn.execute(
            'SELECT * FROM posts ORDER BY id DESC LIMIT ? OFFSET ?',
            (limit, offset)
        ).fetchall()
    return {
        'total': total,
        'page': page,
        'posts': [_row_to_dict(r) for r in rows],
    }


@router.get('/posts/{post_id}')
def get_post(post_id: int):
    with _get_conn() as conn:
        row = conn.execute('SELECT * FROM posts WHERE id = ?', (post_id,)).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail='게시글을 찾을 수 없습니다')
    return _row_to_dict(row)


@router.post('/posts', status_code=201)
def create_post(body: PostCreate):
    now = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M')
    with _get_conn() as conn:
        cur = conn.execute(
            'INSERT INTO posts (category, title, content, created_at) VALUES (?, ?, ?, ?)',
            (body.category, body.title, body.content, now),
        )
        conn.commit()
        post_id = cur.lastrowid
        row = conn.execute('SELECT * FROM posts WHERE id = ?', (post_id,)).fetchone()
    return _row_to_dict(row)
