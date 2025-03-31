from datetime import datetime, timezone
from functools import partial
from typing import Optional

from sqlmodel import SQLModel, Field


class URLQueueItem(SQLModel, table=True):
    __tablename__ = "queue"
    id: Optional[int] = Field(default=None, primary_key=True)
    url: str
    parent_id: Optional[int] = Field(default=None, nullable=True)
    done: bool = Field(default=False, nullable=False)
    created_at: datetime = Field(default=datetime.now(timezone.utc), nullable=False)
    last_edited: datetime = Field(default_factory=partial(datetime.now, timezone.utc), nullable=False)


class PageInfo(SQLModel, table=True):
    __tablename__ = "pages"
    id: Optional[int] = Field(default=None, primary_key=True)
    url_id: int = Field(foreign_key="queue.id")
    title: str = Field(nullable=False)
    created_at: datetime = Field(default=datetime.now(timezone.utc), nullable=False)
