# Deployment Guide

This guide covers deploying the Email Analytics Dashboard to various hosting platforms.

## Prerequisites

1. **GitHub Account** - Push your code to GitHub first
2. **Database with scraped data** - Make sure you've run the scraper locally first

## Option 1: Render (Recommended - Free)

### Step 1: Push to GitHub

```bash
cd email-analytics-dashboard
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/email-analytics-dashboard.git
git push -u origin main
```

### Step 2: Deploy Database

1. Go to https://render.com and sign up
2. Click **"New +"** → **"PostgreSQL"**
3. Name: `email-analytics-db`
4. Database: `email_analytics`
5. Click **"Create Database"**
6. **Save the connection details** (you'll need them)

### Step 3: Import Your Data

Since you've already scraped emails locally, you need to export and import:

**Export from local database:**
```bash
pg_dump -U postgres -d email_analytics > backup.sql
```

**Import to Render database:**
```bash
psql -h <render-host> -U <render-user> -d email_analytics < backup.sql
```

### Step 4: Deploy Backend

1. Click **"New +"** → **"Web Service"**
2. Connect your GitHub repository
3. Name: `email-analytics-backend`
4. Root Directory: Leave blank
5. Build Command: `pip install -r requirements.txt`
6. Start Command: `cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT`
7. Add Environment Variables:
   - `DB_HOST` - from Render database
   - `DB_PORT` - from Render database
   - `DB_NAME` - `email_analytics`
   - `DB_USER` - from Render database
   - `DB_PASSWORD` - from Render database
8. Click **"Create Web Service"**

### Step 5: Deploy Frontend

1. Click **"New +"** → **"Static Site"**
2. Connect your GitHub repository
3. Name: `email-analytics-frontend`
4. Build Command: `cd frontend && npm install && npm run build`
5. Publish Directory: `frontend/build`
6. Add Environment Variable:
   - `REACT_APP_API_URL` - URL of your backend (from step 4)
7. Click **"Create Static Site"**

### Step 6: Update Frontend API URL

Update `frontend/src/App.jsx` line 15:
```javascript
const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';
```

Commit and push:
```bash
git add .
git commit -m "Update API URL for production"
git push
```

Render will auto-deploy the changes.

---

## Option 2: Railway (Easiest)

### Step 1: Push to GitHub (same as above)

### Step 2: Deploy on Railway

1. Go to https://railway.app and sign up with GitHub
2. Click **"New Project"** → **"Deploy from GitHub repo"**
3. Select your repository
4. Railway will auto-detect Python and Node.js

### Step 3: Add PostgreSQL

1. Click **"New"** → **"Database"** → **"PostgreSQL"**
2. Railway will automatically set environment variables

### Step 4: Configure Services

**Backend:**
- Start Command: `cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT`
- Environment variables are auto-configured

**Frontend:**
- Build Command: `cd frontend && npm install && npm run build`
- Start Command: `cd frontend && npm start`

### Step 5: Import Data

Use Railway's database connection string to import your local data.

---

## Option 3: Vercel (Frontend Only)

If you want to keep the backend local or on another service:

1. Go to https://vercel.com
2. Import your GitHub repository
3. Framework Preset: **Create React App**
4. Root Directory: `frontend`
5. Build Command: `npm run build`
6. Output Directory: `build`
7. Add Environment Variable:
   - `REACT_APP_API_URL` - Your backend URL
8. Click **"Deploy"**

---

## Important Notes

### CORS Configuration

Update `backend/main.py` to allow your frontend domain:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://your-frontend-domain.vercel.app",  # Add your domain
        "https://your-frontend-domain.onrender.com"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Database Migration

Since you've already scraped emails locally, you have two options:

**Option A: Export and Import**
- Export local database
- Import to hosted database
- Recommended if you have a lot of emails

**Option B: Re-scrape**
- Run the scraper again after deployment
- Simpler but requires logging in again

### Security

For production:
1. Use strong database passwords
2. Don't commit `.env` file
3. Use environment variables on hosting platform
4. Enable SSL/HTTPS (most platforms do this automatically)

---

## Costs

- **Render Free Tier:** Database sleeps after 90 days of inactivity
- **Railway Free Tier:** $5 credit/month (usually enough)
- **Vercel Free Tier:** Unlimited for personal projects
- **DigitalOcean:** $5/month minimum

---

## Troubleshooting

### Frontend can't connect to backend
- Check CORS settings
- Verify `REACT_APP_API_URL` is set correctly
- Ensure backend is running

### Database connection failed
- Verify all environment variables are set
- Check database is running
- Verify connection string format

### Build failed
- Check build logs
- Ensure all dependencies are in `requirements.txt` and `package.json`
- Verify Python and Node versions

---

## Recommended Approach

**For beginners:** Use **Railway** - it's the easiest with auto-configuration

**For free hosting:** Use **Render** - generous free tier

**For best performance:** Use **Vercel (frontend)** + **Railway (backend + DB)**

---

## Need Help?

Check the hosting platform's documentation:
- Render: https://render.com/docs
- Railway: https://docs.railway.app
- Vercel: https://vercel.com/docs
