# 🚀 Deploying to Render - Complete Guide

This guide will walk you through deploying your Biometric Attendance System to Render with PostgreSQL database.

## 📋 Prerequisites

- ✅ GitHub account with your code pushed to a repository
- ✅ Render account (sign up at [render.com](https://render.com))
- ✅ Supabase account with PostgreSQL database (or use Render's PostgreSQL)

---

## 🗄️ Step 1: Set Up PostgreSQL Database

### Option A: Using Supabase (Recommended - You're already doing this!)

You already have Supabase credentials. You'll use the **DATABASE_URL** from Supabase.

**Get your DATABASE_URL:**
1. Go to your Supabase project dashboard
2. Click **Settings** → **Database**
3. Scroll to **Connection String** → **URI**
4. Copy the connection string (it looks like: `postgresql://postgres:[password]@[host]:5432/postgres`)

### Option B: Using Render PostgreSQL

1. In Render dashboard, click **New** → **PostgreSQL**
2. Name: `attendance-db`
3. Database: `attendance_db`
4. User: `attendance_user`
5. Region: Choose closest to you
6. Plan: **Free** (or paid for better performance)
7. Click **Create Database**
8. Copy the **Internal Database URL** (starts with `postgresql://`)

---

## 🌐 Step 2: Create Web Service on Render

1. **Go to Render Dashboard** → Click **New** → **Web Service**

2. **Connect Your Repository:**
   - Click **Connect GitHub** (or GitLab/Bitbucket)
   - Authorize Render to access your repositories
   - Select your biometric-attendance-system repository

3. **Configure the Web Service:**
   - **Name:** `biometric-attendance-system` (or your preferred name)
   - **Region:** Choose closest to you
   - **Branch:** `main`
   - **Root Directory:** `biometric-attendance-system` (the folder containing app.py)
   - **Runtime:** `Python 3`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app:app`

4. **Choose Plan:**
   - **Free** tier is fine for testing
   - **Paid** ($7/month) recommended for production with face recognition

---

## 🔐 Step 3: Configure Environment Variables

In the **Environment Variables** section, add these variables:

### Required Variables:

```bash
# Database Configuration
DATABASE_URL=postgresql://postgres:[YOUR_PASSWORD]@[HOST]:5432/postgres
DATABASE_TYPE=postgresql

# Application Secret (generate a random string)
SECRET_KEY=your-super-secret-key-change-this-to-random-string

# Supabase (you already added these - good!)
VITE_SUPABASE_URL=https://fyhwkrpuhzznymzdvann.supabase.co
VITE_SUPABASE_PUBLISHABLE_KEY=sb_publishable_Yi7rkRlY0seiD4vz8DmaRA_CzEBcBVa
```

### How to Add Environment Variables:

1. Scroll to **Environment Variables** section
2. Click **Add Environment Variable**
3. Enter **Key** and **Value**
4. Repeat for each variable above

> [!IMPORTANT]
> Replace `[YOUR_PASSWORD]` and `[HOST]` in DATABASE_URL with your actual Supabase credentials!

---

## 🛠️ Step 4: Deploy!

1. Click **Create Web Service** at the bottom
2. Render will start building and deploying your app
3. Wait for the build to complete (5-10 minutes)
4. Watch the logs for any errors

### Expected Build Process:
```
==> Installing dependencies
==> pip install -r requirements.txt
==> Starting application
==> gunicorn app:app
```

---

## 🎯 Step 5: Initialize Database

After deployment succeeds, you need to create database tables and admin user.

### Method 1: Using Render Shell (Recommended)

1. In your Render service dashboard, click **Shell** tab
2. Run these commands:

```bash
# Initialize database tables
python init_db.py

# Verify tables were created
python -c "from app import app, db; from models import Admin; app.app_context().push(); print('Tables:', db.engine.table_names())"
```

### Method 2: Using Local Script with Remote Database

1. On your local machine, temporarily set DATABASE_URL:
```bash
# Windows PowerShell
$env:DATABASE_URL="your-supabase-database-url"
python init_db.py
```

---

## ✅ Step 6: Test Your Deployment

1. **Get Your App URL:**
   - Render provides a URL like: `https://biometric-attendance-system.onrender.com`
   - Find it at the top of your service dashboard

2. **Test Login:**
   - Go to your app URL
   - You should see the login page
   - Default admin credentials (if created by init_db.py):
     - Email: `admin@example.com`
     - Password: `admin123`

3. **Test Basic Features:**
   - Login as admin
   - Try adding a faculty member
   - Check if database is working

---

## 🐛 Troubleshooting

### Build Fails with "face-recognition" Error

**Problem:** `dlib` or `cmake` installation fails

**Solution 1 - Use Docker (Paid tier required):**
Create a `Dockerfile` in your project root:

```dockerfile
FROM python:3.11-slim

# Install system dependencies for face-recognition
RUN apt-get update && apt-get install -y \
    cmake \
    build-essential \
    libopenblas-dev \
    liblapack-dev \
    libx11-dev \
    libgtk-3-dev

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
CMD ["gunicorn", "app:app"]
```

Then in Render, change **Runtime** to **Docker**.

**Solution 2 - Disable Face Recognition (Free tier):**
Temporarily comment out face recognition in `requirements.txt`:
```
# face-recognition  # Disabled for Render free tier
```

### Database Connection Error

**Check:**
1. DATABASE_URL is correct (copy from Supabase exactly)
2. DATABASE_TYPE is set to `postgresql`
3. Database is accessible (Supabase should be public by default)

### Application Crashes on Start

**Check Logs:**
1. Go to **Logs** tab in Render dashboard
2. Look for Python errors
3. Common issues:
   - Missing environment variables
   - Database connection failed
   - Import errors

### Static Files Not Loading

Add to your `app.py` (if not already present):
```python
app.config['STATIC_FOLDER'] = 'static'
```

---

## 📊 Post-Deployment

### Create Admin User (if not exists)

Access Render Shell and run:
```python
python -c "
from app import app, db
from models import Admin
from werkzeug.security import generate_password_hash

with app.app_context():
    admin = Admin(
        name='Admin',
        email='admin@example.com',
        password=generate_password_hash('admin123')
    )
    db.session.add(admin)
    db.session.commit()
    print('Admin created!')
"
```

### Monitor Your App

- **Logs:** Check regularly for errors
- **Metrics:** Render provides CPU/Memory usage
- **Uptime:** Free tier sleeps after 15 min inactivity

---

## 🔄 Updating Your App

When you push changes to GitHub:
1. Render automatically detects the push
2. Rebuilds and redeploys your app
3. No manual intervention needed!

---

## 💡 Tips

1. **Use Paid Tier for Production:** Free tier has limitations
2. **Set Up Custom Domain:** Available in Render settings
3. **Enable HTTPS:** Automatic with Render
4. **Monitor Logs:** Check for errors regularly
5. **Backup Database:** Export from Supabase regularly

---

## 🆘 Need Help?

- **Render Docs:** [docs.render.com](https://docs.render.com)
- **Supabase Docs:** [supabase.com/docs](https://supabase.com/docs)
- **Check Logs:** Most issues show up in Render logs

---

## 📝 Quick Reference

### Your Configuration:
- **Supabase URL:** `https://fyhwkrpuhzznymzdvann.supabase.co`
- **Database Type:** PostgreSQL
- **Python Version:** 3.11
- **Web Framework:** Flask + Gunicorn

### Required Files in Your Repo:
- ✅ `requirements.txt` - Python dependencies
- ✅ `Procfile` - Tells Render how to start app
- ✅ `runtime.txt` - Python version
- ✅ `app.py` - Main application
- ✅ `.gitignore` - Excludes .env from git

---

**🎉 Congratulations!** Your biometric attendance system should now be live on Render!
