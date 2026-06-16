create table events (
    id bigint generated always as identity primary key,
    project text not null,
    event_type text not null,
    source text,
    metadata jsonb,
    created_at timestamptz not null default now()
);
