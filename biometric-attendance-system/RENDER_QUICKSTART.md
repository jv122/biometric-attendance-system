# 🚀 Quick Start - Render Deployment

## What You Need to Add in Render

### Environment Variables (Add these in Render Dashboard)

```bash
# 1. Database URL (Get from Supabase)
DATABASE_URL=postgresql://postgres.xxxxx:your_password@aws-0-region.pooler.supabase.com:5432/postgres

# 2. Database Type
DATABASE_TYPE=postgresql

# 3. Secret Key (Generate a random one!)
SECRET_KEY=generate-a-random-32-character-string-here

# 4. Supabase (Optional - you already added these)
VITE_SUPABASE_URL=https://fyhwkrpuhzznymzdvann.supabase.co
VITE_SUPABASE_PUBLISHABLE_KEY=sb_publishable_Yi7rkRlY0seiD4vz8DmaRA_CzEBcBVa
```

## How to Get Your Supabase DATABASE_URL

1. Go to [Supabase Dashboard](https://supabase.com/dashboard)
2. Select your project
3. Click **Settings** (gear icon) → **Database**
4. Scroll to **Connection String** section
5. Click **URI** tab
6. Copy the connection string
7. **IMPORTANT:** Replace `[YOUR-PASSWORD]` with your actual database password

Example:
```
postgresql://postgres.xxxxx:MyActualPassword123@aws-0-us-east-1.pooler.supabase.com:5432/postgres
```

## Generate a SECRET_KEY

Run this in your terminal:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

Copy the output and use it as your SECRET_KEY.

## Render Service Configuration

- **Build Command:** `pip install -r requirements.txt`
- **Start Command:** `gunicorn app:app`
- **Root Directory:** `biometric-attendance-system`

## After Deployment

1. Wait for build to complete
2. Click **Shell** tab in Render
3. Run: `python init_db.py`
4. Visit your app URL
5. Login with default admin (if created):
   - Email: `admin@example.com`
   - Password: `admin123`

---

**Need detailed instructions?** See [RENDER_DEPLOYMENT.md](./RENDER_DEPLOYMENT.md)
