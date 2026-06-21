---
icon: lucide/cloud-upload
---

# Deployment Workflow

This guide explains how to promote CounterHub from local development to hosted Supabase and FastAPI Cloud.

The goal is to keep deployment simple and repeatable:

- verify locally
- deploy the database
- configure backend environment variables
- deploy the backend

## Prerequisites

Before you deploy, make sure these are true:

- local development works
- `supabase db reset` succeeds locally
- your app runs locally with `uv run fastapi dev app/main.py`
- tests and checks pass
- your seed data is only for local use

Recommended verification:

```bash
uv run ruff check
uv run ty check
uv run pytest
```

## Database Deployment

Supabase hosts the database.

First, authenticate the CLI:

```bash
supabase login
```

Then link the local repo to your hosted Supabase project:

```bash
supabase link --project-ref YOUR_PROJECT_REF
```

Notes:

- `YOUR_PROJECT_REF` is the Supabase project identifier from the dashboard
- the CLI may ask for the database password
- once linked, commands like `supabase db push` know which remote project to target

To apply the local migration files to the hosted database, run:

```bash
supabase db push
```

For this repo, that means it will:

- create the daily-rollup schema from `supabase/migrations/20260621205825_initial_counter_daily_schema.sql`
- register `dotfiles` as the first allowed counter from `supabase/migrations/20260621214918_register_dotfiles_counter.sql`

Important:

- `supabase db push` is for schema changes
- `supabase/seed.sql` is for local development history samples and should not be treated as production usage data
- this repo registers `dotfiles` in a dedicated follow-up migration, so `db reset --linked --no-seed` still leaves the remote database ready to accept real increments for that counter

If you need to wipe the remote database and rebuild it from local migrations without loading local seed data, use:

```bash
supabase db reset --linked --no-seed
```

## Backend Deployment

FastAPI Cloud hosts the backend application.

CounterHub needs these environment variables:

- `SUPABASE_URL`
- `SUPABASE_KEY`

You can set them with the FastAPI Cloud CLI:

```bash
fastapi cloud env set SUPABASE_URL "https://YOUR_PROJECT_REF.supabase.co"
fastapi cloud env set --secret SUPABASE_KEY "YOUR_SUPABASE_SERVICE_ROLE_KEY"
```

Use a server-side key here, not a browser-exposed public key.

Once the environment variables are set, deploy the backend:

```bash
fastapi deploy
```

## Recommended Order

For this project, the safest order is usually:

1. deploy database changes first
2. then deploy the FastAPI app

Why:

- adding database objects first is usually compatible with the old app
- then the new app can start using those objects after deployment

This matches FastAPI Cloud's guidance for gradual deployments: add database structure before deploying code that depends on it, and remove old structure only after the new code is fully deployed.

## Full Release Sequence

```bash
supabase login
supabase link --project-ref YOUR_PROJECT_REF
supabase db push
fastapi cloud env set SUPABASE_URL "https://YOUR_PROJECT_REF.supabase.co"
fastapi cloud env set --secret SUPABASE_KEY "YOUR_SUPABASE_SERVICE_ROLE_KEY"
fastapi deploy
```

## Verification

Check the app health endpoint:

```bash
curl https://YOUR_FASTAPI_CLOUD_URL/
```

Check that a counter can increment:

```bash
curl -X POST https://YOUR_FASTAPI_CLOUD_URL/count/dotfiles
```

Check that the summary reads back correctly:

```bash
curl https://YOUR_FASTAPI_CLOUD_URL/count/dotfiles
```

## Future Changes

As long as the project is early, the workflow can stay simple.

Later, when the app is in active use:

- keep adding new migration files instead of rewriting history
- avoid database changes that both add and remove things at once
- prefer staged changes so old and new app versions can both work during deployment

## Source References

This workflow is based on the current official docs for:

- Supabase CLI login, link, and `db push`
- FastAPI Cloud environment variables and `fastapi deploy`
- FastAPI Cloud deployment guidance for database migrations
