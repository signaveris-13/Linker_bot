-- Run this in the Supabase SQL editor to set up your links table.

create table if not exists links (
  id          bigint generated always as identity primary key,
  url         text        not null,
  title       text,
  summary     text,
  read        boolean     not null default false,
  created_at  timestamptz not null default now()
);

-- Optional: index for fast "unread" queries
create index if not exists links_read_idx on links (read, created_at desc);
