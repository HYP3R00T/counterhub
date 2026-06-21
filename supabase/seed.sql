-- Local development seed data for CounterHub.
--
-- This file registers a few allowed counters and gives them some realistic
-- daily history for local testing.

insert into public.counters (id, description)
values
    ('dotfiles', 'Dotfiles bootstrap and setup usage'),
    ('portfolio', 'Portfolio actions such as resume downloads'),
    ('homelab', 'Homelab automation and service usage')
on conflict (id) do update set
    description = excluded.description;

insert into public.counter_daily (counter_id, bucket_date, count, updated_at)
values
    ('dotfiles', current_date - 10, 4, now() - interval '10 days'),
    ('dotfiles', current_date - 3, 7, now() - interval '3 days'),
    ('dotfiles', current_date, 2, now()),
    ('portfolio', current_date - 5, 12, now() - interval '5 days'),
    ('homelab', current_date - 1, 3, now() - interval '1 day'),
    ('homelab', current_date, 4, now())
on conflict (counter_id, bucket_date) do update set
    count = excluded.count,
    updated_at = excluded.updated_at;
