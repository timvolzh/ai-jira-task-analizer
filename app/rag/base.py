from __future__ import annotations

from abc import ABC, abstractmethod


class Retriever(ABC):
    @abstractmethod
    def retrieve(self) -> str:
        raise NotImplementedError
