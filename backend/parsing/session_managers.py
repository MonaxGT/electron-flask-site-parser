import asyncio
import aiohttp
import requests
from requests import Session, Response
from bs4 import BeautifulSoup
from bs4.element import Tag
from search_engine_scraper import serve_search_engines
from parsing.exceptions import ServerIsDownException

from typing import Iterable


class SessionManager:
    def __init__(self, cookies=None):
        self.cookies = cookies if cookies else {}
        self.server = serve_search_engines()

    async def afetch(self, url: str, session):
        proxy = next(self.server.proxy_pool)
        async with session.get(url, proxy=proxy) as response:
            html = await response.read()
            return url, html

    async def fetch(self, urls: Iterable[str]):
        async with aiohttp.ClientSession(headers=self.headers,
                                         cookies=self.cookies) as aiosession:
            tasks = [self.afetch(url, aiosession) for url in urls]
            return await asyncio.gather(*tasks)

    def get(self, url) -> Response:
        for i in range(1, 21):
            try:
                proxy = next(self.server.proxy_pool)
                resp = requests.get(url, cookies=self.cookies,
                                    proxies={'http': proxy})
                if resp.status_code == 200:
                    break
            except Exception:
                resp = None
        return resp

    def get_page(self, url: str) -> str:
        response = self.get(url)
        if not response:
            return ''
        try:
            return response.content.decode(response.encoding)
        except UnicodeDecodeError:
            return ''

    def request_search(self, search_request: str) -> Response:
        raise NotImplementedError


class BHFSessionManager(SessionManager):
    def __init__(self, main_page_link):
        self.main_page_link = main_page_link
        self.cookies = {
            "xf_csrf": "dEw01PbIXwb9JX9y",
            "xf_session": "HP4zNRSYieD93UeQ6o7KtsHms6fGa-GV",
            "xf_tfa_trust": "ZJ9squSlivYkeuPslJGzAXQpyg5mWb_7",
            "xf_user": "359935%2CBiYBP9OW3BWpq3Bii4-5-66hwAiE47H00mGAl6Dk",
            "cf_data": "ab1128120942ac322727e50b5d10f788",
            "__cfduid": "d43885b89508e838aa6572a1c81f2bf4d1599119586",
            "cf_clearance": "",
        }
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 6.3; Win64; x64; rv:79.0) "
                          "Gecko/20100101 Firefox/79.0",
        }

    def request_search(self, search_request: str) -> Response:
        with Session() as session:
            session.headers.update(self.headers)
            main_page_response = session.get(
                self.main_page_link, cookies=self.cookies)
            if main_page_response.status_code < 500:
                main_page = BeautifulSoup(
                    main_page_response.content, "html.parser"
                )
                xfToken = self._find_xfToken(main_page)
                data = {"keywords": search_request, "_xfToken": xfToken}
                return session.post(
                    f"{self.main_page_link}/search/search",
                    cookies=self.cookies,
                    data=data
                )
            else:
                raise ServerIsDownException(
                    f'{self.main_page_link} server is down'
                )

    def _find_xfToken(self, html_page: Tag):
        token = html_page.find("input", {"name": "_xfToken"})
        if not token:
            raise ValueError("You are unauthorized!")
        return token['value']


class LolzSessionManager(SessionManager):
    def __init__(self, main_page_link):
        super().__init__()
        self.main_page_link = main_page_link
        self.cookies = {
            "xf_session": "023f2a4242ca875122dcc5aac985c259",
            "xf_market_currency": "usd",
            "G_ENABLED_IDPS": "google",
            "df_id": "8fc954a8a7f071d56e1abbe7505d7b31",
        }
