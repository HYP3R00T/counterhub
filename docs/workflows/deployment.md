---
icon: lucide/cloud-upload
---

# Deployment Workflow

This guide explains how to promote CounterHub from local development to hosted Supabase and FastAPI Cloud.

The goal is to keep deployment simple and repeatable:

1. verify locally
2. push the database schema to Supabase
3. configure environment variables in FastAPI Cloud
4. deploy the FastAPI app

## What Gets Deployed Where

- Supabase hosts the database
- FastAPI Cloud hosts the backend application
- Git stores the migration files, code, and docs

## Before You Deploy

Make sure these are true first:

- local development works
- `supabase db reset` succeeds locally
- your seed data is only for local use
- your app runs locally with `uv run fastapi dev app/main.py`
- tests and checks pass

Recommended verification:

```bash
uv run ruff check
uv run ty check
uv run pytest
```

## 1. Log In To Supabase CLI

```bash
supabase login
```

This connects the CLI to your Supabase account.

## 2. Link The Local Repo To Your Hosted Supabase Project

```bash
supabase link --project-ref YOUR_PROJECT_REF
```

Notes:

- `YOUR_PROJECT_REF` is the Supabase project identifier from the dashboard
- the CLI may ask for the database password
- once linked, commands like `supabase db push` know which remote project to target

## 3. Push Database Migrations To Hosted Supabase

```bash
supabase db push
```

This applies your local migration files to the hosted Supabase database.

For this repo, that means it will:

- create the daily-rollup schema from `supabase/migrations/20260621205825_initial_counter_daily_schema.sql`
- register `dotfiles` as the first allowed counter from `supabase/migrations/20260621214918_register_dotfiles_counter.sql`

Important:

- `supabase db push` is for schema changes
- `supabase/seed.sql` is for local development history samples and should not be treated as production usage data
- this repo registers `dotfiles` in a dedicated follow-up migration, so `db reset --linked --no-seed` still leaves the remote database ready to accept real increments for that counter

## 4. Set FastAPI Cloud Environment Variables

CounterHub needs:

- `SUPABASE_URL`
- `SUPABASE_KEY`

You can set them with the FastAPI Cloud CLI.

Example:

```bash
fastapi cloud env set SUPABASE_URL "https://YOUR_PROJECT_REF.supabase.co"
fastapi cloud env set --secret SUPABASE_KEY "YOUR_SUPABASE_SERVICE_ROLE_KEY"
```

Use a server-side key here, not a browser-exposed public key.

## 5. Deploy To FastAPI Cloud

```bash
fastapi deploy
```

FastAPI Cloud will upload the app, install dependencies, and deploy it.

## Recommended Deployment Order

For this project, the safest order is usually:

1. push database changes first
2. then deploy the FastAPI app

Why:

- adding database objects first is usually compatible with the old app
- then the new app can start using those objects after deployment

This matches FastAPI Cloud's guidance for gradual deployments: add database structure before deploying code that depends on it, and remove old structure only after the new code is fully deployed.

## Typical Full Release Sequence

```bash
supabase login
supabase link --project-ref YOUR_PROJECT_REF
supabase db push
fastapi cloud env set SUPABASE_URL "https://YOUR_PROJECT_REF.supabase.co"
fastapi cloud env set --secret SUPABASE_KEY "YOUR_SUPABASE_SERVICE_ROLE_KEY"
fastapi deploy
```

## After Deployment

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

## Notes For Future Changes

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
