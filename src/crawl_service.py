import logging
import sqlite3
from collections import Counter
from http import HTTPStatus
from typing import List

import requests
from bs4 import BeautifulSoup, PageElement, Comment
from sqlmodel import Session, SQLModel, create_engine, select

from src.models import URLQueueItem, PageInfo, PageWord


class QueueEmptyError(Exception):
    pass


class PageNotFoundError(Exception):
    pass

class RateLimitError(Exception):
    pass

class PageRequestError(Exception):
    pass

class PageParsingError(Exception):
    pass


class CrawlService:
    def __init__(self, db_filename: str | None = None):
        if db_filename is None:
            # Create an in-memory database
            self._engine = create_engine("sqlite:///:memory:")
        else:
            db = sqlite3.connect('db/' + db_filename + '.sqlite3')
            db.close()
            db_uri = f"sqlite:///db/{db_filename}.sqlite3"
            self._engine = create_engine(db_uri)

        # Apply schema (this will not touch existing tables)
        SQLModel.metadata.create_all(bind=self._engine)

        self._session = Session(self._engine)
        self._logger = logging.getLogger()

    def __del__(self):
        self._session.close()

    def get_next_url(self, default: str | None = None) -> URLQueueItem:
        statement = select(URLQueueItem).where(URLQueueItem.done == False).order_by(URLQueueItem.created_at)
        result = self._session.exec(statement)
        url = result.first()
        if url is None:
            if default is not None:
                default_url = URLQueueItem(url=default)
                self._logger.debug(f"Returning default URL: {default_url}")
                self._session.add(default_url)
                self._session.commit()
                return default_url
            else:
                raise QueueEmptyError("Queue is empty and no default given")
        else:
            self._logger.debug(f"Returning db-retrieved URL: {url}")
            return url

    def _tag_visible(self, element: PageElement) -> bool:
        if element.parent.name in ['style', 'script', 'head', 'title', 'meta', '[document]']:
            return False
        if isinstance(element, Comment):
            return False
        return True

    def store_page_info_and_get_links(self, url: URLQueueItem) -> List[URLQueueItem]:
        result = requests.get(url.url)
        if result.status_code == HTTPStatus.NOT_FOUND:
            raise PageNotFoundError(url.url)
        if result.status_code == HTTPStatus.TOO_MANY_REQUESTS:
            raise RateLimitError(url.url)
        if result.status_code != HTTPStatus.OK:
            raise PageRequestError(f"received status {result.status_code} at {url.url}")

        soup = BeautifulSoup(result.content, "html5lib")

        if soup.title.string is not None:
            meta_description = None
            for meta_tag in soup.find_all("meta"):
                if meta_tag.get("name") == "description":
                    meta_description = meta_tag.get("content")

            page_info = PageInfo(url_id=url.id, title=soup.title.string, description=meta_description)
            self._session.add(page_info)

            all_text = soup.findAll(text=True)
            visible_text = filter(self._tag_visible, all_text)
            all_long_words = []
            for text in visible_text:
                stripped = text.strip()
                split_text = stripped.split(' ')
                for word in split_text:
                    if len(word) > 5:
                        all_long_words.append(word)
            word_counter = Counter(all_long_words)

            for word in word_counter.most_common(25):
                self._session.add(PageWord(word=word[0], page=page_info))

            self._logger.debug(f"Storing page: {page_info}")
            self._session.commit()
        else:
            raise PageParsingError("No page title found")

        links = []
        for a_tag in soup.find_all('a'):
            link = a_tag.get('href')

            if link is None:
                continue

            link_split = link.split(":")
            if link_split is not None and link_split[0] == "http" or link_split[0] == "https":
                links.append(URLQueueItem(url=link, parent_id=url.id))
        self._logger.debug(f"Found {len(links)} links at {url.url}")
        return links


    def store_unique_page_links(self, urls: List[URLQueueItem]) -> None:
        for link in urls:
            search_url = select(URLQueueItem).where(URLQueueItem.url == link.url)
            result = self._session.exec(search_url)
            if result.first() is None:
                self._session.add(link)
                self._session.commit()
            else:
                self._logger.debug(f"{link.url} already exists in queue, skipping")

    def mark_as_done(self, url: URLQueueItem) -> None:
        self._logger.debug(f"Marking as done: {url.url} ({url.id})")
        url.done = True
        self._session.add(url)
        self._session.commit()

    def get_all_page_infos(self) -> List[PageInfo]:
        statement = select(PageInfo)
        result = self._session.exec(statement)
        return [page_info for page_info in result.all()]
