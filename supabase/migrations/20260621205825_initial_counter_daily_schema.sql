create table public.counter_daily (
    counter_id text not null,
    bucket_date date not null default current_date,
    count bigint not null default 0,
    updated_at timestamptz not null default now(),
    primary key (counter_id, bucket_date),
    check (char_length(trim(counter_id)) > 0),
    check (count >= 0)
);

create index counter_daily_counter_date_idx
    on public.counter_daily (counter_id, bucket_date desc);

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

create or replace function public.get_counter_summary(counter_name text)
returns table (
    counter_id text,
    total_count bigint,
    last_updated_at timestamptz,
    first_bucket_date date,
    last_bucket_date date
)
language sql
stable
as $$
    select
        counter_name as counter_id,
        coalesce(sum(cd.count), 0) as total_count,
        max(cd.updated_at) as last_updated_at,
        min(cd.bucket_date) as first_bucket_date,
        max(cd.bucket_date) as last_bucket_date
    from public.counter_daily as cd
    where cd.counter_id = counter_name;
$$;

create or replace function public.get_counter_series(
    counter_name text,
    start_date date default null,
    end_date date default null
)
returns table (
    bucket_date date,
    count bigint
)
language sql
stable
as $$
    select
        cd.bucket_date,
        cd.count
    from public.counter_daily as cd
    where cd.counter_id = counter_name
      and (start_date is null or cd.bucket_date >= start_date)
      and (end_date is null or cd.bucket_date <= end_date)
    order by cd.bucket_date;
$$;

alter table public.counter_daily enable row level security;

revoke all on table public.counter_daily from anon, authenticated;
grant select, insert, update on table public.counter_daily to service_role;

revoke execute on function public.increment_counter(text) from public;
revoke execute on function public.increment_counter(text) from anon, authenticated;
grant execute on function public.increment_counter(text) to service_role;

revoke execute on function public.get_counter_summary(text) from public;
revoke execute on function public.get_counter_summary(text) from anon, authenticated;
grant execute on function public.get_counter_summary(text) to service_role;

revoke execute on function public.get_counter_series(text, date, date) from public;
revoke execute on function public.get_counter_series(text, date, date) from anon, authenticated;
grant execute on function public.get_counter_series(text, date, date) to service_role;
