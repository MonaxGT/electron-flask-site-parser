import re
from urllib.parse import urlencode
import asyncio
from collections import namedtuple
from bs4 import BeautifulSoup
from parsing.session_managers import (
    SessionManager, BHFSessionManager, LolzSessionManager
)
from parsing.scrape import MessageScraper, BHFScraper, LolzScraper, Message
from parsing.exceptions import NoSearchResultsException

from typing import Iterable, List, Iterator
from bs4.element import Tag


Page = namedtuple('Page', ('link', 'html'))


class Crawler:
    def __init__(self,
                 session_manager: SessionManager = None,
                 scraper: MessageScraper = None,
                 main_page_link: str = None):
        self.session_manager = session_manager
        self.scraper = scraper
        self.main_page_link = main_page_link

    def search(self, search_request: str, *,
               one_page_only=False) -> Iterable[Page]:
        raise NotImplementedError

    def get_messages(self,
                     page_html: str,
                     search_request: str) -> Iterable[Message]:
        return self.scraper.get_messages(page_html, search_request)

    def _get_result_pages(self, html_page: Tag, one_page_only: bool = False):
        yield html_page
        if not one_page_only:
            while next_page := self._get_next_page_url(html_page):
                yield next_page

    def _get_next_page_url(self, html_page: Tag):
        raise NotImplementedError


class AsyncCrawler(Crawler):
    def __init__(self,
                 session_manager: SessionManager = None,
                 scraper: MessageScraper = None,
                 main_page_link: str = None):
        super().__init__(session_manager, scraper, main_page_link)

    def search(self, search_request: str, *,
               one_page_only=False) -> List[Page]:
        pages = []
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(
            self._search_async(search_request,
                               pages,
                               one_page_only)
        )
        return pages

    async def _search_async(self,
                            search_request: str,
                            pages: List[Page],
                            one_page_only):
        raise NotImplementedError


class GoogleCrawler(Crawler):
    MAX_RESULTS = 1_000_000
    RESULTS_PER_PAGE = 10

    @classmethod
    def get_results(cls, search_request: str, one_page_only):
        url_data = {
            'hl': 'en',
            'q': f'"{search_request}"'
        }
        session_manager = SessionManager()

        if one_page_only:
            url_data.update({'start': 0})
            yield from cls._get_links(url_data, session_manager)
        else:
            for result_counter in range(0, cls.MAX_RESULTS,
                                        cls.RESULTS_PER_PAGE):
                url_data.update({'start': result_counter})
                yield from cls._get_links(url_data, session_manager)

    @staticmethod
    def _get_links(url_data, session_manager):
        url = f'https://google.com/search?{urlencode(url_data)}+site%3Alolz.guru'   # noqa: E501
        google_html = session_manager.get_page(url)
        google_page = BeautifulSoup(google_html, 'html.parser')
        return (res.find('a')['href'] for res in
                google_page.find_all('div', {'class': 'r'}))


class BHFCrawler(AsyncCrawler):
    def __init__(self, *,
                 session_manager: SessionManager = None,
                 scraper: MessageScraper = None,
                 main_page_link: str = "https://bhf.io"):
        if not session_manager:
            session_manager = BHFSessionManager(main_page_link)
        if not scraper:
            scraper = BHFScraper()
        super().__init__(session_manager, scraper, main_page_link)

    async def _search_async(self,
                            search_request: str,
                            pages: List[Page],
                            one_page_only):
        search_results_response = self.session_manager.\
            request_search(search_request)
        search_results = BeautifulSoup(
            search_results_response.content.decode("utf-8"), 'html.parser'
        )
        main_content = search_results\
            .find('div', {'uix_component': 'MainContent'})

        if main_content.find('div', {'class': 'blockMessage'}):
            raise NoSearchResultsException(
                f'Search term "{search_request}": nothing found'
            )

        thread_links = self._get_thread_links(
            search_results, one_page_only
        )
        threads = await self.session_manager.fetch(thread_links)
        pages.extend(Page(url, html) for url, html in threads)

    def _get_thread_links(self, html_page: Tag, one_page_only: bool = False):
        """Get links for threads listed on html page"""
        for page in self._get_result_pages(html_page, one_page_only):
            yield from (
                f"https://bhf.io{link['href']}" for link in
                html_page.find_all("a", {"href": re.compile(r"^/thread")})
            )

    def _get_result_pages(self, html_page: Tag, one_page_only: bool) -> Tag:
        yield html_page
        if not one_page_only:
            while relative_url := self._get_next_page_url(html_page):
                next_page_url = self.main_page_link + relative_url
                html = self.session_manager.get_page(next_page_url)
                yield BeautifulSoup(html, 'html.parser')

    def _get_next_page_url(self, html_page: Tag):
        link_html = html_page.find("link", {"rel": "next"})
        return link_html['href']


class LolzCrawler(Crawler):
    def __init__(self, *,
                 session_manager: SessionManager = None,
                 scraper: MessageScraper = None,
                 main_page_link: str = "https://lolz.guru"):
        if not session_manager:
            session_manager = LolzSessionManager(main_page_link)
        if not scraper:
            scraper = LolzScraper()
        super().__init__(session_manager, scraper, main_page_link)

    def search(self, search_request: str, *,
               one_page_only=False) -> Iterator[Page]:
        for url in GoogleCrawler.get_results(search_request, one_page_only):
            if 'forums' in url:
                continue
            html = self.session_manager.get_page(url)
            yield Page(url, html)
