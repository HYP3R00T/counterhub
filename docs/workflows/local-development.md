---
icon: lucide/server-cog
---

# Local Development Workflow

This guide explains how to develop CounterHub locally with a local Supabase stack and a local FastAPI app.

The goal is to make local development reproducible, safe, and easy to pick up again months later.

## Overview

Recommended local setup:

- run Supabase locally with the Supabase CLI
- keep schema changes in `supabase/migrations/`
- run FastAPI locally against the local Supabase instance
- reset the database from migrations whenever you need a clean state
- only push migrations to the hosted Supabase project after local testing looks good

## Prerequisites

Install these first:

- Docker-compatible container runtime
- Supabase CLI
- Python 3.13+
- `mise`
- `uv`

Project setup:

```bash
mise install
uv sync
prek install --hook-type pre-commit --overwrite
prek install --hook-type commit-msg --overwrite
```

## 1. Start Supabase Locally

Initialize Supabase in the repo if needed:

```bash
supabase init
```

Start the local Supabase stack:

```bash
supabase start
```

This gives you a local Postgres database and the rest of the local Supabase services.

Important rules:

- do not expose the local Supabase stack publicly
- use the local stack for development and schema testing
- treat migration files as the source of truth

## 2. Configure Local Environment Variables

CounterHub currently expects:

- `SUPABASE_URL`
- `SUPABASE_KEY`

Create a local `.env` file with values from the local Supabase stack.

Example shape:

```dotenv
SUPABASE_URL=http://127.0.0.1:54321
SUPABASE_KEY=your-local-anon-or-service-key
```

Notes:

- keep `.env` local only
- never commit secrets
- when switching to production, these values will point to the hosted Supabase project instead

## 3. Run the FastAPI App Locally

Start the app:

```bash
uv run fastapi dev app/main.py
```

Then open:

- API root: `http://127.0.0.1:8000/`
- interactive docs: `http://127.0.0.1:8000/docs`

Use this phase to verify behavior, inspect payloads, and confirm the local app can talk to the local Supabase database.

## 4. Create Schema Changes with Migrations

When you need to change the database schema, create a migration:

```bash
supabase migration new describe_your_change
```

Add the SQL to the new file in `supabase/migrations/`.

Apply the migration locally:

```bash
supabase migration up
```

If you prefer making schema changes through the local Supabase UI first, capture them back into code immediately:

```bash
supabase db diff -f describe_your_change
```

Rule:

- local UI changes are acceptable only if you immediately convert them into migration files
- remote dashboard changes should be avoided once migrations are your workflow

## 5. Reset the Local Database

When you want a clean rebuild from migrations:

```bash
supabase db reset
```

Use this whenever:

- you want to verify the migration history still builds from scratch
- you added or changed seed data
- local schema state feels messy or out of sync

This is one of the most important safety checks in the workflow.

## 6. Seed Local Data

This repository now includes `supabase/seed.sql` for repeatable local demo data.

If you want to change or extend that local dataset, edit:

- `supabase/seed.sql`

Then run:

```bash
supabase db reset
```

That rebuilds the database from migrations and reapplies the seed data automatically because seeding is enabled in `supabase/config.toml`.

This is useful for:

- example counters like `dotfiles` and `portfolio`
- daily history for local charting tests
- local API demos
- reproducible manual testing

## 7. Recommended Daily Workflow

A normal development session should look like this:

```bash
supabase start
uv run fastapi dev app/main.py
```

If you are changing schema:

```bash
supabase migration new add_events_table
supabase migration up
supabase db reset
```

Before you consider the work stable:

```bash
uv run ruff check
uv run ruff format --check
uv run ty check
uv run pytest --cov --cov-report=term-missing --cov-fail-under=80
```

## 8. Rules to Protect Future You

Follow these rules consistently:

- do not treat the hosted Supabase dashboard as the source of truth
- keep all schema changes in migration files
- test migrations locally before pushing them anywhere
- use `supabase db reset` regularly
- keep docs updated when the workflow changes
- label future architecture clearly if the code has not caught up yet

## 9. Later Promotion to Cloud

Once local development looks good, the usual next steps are:

```bash
supabase login
supabase link
supabase db push
```

Then deploy the FastAPI app separately to FastAPI Cloud with the hosted Supabase environment variables.

This local-first workflow is the recommended way to develop CounterHub.
