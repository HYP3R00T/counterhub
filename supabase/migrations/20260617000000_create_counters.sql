create table public.counters (
    id text primary key,
    count integer not null default 0,
    updated_at timestamptz not null default now()
);

grant all on table public.counters to anon, authenticated, service_role;

-- seed known counters here; only these can be incremented
insert into public.counters (id) values ('dotfiles');
