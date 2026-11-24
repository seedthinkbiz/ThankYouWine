-- 땡큐와인 회원: 내가 산 와인 모아 보기 + 산 와인에만 별점·한 줄 메모 (2026-11-24)
-- 코르크매치와 같은 Supabase 프로젝트(bgkignhdshaclcgxrsbp)를 써요. 코르크매치의 supabase-schema.sql(관리자 is_admin)을 먼저 실행한 프로젝트에 실행합니다.
-- Supabase 대시보드 → SQL Editor → New query 에 전부 붙여넣고 Run. 여러 번 실행해도 괜찮아요.
--
-- 개인정보 원칙
--  · 구매 내역엔 가격·결제 금액·주소를 올리지 않아요. 와인 이름·구매 날짜·병 수만.
--  · 선불권 금액(충전·사용·잔액)만 예외로, 그 손님 본인에게만 보여요.
--  · 장부 손님 전체를 올리지 않아요. 회원이 가입하고 휴대폰 번호를 남기면, 관리자가 장부 손님과 맞는지 확인하고 '연결'한 사람의 구매만 올라가요.
--  · 구매 내역과 별점·메모는 본인과 관리자만 봐요.

-- ① 땡큐와인 회원 정보 (본인만 읽고 쓰기, 관리자는 보기)
create table if not exists public.ty_profiles (
  id uuid primary key references auth.users(id) on delete cascade,
  name text not null default '' check (char_length(name) <= 50),
  phone text not null default '' check (char_length(phone) <= 20),
  email text not null default '' check (char_length(email) <= 200),
  agreed_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
alter table public.ty_profiles enable row level security;
drop policy if exists ty_profiles_own on public.ty_profiles;
create policy ty_profiles_own on public.ty_profiles for all to authenticated
  using (id = auth.uid()) with check (id = auth.uid());
drop policy if exists ty_profiles_admin on public.ty_profiles;
create policy ty_profiles_admin on public.ty_profiles for select to authenticated
  using (public.is_admin());

-- ② 회원 ↔ 장부 손님 연결 (관리자만 만들고 지움, 본인은 연결됐는지만 봄)
create table if not exists public.ty_links (
  user_id uuid primary key references auth.users(id) on delete cascade,
  ref text not null unique check (char_length(ref) <= 80),       -- 장부 members 문서 id
  linked_at timestamptz not null default now()
);
alter table public.ty_links enable row level security;
drop policy if exists ty_links_own_read on public.ty_links;
create policy ty_links_own_read on public.ty_links for select to authenticated using (user_id = auth.uid());
drop policy if exists ty_links_admin on public.ty_links;
create policy ty_links_admin on public.ty_links for all to authenticated
  using (public.is_admin()) with check (public.is_admin());

-- ③ 구매 내역 (연결된 회원 것만, 관리자가 장부 파일로 올림). 가격 칸은 일부러 없어요.
create table if not exists public.ty_purchases (
  id text primary key check (char_length(id) <= 120),             -- 장부 판매 문서 id + 줄 번호
  ref text not null check (char_length(ref) <= 80),
  date date,
  wine_key text not null check (char_length(wine_key) <= 40),     -- 사이트 와인 목록 키(w…) 또는 목록에 없는 와인(x…)
  wine text not null check (char_length(wine) <= 120),
  qty int check (qty between 0 and 999),
  updated_at timestamptz not null default now()
);
create index if not exists ty_purchases_ref on public.ty_purchases(ref);

-- ③-2 선불권(충전·사용·잔액): 연결된 본인 것만 보기, 관리자가 장부에서 올림. 본인 계정 안에서만 금액이 보여요.
create table if not exists public.ty_prepaid (
  id text primary key check (char_length(id) <= 120),
  ref text not null check (char_length(ref) <= 80),
  date date,
  kind text not null check (kind in ('충전','사용','조정')),
  amount int not null check (amount between -100000000 and 100000000),   -- 충전 +, 사용 −
  label text not null default '' check (char_length(label) <= 120),
  updated_at timestamptz not null default now()
);
create index if not exists ty_prepaid_ref on public.ty_prepaid(ref);
alter table public.ty_prepaid enable row level security;
drop policy if exists ty_prepaid_own on public.ty_prepaid;
create policy ty_prepaid_own on public.ty_prepaid for select to authenticated
  using (ref = (select l.ref from public.ty_links l where l.user_id = auth.uid()));
drop policy if exists ty_prepaid_admin on public.ty_prepaid;
create policy ty_prepaid_admin on public.ty_prepaid for all to authenticated
  using (public.is_admin()) with check (public.is_admin());

-- 연결을 끊거나(관리자) 계정이 지워지면(코르크매치 탈퇴 포함) 그 사람 구매 내역·선불권도 같이 지워요.
create or replace function public.ty_links_cleanup()
returns trigger language plpgsql security definer set search_path = public as $$
begin
  delete from public.ty_purchases where ref = old.ref;
  delete from public.ty_prepaid where ref = old.ref;
  return old;
end $$;
drop trigger if exists ty_links_cleanup on public.ty_links;
create trigger ty_links_cleanup after delete on public.ty_links for each row execute function public.ty_links_cleanup();
alter table public.ty_purchases enable row level security;
drop policy if exists ty_purchases_own on public.ty_purchases;
create policy ty_purchases_own on public.ty_purchases for select to authenticated
  using (ref = (select l.ref from public.ty_links l where l.user_id = auth.uid()));
drop policy if exists ty_purchases_admin on public.ty_purchases;
create policy ty_purchases_admin on public.ty_purchases for all to authenticated
  using (public.is_admin()) with check (public.is_admin());

-- ④ 별점·한 줄 메모: 산 와인에만 남길 수 있어요
create or replace function public.ty_bought(k text)
returns boolean language sql stable security definer set search_path = public as $$
  select exists (
    select 1 from public.ty_purchases p join public.ty_links l on l.ref = p.ref
    where l.user_id = auth.uid() and p.wine_key = k);
$$;
revoke all on function public.ty_bought(text) from public, anon;
grant execute on function public.ty_bought(text) to authenticated;

create table if not exists public.ty_reviews (
  user_id uuid not null references auth.users(id) on delete cascade,
  wine_key text not null check (char_length(wine_key) <= 40),
  stars numeric(2,1) check (stars is null or (stars between 0.5 and 5 and stars * 2 = floor(stars * 2))),
  note text not null default '' check (char_length(note) <= 100),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  primary key (user_id, wine_key)
);
alter table public.ty_reviews enable row level security;
drop policy if exists ty_reviews_read on public.ty_reviews;
create policy ty_reviews_read on public.ty_reviews for select to authenticated
  using (user_id = auth.uid() or public.is_admin());
drop policy if exists ty_reviews_insert on public.ty_reviews;
create policy ty_reviews_insert on public.ty_reviews for insert to authenticated
  with check (user_id = auth.uid() and public.ty_bought(wine_key));
drop policy if exists ty_reviews_update on public.ty_reviews;
create policy ty_reviews_update on public.ty_reviews for update to authenticated
  using (user_id = auth.uid()) with check (user_id = auth.uid() and public.ty_bought(wine_key));
drop policy if exists ty_reviews_delete on public.ty_reviews;
create policy ty_reviews_delete on public.ty_reviews for delete to authenticated using (user_id = auth.uid());

-- ⑤ 땡큐와인 회원 탈퇴: 땡큐와인 정보(회원 정보·연결·별점)를 지워요.
--    같은 로그인을 코르크매치·비노나루에서 쓰고 있지 않으면 로그인 계정까지 지워요.
create or replace function public.ty_leave()
returns void language plpgsql security definer set search_path = public, auth as $$
declare uid uuid := auth.uid(); other boolean := false;
begin
  if uid is null then raise exception 'not signed in'; end if;
  delete from public.ty_reviews where user_id = uid;
  delete from public.ty_links where user_id = uid;
  delete from public.ty_profiles where id = uid;
  if to_regclass('public.profiles') is not null then
    execute 'select exists(select 1 from public.profiles where id = $1)' into other using uid;
  end if;
  if not other and to_regclass('public.vn_members') is not null then
    execute 'select exists(select 1 from public.vn_members where id = $1)' into other using uid;
  end if;
  if not other then delete from auth.users where id = uid; end if;
end $$;
revoke all on function public.ty_leave() from public, anon;
grant execute on function public.ty_leave() to authenticated;
