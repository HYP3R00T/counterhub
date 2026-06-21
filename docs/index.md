---
icon: lucide/chart-column
---

# CounterHub Docs

CounterHub is a lightweight counter backend for scripts, static websites, homelab services, and personal tools.

This documentation is the long-term runbook for the project. Use it when you need to set up local development, remember the architecture, or revisit deployment steps later.

## What CounterHub Does

CounterHub sits between lightweight clients and Supabase:

```text
Client -> CounterHub -> Supabase
```

Clients call a simple endpoint like:

```text
POST /count/dotfiles
```

CounterHub increments the named counter and stores the result in daily buckets in Supabase.

## Docs Map

- [Local development workflow](workflows/local-development.md): set up Supabase locally, run the FastAPI app, create migrations, reset the database, and use seed data.
- [Deployment workflow](workflows/deployment.md): push schema changes to Supabase, configure FastAPI Cloud environment variables, and deploy the app.
- [Database schema](database/schema.md): understand the initial migration, the daily rollup table, permissions, and the SQL functions.

## Current State

The current codebase stores daily counter rollups in Supabase and exposes async FastAPI endpoints to increment counters, read summaries, and fetch simple time-series data.
