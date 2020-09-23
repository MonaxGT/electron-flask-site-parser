import re
import asyncio
from collections import namedtuple
from bs4 import BeautifulSoup
from parsing.session_managers import SessionManager, BHFSessionManager
from parsing.scrape import MessageScraper, BHFScraper, Message
from parsing.exceptions import NoSearchResultsException

from typing import Iterable, List
from bs4.element import Tag


Page = namedtuple('Page', ('link', 'html'))


class Crawler:
    def search(self, search_request: str, *,
               one_page_only=False) -> List[Page]:
        raise NotImplementedError

    def get_result_pages(self, html_page: Tag, one_page_only: bool = False):
        yield html_page
        if not one_page_only:
            while next_page := self._get_next_page_url(html_page):
                yield next_page

    def get_messages(self,
                     page_html: str,
                     search_request: str) -> Iterable[Message]:
        raise NotImplementedError

    def _get_next_page_url(self, html_page: Tag):
        raise NotImplementedError


class AsyncCrawler(Crawler):
    def search(self, search_request: str, *,
               one_page_only=False) -> List[Page]:
        pages = []
        loop = asyncio.get_event_loop()
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


class BHFCrawler(AsyncCrawler):
    def __init__(self, *,
                 session_manager: SessionManager = None,
                 scraper: MessageScraper = None,
                 main_page_link: str = "https://bhf.io"):
        if not session_manager:
            session_manager = BHFSessionManager(main_page_link)
        if not scraper:
            scraper = BHFScraper()

        self.session_manager = session_manager
        self.scraper = scraper
        self.main_page_link = main_page_link

    def get_messages(self,
                     page_html: str,
                     search_request: str) -> Iterable[Message]:
        return self.scraper.get_messages(page_html, search_request)

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
        for page in self.get_result_pages(html_page, one_page_only):
            yield from (
                f"https://bhf.io{link['href']}" for link in
                html_page.find_all("a", {"href": re.compile(r"^/thread")})
            )

    def _get_result_pages(self, html_page: Tag, one_page_only: bool):
        yield html_page
        if not one_page_only:
            while next_page := self._get_next_page_url(html_page):
                yield next_page

    def _get_next_page_url(html_page: Tag):
        return html_page.find("link", {"rel": "next"})
