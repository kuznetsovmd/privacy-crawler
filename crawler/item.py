from dataclasses import dataclass
from abc import ABC, abstractmethod
from typing import Optional, ClassVar


@dataclass
class Item(ABC):
    _counter: ClassVar[int] = 0
    
    id: Optional[int] = None
    page: Optional[int] = None

    def __post_init__(self):
        cls = self.__class__
        if self.id is None:
            self.id = cls._counter
            cls._counter += 1
        else:
            cls._counter = max(cls._counter, self.id + 1)

    @abstractmethod
    def __hash__(self):
        pass

    @abstractmethod
    def __eq__(self, other):
        pass

    @abstractmethod
    def to_json(self) -> str:
        pass

    @classmethod
    @abstractmethod
    def from_json(cls, data: str, ignore_id: bool) -> 'Item':
        pass
        