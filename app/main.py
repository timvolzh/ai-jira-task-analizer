from __future__ import annotations

import argparse
import uuid
from pathlib import Path
from typing import List, Optional

from dotenv import load_dotenv

from app.config import Settings
from app.connectors.jira_connector import JiraConnector
from app.connectors.seldon_connector import SeldonConnector
from app.pipeline.runner import Runner
from app.rag.file_retriever import FileRetriever
from app.utils.logging import configure_logging, get_logger, log_exception


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Jira to MLServer processing pipeline")
    parser.add_argument("--dry-run", action="store_true", help="Do not call MLServer")
    parser.add_argument("--max-issues", type=int, default=None, help="Override issue limit")
    parser.add_argument("--output-dir", type=str, default=None, help="Output directory")
    parser.add_argument("--write-summary", action="store_true", help="Write summary.md")
    parser.add_argument(
        "--only-keys",
        type=str,
        default=None,
        help="Comma-separated list of issue keys",
    )
    return parser.parse_args()


def main() -> int:
    load_dotenv()
    args = parse_args()
    settings = Settings()

    run_id = str(uuid.uuid4())
    configure_logging(settings.log_level, run_id)
    logger = get_logger()

    output_dir = Path(args.output_dir or settings.output_dir)
    max_issues = args.max_issues or settings.limit
    only_keys: Optional[List[str]] = None
    if args.only_keys:
        only_keys = [key.strip() for key in args.only_keys.split(",") if key.strip()]

    logger.info(
        "pipeline_start",
        dry_run=args.dry_run,
        max_issues=max_issues,
        output_dir=str(output_dir),
        only_keys=only_keys,
    )

    try:
        jira_connector = JiraConnector(
            url=settings.jira_url,
            username=settings.jira_user,
            token=settings.jira_token,
        )
        seldon_connector = SeldonConnector(
            base_url=settings.mlserver_url,
            model_name=settings.model_name,
            request_timeout=settings.request_timeout,
        )
        retriever = FileRetriever(path=Path(settings.rag_path), max_chars=settings.rag_max_chars)

        runner = Runner(
            jira_connector=jira_connector,
            seldon_connector=seldon_connector,
            retriever=retriever,
            system_prompt_path=Path(settings.system_prompt_path),
            max_prompt_chars=settings.max_prompt_chars,
            output_dir=output_dir,
        )

        runner.run(
            jql=settings.jql,
            limit=max_issues,
            fields=settings.fields,
            include_comments=settings.include_comments,
            dry_run=args.dry_run,
            write_summary=args.write_summary,
            only_keys=only_keys,
        )

        logger.info("pipeline_complete")
        return 0
    except Exception as exc:  # pragma: no cover - entrypoint
        log_exception(logger, "pipeline_failed", error=str(exc))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
