-- 땡큐와인 앱 알림(웹 푸시): 특가·신규 입고 소식 (2026-11-25)
-- 코르크매치와 같은 Supabase 프로젝트(bgkignhdshaclcgxrsbp), supabase-thankyou.sql 다음에 실행해요.
-- SQL Editor → New query 에 전부 붙여넣고 Run. 여러 번 실행해도 괜찮아요.
--
-- 원칙
--  · 손님은 로그인 없이 알림을 켤 수 있어요. 저장되는 건 브라우저가 만든 '알림 받을 주소'와 받을 소식 종류, 동의 시각뿐이에요.
--  · 알림 주소 목록은 관리자만 봐요. 손님 브라우저는 자기 주소를 넣고·빼고·상태를 묻는 함수만 쓸 수 있어요.
--  · 알림 서명 키는 관리자 화면에서 처음 한 번 만들어 여기에 저장해요(사람이 키를 옮겨 적지 않아요). 비밀 키는 관리자만 읽어요.

-- ① 알림 받는 기기
create table if not exists public.ty_push_subs (
  endpoint text primary key check (endpoint ~ '^https://' and char_length(endpoint) <= 1000),
  p256dh text not null check (char_length(p256dh) <= 200),
  auth text not null check (char_length(auth) <= 100),
  topics text[] not null default array['sale','new'] check (topics <@ array['sale','new']),
  user_id uuid references auth.users(id) on delete set null,
  ua text not null default '' check (char_length(ua) <= 300),
  agreed_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
alter table public.ty_push_subs enable row level security;
drop policy if exists ty_push_subs_admin on public.ty_push_subs;
create policy ty_push_subs_admin on public.ty_push_subs for all to authenticated
  using (public.is_admin()) with check (public.is_admin());

create or replace function public.ty_push_subscribe(p_endpoint text, p_p256dh text, p_auth text, p_topics text[], p_ua text default '')
returns timestamptz language plpgsql security definer set search_path = public as $$
declare t text[]; at timestamptz;
begin
  select coalesce(array_agg(distinct x), array[]::text[]) into t from unnest(p_topics) x where x in ('sale','new');
  if cardinality(t) = 0 then
    delete from public.ty_push_subs where endpoint = p_endpoint; return null;
  end if;
  insert into public.ty_push_subs(endpoint, p256dh, auth, topics, user_id, ua)
  values (p_endpoint, p_p256dh, p_auth, t, auth.uid(), left(coalesce(p_ua,''), 300))
  on conflict (endpoint) do update set p256dh = excluded.p256dh, auth = excluded.auth, topics = excluded.topics,
    user_id = coalesce(excluded.user_id, ty_push_subs.user_id), ua = excluded.ua, updated_at = now()
  returning agreed_at into at;
  return at;
end $$;
grant execute on function public.ty_push_subscribe(text, text, text, text[], text) to anon, authenticated;

create or replace function public.ty_push_unsubscribe(p_endpoint text)
returns void language sql security definer set search_path = public as $$
  delete from public.ty_push_subs where endpoint = p_endpoint;
$$;
grant execute on function public.ty_push_unsubscribe(text) to anon, authenticated;

-- 내 기기가 등록돼 있는지(받는 소식 종류·동의 시각). 주소를 아는 기기만 물을 수 있어요.
create or replace function public.ty_push_status(p_endpoint text)
returns table(topics text[], agreed_at timestamptz) language sql stable security definer set search_path = public as $$
  select topics, agreed_at from public.ty_push_subs where endpoint = p_endpoint;
$$;
grant execute on function public.ty_push_status(text) to anon, authenticated;

-- ② 알림 서명 키(VAPID). 한 줄만 있어요.
create table if not exists public.ty_push_config (
  id int primary key default 1 check (id = 1),
  public_key text not null,
  private_key text not null,
  created_at timestamptz not null default now()
);
alter table public.ty_push_config enable row level security;
drop policy if exists ty_push_config_admin on public.ty_push_config;
create policy ty_push_config_admin on public.ty_push_config for all to authenticated
  using (public.is_admin()) with check (public.is_admin());

create or replace function public.ty_push_public_key()
returns text language sql stable security definer set search_path = public as $$
  select public_key from public.ty_push_config where id = 1;
$$;
grant execute on function public.ty_push_public_key() to anon, authenticated;

-- ③ 보낸 알림 기록 (관리자만)
create table if not exists public.ty_push_log (
  id bigint generated always as identity primary key,
  sent_at timestamptz not null default now(),
  topic text not null,
  title text not null,
  body text not null default '',
  url text not null default '',
  test boolean not null default false,
  sent int not null default 0,
  failed int not null default 0,
  removed int not null default 0,
  by_email text not null default ''
);
alter table public.ty_push_log enable row level security;
drop policy if exists ty_push_log_admin on public.ty_push_log;
create policy ty_push_log_admin on public.ty_push_log for all to authenticated
  using (public.is_admin()) with check (public.is_admin());
