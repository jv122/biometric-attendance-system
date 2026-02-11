# PostgreSQL Setup Guide - Supabase

This guide will help you set up PostgreSQL for the Biometric Attendance System using Supabase.

## Prerequisites

- A Supabase account (free tier available)
- Python 3.7+ installed
- Git (optional, for version control)

## Step 1: Create a Supabase Project

1. **Sign up for Supabase**
   - Go to [https://supabase.com](https://supabase.com)
   - Click "Start your project" and sign up (free tier available)

2. **Create a New Project**
   - Click "New Project"
   - Fill in the details:
     - **Name**: `biometric-attendance` (or your preferred name)
     - **Database Password**: Create a strong password (SAVE THIS!)
     - **Region**: Choose the closest region to you
   - Click "Create new project"
   - Wait 2-3 minutes for the project to be provisioned

## Step 2: Get Your Database Connection String

1. **Navigate to Database Settings**
   - In your Supabase project dashboard
   - Click on the **Settings** icon (⚙️) in the left sidebar
   - Select **Database**

2. **Copy Connection String**
   - Scroll down to **Connection string**
   - Select the **URI** tab
   - Copy the connection string (it looks like this):
     ```
     postgresql://postgres:[YOUR-PASSWORD]@db.xxxxxxxxxxxxx.supabase.co:5432/postgres
     ```
   - **Important**: Replace `[YOUR-PASSWORD]` with the database password you created in Step 1

## Step 3: Configure Your Application

1. **Update the `.env` file**
   
   Open the `.env` file in your project directory and update it:

   ```env
   # Database Configuration
   DATABASE_TYPE=postgresql

   # PostgreSQL/Supabase Connection
   DATABASE_URL=postgresql://postgres:YOUR_ACTUAL_PASSWORD@db.tkmchhbmxlmpndcusdgo.supabase.co:5432/postgres

   # Application Secret Key
   SECRET_KEY=your-secret-key-change-in-production
   ```

   **Replace**:
   - `YOUR_ACTUAL_PASSWORD` with your Supabase database password
   - The entire `DATABASE_URL` with your copied connection string (with password filled in)

2. **Verify `.env` file location**
   
   Make sure the `.env` file is in the same directory as `app.py`

## Step 4: Install Dependencies

Open a terminal/command prompt in your project directory and run:

```bash
pip install -r requirements.txt
```

This will install:
- `psycopg2-binary` - PostgreSQL adapter
- `python-dotenv` - Environment variable loader
- All other required packages

## Step 5: Initialize the Database

Run the database initialization script:

```bash
python init_db.py
```

**Expected Output**:
```
Database Configuration: Using POSTGRESQL
Dropping existing tables...
Creating tables...
Created Admin: admin@college.edu / admin123
Created Faculty: faculty@college.edu / faculty123
Initialized database with new schema, hashed passwords, and subjects.
```

## Step 6: Verify Database Setup

1. **Check Supabase Dashboard**
   - Go to your Supabase project
   - Click on **Table Editor** in the left sidebar
   - You should see the following tables:
     - `admin`
     - `faculty`
     - `student`
     - `subject`
     - `attendance_record`
     - `attendance_session`
     - `leave_application`
     - `timetable`

2. **Verify Default Data**
   - Click on the `admin` table - should have 1 row
   - Click on the `faculty` table - should have 1 row
   - Click on the `subject` table - should have 7 rows

## Step 7: Run the Application

Start the Flask application:

```bash
python app.py
```

**Expected Output**:
```
Database Configuration: Using POSTGRESQL
DEBUG: App Configuration Loaded. CSRF DISABLED.
 * Running on http://127.0.0.1:5000
```

Open your browser and go to: `http://localhost:5000`

## Default Login Credentials

After initialization, you can log in with:

**Admin Account**:
- Email: `admin@college.edu`
- Password: `admin123`

**Faculty Account**:
- Email: `faculty@college.edu`
- Password: `faculty123`

## Troubleshooting

### Error: "No module named 'psycopg2'"

**Solution**: Install the PostgreSQL adapter
```bash
pip install psycopg2-binary
```

### Error: "connection to server failed"

**Possible causes**:
1. **Wrong password**: Double-check your database password in `.env`
2. **Wrong connection string**: Verify you copied the full URI from Supabase
3. **Network issues**: Check your internet connection
4. **Firewall**: Ensure port 5432 is not blocked

**Solution**: Verify your `.env` file has the correct `DATABASE_URL`

### Error: "relation does not exist"

**Cause**: Database tables haven't been created

**Solution**: Run the initialization script
```bash
python init_db.py
```

### Error: "SSL connection required"

**Cause**: Supabase requires SSL connections

**Solution**: Add `?sslmode=require` to your connection string:
```env
DATABASE_URL=postgresql://postgres:password@db.xxx.supabase.co:5432/postgres?sslmode=require
```

### Want to switch back to SQLite?

Simply change the `.env` file:
```env
DATABASE_TYPE=sqlite
```

The application will automatically use the local SQLite database.

## Supabase Free Tier Limits

- **Database Size**: 500 MB
- **Bandwidth**: 5 GB
- **API Requests**: 500,000 per month

This is more than sufficient for a college attendance system with hundreds of students.

## Security Best Practices

1. **Never commit `.env` to Git**
   - The `.gitignore` file should already exclude it
   - Verify: `git status` should not show `.env`

2. **Use strong passwords**
   - Change the default `SECRET_KEY` in `.env`
   - Use a strong database password

3. **Enable Row Level Security (RLS)** (Optional, for production)
   - In Supabase dashboard, go to Authentication > Policies
   - Create policies to restrict direct database access

## Need Help?

- **Supabase Documentation**: [https://supabase.com/docs](https://supabase.com/docs)
- **PostgreSQL Documentation**: [https://www.postgresql.org/docs/](https://www.postgresql.org/docs/)
- **Project Issues**: Check the README.md or contact your system administrator
