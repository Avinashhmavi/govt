# Quick Test Guide - Google Sheets Integration

## ✅ What's Already Working

1. **Google Sheets Connection** - ✅ Tested and working
2. **Credentials** - ✅ Valid (`gcp.json`)
3. **Sheet Access** - ✅ Connected to sheet ID: `1XT3A8iW5gbWl76qSeSQZ-6BG2hUluGbx24VYxwr1HkE`

## 🚀 Quick Test Steps

### Option 1: Using Docker (Recommended)

```bash
# Build and run with Docker
docker-compose up --build

# Or if using Dockerfile directly
docker build -t govt-app .
docker run -p 5009:5000 govt-app
```

Then:
1. Go to `http://localhost:5009/admin`
2. Login: `admin` / `5555`
3. Click "Sheet सेटअप करा" to initialize
4. Test sync functionality

### Option 2: Manual Python Setup

```bash
# Activate venv (if using uv)
source .venv/bin/activate

# Or create fresh venv
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install gspread google-auth Flask psycopg2-binary python-dotenv werkzeug

# Run the app
python3 app.py
```

### Option 3: Test Google Sheets Connection Only

```bash
# Test connection (no Flask needed)
python3 test_sheets.py
```

This will verify:
- ✅ Google Sheets connection
- ✅ Credentials validity
- ✅ Sheet read/write access

## 📋 Testing Checklist

Once app is running:

- [ ] **Initialize Sheet**: Click "Sheet सेटअप करा" button
- [ ] **Verify Sheet**: Check Google Sheet has all persons
- [ ] **Test Toggle**: Toggle availability in dashboard → Check sheet updates
- [ ] **Test Sheet Edit**: Edit availability in sheet → Click sync → Check database
- [ ] **Test Auto Sync**: Wait 5 minutes → Check if changes sync automatically

## 🔗 Direct Sheet Link

Open your Google Sheet:
https://docs.google.com/spreadsheets/d/1XT3A8iW5gbWl76qSeSQZ-6BG2hUluGbx24VYxwr1HkE

## ✅ Current Status

- Google Sheets API: ✅ Working
- Service Account: ✅ Configured  
- Sheet Access: ✅ Connected
- Ready for: Initialization and sync testing

