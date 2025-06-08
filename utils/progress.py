from contextlib import contextmanager
from typing import Iterable
from tqdm import tqdm

@contextmanager
def progress_bar(iterable: Iterable, desc: str = "Processing", **kwargs):
    bar = tqdm(iterable, desc=desc, **kwargs)
    try:
        yield bar          # tqdm 객체 자체를 내보냄
    finally:
        bar.close()
