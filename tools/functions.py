import json
import logging
import os
import shutil
from pathlib import Path
from typing import (
    Any, Callable, Generator, Iterable,
    Iterator, Optional, Type, TypeVar
)

from bs4 import BeautifulSoup
from file_read_backwards import FileReadBackwards

from crawler.item import Item
from crawler.web.driver import Driver
from tools.config import PathConfig


T = TypeVar("T", bound="Item")


def get_logger():
    return logging.getLogger(f"pid={os.getpid()}")


def read_models(descriptor: Path,
                cls: Type[T]) -> Generator[T, None, None]:
    with descriptor.open("r", encoding="utf-8") as d:
        for line in d:
            line = line.strip()
            if line:
                yield cls.from_json(line)


def write_models(descriptor: Path,
                 models: Iterable[Item],
                 mode: str = "w") -> None:
    with descriptor.open(mode, encoding="utf-8") as out:
        for m in models:
            out.write(m.to_json() + "\n")


def load_last_id_page(path: Path) -> tuple[Optional[int], Optional[str]]:
    if not path.exists():
        return None, None
    with FileReadBackwards(path, encoding="utf-8") as frb:
        for line in frb:
            item = json.loads(line)
            return item.get("id", None), item.get("page", None)
    return None, None


def temp_descriptor(descriptor: Path,
                    suffix: str,
                    label: str) -> Path:
    temp = descriptor.with_name(f".{descriptor.stem}.{suffix}.{label}{descriptor.suffix}")
    temp.touch()
    return temp


def concat_files(input_files: list[Path],
                 output_file: Path,
                 buffer_size: int = 1024 * 1024) -> None:
    with output_file.open("wb") as out_f:
        for file_path in input_files:
            with file_path.open("rb") as in_f:
                shutil.copyfileobj(in_f, out_f, length=buffer_size)


def get_soup_from_url(url: str,
                      cooldown: float = .0,
                      random_cooldown: float = .0) -> Optional[BeautifulSoup]:
    driver = Driver()
    driver.get(url, cooldown=cooldown, random_cooldown=random_cooldown)
    markup = driver.source()
    if not markup:
        return None
    return BeautifulSoup(markup, "lxml").find("body")


def gen_search_urls(template: str,
                    keywords: Iterable[str],
                    pages: int) -> Iterator[tuple[str, Optional[str]]]:
    for keyword in keywords:
        for page in range(1, pages + 1):
            yield template.format(keyword=keyword, page=page), keyword


def skip_to(iterable: Iterable[Any],
            value: Any = None,
            key: Callable[[Any], Any] = lambda x: x) -> Iterator[Any]:
    if value is None:
        yield from iterable
        return
    found = False
    for x in iterable:
        if found:
            yield x
        elif key(x) == value:
            found = True
        continue


def chunked(iterable: Iterable[Any],
            chunk_size: int = 64) -> Generator[list[Any], None, None]:
    chunk = []
    for item in iterable:
        chunk.append(item)
        if len(chunk) >= chunk_size:
            yield chunk
            chunk = []
    if chunk:
        yield chunk


def init(paths: PathConfig) -> None:
    for path in (paths.data, paths.html):
        os.makedirs(path, exist_ok=True)
    paths.descriptor.write_text("", encoding="utf-8")
    if not paths.explicit.exists():
        paths.explicit.write_text('{"policy": "https://mi.com/global/about/privacy/"}')
