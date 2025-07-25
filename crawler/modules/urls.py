from multiprocessing.pool import Pool
from typing import TypeVar

from crawler.modules.module import Module
from crawler.plugins.plugin import Plugin
from tools.functions import get_logger


T = TypeVar("T", bound=Plugin)


class Urls(Module):

    def __init__(self, plugins: list[T]) -> None:
        self.plugins = plugins

    def run(self, p: Pool = None) -> None:
        for plugin in self.plugins:
            plugin.scrap_records(p)
