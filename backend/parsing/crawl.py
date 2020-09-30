import re
import requests
from urllib.parse import urlencode
import asyncio
from collections import namedtuple
from bs4 import BeautifulSoup
from parsing.session_managers import (
    SessionManager, BHFSessionManager, LolzSessionManager
)
from parsing.scrape import MessageScraper, BHFScraper, LolzScraper, Message
from parsing.exceptions import NoSearchResultsException
from utils.patching.patch_search_engine_scraper import (
    patch_serve_search_engines
)
from utils.context import no_print

from typing import Iterable, List, Iterator
from bs4.element import Tag

patch_serve_search_engines()
with no_print():
    from search_engine_scraper import (
        bing, serve_search_engines, PROXY_USAGE_TIMEOUT
    )


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
               one_page_only) -> Iterable[Page]:
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
               one_page_only, max_pages) -> List[Page]:
        pages = []
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(
            self._search_async(search_request,
                               pages,
                               one_page_only,
                               max_pages)
        )
        return pages

    async def _search_async(self,
                            search_request: str,
                            pages: List[Page],
                            one_page_only: bool,
                            max_pages: int):
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


class BingCrawler(Crawler):
    MAX_PAGES_TO_CRAWL = 100
    server = serve_search_engines()

    @classmethod
    def get_results(cls, search_request: str, one_page_only, max_pages):
        with no_print():
            engine = cls.Engine(cls.server)
            return engine.search(search_request, one_page_only, max_pages)

    class Engine(bing):
        def search(self, query: str, one_page_only: bool, max_pages: int):
            """
            Queries the search_engine for the specified query
            """
            url = self.text_query_encoding(query)
            page = self.serve_engine.get_page(url)
            yield from self._get_links(page)
            if not one_page_only:
                page_num = 1
                while page_num <= max_pages:
                    url = self._get_next_page_url(page)
                    if not url:
                        break
                    yield from self._get_links(page)
                    page = self.serve_engine.get_page(url)
                    page_num += 1

        def _get_links(self, page: requests.Response):
            links = self.text_result_parsing(page)
            if not links:
                self.change_proxies()
                links = self.text_result_parsing(page)
            return links

        def _get_next_page_url(self, page_resp: requests.Response):
            if page_resp == '<html>':
                return ''
            page_str = page_resp.content.decode(page_resp.encoding)
            page_html = BeautifulSoup(page_str, 'html.parser')
            a = page_html.find('a', {'class': 'sb_pagN'})
            if a is None:
                return ''
            if 'sb_inactP' not in a['class']:
                return 'https://www.bing.com' + a['href']
            else:
                return ''

        def change_proxies(self):
            self.time_difference = PROXY_USAGE_TIMEOUT
            self.serve_engine.proxy_check()


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
                            one_page_only: bool,
                            max_pages: int):
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
            search_results, one_page_only, max_pages
        )
        threads = await self.session_manager.fetch(thread_links)
        pages.extend(Page(url, html) for url, html in threads)

    def _get_thread_links(self, html_page: Tag, one_page_only: bool,
                          max_pages):
        """Get links for threads listed on html page"""
        for page in self._get_result_pages(html_page, one_page_only,
                                           max_pages):
            yield from (
                f"https://bhf.io{link['href']}" for link in
                html_page.find_all("a", {"href": re.compile(r"^/thread")})
            )

    def _get_result_pages(self, html_page: Tag,
                          one_page_only: bool, max_pages: int) -> Tag:
        yield html_page
        if not one_page_only:
            page_num = 1
            while page_num <= max_pages:
                relative_url = self._get_next_page_url(html_page)
                if not relative_url:
                    break
                next_page_url = self.main_page_link + relative_url
                html = self.session_manager.get_page(next_page_url)
                yield BeautifulSoup(html, 'html.parser')

    def _get_next_page_url(self, html_page: Tag):
        link_html = html_page.find("link", {"rel": "next"})
        return link_html['href']


class LolzCrawler(Crawler):
    SEARCH_PREFIX = 'site:lolz.guru'

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
               one_page_only,
               max_pages) -> Iterator[Page]:
        for url in BingCrawler.get_results(
                f'{self.SEARCH_PREFIX} {search_request}',
                one_page_only=one_page_only,
                max_pages=max_pages):
            if 'forums' in url:
                continue
            html = self.session_manager.get_page(url)
            if not html:
                return
            yield Page(url, html)
