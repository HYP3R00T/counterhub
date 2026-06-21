insert into public.counters (id, description)
values
    ('dotfiles', 'Linux bootstrap and dotfiles management system')
on conflict (id) do update set
    description = excluded.description;
