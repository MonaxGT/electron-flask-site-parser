import contextlib

from openpyxl import Workbook


@contextlib.contextmanager
def excel_document(name: str):
    try:
        workbook = Workbook()
        yield workbook
    finally:
        workbook.save(name)
