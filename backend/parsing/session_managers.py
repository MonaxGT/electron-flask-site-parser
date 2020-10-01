import base64
import asyncio
import aiohttp
import requests
from requests import Session, Response
from bs4 import BeautifulSoup
from bs4.element import Tag
from search_engine_scraper import server
from parsing.exceptions import ServerIsDownException
from secrets import lolz_login, lolz_password
from typing import Iterable


class SessionManager:
    def __init__(self, cookies=None):
        self.cookies = cookies if cookies else {}
        self.server = server

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

    def post(self, url, **kwargs) -> Response:
        return requests.post(url, cookies=self.cookies, **kwargs)

    def get(self, url, **kwargs) -> Response:
        for i in range(1, 21):
            try:
                proxy = next(self.server.proxy_pool)
                resp = requests.get(url, cookies=self.cookies,
                                    proxies={'http': proxy},
                                    **kwargs)
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
        self.authenticate(lolz_login, lolz_password)

    def authenticate(self, login: str, password: str):
        self.cookies = {
            'G_ENABLED_IDPS': 'google',
            'xf_market_currency': 'usd'
        }
        self._get_df_id()
        self._get_xf_session(login, password)
        self._get_xf_user(login, password)

    def _get_df_id(self):
        script_resp = self.get('https://lolz.guru/process-qv9ypsgmv9.js')
        script = script_resp.content.decode('utf8')
        secret_str = eval(script[349:524])
        df_id = base64.b64decode(secret_str).decode()
        self.cookies['df_id'] = df_id

    def _get_xf_session(self, login: str, password: str):
        resp = self.get('https://lolz.guru/login/login',
                        params={'login': login,
                                'password': password,
                                'stopfuckingbrute1337': '1'})
        self.cookies['xf_session'] = resp.cookies['xf_session']

    def _get_xf_user(self, login: str, password: str):
        resp = self.post('https://lolz.guru/login/login',
                         params={'login': login,
                                 'password': password,
                                 'remember': '1',
                                 'stopfuckingbrute1337': '1'})
        self.cookies['xf_session'] = resp.cookies.get('xf_session')
        self.cookies['xf_user'] = resp.cookies.get('xf_user')
        self.cookies['xf_logged_in'] = '1'
