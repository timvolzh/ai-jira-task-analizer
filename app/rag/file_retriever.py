from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from app.rag.base import Retriever


@dataclass
class FileRetriever(Retriever):
    path: Path
    max_chars: int = 2000

    def retrieve(self) -> str:
        if not self.path.exists():
            return ""
        content = self.path.read_text(encoding="utf-8").strip()
        if len(content) <= self.max_chars:
            return content
        return content[: self.max_chars]
