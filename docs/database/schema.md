---
icon: lucide/database
---

# Database Schema

This document explains the current CounterHub database design, why it looks the way it does, and how to read the initial migration.

If you want the exact source of truth, read:

- `supabase/migrations/20260621205825_initial_counter_daily_schema.sql`
- `supabase/migrations/20260621214918_register_dotfiles_counter.sql`

This page is the human explanation of that file.

## Why We Chose This Shape

CounterHub is intentionally simple, but we still want basic history and basic protection.

We do not want to store one raw row for every single hit forever.
But we do want to answer questions like:

- how many times was `dotfiles` used in January?
- what was the increase in February?
- can we draw a simple graph over time?
- can unknown callers create arbitrary counter names?

So instead of raw events or one total counter row, we store **daily rollups** and keep a **registry of allowed counters**.

Example registry:

```text
counters
--------
dotfiles
portfolio
homelab
```

Example history:

```text
counter_id | bucket_date | count
dotfiles   | 2026-01-01  | 4
dotfiles   | 2026-01-12  | 7
dotfiles   | 2026-01-28  | 6
```

This gives us:

- a very simple write API
- much less storage than one row per hit
- enough history for charts and time ranges
- protection against arbitrary counter creation through the public endpoint

## What The Initial Migration Creates

The current migration setup does two conceptual things:

1. the initial schema migration creates the tables, index, SQL functions, and permissions
2. a second migration explicitly registers `dotfiles` as the first allowed counter

## Table Design

### `public.counters`

This is the registry of allowed counters.

Columns:

- `id`: the allowed counter name, like `dotfiles` or `portfolio`
- `description`: optional human-readable description
- `enabled`: whether the counter is currently allowed to receive increments
- `created_at`: when the counter was registered

Purpose:

- stops unknown names from being created by random callers
- gives you a simple allow-list inside the database
- lets you disable a counter without deleting its history

### `public.counter_daily`

This is the daily rollup history.

Columns:

- `counter_id`: the registered counter name
- `bucket_date`: the day the count belongs to
- `count`: the total count for that counter on that day
- `updated_at`: the last time that daily bucket changed

Primary key:

- `(counter_id, bucket_date)`

Why this is useful:

- one row per counter per day
- compact storage
- simple range queries
- safe concurrent increments when paired with the SQL function

## SQL Walkthrough

### 1. Create the counters registry

```sql
create table public.counters (
    id text primary key,
    description text,
    enabled boolean not null default true,
    created_at timestamptz not null default now(),
    check (char_length(trim(id)) > 0)
);
```

This is the allow-list of valid counters. The table itself is created in the initial schema migration, and then counters are intentionally added through follow-up migrations or local seed data.

### 2. Create the daily rollup table

```sql
create table public.counter_daily (
    counter_id text not null references public.counters(id) on delete cascade,
    bucket_date date not null default current_date,
    count bigint not null default 0,
    updated_at timestamptz not null default now(),
    primary key (counter_id, bucket_date),
    check (count >= 0)
);
```

What this means:

- `counter_id` must exist in `public.counters`
- deleting a counter can also remove its daily history
- there is at most one row per counter per day

### 3. Create the lookup index

```sql
create index counter_daily_counter_date_idx
    on public.counter_daily (counter_id, bucket_date desc);
```

This helps the database quickly find the history for one counter in date order.

### 4. Create the atomic increment function

```sql
create or replace function public.increment_counter(counter_name text)
```

This function only inserts or updates a row if the counter exists in `public.counters` and is enabled.

That means:

- known counter: increment works
- unknown counter: no row is created
- disabled counter: no row is created

This keeps the write endpoint simple while protecting the namespace.

### 5. Create the summary function

```sql
create or replace function public.get_counter_summary(counter_name text)
```

This function returns one summary row for a registered counter, including:

- total count across all days
- last updated time
- first day with data
- last day with data

If the counter is not registered, it returns no row.

### 6. Create the series function

```sql
create or replace function public.get_counter_series(
    counter_name text,
    start_date date default null,
    end_date date default null
)
```

This function returns the daily history points for a registered counter.

That is what you use to:

- build a graph
- sum a specific month
- compare time ranges

## Behavior Summary

Current behavior is:

- `POST /count/dotfiles`
  works if `dotfiles` is registered and enabled
- `POST /count/whatever-random-name`
  returns `404` and does not create anything
- `GET /count/dotfiles`
  returns the summary if registered
- `GET /count/dotfiles/series`
  returns the history if registered

## Why This Is Better Than The Two Extremes

Compared with one total row only:

- you gain history and charting
- you can answer month-by-month questions

Compared with one raw row per hit:

- you use much less storage
- the database stays quieter
- the API stays simple

Compared with unrestricted counter creation:

- you prevent arbitrary names from being inserted
- you keep the system cleaner and easier to manage

## Seed Data vs Migrations

It is important to keep these separate.

- migrations define the database structure and intentional production-ready counter registrations
- `supabase/seed.sql` defines repeatable local development history data and extra local-only counters

Structure belongs in migrations.
Fake usage history belongs in the seed file.

## When To Add A New Migration

Right now, because the project is still very early, we kept one clean starting migration.

Later, once this schema is actually in use, do not rewrite history casually.
At that point:

- keep this migration as the initial baseline
- add a new migration for each schema change
- use `supabase db reset` locally to verify the full history still rebuilds correctly

## In Short

This first schema is intentionally simple:

- one `counters` registry table
- one `counter_daily` history table
- one atomic increment function
- one summary function
- one series function
- one backend-only access pattern

That is enough to start building, show totals, draw simple graphs, and prevent arbitrary counter names from being created.
