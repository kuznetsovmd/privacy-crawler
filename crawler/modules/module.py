from abc import ABC, abstractmethod
from multiprocessing.pool import Pool


class Module(ABC):

    @abstractmethod
    def run(self, p: Pool = None):
        pass
        