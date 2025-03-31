import logging
import threading
import time

from src.crawl_service import CrawlService, QueueEmptyError, PageNotFoundError, PageParsingError, RateLimitError


def crawler(start_url: str, db_name: str, sleep_time: float, stop_event: threading.Event):
    incremental_sleep_time = sleep_time * 10 # Seems a good place to start
    crawl_service = CrawlService(db_name)
    logger = logging.getLogger()
    while not stop_event.is_set():
        try:
            url = crawl_service.get_next_url(start_url)
        except QueueEmptyError as e:
            logger.error(f"Queue is empty: {e}. Quitting.")
            return

        try:
            links = crawl_service.store_page_info_and_get_links(url)
        except PageNotFoundError as e:
            logger.error(f"Server returned a 404 on: {e}")
            crawl_service.mark_as_done(url)
            time.sleep(sleep_time)
            continue
        except RateLimitError as e:
            logger.error(f"Rate limit exceeded: {e}. Waiting for {incremental_sleep_time} seconds.")
            time.sleep(incremental_sleep_time)
            incremental_sleep_time *= 2
            continue
        except PageParsingError as e:
            logger.error(f"Could not parse page: {e}")
            crawl_service.mark_as_done(url)
            time.sleep(sleep_time)
            continue

        incremental_sleep_time = sleep_time * 10
        crawl_service.store_unique_page_links(links)
        crawl_service.mark_as_done(url)
        time.sleep(sleep_time)
