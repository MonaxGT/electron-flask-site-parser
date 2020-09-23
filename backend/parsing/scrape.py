import re
from datetime import datetime
from collections import namedtuple
from itertools import chain
from typing import List
from bs4 import BeautifulSoup
from bs4.element import Tag


Message = namedtuple("Message", ("text", "date", "username"))
_Message_html = namedtuple("_Message_html", ("message_tree", "text"))


class MessageScraper:
    OMIT_HTML_PATTERN = r"(?<=>)[^<]+"

    def get_messages(self, content, search_term: str) -> List[Message]:
        soup = BeautifulSoup(content, "html.parser")
        messages = self.acquire_messages(soup)
        messages_html = (
            _Message_html(msg, self.acquire_msg_text(msg)) for msg in messages
        )
        searched_messages = filter(
            self._check_for_search_term(search_term), messages_html
        )
        return (self.formalize_message(msg) for msg in searched_messages)

    @classmethod
    def formalize_message(cls, msg_html: _Message_html):
        msg_text = msg_html.text
        msg_date = cls.acquire_date(msg_html.message_tree)
        msg_author = cls.acquire_author(msg_html.message_tree)
        return Message(text=msg_text, date=msg_date, username=msg_author)

    @classmethod
    def omit_html_tags(cls, html: Tag) -> str:
        html_string = str(html)
        matches = re.finditer(cls.OMIT_HTML_PATTERN, html_string)
        msg = " ".join(match.group(0).strip() for match in matches)
        return msg

    @staticmethod
    def _check_for_search_term(search_term: str):
        def contain_search_term(msg_html: _Message_html):
            return search_term.lower() in msg_html.text.lower()

        return contain_search_term

    @staticmethod
    def acquire_messages(page: Tag):
        raise NotImplementedError

    @classmethod
    def acquire_msg_text(cls, msg_tree: Tag) -> str:
        raise NotImplementedError

    @staticmethod
    def acquire_date(msg_tree: Tag):
        raise NotImplementedError

    @staticmethod
    def acquire_author(msg_tree: Tag):
        raise NotImplementedError


class BHFScraper(MessageScraper):
    @staticmethod
    def acquire_messages(page: Tag):
        return page.findAll("article", {"class": "message"})

    @classmethod
    def acquire_msg_text(cls, msg_tree: Tag) -> str:
        msg_block = msg_tree.find("div", {"class": "bbWrapper"})
        quotes = msg_block.findAll("blockquote")
        for quote in quotes:
            quote.extract()
        return cls.omit_html_tags(msg_block)

    @staticmethod
    def acquire_date(msg_tree: Tag):
        datetime_str = msg_tree.find("time")["datetime"]
        return datetime.strptime(datetime_str, "%Y-%m-%dT%H:%M:%S%z")

    @staticmethod
    def acquire_author(msg_tree: Tag):
        return (
            msg_tree.find("h4", {"class": "message-name"})
            .find("a", {"class": re.compile("^username")})
            .string
        )


class LolzScraper(MessageScraper):
    @staticmethod
    def acquire_messages(page: Tag):
        messages = page.findAll("li", {"class": "message"})
        comments = page.findAll("li", {"class": "comment"})
        return chain(messages, comments)

    @classmethod
    def acquire_msg_text(cls, msg_tree: Tag) -> str:
        msg_block = msg_tree.find("blockquote", {"class": "messageText"})
        return cls.omit_html_tags(msg_block).replace('"', '')

    @staticmethod
    def acquire_date(msg_tree: Tag):
        datetime_str = msg_tree.find("span", {"class": "DateTime"})["title"]
        # Aug 22, 2020 at 10:30 PM
        return datetime.strptime(datetime_str, "%b %d, %Y at %I:%M %p")

    @staticmethod
    def acquire_author(msg_tree: Tag):
        return msg_tree["data-author"]


if __name__ == "__main__":
    from pprint import pprint
    import cfscrape

    link = "https://lolz.guru/threads/1810076/"
    search_term = "Спасибо"

    cfscraper = cfscrape.create_scraper()
    content = cfscraper.get(link).content

    scraper = LolzScraper()
    msgs = scraper.get_messages(content, search_term)
    pprint(list(msgs))
