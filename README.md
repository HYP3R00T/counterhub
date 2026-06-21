# CounterHub

CounterHub is a lightweight counter service for scripts, static websites, homelab services, and personal tools.

Its job is simple: accept a request, increment a named counter, and let you read the current value and recent history later.

## Why It Exists

Some projects are static or lightweight. They do not need a full analytics stack.
They just need to answer questions like:

- how many times was this script run?
- how many times was this resume downloaded?
- how many times was this bootstrap command used?
- how many times did this service check in?
- how did usage change over time?

CounterHub gives those projects one small backend endpoint they can call.

```text
Client
(script, website, homelab, tool)
        |
        v
    CounterHub
        |
        v
    Supabase
```

## Current API

```text
GET  /
POST /count/{counter_id}
GET  /count/{counter_id}
GET  /count/{counter_id}/series?start=YYYY-MM-DD&end=YYYY-MM-DD
```

Increment a counter:

```bash
curl -X POST http://127.0.0.1:8000/count/dotfiles
```

Read the overall summary:

```bash
curl http://127.0.0.1:8000/count/dotfiles
```

Read the daily series for a graph:

```bash
curl "http://127.0.0.1:8000/count/dotfiles/series?start=2026-01-01&end=2026-01-31"
```

Example summary response:

```json
{
  "counter_id": "dotfiles",
  "total_count": 42,
  "last_updated_at": "2026-06-21T12:34:56.000000+00:00",
  "first_bucket_date": "2026-06-01",
  "last_bucket_date": "2026-06-21"
}
```

Example series response:

```json
{
  "counter_id": "dotfiles",
  "start_date": "2026-01-01",
  "end_date": "2026-01-31",
  "total_count": 17,
  "points": [
    {"bucket_date": "2026-01-01", "count": 4},
    {"bucket_date": "2026-01-12", "count": 7},
    {"bucket_date": "2026-01-28", "count": 6}
  ]
}
```

## Current Repository State

The repository implements a deliberately small first version of CounterHub:

- one daily rollup table in Supabase
- one atomic SQL function for increments
- one async FastAPI endpoint to increment a counter
- one async FastAPI endpoint to read the overall summary
- one async FastAPI endpoint to read daily history for charts

This keeps the client experience simple while still preserving time-based history without storing one row per hit.

## Stack

- Python 3.13+
- FastAPI
- Supabase
- `uv`
- `ruff`
- `ty`
- `pytest`

## Local Development

```bash
mise install
uv sync
prek install --hook-type pre-commit --overwrite
prek install --hook-type commit-msg --overwrite
```

Run the app with Supabase configured:

```bash
uv run fastapi dev app/main.py
```

Required environment variables:

- `SUPABASE_URL`
- `SUPABASE_KEY`

For backend deployment, `SUPABASE_KEY` should be a server-side key, not a browser-exposed public key.

## Quality Checks

```bash
uv run ruff check
uv run ruff format --check
uv run ty check
uv run pytest --cov --cov-report=term-missing --cov-fail-under=80
```
