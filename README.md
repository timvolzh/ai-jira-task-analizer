# ai-jira-task-analizer

Небольшой модульный пайплайн для периодического запуска в GitLab CI Scheduler: извлекает задачи из Jira, строит промпт (system + RAG + issue data), отправляет в Seldon MLServer и сохраняет результаты в `output/`.

## Возможности

- Запуск как job GitLab CI (без встроенного планировщика).
- Интеграции вынесены в отдельные коннекторы (Jira, MLServer).
- RAG для MVP читается из локального файла с ограничением по длине.
- Structured logging в stdout с `run_id` для трассировки.
- Ретраи с backoff для Jira и MLServer.
- Сохранение результатов в `output/` и опциональный `summary.md`.

## Структура проекта

```
app/
  connectors/
  pipeline/
  rag/
  utils/
  config.py
  main.py
```

## Локальный запуск

1. Создайте `.env` на основе `.env.example` и заполните переменные.
2. Подготовьте файлы `system_prompt.txt` и `rag.txt` по примерам.
3. Установите зависимости и запустите:

```bash
pip install -r requirements.txt
python -m app.main --write-summary
```

## Запуск в GitLab CI

- Используется `.gitlab-ci.yml`, который:
  - запускается в официальном Python image,
  - устанавливает зависимости,
  - выполняет `python -m app.main`,
  - сохраняет `output/` и `summary.md` как artifacts, если они были созданы.
- Все переменные (например `JIRA_URL`, `MLSERVER_URL`, `MODEL_NAME`) задаются через GitLab CI Variables.

> Расписание запуска настраивается через GitLab UI Scheduler (CI/CD → Schedules). Внутри проекта нет собственного планировщика.

## CLI опции

- `--dry-run` — не вызывает MLServer, только логирует промпты и найденные задачи.
- `--max-issues N` — переопределяет лимит из конфига.
- `--output-dir PATH` — путь для JSON-файлов результата.
- `--write-summary` — создаёт `summary.md`.
- `--only-keys KEY1,KEY2` — обработать только выбранные задачи.

## Переменные окружения

См. `.env.example` для полного списка. Основные:

- `JIRA_URL`, `JIRA_USER`, `JIRA_TOKEN`
- `JQL`, `LIMIT`, `FIELDS`, `INCLUDE_COMMENTS`
- `MLSERVER_URL`, `MODEL_NAME`, `REQUEST_TIMEOUT`
- `SYSTEM_PROMPT_PATH`, `RAG_PATH`, `RAG_MAX_CHARS`, `MAX_PROMPT_CHARS`
- `OUTPUT_DIR`, `LOG_LEVEL`
