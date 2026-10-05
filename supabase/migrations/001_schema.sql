-- StroyTablica: схема, восстановленная по SQL в tg-webhook / platega-callback / subscription-cron
create schema if not exists app;
create schema if not exists userdata;

create table app.users (
  id bigint generated always as identity primary key,
  tg_user_id bigint not null unique,
  tg_username text,
  first_name text,
  plan text not null default 'free' check (plan in ('free','start','business','team')),
  plan_started_at timestamptz,
  plan_expires_at timestamptz,
  referral_code text,
  awaiting_support boolean not null default false,
  ui_lang text not null default 'ru',
  created_at timestamptz not null default now()
);

create table app.plan_limits (
  plan text primary key,
  files_per_month int,
  questions_per_file int,
  max_rows int not null
);
insert into app.plan_limits (plan, files_per_month, questions_per_file, max_rows) values
  ('free', 3, 15, 2000),
  ('start', 30, null, 20000),
  ('business', null, null, 200000),
  ('team', null, null, 200000);

create table app.files (
  id bigint generated always as identity primary key,
  user_id bigint not null references app.users(id) on delete cascade,
  tg_file_id text,
  file_name text,
  sheet_name text,
  columns_map jsonb,
  row_count int,
  table_name text,
  is_active boolean not null default false,
  uploaded_at timestamptz not null default now()
);
create index on app.files (user_id, uploaded_at desc);

create table app.questions (
  id bigint generated always as identity primary key,
  user_id bigint not null references app.users(id) on delete cascade,
  file_id bigint references app.files(id) on delete set null,
  question text,
  answer text,
  sql_queries jsonb,
  input_tokens int,
  output_tokens int,
  cache_read_tokens int,
  model text,
  latency_ms int,
  created_at timestamptz not null default now()
);
create index on app.questions (user_id, created_at);
create index on app.questions (file_id);

create table app.events (
  id bigint generated always as identity primary key,
  user_id bigint references app.users(id) on delete cascade,
  event_type text not null,
  created_at timestamptz not null default now()
);
create index on app.events (user_id, event_type, created_at);

create table app.payments (
  id bigint generated always as identity primary key,
  user_id bigint not null references app.users(id) on delete cascade,
  plan text not null,
  period text not null check (period in ('month','year')),
  amount numeric not null,
  status text not null default 'pending',
  platega_tx_id text unique,
  created_at timestamptz not null default now(),
  confirmed_at timestamptz
);

create table app.bot_assets (
  name text primary key,
  telegram_file_id text not null,
  updated_at timestamptz not null default now()
);

-- схемы не публикуются через API; доступ только по прямому подключению (SUPABASE_DB_URL)
revoke all on schema app, userdata from anon, authenticated;
revoke all on all tables in schema app from anon, authenticated;
alter table app.users enable row level security;
alter table app.plan_limits enable row level security;
alter table app.files enable row level security;
alter table app.questions enable row level security;
alter table app.events enable row level security;
alter table app.payments enable row level security;
alter table app.bot_assets enable row level security;
