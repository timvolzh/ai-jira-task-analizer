from __future__ import annotations

from dataclasses import dataclass

from app.pipeline.models import JiraIssue


@dataclass
class PromptBuilder:
    system_prompt: str
    rag_context: str
    max_prompt_chars: int = 6000

    def build(self, issue: JiraIssue) -> str:
        system_text = self.system_prompt.strip()
        rag_text = self.rag_context.strip()
        description = (issue.description or "").strip()
        comments_text = "\n".join(comment.strip() for comment in issue.comments if comment.strip())

        prompt = self._assemble_prompt(
            issue_key=issue.key,
            summary=issue.summary.strip(),
            system_text=system_text,
            rag_text=rag_text,
            description=description,
            comments=comments_text,
        )

        if len(prompt) <= self.max_prompt_chars:
            return prompt

        trimmed = self._trim_prompt(
            issue_key=issue.key,
            summary=issue.summary.strip(),
            system_text=system_text,
            rag_text=rag_text,
            description=description,
            comments=comments_text,
        )
        return trimmed

    def _assemble_prompt(
        self,
        *,
        issue_key: str,
        summary: str,
        system_text: str,
        rag_text: str,
        description: str,
        comments: str,
    ) -> str:
        parts = [
            "System Prompt:\n" + system_text,
            "RAG Context:\n" + rag_text if rag_text else "RAG Context:\n",
            "Issue Data:\n" + self._issue_block(issue_key, summary, description, comments),
        ]
        return "\n\n".join(parts).strip()

    def _issue_block(self, issue_key: str, summary: str, description: str, comments: str) -> str:
        lines = [f"Key: {issue_key}", f"Summary: {summary}"]
        if description:
            lines.append("Description:\n" + description)
        if comments:
            lines.append("Comments:\n" + comments)
        return "\n".join(lines)

    def _trim_prompt(
        self,
        *,
        issue_key: str,
        summary: str,
        system_text: str,
        rag_text: str,
        description: str,
        comments: str,
    ) -> str:
        trimmed_rag = rag_text
        trimmed_description = description
        trimmed_comments = comments

        prompt = self._assemble_prompt(
            issue_key=issue_key,
            summary=summary,
            system_text=system_text,
            rag_text=trimmed_rag,
            description=trimmed_description,
            comments=trimmed_comments,
        )
        overflow = len(prompt) - self.max_prompt_chars

        if overflow > 0:
            trimmed_comments, overflow = self._truncate_field(trimmed_comments, overflow)
        if overflow > 0:
            trimmed_description, overflow = self._truncate_field(trimmed_description, overflow)
        if overflow > 0:
            trimmed_rag, overflow = self._truncate_field(trimmed_rag, overflow)

        return self._assemble_prompt(
            issue_key=issue_key,
            summary=summary,
            system_text=system_text,
            rag_text=trimmed_rag,
            description=trimmed_description,
            comments=trimmed_comments,
        )

    @staticmethod
    def _truncate_field(value: str, overflow: int) -> tuple[str, int]:
        if not value or overflow <= 0:
            return value, overflow
        if overflow >= len(value):
            return "", overflow - len(value)
        return value[:-overflow], 0
