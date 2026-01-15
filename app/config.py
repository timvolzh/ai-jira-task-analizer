from __future__ import annotations

from typing import List

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    jira_url: str = Field(alias="JIRA_URL")
    jira_user: str = Field(alias="JIRA_USER")
    jira_token: str = Field(alias="JIRA_TOKEN")
    jql: str = Field(alias="JQL", default="")
    limit: int = Field(alias="LIMIT", default=50)
    fields: List[str] = Field(alias="FIELDS", default_factory=lambda: ["summary", "description"])
    include_comments: bool = Field(alias="INCLUDE_COMMENTS", default=False)

    mlserver_url: str = Field(alias="MLSERVER_URL")
    model_name: str = Field(alias="MODEL_NAME")
    request_timeout: float = Field(alias="REQUEST_TIMEOUT", default=30.0)

    system_prompt_path: str = Field(alias="SYSTEM_PROMPT_PATH", default="system_prompt.txt")
    rag_path: str = Field(alias="RAG_PATH", default="rag.txt")
    rag_max_chars: int = Field(alias="RAG_MAX_CHARS", default=2000)
    max_prompt_chars: int = Field(alias="MAX_PROMPT_CHARS", default=6000)

    output_dir: str = Field(alias="OUTPUT_DIR", default="output")
    log_level: str = Field(alias="LOG_LEVEL", default="INFO")

    @field_validator("fields", mode="before")
    @classmethod
    def _split_fields(cls, value: str | List[str]) -> List[str]:
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value
