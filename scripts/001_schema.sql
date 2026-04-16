-- ============================================
-- RE Expert - Full Database Schema
-- Run this in Supabase SQL Editor
-- ============================================

-- 1. PROFILES (extends Supabase auth.users)
create table public.profiles (
  id uuid references auth.users on delete cascade primary key,
  full_name text,
  role text default 'user' check (role in ('user', 'admin', 'viewer')),
  avatar_url text,
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

-- Auto-create profile on signup
create or replace function public.handle_new_user()
returns trigger as $$
begin
  insert into public.profiles (id, full_name)
  values (new.id, new.raw_user_meta_data->>'full_name');
  return new;
end;
$$ language plpgsql security definer;

create trigger on_auth_user_created
  after insert on auth.users
  for each row execute procedure public.handle_new_user();

-- 2. CONVERSATIONS
create table public.conversations (
  id uuid default gen_random_uuid() primary key,
  user_id uuid references public.profiles(id) on delete cascade not null,
  title text not null default 'Nueva conversación',
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

-- 3. MESSAGES
create table public.messages (
  id uuid default gen_random_uuid() primary key,
  conversation_id uuid references public.conversations(id) on delete cascade not null,
  role text not null check (role in ('user', 'assistant', 'system')),
  content text not null,
  tokens_used integer,
  created_at timestamptz default now()
);

-- 4. MATERIALS (precios de materiales)
create table public.materials (
  id uuid default gen_random_uuid() primary key,
  name text not null,
  unit text not null,
  current_price numeric(12,2) not null,
  previous_price numeric(12,2),
  variation_pct numeric(5,2),
  trend text default 'stable' check (trend in ('up', 'down', 'stable')),
  source text,
  updated_at timestamptz default now()
);

-- 5. MATERIAL PRICE HISTORY
create table public.material_prices (
  id uuid default gen_random_uuid() primary key,
  material_id uuid references public.materials(id) on delete cascade not null,
  price numeric(12,2) not null,
  recorded_at timestamptz default now()
);

-- 6. PROJECTS
create table public.projects (
  id uuid default gen_random_uuid() primary key,
  user_id uuid references public.profiles(id) on delete cascade not null,
  name text not null,
  description text,
  budget numeric(14,2),
  spent numeric(14,2) default 0,
  progress_pct numeric(5,2) default 0,
  start_date date,
  end_date date,
  status text default 'active' check (status in ('active', 'paused', 'completed', 'cancelled')),
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

-- 7. PAYMENTS
create table public.payments (
  id uuid default gen_random_uuid() primary key,
  project_id uuid references public.projects(id) on delete cascade not null,
  vendor text not null,
  description text,
  amount numeric(12,2) not null,
  status text default 'pending' check (status in ('paid', 'pending', 'overdue')),
  due_date date,
  paid_date date,
  created_at timestamptz default now()
);

-- 8. MILESTONES (hitos del proyecto)
create table public.milestones (
  id uuid default gen_random_uuid() primary key,
  project_id uuid references public.projects(id) on delete cascade not null,
  name text not null,
  target_date date,
  actual_date date,
  status text default 'pending' check (status in ('done', 'active', 'delayed', 'pending')),
  created_at timestamptz default now()
);

-- 9. PROJECT COSTS (rubros de costos)
create table public.project_costs (
  id uuid default gen_random_uuid() primary key,
  project_id uuid references public.projects(id) on delete cascade not null,
  category text not null,
  budgeted numeric(12,2) not null,
  actual numeric(12,2) default 0,
  variance_pct numeric(5,2),
  updated_at timestamptz default now()
);

-- 10. ALERTS
create table public.alerts (
  id uuid default gen_random_uuid() primary key,
  project_id uuid references public.projects(id) on delete cascade not null,
  severity text default 'medium' check (severity in ('high', 'medium', 'low')),
  title text not null,
  description text,
  is_read boolean default false,
  created_at timestamptz default now()
);

-- ============================================
-- INDEXES
-- ============================================
create index idx_messages_conversation on public.messages(conversation_id);
create index idx_messages_created on public.messages(created_at);
create index idx_conversations_user on public.conversations(user_id);
create index idx_payments_project on public.payments(project_id);
create index idx_material_prices_material on public.material_prices(material_id);
create index idx_milestones_project on public.milestones(project_id);
create index idx_project_costs_project on public.project_costs(project_id);
create index idx_alerts_project on public.alerts(project_id);

-- ============================================
-- ROW LEVEL SECURITY (RLS)
-- ============================================

-- Enable RLS on all tables
alter table public.profiles enable row level security;
alter table public.conversations enable row level security;
alter table public.messages enable row level security;
alter table public.materials enable row level security;
alter table public.material_prices enable row level security;
alter table public.projects enable row level security;
alter table public.payments enable row level security;
alter table public.milestones enable row level security;
alter table public.project_costs enable row level security;
alter table public.alerts enable row level security;

-- PROFILES: users can read/update their own profile
create policy "Users can view own profile"
  on public.profiles for select using (auth.uid() = id);

create policy "Users can update own profile"
  on public.profiles for update using (auth.uid() = id);

-- CONVERSATIONS: users see only their own
create policy "Users can CRUD own conversations"
  on public.conversations for all using (auth.uid() = user_id);

-- MESSAGES: users see messages from their conversations
create policy "Users can CRUD own messages"
  on public.messages for all
  using (conversation_id in (
    select id from public.conversations where user_id = auth.uid()
  ));

-- MATERIALS: everyone can read, only admins can write
create policy "Anyone can read materials"
  on public.materials for select using (true);

create policy "Anyone can read material prices"
  on public.material_prices for select using (true);

-- PROJECTS: users see only their own
create policy "Users can CRUD own projects"
  on public.projects for all using (auth.uid() = user_id);

-- PAYMENTS: users see payments from their projects
create policy "Users can CRUD own payments"
  on public.payments for all
  using (project_id in (
    select id from public.projects where user_id = auth.uid()
  ));

-- MILESTONES: users see milestones from their projects
create policy "Users can CRUD own milestones"
  on public.milestones for all
  using (project_id in (
    select id from public.projects where user_id = auth.uid()
  ));

-- PROJECT COSTS: users see costs from their projects
create policy "Users can CRUD own project costs"
  on public.project_costs for all
  using (project_id in (
    select id from public.projects where user_id = auth.uid()
  ));

-- ALERTS: users see alerts from their projects
create policy "Users can CRUD own alerts"
  on public.alerts for all
  using (project_id in (
    select id from public.projects where user_id = auth.uid()
  ));

-- ============================================
-- UPDATED_AT TRIGGER
-- ============================================
create or replace function public.update_updated_at()
returns trigger as $$
begin
  new.updated_at = now();
  return new;
end;
$$ language plpgsql;

create trigger set_updated_at before update on public.profiles
  for each row execute procedure public.update_updated_at();

create trigger set_updated_at before update on public.conversations
  for each row execute procedure public.update_updated_at();

create trigger set_updated_at before update on public.materials
  for each row execute procedure public.update_updated_at();

create trigger set_updated_at before update on public.projects
  for each row execute procedure public.update_updated_at();

create trigger set_updated_at before update on public.project_costs
  for each row execute procedure public.update_updated_at();
