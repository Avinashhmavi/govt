# Fix Google Sheets Permissions

## Current Issue
The service account can **read** from the sheet but cannot **write/clear** it.

## Solution

### Step 1: Verify Service Account Email
The service account email is:
```
govt-524@concise-base-470907-q8.iam.gserviceaccount.com
```

### Step 2: Share Sheet with Editor Access

1. Open your Google Sheet:
   https://docs.google.com/spreadsheets/d/1XT3A8iW5gbWl76qSeSQZ-6BG2hUluGbx24VYxwr1HkE

2. Click the **"Share"** button (top right)

3. In the "Add people and groups" field, paste:
   ```
   govt-524@concise-base-470907-q8.iam.gserviceaccount.com
   ```

4. **IMPORTANT**: Change the permission from "Viewer" to **"Editor"**

5. Uncheck "Notify people" (service accounts don't need notifications)

6. Click **"Share"**

### Step 3: Verify Permissions

After sharing, wait 1-2 minutes for permissions to propagate, then test again:

```bash
source .venv/bin/activate
python3 init_sheet.py
# Type "yes" when prompted
```

### Alternative: Test Read-Only First

If you want to test read-only functionality first, you can:

1. Keep the sheet shared with "Viewer" access
2. Manually add some test data to the sheet
3. Test the sync FROM sheet TO database (read-only operation)

But for full functionality (initialization, updates), you need **Editor** access.

## Verification Checklist

- [ ] Sheet is shared with service account email
- [ ] Permission is set to **"Editor"** (not Viewer or Commenter)
- [ ] "Notify people" is unchecked
- [ ] Waited 1-2 minutes after sharing
- [ ] Test initialization again

## Current Status

✅ **Connection**: Working  
✅ **Read Access**: Working  
❌ **Write Access**: Needs Editor permission  
✅ **Code**: Ready and tested

