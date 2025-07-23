import logging
import shutil
import json
import os

from typing import Any, Callable, Generator, Iterable, Iterator, List, Optional, Tuple, Type, TypeVar
from file_read_backwards import FileReadBackwards
from bs4 import BeautifulSoup
from pathlib import Path

from crawler.web.driver import Driver


T = TypeVar("T")


def get_logger():
    return logging.getLogger(f"pid={os.getpid()}")


def read_models(descriptor, cls):
    with descriptor.open("r", encoding="utf-8") as desc:
        for line in desc:
            line = line.strip()
            if line:
                yield cls.from_json(line)


def write_models(descriptor, models, mode="w"):
    with descriptor.open(mode, encoding="utf-8") as out:
        for m in models:
            out.write(m.to_json() + "\n")


def read_lines(path: Path) -> Iterator[str]:
    if path.exists():
        with path.open("r", encoding="utf-8") as f:
            yield from f


def read_object_chunks_from_id(
    path: Path,
    cls: Type[T],
    chunk_size: int = 20,
    start_from: int = 0,
) -> Iterator[List[T]]:
    chunk = []
    for line in read_lines(path):
        obj = cls.from_json(line)
        if obj.id is not None and obj.id > start_from:
            chunk.append(obj)
            if len(chunk) >= chunk_size:
                yield chunk
                chunk = []
    if chunk:
        yield chunk


def load_last_id_page(path: Path) -> Tuple[int, Optional[str]]:
    if not path.exists():
        return None, None
    with FileReadBackwards(path, encoding="utf-8") as frb:
        for line in frb:
            item = json.loads(line)
            return item.get("id", None), item.get("page", None)
    return None, None


def temp_descriptor(descriptor, suffix, label):
    temp = descriptor.with_name(f".{descriptor.stem}.{suffix}.{label}{descriptor.suffix}")
    temp.touch()
    return temp


def concat_files(input_files: List[Path], output_file: Path, buffer_size=1024 * 1024):
    with output_file.open("wb") as out_f:
        for file_path in input_files:
            with file_path.open("rb") as in_f:
                shutil.copyfileobj(in_f, out_f, length=buffer_size)


def get_soup_from_url(url: str, cooldown=0.0, random_cooldown=0.0) -> Optional[BeautifulSoup]:
    driver = Driver()
    driver.get(url, cooldown=cooldown, random_cooldown=random_cooldown)
    markup = driver.source()
    if not markup:
        return None
    return BeautifulSoup(markup, "lxml").find("body")

    
def gen_search_urls(template: str, keywords: Iterable[str], pages: int) -> Iterator[Tuple[str, str]]:
    for keyword in keywords:
        for page in range(1, pages + 1):
            yield template.format(keyword=keyword, page=page), keyword


def skip_to(
    iterable: Iterable[T],
    value: Any = None,
    key: Callable[[T], str] = lambda x: x
) -> Iterator[T]:
    if value is None:
        yield from iterable
        return

    found = False
    for x in iterable:
        if not found:
            if key(x) == value:
                found = True
            continue
        yield x


def chunked(
    iterable: Iterable[T],
    chunk_size: int = 20
) -> Generator[List[T], None, None]:
    buffer: List[T] = []

    for item in iterable:
        buffer.append(item)
        if len(buffer) >= chunk_size:
            yield buffer
            buffer = []

    if buffer:
        yield buffer


def init(paths):
    for path in (paths.data, paths.html):
        os.makedirs(path, exist_ok=True)
    for file_path in (paths.descriptor,):
        file_path.write_text('', encoding='utf-8')
    for file_path in (paths.explicit,):
        file_path.touch(exist_ok=True)
        