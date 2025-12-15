# Google Sheets Integration Testing Instructions

## Prerequisites

1. **Install Dependencies**
   ```bash
   pip install gspread google-auth
   ```
   Or if using Docker, dependencies will be installed automatically.

2. **Verify Google Sheet Access**
   - Ensure the Google Sheet is shared with: `govt-524@concise-base-470907-q8.iam.gserviceaccount.com`
   - The service account should have Editor access

## Testing Steps

### Option 1: Using the Test Script

Run the test script:
```bash
python3 test_sheets.py
```

This will:
1. Test Google Sheets connection
2. Test database connection
3. Optionally initialize the sheet with all data
4. Test person lookup functionality

### Option 2: Using the Flask App

1. **Start the Flask application:**
   ```bash
   python3 app.py
   ```
   Or using Docker:
   ```bash
   docker-compose up
   ```

2. **Access Admin Dashboard:**
   - Navigate to: `http://localhost:5009/admin` (or your configured port)
   - Login with:
     - Username: `admin`
     - Password: `5555`

3. **Initialize the Sheet:**
   - Click the "Sheet सेटअप करा" (Setup Sheet) button
   - Confirm the action
   - Wait for completion message

4. **Test Sync:**
   - Click "Google Sheets सह सिंक करा" (Sync with Google Sheets) button
   - Check the sync status message

5. **Test Toggle:**
   - Toggle any person's availability using the switch
   - Check Google Sheet - it should update immediately

6. **Test Sheet → Database Sync:**
   - Manually change availability in Google Sheet
   - Wait 5 minutes OR click sync button
   - Check if database updated

## Expected Results

### After Initialization:
- Google Sheet should have:
  - Header row: Name (नाव) | Office Number (कार्यालय क्रमांक) | Availability Status (उपलब्धता)
  - All persons from database with their availability status
  - Header row formatted with blue background

### After Toggle:
- When admin toggles availability in dashboard:
  - Database updates immediately
  - Google Sheet updates immediately (within seconds)

### After Sheet Edit:
- When someone edits availability in Google Sheet:
  - Changes sync to database within 5 minutes (automatic)
  - OR immediately if manual sync button is clicked

## Troubleshooting

### "Google Sheets sync is not configured"
- Check that `gcp.json` exists in the project root
- Verify the file contains valid service account credentials

### "Failed to initialize Google Sheets client"
- Check that the sheet is shared with the service account email
- Verify the sheet ID is correct: `1XT3A8iW5gbWl76qSeSQZ-6BG2hUluGbx24VYxwr1HkE`
- Check credentials file path

### "Database connection error"
- Verify database environment variables are set:
  - DB_HOST
  - DB_PORT
  - DB_NAME
  - DB_USER
  - DB_PASSWORD

### Dependencies not installing
- Try: `pip install --break-system-packages gspread google-auth`
- Or use Docker: `docker-compose build`

## Manual Verification

1. **Check Google Sheet:**
   - Open: https://docs.google.com/spreadsheets/d/1XT3A8iW5gbWl76qSeSQZ-6BG2hUluGbx24VYxwr1HkE
   - Verify headers and data are present

2. **Check Database:**
   - Query: `SELECT name, office_number, is_available FROM persons LIMIT 10;`
   - Verify data matches sheet

3. **Test Bidirectional Sync:**
   - Change availability in sheet → Check database after sync
   - Change availability in dashboard → Check sheet immediately

