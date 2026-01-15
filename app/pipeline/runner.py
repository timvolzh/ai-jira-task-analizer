from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional

from app.pipeline.models import JiraIssue
from app.pipeline.processor import Processor
from app.pipeline.prompt_builder import PromptBuilder
from app.rag.base import Retriever
from app.utils.logging import get_logger


@dataclass
class Runner:
    jira_connector: "JiraConnector"
    seldon_connector: "SeldonConnector"
    retriever: Retriever
    system_prompt_path: Path
    max_prompt_chars: int
    output_dir: Path

    def run(
        self,
        *,
        jql: str,
        limit: int,
        fields: List[str],
        include_comments: bool,
        dry_run: bool,
        write_summary: bool,
        only_keys: Optional[List[str]] = None,
    ) -> List["InferenceResult"]:
        logger = get_logger()
        issues = self._fetch_issues(
            jql=jql,
            limit=limit,
            fields=fields,
            include_comments=include_comments,
            only_keys=only_keys,
        )
        logger.info("issues_fetched", count=len(issues))

        system_prompt = self.system_prompt_path.read_text(encoding="utf-8")
        rag_context = self.retriever.retrieve()

        prompt_builder = PromptBuilder(
            system_prompt=system_prompt,
            rag_context=rag_context,
            max_prompt_chars=self.max_prompt_chars,
        )

        processor = Processor(
            prompt_builder=prompt_builder,
            seldon_connector=self.seldon_connector,
            output_dir=self.output_dir,
            dry_run=dry_run,
            write_summary=write_summary,
        )
        return processor.process(issues)

    def _fetch_issues(
        self,
        *,
        jql: str,
        limit: int,
        fields: List[str],
        include_comments: bool,
        only_keys: Optional[List[str]],
    ) -> List[JiraIssue]:
        if only_keys:
            return self.jira_connector.fetch_issues_by_keys(
                only_keys,
                fields=fields,
                include_comments=include_comments,
            )
        return self.jira_connector.fetch_issues(
            jql=jql,
            limit=limit,
            fields=fields,
            include_comments=include_comments,
        )
