#!/usr/bin/env python3
"""
Initialize Google Sheet with database data
"""

import os
import sys
from dotenv import load_dotenv

load_dotenv()

try:
    from google_sheets_sync import GoogleSheetsSync
    from app import get_db_connection
    
    print("=" * 60)
    print("Google Sheet Initialization")
    print("=" * 60)
    
    credentials_path = os.getenv("GOOGLE_SHEETS_CREDENTIALS_PATH", "gcp.json")
    sheet_id = os.getenv("GOOGLE_SHEET_ID", "1XT3A8iW5gbWl76qSeSQZ-6BG2hUluGbx24VYxwr1HkE")
    worksheet_name = os.getenv("GOOGLE_SHEET_NAME", "Sheet1")
    
    print(f"\nConnecting to Google Sheet...")
    sheets_sync = GoogleSheetsSync(
        credentials_path=credentials_path,
        sheet_id=sheet_id,
        worksheet_name=worksheet_name
    )
    print("✓ Connected to Google Sheet")
    
    print(f"\nConnecting to database...")
    conn = get_db_connection()
    if not conn:
        print("✗ Database connection failed")
        print("Please check your database configuration in .env file")
        sys.exit(1)
    print("✓ Connected to database")
    
    print(f"\nInitializing sheet with database data...")
    print("WARNING: This will CLEAR all existing data in the sheet!")
    
    response = input("Continue? (yes/no): ")
    if response.lower() != 'yes':
        print("Cancelled.")
        sys.exit(0)
    
    success, message, rows_added = sheets_sync.initialize_sheet(get_db_connection)
    
    if success:
        print(f"\n✓ SUCCESS!")
        print(f"  {message}")
        print(f"  {rows_added} rows added to sheet")
        print(f"\nSheet URL: https://docs.google.com/spreadsheets/d/{sheet_id}")
    else:
        print(f"\n✗ ERROR: {message}")
        sys.exit(1)
        
except ImportError as e:
    print(f"ERROR: Missing dependencies: {e}")
    print("Please install: pip install gspread google-auth Flask psycopg2-binary")
    sys.exit(1)
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

