# Deployment Guide: Alternate History Engine

Complete guide to deploy your Alternate History Engine to production:
- **Frontend**: Vercel
- **Backend**: Railway

---

## 📋 Pre-Deployment Checklist

### What You Have
- ✅ FastAPI backend with MongoDB Atlas
- ✅ React frontend (Vite)
- ✅ MongoDB Atlas database (already configured)
- ✅ 4 AI API keys (Qwen/Grok, Gemini, DeepSeek, Groq)

### What You Need
- [ ] GitHub account
- [ ] Vercel account (free tier works)
- [ ] Railway account (free tier works)
- [ ] Your MongoDB Atlas connection string
- [ ] Your AI API keys

---

## 🚀 Part 1: Deploy Backend to Railway

### Step 1: Prepare Backend for Railway

**Files to Create:**

#### 1. Create `Procfile` in project root
```
web: uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

#### 2. Create `runtime.txt` in project root
```
python-3.11
```

#### 3. Update `requirements.txt` (add if missing)
```
python-dotenv
openai
google-generativeai
groq
pymongo
fastapi
uvicorn
pydantic-settings
apscheduler
httpx
```

### Step 2: Push Code to GitHub

```bash
# If not already a git repo
git init
git add .
git commit -m "Prepare for deployment"

# Create a new repo on GitHub, then:
git remote add origin https://github.com/YOUR_USERNAME/alternate_history.git
git branch -M main
git push -u origin main
```

### Step 3: Deploy on Railway

1. **Go to [Railway.app](https://railway.app/)**
2. **Click "Start a New Project"**
3. **Select "Deploy from GitHub repo"**
4. **Choose your `alternate_history` repository**
5. **Railway will auto-detect it's a Python app**

### Step 4: Configure Environment Variables on Railway

In Railway dashboard → Your Project → Variables tab, add:

```bash
# AI Model API Keys
AI_ML=your_qwen_api_key
Gemini_Key=your_gemini_api_key
OpenRouter=your_openrouter_api_key
Groq=your_groq_api_key

# Database
MONGO_URI=mongodb+srv://shonee114:shone123@cluster0.s4ywegj.mongodb.net/?appName=Cluster0
DB_NAME=alternate_history
UNIVERSE_ID=cold_war_no_moon_landing

# Security
ADMIN_API_KEY=your-secure-admin-key-here

# Scheduler
ENABLE_SCHEDULER=True
SCHEDULE_TIME=09:51
TIMEZONE=Asia/Kolkata
API_BASE_URL=https://your-app-name.up.railway.app
```

> [!IMPORTANT]
> Replace `your-app-name` with your actual Railway app URL (you'll get this after deployment)

### Step 5: Configure Railway Settings

1. **In Settings → Networking:**
   - Railway will auto-assign a domain like `your-app.up.railway.app`
   - Note this URL - you'll need it for the frontend

2. **In Settings → Deploy:**
   - Root Directory: `/` (leave as default)
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

### Step 6: Test Backend Deployment

Once deployed, visit:
- `https://your-app.up.railway.app/health` → Should return `{"status": "healthy"}`
- `https://your-app.up.railway.app/timeline` → Should return your timeline events

---

## 🎨 Part 2: Deploy Frontend to Vercel

### Step 1: Update Frontend API URL

**File to Modify:** `alt history frontend/src/api.js`

**Current (Line 2):**
```javascript
const API_BASE_URL = 'http://localhost:8000';
```

**Change to:**
```javascript
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
```

This allows environment-based configuration.

### Step 2: Create Environment File for Vercel

**Create:** `alt history frontend/.env.production`

```bash
VITE_API_URL=https://your-app.up.railway.app
```

> [!IMPORTANT]
> Replace `your-app.up.railway.app` with your actual Railway backend URL

### Step 3: Update Build Configuration (Optional)

**Create:** `alt history frontend/vercel.json`

```json
{
  "buildCommand": "npm run build",
  "outputDirectory": "dist",
  "devCommand": "npm run dev",
  "installCommand": "npm install"
}
```

### Step 4: Deploy on Vercel

#### Option A: Via Vercel Dashboard (Recommended)

1. **Go to [Vercel.com](https://vercel.com/)**
2. **Click "Add New Project"**
3. **Import your GitHub repository**
4. **Configure:**
   - Framework Preset: **Vite**
   - Root Directory: **alt history frontend**
   - Build Command: `npm run build`
   - Output Directory: `dist`
5. **Add Environment Variable:**
   - Name: `VITE_API_URL`
   - Value: `https://your-app.up.railway.app`
6. **Click "Deploy"**

#### Option B: Via Vercel CLI

```bash
cd "alt history frontend"
npm install -g vercel
vercel

# Follow prompts:
# - Link to existing project? No
# - Project name: alternate-history-frontend
# - Directory: ./
# - Override settings? No
```

Then add environment variable in Vercel dashboard.

### Step 5: Test Frontend Deployment

Visit your Vercel URL (e.g., `https://alternate-history-frontend.vercel.app`)

Test commands in terminal:
- `help`
- `timeline`
- `latest`
- `status`

---

## 🔧 Required Code Changes Summary

### Backend (Railway)
**Files to CREATE:**
1. `Procfile` - Railway start command
2. `runtime.txt` - Python version

**No code changes needed** - Backend already uses environment variables

### Frontend (Vercel)
**Files to MODIFY:**
1. `alt history frontend/src/api.js` - Line 2, change API_BASE_URL to use environment variable

**Files to CREATE:**
1. `alt history frontend/.env.production` - Production API URL

**Optional:**
1. `alt history frontend/vercel.json` - Build configuration

---

## 🔒 Security Considerations

### 1. Update CORS on Backend

**File:** `app/main.py`

**Current (Line 20):**
```python
allow_origins=["*"],
```

**Change to:**
```python
allow_origins=[
    "https://your-frontend.vercel.app",
    "http://localhost:5173"  # Keep for local development
],
```

### 2. Change Admin API Key

In Railway environment variables, change:
```bash
ADMIN_API_KEY=use-a-strong-random-key-here
```

Generate a secure key:
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 3. MongoDB Atlas Network Access

1. Go to MongoDB Atlas → Network Access
2. Add Railway's IP addresses OR
3. Allow access from anywhere (0.0.0.0/0) - less secure but easier

---

## 📊 Environment Variables Reference

### Railway (Backend)

| Variable | Example | Required |
|----------|---------|----------|
| `AI_ML` | `sk-...` | Yes |
| `Gemini_Key` | `AIza...` | Yes |
| `OpenRouter` | `sk-or-...` | Yes |
| `Groq` | `gsk_...` | Yes |
| `MONGO_URI` | `mongodb+srv://...` | Yes |
| `DB_NAME` | `alternate_history` | Yes |
| `UNIVERSE_ID` | `cold_war_no_moon_landing` | Yes |
| `ADMIN_API_KEY` | `your-secure-key` | Yes |
| `ENABLE_SCHEDULER` | `True` | Yes |
| `SCHEDULE_TIME` | `09:51` | Yes |
| `TIMEZONE` | `Asia/Kolkata` | Yes |
| `API_BASE_URL` | `https://your-app.up.railway.app` | Yes |

### Vercel (Frontend)

| Variable | Example | Required |
|----------|---------|----------|
| `VITE_API_URL` | `https://your-app.up.railway.app` | Yes |

---

## 🧪 Testing Deployment

### Backend Health Check
```bash
curl https://your-app.up.railway.app/health
# Expected: {"status":"healthy"}
```

### Frontend API Connection
1. Visit your Vercel URL
2. Type `timeline` in terminal
3. Should display events from MongoDB Atlas

### Scheduler Check
```bash
curl https://your-app.up.railway.app/health/scheduler
# Expected: {"status":"running","next_run_time":"...","timezone":"Asia/Kolkata"}
```

### Admin Endpoint Test
```bash
curl -X POST https://your-app.up.railway.app/admin/simulate/day \
  -H "x-admin-key: your-admin-key"
# Expected: {"day_index":3,"message":"Day 3 simulation completed successfully"}
```

---

## 🐛 Troubleshooting

### Backend Issues

**Problem:** Railway build fails
- **Solution:** Check `requirements.txt` has all dependencies
- **Solution:** Ensure `Procfile` exists with correct command

**Problem:** MongoDB connection timeout
- **Solution:** Check MongoDB Atlas Network Access allows Railway IPs
- **Solution:** Verify `MONGO_URI` environment variable is correct

**Problem:** Scheduler not running
- **Solution:** Check `ENABLE_SCHEDULER=True` in Railway env vars
- **Solution:** Verify `API_BASE_URL` points to Railway domain

### Frontend Issues

**Problem:** API calls fail (CORS error)
- **Solution:** Update `allow_origins` in `app/main.py` to include Vercel URL
- **Solution:** Redeploy backend after CORS change

**Problem:** API returns 404
- **Solution:** Check `VITE_API_URL` environment variable in Vercel
- **Solution:** Ensure Railway backend is running

**Problem:** Build fails on Vercel
- **Solution:** Ensure Root Directory is set to `alt history frontend`
- **Solution:** Check Framework Preset is set to **Vite**

---

## 📝 Deployment Checklist

### Pre-Deployment
- [ ] MongoDB Atlas configured and accessible
- [ ] All AI API keys ready
- [ ] Code pushed to GitHub

### Backend (Railway)
- [ ] Created `Procfile`
- [ ] Created `runtime.txt`
- [ ] Deployed to Railway
- [ ] Added all environment variables
- [ ] Tested `/health` endpoint
- [ ] Tested `/timeline` endpoint
- [ ] Noted Railway URL for frontend

### Frontend (Vercel)
- [ ] Updated `api.js` to use environment variable
- [ ] Created `.env.production` with Railway URL
- [ ] Deployed to Vercel
- [ ] Added `VITE_API_URL` environment variable
- [ ] Tested terminal interface
- [ ] Tested API connectivity

### Security
- [ ] Updated CORS to allow only Vercel domain
- [ ] Changed `ADMIN_API_KEY` to secure value
- [ ] Configured MongoDB Atlas network access

### Final Testing
- [ ] Frontend loads successfully
- [ ] Timeline command works
- [ ] Latest command works
- [ ] Status command shows scheduler running
- [ ] Simulate command works with admin key

---

## 🎉 Success!

Your Alternate History Engine is now deployed:
- **Frontend**: `https://your-app.vercel.app`
- **Backend**: `https://your-app.up.railway.app`
- **Database**: MongoDB Atlas (cloud)

The scheduler will automatically generate new timeline events daily at 09:51 IST!

---

## 💡 Tips

1. **Free Tier Limits:**
   - Railway: 500 hours/month, $5 credit
   - Vercel: Unlimited deployments
   - MongoDB Atlas: 512MB free forever

2. **Monitoring:**
   - Railway: Check logs in dashboard
   - Vercel: Check deployment logs
   - MongoDB Atlas: Monitor in Atlas dashboard

3. **Updates:**
   - Push to GitHub → Railway auto-deploys
   - Push to GitHub → Vercel auto-deploys

4. **Custom Domains:**
   - Railway: Settings → Networking → Custom Domain
   - Vercel: Settings → Domains → Add Domain
