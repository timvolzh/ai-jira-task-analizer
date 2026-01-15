from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from atlassian import Jira
from tenacity import retry, stop_after_attempt, wait_exponential

from app.pipeline.models import JiraIssue
from app.utils.errors import JiraError
from app.utils.logging import get_logger


@dataclass
class JiraConnector:
    url: str
    username: str
    token: str

    def __post_init__(self) -> None:
        self._client = Jira(url=self.url, username=self.username, password=self.token)

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=8))
    def fetch_issues(
        self,
        *,
        jql: str,
        limit: int,
        fields: List[str],
        include_comments: bool,
    ) -> List[JiraIssue]:
        logger = get_logger()
        try:
            response = self._client.jql(jql, start=0, limit=limit, fields=fields)
        except Exception as exc:  # pragma: no cover - external dependency
            logger.error("jira_jql_failed", error=str(exc))
            raise JiraError("Failed to query Jira") from exc

        issues = response.get("issues", [])
        results: List[JiraIssue] = []
        for item in issues:
            results.append(self._parse_issue(item, fields, include_comments))
        return results

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=8))
    def fetch_issue_by_key(
        self,
        issue_key: str,
        *,
        fields: List[str],
        include_comments: bool,
    ) -> JiraIssue:
        logger = get_logger()
        try:
            issue = self._client.issue(issue_key, fields=fields)
        except Exception as exc:  # pragma: no cover - external dependency
            logger.error("jira_issue_failed", issue_key=issue_key, error=str(exc))
            raise JiraError(f"Failed to fetch issue {issue_key}") from exc
        return self._parse_issue(issue, fields, include_comments)

    def fetch_issues_by_keys(
        self,
        issue_keys: List[str],
        *,
        fields: List[str],
        include_comments: bool,
    ) -> List[JiraIssue]:
        return [
            self.fetch_issue_by_key(key.strip(), fields=fields, include_comments=include_comments)
            for key in issue_keys
            if key.strip()
        ]

    def _parse_issue(
        self,
        issue: dict,
        fields: List[str],
        include_comments: bool,
    ) -> JiraIssue:
        key = issue.get("key", "")
        issue_fields = issue.get("fields", {})
        summary = issue_fields.get("summary") or ""
        description = issue_fields.get("description") or ""
        comments: List[str] = []

        if include_comments:
            comments = self._fetch_comments(key)

        return JiraIssue(
            key=key,
            summary=str(summary),
            description=str(description),
            comments=comments,
        )

    def _fetch_comments(self, issue_key: str) -> List[str]:
        logger = get_logger()
        try:
            response = self._client.issue_comments(issue_key)
        except Exception as exc:  # pragma: no cover - external dependency
            logger.error("jira_comments_failed", issue_key=issue_key, error=str(exc))
            raise JiraError(f"Failed to fetch comments for {issue_key}") from exc
        comments_payload = response.get("comments", []) if isinstance(response, dict) else response
        comments: List[str] = []
        for item in comments_payload or []:
            body = item.get("body") if isinstance(item, dict) else None
            if body:
                comments.append(str(body))
        return comments
