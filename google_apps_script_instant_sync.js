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
  // Only sync if the edit was in the Status column (Column C = index 3)
  // Also check that it's not the date row (row 1) or header row (row 2)
  const editedColumn = e.range.getColumn();
  const editedRow = e.range.getRow();
  
  if (editedColumn === 3 && editedRow > 2) { // Column C is the Status column, and row > 2 (skip date and header rows)
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
 * Update the date row (row 1) with current date
 * This function is called automatically when the sheet opens and daily at midnight via trigger.
 */
function updateDateRow() {
  try {
    const sheet = SpreadsheetApp.getActiveSheet();
    const today = new Date();
    const dateString = Utilities.formatDate(today, Session.getScriptTimeZone(), 'dd-MMM-yyyy');
    const dateDisplay = '📅 Today: ' + dateString;
    
    // Update cell A1 (date row is merged across A1:C1)
    sheet.getRange('A1').setValue(dateDisplay);
    
    Logger.log('Date row updated to: ' + dateDisplay);
  } catch (error) {
    Logger.log('Error updating date row: ' + error.toString());
  }
}

/**
 * Set up time-based trigger for daily date updates
 * This creates a trigger that runs updateDateRow() every day at midnight
 * The trigger is automatically created when the sheet is first opened
 */
function setupDailyDateTrigger() {
  try {
    // Delete existing triggers for this function to avoid duplicates
    const triggers = ScriptApp.getProjectTriggers();
    triggers.forEach(trigger => {
      if (trigger.getHandlerFunction() === 'updateDateRow' && 
          trigger.getEventType() === ScriptApp.EventType.CLOCK) {
        ScriptApp.deleteTrigger(trigger);
      }
    });
    
    // Create new daily trigger at midnight (12am-1am)
    ScriptApp.newTrigger('updateDateRow')
      .timeBased()
      .everyDays(1)
      .atHour(0)  // Midnight
      .create();
    
    Logger.log('Daily date trigger created successfully');
    return true;
  } catch (error) {
    Logger.log('Error setting up daily date trigger: ' + error.toString());
    return false;
  }
}

/**
 * Add custom menu for manual sync
 * Also sets up daily date trigger automatically if it doesn't exist
 */
function onOpen() {
  // Update date row when sheet opens
  updateDateRow();
  
  // Check if daily trigger exists, if not, create it
  const triggers = ScriptApp.getProjectTriggers();
  const hasDailyTrigger = triggers.some(t => 
    t.getHandlerFunction() === 'updateDateRow' && 
    t.getEventType() === ScriptApp.EventType.CLOCK
  );
  
  if (!hasDailyTrigger) {
    setupDailyDateTrigger();
  }
  
  const ui = SpreadsheetApp.getUi();
  ui.createMenu('Database Sync')
    .addItem('Sync Now', 'manualSync')
    .addItem('Update Date', 'updateDateRow')
    .addItem('Setup Daily Date Trigger', 'setupDailyDateTrigger')
    .addToUi();
}

