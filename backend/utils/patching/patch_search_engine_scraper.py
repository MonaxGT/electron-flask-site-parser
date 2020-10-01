import os
import time
import random
import requests
import search_engine_scraper
from search_engine_scraper import (
    serve_search_engines, server, PROXY_USAGE_TIMEOUT
)


def patch_serve_search_engines():
    _patch_load_user_agents()
    _patch_get_page()


def _patch_load_user_agents():
    def load_user_agents(self, uafile: str):
        """
        Get User-Agents from a file
        """
        uas = []

        with open(uafile, 'rb') as uaf:
            for ua in uaf.readlines():
                if ua:
                    uas.append(ua.strip())
        random.shuffle(uas)
        return uas

    serve_search_engines.load_user_agents = load_user_agents
    bind(server, load_user_agents, 'load_user_agents')

    user_agents_filename = os.path.join(
        os.path.dirname(search_engine_scraper.__file__),
        'user_agents.txt'
    )
    server.user_agents = server.load_user_agents(uafile=user_agents_filename)


def _patch_get_page():
    def get_page(self, url: str):
        """
        'Gets' the specified URL through requests
        Checks if proxies are being used for 15 minutes, if so it fetches
        20 new proxies. proxy_pool provides a pool of proxies through which
        requests are to be made

        """
        self.new_proxy_time = time.time()
        if self.new_proxy_time-self.old_proxy_time >= PROXY_USAGE_TIMEOUT:
            self.proxy_check()
        else:
            self.proxy_pool = self.proxy_pool

        for i in range(1, 21):
            try:
                proxy = next(self.proxy_pool)
                ua = random.choice(self.user_agents)
                headers = {
                    "Connection": "close",
                    "User-Agent": ua
                }
                page = requests.get(
                    url, proxies={"http": proxy}, headers=headers
                )
                if page.status_code == 200:
                    break
            except Exception:
                # Skip if chosen proxy failed
                page = None
        return page

    serve_search_engines.get_page = get_page
    bind(server, get_page, 'get_page')


def bind(instance, func, as_name):
    setattr(instance, as_name, func.__get__(instance, instance.__class__))
