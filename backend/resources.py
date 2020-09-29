from flask_restful import Resource, reqparse, abort
from parsing.parse import parse_messages
from parsing.crawl import BHFCrawler, LolzCrawler
from parsing.exceptions import ServerIsDownException


class ParseMessages(Resource):
    def __init__(self, crawler_class):
        self.parser = reqparse.RequestParser()
        self.parser.add_argument('filename', required=True, location='json')
        self.parser.add_argument('keywords', required=True, location='json')
        self.parser.add_argument('one_search_page_only', location='json',
                                 type=bool, default=False)
        self.crawler_class = crawler_class

    def post(self):
        args = self.parser.parse_args()
        filename = args['filename']
        keywords: str = args['keywords']
        one_search_page_only = args['one_search_page_only']

        try:
            crawler = BHFCrawler()
            search_terms = keywords.strip().splitlines()
            parse_messages(crawler, search_terms,
                           filename, one_search_page_only)
        except ServerIsDownException:
            abort(502, message='The server to be parsed is down')
        else:
            return filename, 201


class BHFMessages(ParseMessages):
    def __init__(self):
        super().__init__(BHFCrawler)


class LolzMessages(ParseMessages):
    def __init__(self):
        super().__init__(LolzCrawler)
