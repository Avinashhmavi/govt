# Instant Sync Setup Guide

## ✅ Current Setup: Near-Instant Sync (30 seconds)

Your app is now configured for **near-instant sync** - changes sync every **30 seconds** automatically. This is the simplest solution and works immediately.

### How It Works:
- Changes in Google Sheet → Wait max 30 seconds → Database updated automatically
- No setup required - already working!

---

## 🚀 Option 2: True Instant Sync (Google Apps Script)

For **truly instant sync** (immediate when you edit the sheet), you can install a Google Apps Script.

### Requirements:
- Your Flask app must be publicly accessible (not localhost)
- Use a tunneling service like ngrok for local testing

### Setup Steps:

#### 1. Make Your App Publicly Accessible

**Option A: Using ngrok (for local testing)**
```bash
# Install ngrok: https://ngrok.com/download
ngrok http 5009

# Copy the HTTPS URL (e.g., https://abc123.ngrok.io)
```

**Option B: Deploy to Production**
- Deploy your Flask app to a cloud service (Heroku, AWS, etc.)
- Get your public URL

#### 2. Install Google Apps Script

1. **Open your Google Sheet:**
   https://docs.google.com/spreadsheets/d/1XT3A8iW5gbWl76qSeSQZ-6BG2hUluGbx24VYxwr1HkE

2. **Go to Extensions → Apps Script**

3. **Delete any existing code** and paste the code from `google_apps_script_instant_sync.js`

4. **Replace `YOUR_SYNC_URL`** with your public URL:
   ```javascript
   const SYNC_URL = 'https://your-domain.com/admin/sync_sheets';
   // Or if using ngrok:
   const SYNC_URL = 'https://abc123.ngrok.io/admin/sync_sheets';
   ```

5. **Save the script** (Ctrl+S or Cmd+S)

6. **Set up Trigger:**
   - Click on the clock icon (Triggers) in the left sidebar
   - Click "+ Add Trigger" (bottom right)
   - Configure:
     - **Function to run:** `onEdit`
     - **Event source:** From spreadsheet
     - **Event type:** On edit
   - Click **Save**
   - Authorize the script when prompted

#### 3. Test It

1. Edit a status in your Google Sheet
2. Wait 2-3 seconds
3. Check your database - it should update instantly!

#### 4. Manual Sync Menu

The script also adds a menu item:
- **Database Sync → Sync Now** (in Google Sheets menu bar)
- Click it anytime to trigger immediate sync

---

## 📊 Comparison

| Method | Speed | Setup Complexity | Best For |
|--------|-------|------------------|----------|
| **30-second polling** | ~30 seconds | ✅ None (already active) | Most users |
| **Google Apps Script** | Instant | ⚠️ Requires public URL | Production deployments |

---

## 🔧 Current Configuration

Your app is set to sync every **30 seconds** by default. To change this:

**Environment Variable:**
```bash
export SYNC_INTERVAL_MINUTES=0.5  # 30 seconds (current)
export SYNC_INTERVAL_MINUTES=1    # 1 minute
export SYNC_INTERVAL_MINUTES=2    # 2 minutes
```

Or edit `.env` file:
```
SYNC_INTERVAL_MINUTES=0.5
```

---

## ✅ Recommendation

**For most use cases, 30-second sync is perfect:**
- ✅ No setup required
- ✅ Works immediately
- ✅ Very fast (30 seconds is practically instant for availability tracking)
- ✅ No external dependencies

**Use Google Apps Script only if:**
- You need true instant sync (< 5 seconds)
- Your app is deployed publicly
- You're comfortable with Apps Script setup

---

## 🎯 Current Status

✅ **30-second auto-sync is ACTIVE** - Changes sync within 30 seconds automatically!

