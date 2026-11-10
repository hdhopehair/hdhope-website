-- ============================================================================
-- HD Hope Hair Salon CMS — Supabase schema (V2)
-- 在 Supabase Dashboard → SQL Editor 一次貼上執行即可。
-- 內容：資料表、驗證/權限（RLS）、圖片儲存桶、updated_at 觸發器
-- ============================================================================

create extension if not exists pgcrypto;

-- ---------------------------------------------------------------- 1. 管理員名單
-- 只有列在 admins 的帳號能寫入資料；一般訪客與登入會員都不行。
create table if not exists public.admins (
  user_id    uuid primary key references auth.users(id) on delete cascade,
  email      text,
  created_at timestamptz not null default now()
);

comment on table public.admins is '後台管理員白名單，需與 Supabase Auth 使用者對應';

-- ---------------------------------------------------------------- 2. 設計師
create table if not exists public.stylists (
  id            uuid primary key default gen_random_uuid(),
  slug          text not null unique check (slug ~ '^[a-z0-9-]{2,40}$'),
  status        text not null default 'draft' check (status in ('draft','published','hidden')),
  sort_order    integer not null default 0,
  name          text not null default '',
  name_en       text not null default '',
  title         text not null default '',
  photo_path    text not null default '',
  photo_note    text not null default '',
  paragraphs    jsonb not null default '[]'::jsonb,   -- 個人介紹，多段
  philosophy    text not null default '',
  specialties   jsonb not null default '[]'::jsonb,   -- 擅長技術標籤
  styles        jsonb not null default '[]'::jsonb,   -- 風格標籤
  experience    text not null default '',
  tags          jsonb not null default '[]'::jsonb,
  instagram_url text not null default '',
  line_url      text not null default '',
  prices        jsonb not null default '[]'::jsonb,   -- [{name,val,note}]
  seo_title     text not null default '',
  seo_desc      text not null default '',
  created_at    timestamptz not null default now(),
  updated_at    timestamptz not null default now()
);
create index if not exists stylists_status_idx on public.stylists (status, sort_order);

-- ---------------------------------------------------------------- 3. 作品
create table if not exists public.works (
  id            uuid primary key default gen_random_uuid(),
  slug          text not null unique check (slug ~ '^[a-z0-9-]{2,60}$'),
  status        text not null default 'draft' check (status in ('draft','published','hidden')),
  sort_order    integer not null default 0,
  title         text not null default '',
  category      text not null default 'color'
                check (category in ('color','bleach','straightening','perm','cut','treatment','mens')),
  stylist_id    uuid references public.stylists(id) on delete set null,
  service_slug  text not null default '',
  photos        jsonb not null default '[]'::jsonb,   -- [{path,alt,crop}]
  alt           text not null default '',
  color_desc    text not null default '',
  bleached      text not null default '',
  completed_at  date,
  description   text not null default '',
  photo_note    text not null default '',
  seo_title     text not null default '',
  seo_desc      text not null default '',
  created_at    timestamptz not null default now(),
  updated_at    timestamptz not null default now()
);
create index if not exists works_status_idx on public.works (status, sort_order);
create index if not exists works_stylist_idx on public.works (stylist_id);
create index if not exists works_category_idx on public.works (category);

-- ---------------------------------------------------------------- 4. 媒體庫
create table if not exists public.media (
  id            uuid primary key default gen_random_uuid(),
  storage_path  text not null unique,   -- 例如 stylists/ryan-2026-11.webp
  filename      text not null default '',
  mime          text not null default 'image/webp',
  size_bytes    bigint not null default 0,
  width         integer,
  height        integer,
  alt           text not null default '',
  uploaded_by   uuid references auth.users(id) on delete set null,
  created_at    timestamptz not null default now()
);

-- ---------------------------------------------------------------- 5. 網站設定
create table if not exists public.settings (
  key        text primary key,          -- home | brand | contact
  value      jsonb not null default '{}'::jsonb,
  updated_at timestamptz not null default now()
);

-- ---------------------------------------------------------------- 6. 共用函式
create or replace function public.is_admin()
returns boolean
language sql stable security definer set search_path = public
as $$
  select exists (select 1 from public.admins a where a.user_id = auth.uid());
$$;

create or replace function public.touch_updated_at()
returns trigger language plpgsql as $$
begin
  new.updated_at = now();
  return new;
end $$;

drop trigger if exists stylists_touch on public.stylists;
create trigger stylists_touch before update on public.stylists
  for each row execute function public.touch_updated_at();

drop trigger if exists works_touch on public.works;
create trigger works_touch before update on public.works
  for each row execute function public.touch_updated_at();

drop trigger if exists settings_touch on public.settings;
create trigger settings_touch before update on public.settings
  for each row execute function public.touch_updated_at();

-- ---------------------------------------------------------------- 7. RLS
alter table public.admins   enable row level security;
alter table public.stylists enable row level security;
alter table public.works    enable row level security;
alter table public.media    enable row level security;
alter table public.settings enable row level security;

-- admins：管理員唯讀自己的名單列
drop policy if exists admins_self_read on public.admins;
create policy admins_self_read on public.admins
  for select using (auth.uid() = user_id);

-- stylists：公開只讀已發布；管理員全權
drop policy if exists stylists_public_read on public.stylists;
create policy stylists_public_read on public.stylists
  for select using (status = 'published' or public.is_admin());

drop policy if exists stylists_admin_write on public.stylists;
create policy stylists_admin_write on public.stylists
  for all using (public.is_admin()) with check (public.is_admin());

-- works：公開只讀已發布；管理員全權
drop policy if exists works_public_read on public.works;
create policy works_public_read on public.works
  for select using (status = 'published' or public.is_admin());

drop policy if exists works_admin_write on public.works;
create policy works_admin_write on public.works
  for all using (public.is_admin()) with check (public.is_admin());

-- media：公開可讀（圖片要能被官網載入）；只有管理員可新增/刪除
drop policy if exists media_public_read on public.media;
create policy media_public_read on public.media
  for select using (true);

drop policy if exists media_admin_write on public.media;
create policy media_admin_write on public.media
  for all using (public.is_admin()) with check (public.is_admin());

-- settings：公開可讀（官網要顯示），管理員可寫
drop policy if exists settings_public_read on public.settings;
create policy settings_public_read on public.settings
  for select using (true);

drop policy if exists settings_admin_write on public.settings;
create policy settings_admin_write on public.settings
  for all using (public.is_admin()) with check (public.is_admin());

-- ---------------------------------------------------------------- 8. 圖片儲存桶
insert into storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
values ('media', 'media', true, 8388608,
        array['image/jpeg','image/png','image/webp'])
on conflict (id) do update
  set public = excluded.public,
      file_size_limit = excluded.file_size_limit,
      allowed_mime_types = excluded.allowed_mime_types;

drop policy if exists media_obj_read on storage.objects;
create policy media_obj_read on storage.objects
  for select using (bucket_id = 'media');

drop policy if exists media_obj_write on storage.objects;
create policy media_obj_write on storage.objects
  for insert with check (bucket_id = 'media' and public.is_admin());

drop policy if exists media_obj_update on storage.objects;
create policy media_obj_update on storage.objects
  for update using (bucket_id = 'media' and public.is_admin());

drop policy if exists media_obj_delete on storage.objects;
create policy media_obj_delete on storage.objects
  for delete using (bucket_id = 'media' and public.is_admin());

-- ---------------------------------------------------------------- 9. 建立第一位管理員
-- 1) Authentication → Users → Add user（Email + 密碼，勾選 Auto Confirm）
-- 2) 執行下面這行（把 email 換成你的帳號），之後就能用該帳號登入 /admin/
--
-- insert into public.admins (user_id, email)
-- select id, email from auth.users where email = 'owner@hdhopehair.com';
