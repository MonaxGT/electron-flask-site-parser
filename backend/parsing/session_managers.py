import asyncio
import aiohttp
from requests import Session, Response
from bs4 import BeautifulSoup
from bs4.element import Tag
from parsing.exceptions import ServerIsDownException

from typing import Iterable


class SessionManager:
    async def afetch(self, url: str, session):
        async with session.get(url) as response:
            html = await response.read()
            return url, html

    async def fetch(self, urls: Iterable[str]):
        async with aiohttp.ClientSession(headers=self.headers,
                                         cookies=self.cookies) as aiosession:
            tasks = [self.afetch(url, aiosession) for url in urls]
            return await asyncio.gather(*tasks)

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

    def get(self, relative_url) -> Response:
        url = self.main_page_link + relative_url
        with Session() as session:
            return session.get(url, cookies=self.cookies)

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
