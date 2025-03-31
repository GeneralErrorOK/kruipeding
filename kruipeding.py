import argparse
import signal
import threading
import logging

from src.crawler import crawler
from src.utils import is_valid_url

STOP = threading.Event()


def signalhandler(sig, frame):
    STOP.set()


def main(args: argparse.Namespace):
    if not is_valid_url(args.url):
        print("Invalid URL... It should be in the format: https://www.website.com")
        return
    crawler(args.url, args.db_name, args.sleep, STOP)


if __name__ == "__main__":
    signal.signal(signal.SIGINT, signalhandler)
    signal.signal(signal.SIGTERM, signalhandler)

    parser = argparse.ArgumentParser(
        prog='Kruipeding',
        description='A creepy crawler. Just for the fun.')
    parser.add_argument('url', type=str, help='URL to start the endeavour at')
    parser.add_argument('db_name', type=str, help='Filename for the sqlite database')
    parser.add_argument('-d', '--debug', action='store_true', help='Enable debug mode')
    parser.add_argument('-s', '--sleep', type=float, default=0.5, help='Sleep time in between requests.')
    args = parser.parse_args()

    logging.basicConfig(level=logging.DEBUG if args.debug else logging.INFO,
                        format='%(asctime)s - %(levelname)s (%(module)s, %(processName)s, %(threadName)s): %(message)s')

    main(args)
