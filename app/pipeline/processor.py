from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional

from app.pipeline.models import InferenceResult, JiraIssue
from app.utils.logging import get_logger
from app.utils.time import format_timestamp, utc_now


@dataclass
class Processor:
    prompt_builder: "PromptBuilder"
    seldon_connector: "SeldonConnector"
    output_dir: Path
    dry_run: bool = False
    write_summary: bool = False

    def process(self, issues: Iterable[JiraIssue]) -> List[InferenceResult]:
        logger = get_logger()
        self.output_dir.mkdir(parents=True, exist_ok=True)
        results: List[InferenceResult] = []

        for issue in issues:
            prompt = self.prompt_builder.build(issue)
            logger.info(
                "issue_prompt_built",
                issue_key=issue.key,
                prompt_chars=len(prompt),
                dry_run=self.dry_run,
            )

            response: dict
            extracted_text: Optional[str] = None

            if self.dry_run:
                logger.info("issue_prompt_preview", issue_key=issue.key, prompt=prompt)
                response = {"status": "dry_run"}
            else:
                response = self.seldon_connector.infer(prompt)
                extracted_text = self.seldon_connector.extract_text(response)

            result = InferenceResult(
                issue_key=issue.key,
                prompt=prompt,
                response=response,
                extracted_text=extracted_text,
            )
            results.append(result)

            self._write_output(result)
            logger.info(
                "issue_processed",
                issue_key=issue.key,
                has_text=bool(extracted_text),
            )

        if self.write_summary:
            self._write_summary(results)

        return results

    def _write_output(self, result: InferenceResult) -> None:
        timestamp = format_timestamp(utc_now())
        filename = f"{result.issue_key}_{timestamp}.json"
        payload = {
            "issue_key": result.issue_key,
            "prompt": result.prompt,
            "response": result.response,
            "extracted_text": result.extracted_text,
            "timestamp": timestamp,
        }
        output_path = self.output_dir / filename
        with output_path.open("w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2)

    def _write_summary(self, results: List[InferenceResult]) -> None:
        summary_lines = ["# Jira Issue Summaries", ""]
        for result in results:
            summary_lines.append(f"## {result.issue_key}")
            if result.extracted_text:
                summary_lines.append(result.extracted_text.strip())
            else:
                summary_lines.append("No textual output extracted.")
            summary_lines.append("")

        summary_path = Path("summary.md")
        summary_path.write_text("\n".join(summary_lines), encoding="utf-8")
