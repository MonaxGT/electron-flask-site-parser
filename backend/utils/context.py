import os
from contextlib import contextmanager, redirect_stdout


@contextmanager
def no_print():
    with open(os.devnull, 'w') as void:
        with redirect_stdout(void):
            yield
