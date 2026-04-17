-- ============================================
-- Migration 0002: Add email, plan, last_login to profiles
-- Run this in Supabase SQL Editor
-- ============================================

-- 1. Add email column
ALTER TABLE public.profiles ADD COLUMN email VARCHAR(255);

-- 2. Backfill email from auth.users
UPDATE public.profiles p
SET email = u.email
FROM auth.users u
WHERE p.id = u.id;

-- 3. Set NOT NULL constraint
ALTER TABLE public.profiles ALTER COLUMN email SET NOT NULL;

-- 4. Unique index on email
CREATE UNIQUE INDEX ix_profiles_email ON public.profiles(email);

-- 5. Add plan column (free, pro, enterprise)
ALTER TABLE public.profiles
ADD COLUMN plan VARCHAR(20) NOT NULL DEFAULT 'free';

-- 6. Add last_login column
ALTER TABLE public.profiles
ADD COLUMN last_login TIMESTAMPTZ;

-- 7. Update trigger to include email on signup
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS trigger AS $$
BEGIN
    INSERT INTO public.profiles (id, email, full_name)
    VALUES (
        NEW.id,
        NEW.email,
        NEW.raw_user_meta_data->>'full_name'
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
