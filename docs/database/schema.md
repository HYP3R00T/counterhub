---
icon: lucide/database
---

# Database Schema

This document explains the current CounterHub database design, why it looks the way it does, and how to read the initial migration.

If you want the exact source of truth, read:

- `supabase/migrations/20260621205825_initial_counter_daily_schema.sql`

This page is the human explanation of that file.

## Why We Chose This Shape

CounterHub is intentionally simple, but we still want basic history.

We do not want to store one raw row for every single hit forever.
But we do want to answer questions like:

- how many times was `dotfiles` used in January?
- what was the increase in February?
- can we draw a simple graph over time?

So instead of raw events or one total counter row, we store **daily rollups**.

Example:

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

## What The Initial Migration Creates

The initial migration does five main things:

1. creates the `counter_daily` table
2. creates an index for date-based lookups
3. creates an atomic increment SQL function
4. creates summary and series SQL functions
5. enables RLS and restricts direct access to the backend role

## Table Design

The main table is `public.counter_daily`.

Columns:

- `counter_id`: the counter name, like `dotfiles` or `portfolio`
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

### 1. Create the daily rollup table

```sql
create table public.counter_daily (
    counter_id text not null,
    bucket_date date not null default current_date,
    count bigint not null default 0,
    updated_at timestamptz not null default now(),
    primary key (counter_id, bucket_date),
    check (char_length(trim(counter_id)) > 0),
    check (count >= 0)
);
```

What this means:

- `counter_id`: the named thing being counted
- `bucket_date`: the day we are storing the count for
- `count`: how many increments happened on that day
- `primary key (counter_id, bucket_date)`: one row per counter per day
- `bigint`: safe for large totals
- checks reject blank counter names and negative counts

### 2. Create the lookup index

```sql
create index counter_daily_counter_date_idx
    on public.counter_daily (counter_id, bucket_date desc);
```

This helps the database quickly find the history for one counter in date order.

### 3. Create the atomic increment function

```sql
create or replace function public.increment_counter(counter_name text)
returns table (
    counter_id text,
    total_count bigint,
    today_count bigint,
    updated_at timestamptz
)
language sql
as $$
    with upserted as (
        insert into public.counter_daily (counter_id, bucket_date, count, updated_at)
        values (counter_name, current_date, 1, now())
        on conflict (counter_id, bucket_date)
        do update set
            count = public.counter_daily.count + 1,
            updated_at = now()
        returning counter_id, count, updated_at
    )
    select
        upserted.counter_id,
        (
            select coalesce(sum(cd.count), 0)
            from public.counter_daily as cd
            where cd.counter_id = upserted.counter_id
        ) as total_count,
        upserted.count as today_count,
        upserted.updated_at
    from upserted;
$$;
```

What it does:

- if today’s row does not exist, create it with `count = 1`
- if today’s row already exists, increment it by one
- return the overall total plus today’s current count

Why this matters:

- the client still only calls one simple endpoint
- concurrent requests do not lose increments
- we keep history without storing every raw hit as its own row

### 4. Create the summary function

```sql
create or replace function public.get_counter_summary(counter_name text)
returns table (
    counter_id text,
    total_count bigint,
    last_updated_at timestamptz,
    first_bucket_date date,
    last_bucket_date date
)
```

This function returns the overall picture for one counter:

- total count across all days
- last time the counter changed
- first day we have data
- most recent day we have data

### 5. Create the series function

```sql
create or replace function public.get_counter_series(
    counter_name text,
    start_date date default null,
    end_date date default null
)
returns table (
    bucket_date date,
    count bigint
)
```

This function returns the daily points for a counter.

That is what you use to:

- build a graph
- sum a specific month
- compare time ranges

## Why This Is Better Than The Two Extremes

Compared with one total row only:

- you gain history and charting
- you can answer month-by-month questions

Compared with one raw row per hit:

- you use much less storage
- the database stays quieter
- the API stays simple

This is the middle ground that fits CounterHub well.

## Seed Data vs Migrations

It is important to keep these separate.

- migrations define the database structure
- `supabase/seed.sql` defines repeatable local development data

Structure belongs in migrations.
Sample data belongs in the seed file.

## When To Add A New Migration

Right now, because the project is still very early, we kept one clean starting migration.

Later, once this schema is actually in use, do not rewrite history casually.
At that point:

- keep this migration as the initial baseline
- add a new migration for each schema change
- use `supabase db reset` locally to verify the full history still rebuilds correctly

## In Short

This first schema is intentionally simple:

- one `counter_daily` table
- one atomic increment function
- one summary function
- one series function
- one backend-only access pattern

That is enough to start building, show totals, and draw simple graphs without overbuilding the system.
