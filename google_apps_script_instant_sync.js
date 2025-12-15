/**
 * Google Apps Script for Instant Sync
 * 
 * This script triggers instant sync to your database when changes are made in the Google Sheet.
 * 
 * SETUP INSTRUCTIONS:
 * 1. Open your Google Sheet
 * 2. Go to Extensions > Apps Script
 * 3. Paste this code
 * 4. Replace YOUR_SYNC_URL with your Flask app's public URL (e.g., https://your-domain.com/admin/sync_sheets)
 * 5. Save the script
 * 6. Set up a trigger: Edit > Current project's triggers > Add Trigger
 *    - Choose function: onEdit
 *    - Event source: From spreadsheet
 *    - Event type: On edit
 *    - Click Save
 * 
 * NOTE: Your Flask app must be publicly accessible (not localhost) for this to work.
 * For local testing, use a tunneling service like ngrok:
 *   ngrok http 5009
 *   Then use the ngrok URL as YOUR_SYNC_URL
 */

// Replace this with your Flask app's sync endpoint URL
const SYNC_URL = 'YOUR_SYNC_URL/admin/sync_sheets'; // e.g., 'https://your-domain.com/admin/sync_sheets'

/**
 * Triggered when any cell is edited in the sheet
 */
function onEdit(e) {
  // Only sync if the edit was in the Status column (Column C = index 2)
  const editedColumn = e.range.getColumn();
  
  if (editedColumn === 3) { // Column C is the Status column
    // Wait 2 seconds to allow user to finish editing
    Utilities.sleep(2000);
    
    // Trigger sync
    triggerSync();
  }
}

/**
 * Triggers the sync by calling the Flask app endpoint
 */
function triggerSync() {
  try {
    const options = {
      'method': 'post',
      'contentType': 'application/json',
      'muteHttpExceptions': true
    };
    
    const response = UrlFetchApp.fetch(SYNC_URL, options);
    const result = JSON.parse(response.getContentText());
    
    if (result.success) {
      Logger.log(`Sync successful: ${result.updated_count} updated`);
    } else {
      Logger.log(`Sync failed: ${result.error}`);
    }
  } catch (error) {
    Logger.log(`Error triggering sync: ${error.toString()}`);
  }
}

/**
 * Manual sync function (can be called from menu)
 */
function manualSync() {
  triggerSync();
  SpreadsheetApp.getUi().alert('Sync triggered! Check your database.');
}

/**
 * Add custom menu for manual sync
 */
function onOpen() {
  const ui = SpreadsheetApp.getUi();
  ui.createMenu('Database Sync')
    .addItem('Sync Now', 'manualSync')
    .addToUi();
}

