from datetime import datetime, timezone
from functools import partial
from typing import Optional, List

from sqlmodel import SQLModel, Field, Relationship


class URLQueueItem(SQLModel, table=True):
    __tablename__ = "urls"
    id: Optional[int] = Field(default=None, primary_key=True)
    url: str
    parent_id: Optional[int] = Field(default=None, nullable=True)
    done: bool = Field(default=False, nullable=False)
    created_at: datetime = Field(default=datetime.now(timezone.utc), nullable=False)
    last_edited: datetime = Field(default_factory=partial(datetime.now, timezone.utc), nullable=False)


class PageInfo(SQLModel, table=True):
    __tablename__ = "pages"
    id: Optional[int] = Field(default=None, primary_key=True)
    url_id: int = Field(foreign_key="urls.id")
    title: str = Field(nullable=False)
    description: str = Field(nullable=True)
    words: List["PageWord"] = Relationship(back_populates="page")
    created_at: datetime = Field(default=datetime.now(timezone.utc), nullable=False)

class PageWord(SQLModel, table=True):
    __tablename__ = "words"
    id: Optional[int] = Field(default=None, primary_key=True)
    word: str = Field(nullable=False)
    page_id: int = Field(foreign_key="pages.id")
    page: PageInfo = Relationship(back_populates="words")
