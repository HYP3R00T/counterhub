# CounterHub

CounterHub is a lightweight event-tracking and analytics service that gives static websites, scripts, and personal infrastructure a simple way to collect and expose usage metrics.

Its job is to collect events, store them, and provide counters and simple analytics for your projects.

## Why It Exists

Static websites, documentation sites, scripts, and lightweight tools can display information, but they cannot reliably remember things like:

- how many times a script was executed
- how many times a resume was downloaded
- how many times a bootstrap process was run
- whether a homelab service has checked in recently
- basic usage metrics across projects

CounterHub solves that by acting as the middleman between clients and storage.

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

## Core Idea

Clients do not directly increment counters. They send events to CounterHub.

Example event:

```json
{
  "project": "dotfiles",
  "event": "install"
}
```

CounterHub stores that event in Supabase.

Later, when another project wants to display a metric such as:

```text
Dotfiles installs: 137
```

it can ask CounterHub for derived statistics:

```http
GET /projects/dotfiles/stats
```

CounterHub then calculates that result from the stored events.

## Key Design Decision

CounterHub stores **events**, not just counters.

Instead of storing only a value like:

```text
dotfiles = 137
```

it stores an event history like:

```text
dotfiles install
dotfiles install
dotfiles install
...
```

That keeps the system flexible and makes future analytics possible without redesigning the database.

From the same event history, CounterHub can support questions like:

- total installs
- installs this month
- last install time
- unique machines
- most active project
- activity trends

## Example Use Cases

The initial use case is tracking dotfile bootstrap executions, but the platform is intentionally generic.

Other projects could send events like:

```json
{
  "project": "homelab",
  "event": "heartbeat"
}
```

or:

```json
{
  "project": "portfolio",
  "event": "resume_download"
}
```

without changing the architecture.

## API Direction

The intended API shape is:

```text
POST /events
GET  /projects/{project}/stats
```

A stats response might look like:

```json
{
  "project": "dotfiles",
  "total_events": 137,
  "install": 137,
  "last_event": "2026-06-21T12:34:56.000000+00:00"
}
```

## Current Repository State

The current repository is an early FastAPI and Supabase implementation. The app currently exposes a simple counter-oriented MVP while the broader product direction is event storage and derived analytics.

Current endpoints in the codebase:

- `GET /` returns service status and database reachability
- `POST /counter/{counter_id}/increment` increments a known counter
- `GET /counter/{counter_id}` returns the current value for a counter

That makes the current service a stepping stone toward the event-based design described above.

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

## Quality Checks

```bash
uv run ruff check
uv run ruff format --check
uv run ty check
uv run pytest --cov --cov-report=term-missing --cov-fail-under=80
```
