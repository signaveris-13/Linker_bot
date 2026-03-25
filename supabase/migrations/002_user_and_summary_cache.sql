-- Per-user links + optional cached article summary (Article summary prompt)

alter table links add column if not exists telegram_user_id bigint;
alter table links add column if not exists content_language text;
alter table links add column if not exists cached_summary text;
alter table links add column if not exists cached_summary_lang text;

create index if not exists links_user_unread_idx
  on links (telegram_user_id, read, created_at desc);
