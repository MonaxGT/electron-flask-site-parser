from parsing.helpers import excel_document

from typing import Iterable
from parsing.crawl import Crawler
from parsing.exceptions import NoSearchResultsException


def parse_messages(crawler: Crawler,
                   search_requests: Iterable[str],
                   workbook_path: str,
                   search_one_page_only: bool = False):
    row_counter = 1

    with excel_document(workbook_path) as workbook:
        for search_counter, search_request in enumerate(search_requests):
            try:
                search_results = crawler.search(
                    search_request,
                    one_page_only=search_one_page_only
                )
            except NoSearchResultsException:
                continue

            if not search_results:
                print(f'Search request "{search_request}": nothing found')
                continue

            sheet = workbook.create_sheet(search_request, search_counter)
            sheet.title = search_request

            for page in search_results:
                messages = crawler.get_messages(page.html, search_request)
                for message in messages:
                    cell_1 = sheet.cell(row=row_counter, column=1)
                    cell_1.value = message.date.strftime("%Y/%m/%d  %H:%M")

                    cell_2 = sheet.cell(row=row_counter, column=2)
                    cell_2.value = message.username
                    cell_2.style = "Hyperlink"
                    cell_2.hyperlink = page.link

                    cell_3 = sheet.cell(row=row_counter, column=3)
                    cell_3.value = message.text

                    row_counter += 1


if __name__ == '__main__':
    from parsing.crawl import BHFCrawler
    crawler = BHFCrawler()
    parse_messages(
        crawler,
        ['+380'],
        '/home/mean/Projects/CP/res.xlsx',
        search_one_page_only=True
    )
