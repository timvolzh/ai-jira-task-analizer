from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

import requests
from tenacity import retry, stop_after_attempt, wait_exponential

from app.utils.errors import SeldonError
from app.utils.logging import get_logger


@dataclass
class SeldonConnector:
    base_url: str
    model_name: str
    request_timeout: float = 30.0

    def __post_init__(self) -> None:
        self._session = requests.Session()

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=8))
    def infer(self, text: str) -> Dict[str, Any]:
        logger = get_logger()
        url = f"{self.base_url.rstrip('/')}/v2/models/{self.model_name}/infer"
        payload = self.build_payload(text)
        try:
            response = self._session.post(url, json=payload, timeout=self.request_timeout)
            response.raise_for_status()
        except Exception as exc:  # pragma: no cover - external dependency
            logger.error("mlserver_request_failed", error=str(exc))
            raise SeldonError("MLServer inference request failed") from exc
        return response.json()

    @staticmethod
    def build_payload(text: str) -> Dict[str, Any]:
        return {
            "inputs": [
                {
                    "name": "text",
                    "shape": [1],
                    "datatype": "BYTES",
                    "data": [text],
                }
            ]
        }

    @staticmethod
    def extract_text(response: Dict[str, Any]) -> Optional[str]:
        outputs = response.get("outputs") if isinstance(response, dict) else None
        if not outputs:
            return None
        first = outputs[0]
        data = first.get("data") if isinstance(first, dict) else None
        if not data:
            return None
        value = data[0]
        if isinstance(value, str):
            return value
        return str(value)
