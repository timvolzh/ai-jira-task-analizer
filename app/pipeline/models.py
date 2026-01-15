from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class JiraIssue:
    key: str
    summary: str
    description: str
    comments: List[str] = field(default_factory=list)


@dataclass
class InferenceResult:
    issue_key: str
    prompt: str
    response: dict
    extracted_text: Optional[str] = None
