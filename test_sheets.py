#!/usr/bin/env python3
"""
Test script for Google Sheets integration
"""

import os
import sys

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from google_sheets_sync import GoogleSheetsSync
    
    # Try to import database connection, but don't fail if Flask isn't available
    try:
        from app import get_db_connection
        DB_AVAILABLE = True
    except ImportError:
        print("Note: Flask app not available, skipping database tests")
        DB_AVAILABLE = False
        def get_db_connection():
            return None
    
    print("=" * 60)
    print("Google Sheets Integration Test")
    print("=" * 60)
    
    # Configuration
    credentials_path = os.getenv("GOOGLE_SHEETS_CREDENTIALS_PATH", "gcp.json")
    sheet_id = os.getenv("GOOGLE_SHEET_ID", "1XT3A8iW5gbWl76qSeSQZ-6BG2hUluGbx24VYxwr1HkE")
    worksheet_name = os.getenv("GOOGLE_SHEET_NAME", "Sheet1")
    
    print(f"\n1. Testing Google Sheets connection...")
    print(f"   Credentials: {credentials_path}")
    print(f"   Sheet ID: {sheet_id}")
    print(f"   Worksheet: {worksheet_name}")
    
    # Check if credentials file exists
    if not os.path.exists(credentials_path):
        print(f"   ERROR: Credentials file not found: {credentials_path}")
        sys.exit(1)
    
    print(f"   ✓ Credentials file found")
    
    # Initialize sync service
    try:
        sheets_sync = GoogleSheetsSync(
            credentials_path=credentials_path,
            sheet_id=sheet_id,
            worksheet_name=worksheet_name
        )
        print(f"   ✓ Successfully connected to Google Sheet")
    except Exception as e:
        print(f"   ERROR: Failed to connect: {e}")
        sys.exit(1)
    
    # Test reading current sheet data
    print(f"\n2. Testing sheet read...")
    try:
        data = sheets_sync.read_availability_data()
        print(f"   ✓ Successfully read {len(data)} rows from sheet")
        if len(data) > 0:
            print(f"   Sample row: {data[0]}")
    except Exception as e:
        print(f"   ERROR: Failed to read sheet: {e}")
        sys.exit(1)
    
    # Test database connection
    if DB_AVAILABLE:
        print(f"\n3. Testing database connection...")
        try:
            conn = get_db_connection()
            if conn:
                print(f"   ✓ Database connection successful")
                from psycopg2.extras import RealDictCursor
                cursor = conn.cursor(cursor_factory=RealDictCursor)
                cursor.execute("SELECT COUNT(*) as count FROM persons")
                result = cursor.fetchone()
                print(f"   ✓ Found {result['count']} persons in database")
                cursor.close()
                conn.close()
            else:
                print(f"   ⚠ Database connection failed (may need Flask app running)")
        except Exception as e:
            print(f"   ⚠ Database error: {e}")
    else:
        print(f"\n3. Skipping database test (Flask not available)")
    
    # Test initialization
    if DB_AVAILABLE:
        print(f"\n4. Testing sheet initialization...")
        response = input("   Do you want to initialize the sheet? This will CLEAR existing data. (yes/no): ")
        if response.lower() == 'yes':
            try:
                success, message, rows_added = sheets_sync.initialize_sheet(get_db_connection)
                if success:
                    print(f"   ✓ Sheet initialized successfully!")
                    print(f"   {message}")
                    print(f"   {rows_added} rows added")
                else:
                    print(f"   ERROR: {message}")
            except Exception as e:
                print(f"   ERROR: {e}")
        else:
            print(f"   Skipped initialization")
    else:
        print(f"\n4. Skipping initialization test (requires database)")
    
    # Test finding a person
    if DB_AVAILABLE:
        print(f"\n5. Testing person lookup...")
        try:
            conn = get_db_connection()
            if conn:
                from psycopg2.extras import RealDictCursor
                cursor = conn.cursor(cursor_factory=RealDictCursor)
                cursor.execute("SELECT name, office_number FROM persons LIMIT 1")
                person = cursor.fetchone()
                cursor.close()
                conn.close()
                
                if person:
                    row_num = sheets_sync.find_row_by_person(person['name'], person['office_number'] or '')
                    if row_num:
                        print(f"   ✓ Found person '{person['name']}' at row {row_num}")
                    else:
                        print(f"   ⚠ Person '{person['name']}' not found in sheet (may need initialization)")
        except Exception as e:
            print(f"   ⚠ Error: {e}")
    else:
        print(f"\n5. Skipping person lookup test (requires database)")
    
    print(f"\n" + "=" * 60)
    print("Test completed successfully!")
    print("=" * 60)
    
except ImportError as e:
    print(f"ERROR: Missing dependencies: {e}")
    print("Please install: pip install gspread google-auth")
    sys.exit(1)
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

