import random
from search_engine_scraper import serve_search_engines


def patch_serve_search_engines():
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
