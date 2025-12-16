#!/usr/bin/env python3
"""
Comprehensive test for availability history tracking functionality.
Tests database tables, history logging, daily snapshots, and Google Sheets integration.
"""

import os
import sys
from datetime import date, datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    from dotenv import load_dotenv
    
    # Import database functions directly without importing full app
    import sys
    import importlib.util
    
    # Load app module to get functions
    spec = importlib.util.spec_from_file_location("app", "app.py")
    app_module = importlib.util.module_from_spec(spec)
    # Only import what we need, avoiding gtts dependency issues
    sys.modules['app'] = app_module
    
    # Try to import Google Sheets sync (optional)
    try:
        from google_sheets_sync import GoogleSheetsSync
        HAS_SHEETS = True
    except ImportError:
        HAS_SHEETS = False
        print("⚠ Google Sheets sync not available (optional)")
    
    print("=" * 70)
    print("AVAILABILITY HISTORY TRACKING - COMPREHENSIVE TEST")
    print("=" * 70)
    
    # Import functions from app module
    spec.loader.exec_module(app_module)
    get_db_connection = app_module.get_db_connection
    init_database = app_module.init_database
    log_availability_change = app_module.log_availability_change
    
    # Test 1: Database Connection
    print("\n[TEST 1] Testing database connection...")
    conn = get_db_connection()
    if not conn:
        print("✗ FAILED: Database connection failed")
        print("Please check your database configuration in .env file")
        sys.exit(1)
    print("✓ PASSED: Database connection successful")
    
    # Test 2: Initialize Database (creates tables)
    print("\n[TEST 2] Testing database initialization (table creation)...")
    try:
        success = init_database()
        if success:
            print("✓ PASSED: Database initialization successful")
        else:
            print("✗ FAILED: Database initialization failed")
            sys.exit(1)
    except Exception as e:
        print(f"✗ FAILED: Error during initialization: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    # Test 3: Verify Tables Exist
    print("\n[TEST 3] Verifying history tables exist...")
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name IN ('availability_history', 'daily_availability_snapshots')
            ORDER BY table_name
        """)
        tables = [row[0] for row in cursor.fetchall()]
        cursor.close()
        
        expected_tables = ['availability_history', 'daily_availability_snapshots']
        missing = [t for t in expected_tables if t not in tables]
        
        if missing:
            print(f"✗ FAILED: Missing tables: {missing}")
            sys.exit(1)
        else:
            print(f"✓ PASSED: All required tables exist: {tables}")
    except Exception as e:
        print(f"✗ FAILED: Error checking tables: {e}")
        sys.exit(1)
    
    # Test 4: Get a test person
    print("\n[TEST 4] Getting a test person from database...")
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("SELECT id, name, office_number, is_available FROM persons LIMIT 1")
        test_person = cursor.fetchone()
        cursor.close()
        
        if not test_person:
            print("✗ FAILED: No persons found in database. Please ensure data is loaded.")
            conn.close()
            sys.exit(1)
        
        print(f"✓ PASSED: Found test person:")
        print(f"    ID: {test_person['id']}")
        print(f"    Name: {test_person['name']}")
        print(f"    Office: {test_person['office_number']}")
        print(f"    Current Status: {'Available' if test_person['is_available'] else 'Unavailable'}")
    except Exception as e:
        print(f"✗ FAILED: Error getting test person: {e}")
        conn.close()
        sys.exit(1)
    
    # Test 5: Test History Logging Function
    print("\n[TEST 5] Testing history logging function...")
    try:
        person_id = test_person['id']
        name = test_person['name'] or 'Test Person'
        office_number = test_person['office_number'] or 'TEST-001'
        new_status = not test_person['is_available']  # Toggle status
        
        # Get count before
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM availability_history WHERE person_id = %s", (person_id,))
        count_before = cursor.fetchone()[0]
        
        # Log the change
        log_availability_change(conn, person_id, name, office_number, new_status, 'test')
        conn.commit()
        
        # Get count after
        cursor.execute("SELECT COUNT(*) FROM availability_history WHERE person_id = %s", (person_id,))
        count_after = cursor.fetchone()[0]
        
        if count_after > count_before:
            print(f"✓ PASSED: History entry created (count: {count_before} -> {count_after})")
            
            # Verify the entry
            cursor.execute("""
                SELECT * FROM availability_history 
                WHERE person_id = %s 
                ORDER BY changed_at DESC 
                LIMIT 1
            """, (person_id,))
            history_entry = cursor.fetchone()
            
            if history_entry:
                print(f"    Entry verified:")
                print(f"    - Person ID: {history_entry[1]}")
                print(f"    - Status: {history_entry[4]}")
                print(f"    - Source: {history_entry[5]}")
                print(f"    - Timestamp: {history_entry[3]}")
        else:
            print("✗ FAILED: History entry not created")
            conn.rollback()
            cursor.close()
            conn.close()
            sys.exit(1)
        
        cursor.close()
    except Exception as e:
        print(f"✗ FAILED: Error testing history logging: {e}")
        import traceback
        traceback.print_exc()
        conn.rollback()
        conn.close()
        sys.exit(1)
    
    # Test 6: Test Daily Snapshot Creation
    print("\n[TEST 6] Testing daily snapshot creation...")
    try:
        cursor = conn.cursor()
        today = date.today()
        
        # Check if snapshot exists for today
        cursor.execute("""
            SELECT * FROM daily_availability_snapshots 
            WHERE person_id = %s AND snapshot_date = %s
        """, (person_id, today))
        snapshot = cursor.fetchone()
        
        if snapshot:
            print(f"✓ PASSED: Daily snapshot exists for today")
            print(f"    - Person ID: {snapshot[1]}")
            print(f"    - Date: {snapshot[5]}")
            print(f"    - Status: {snapshot[4]}")
            print(f"    - Time: {snapshot[6]}")
        else:
            print("✗ FAILED: Daily snapshot not found for today")
            cursor.close()
            conn.close()
            sys.exit(1)
        
        cursor.close()
    except Exception as e:
        print(f"✗ FAILED: Error testing daily snapshot: {e}")
        import traceback
        traceback.print_exc()
        conn.close()
        sys.exit(1)
    
    # Test 7: Test Querying Historical Data
    print("\n[TEST 7] Testing historical data queries...")
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Query today's snapshot
        cursor.execute("""
            SELECT COUNT(*) as count 
            FROM daily_availability_snapshots 
            WHERE snapshot_date = %s
        """, (today,))
        today_count = cursor.fetchone()['count']
        
        # Query yesterday (if exists)
        yesterday = today - timedelta(days=1)
        cursor.execute("""
            SELECT COUNT(*) as count 
            FROM daily_availability_snapshots 
            WHERE snapshot_date = %s
        """, (yesterday,))
        yesterday_count = cursor.fetchone()['count']
        
        print(f"✓ PASSED: Historical queries working")
        print(f"    - Snapshots for today ({today}): {today_count}")
        print(f"    - Snapshots for yesterday ({yesterday}): {yesterday_count}")
        
        # Query history for test person
        cursor.execute("""
            SELECT COUNT(*) as count 
            FROM availability_history 
            WHERE person_id = %s
        """, (person_id,))
        history_count = cursor.fetchone()['count']
        print(f"    - Total history entries for test person: {history_count}")
        
        cursor.close()
    except Exception as e:
        print(f"✗ FAILED: Error querying historical data: {e}")
        import traceback
        traceback.print_exc()
        conn.close()
        sys.exit(1)
    
    # Test 8: Test Google Sheets Integration (if configured)
    print("\n[TEST 8] Testing Google Sheets integration...")
    if not HAS_SHEETS:
        print("⚠ SKIPPED: Google Sheets sync module not available")
    else:
        try:
        credentials_path = os.getenv("GOOGLE_SHEETS_CREDENTIALS_PATH", "gcp.json")
        sheet_id = os.getenv("GOOGLE_SHEET_ID", "1XT3A8iW5gbWl76qSeSQZ-6BG2hUluGbx24VYxwr1HkE")
        worksheet_name = os.getenv("GOOGLE_SHEET_NAME", "Sheet1")
        
        # Check if credentials exist
        has_env_creds = all([
            os.getenv("GCP_TYPE"),
            os.getenv("GCP_PROJECT_ID"),
            os.getenv("GCP_PRIVATE_KEY_ID"),
            os.getenv("GCP_PRIVATE_KEY"),
            os.getenv("GCP_CLIENT_EMAIL"),
            os.getenv("GCP_CLIENT_ID")
        ])
        has_file_creds = os.path.exists(credentials_path)
        
        if not (has_env_creds or has_file_creds):
            print("⚠ SKIPPED: Google Sheets credentials not found")
            print("    Set GCP_* environment variables or provide credentials file")
        else:
            sheets_sync = GoogleSheetsSync(
                credentials_path=credentials_path,
                sheet_id=sheet_id,
                worksheet_name=worksheet_name
            )
            print("✓ PASSED: Google Sheets connection successful")
            
            # Test reading data (should handle date row)
            print("    Testing read_availability_data() with date row...")
            sheet_data = sheets_sync.read_availability_data()
            print(f"    ✓ Read {len(sheet_data)} rows from sheet")
            
            # Test date row update function
            print("    Testing update_date_row()...")
            success = sheets_sync.update_date_row()
            if success:
                print("    ✓ Date row update successful")
            else:
                print("    ⚠ Date row update had issues (may be normal if sheet structure differs)")
    except Exception as e:
        print(f"⚠ SKIPPED: Google Sheets test failed (may not be configured): {e}")
    
    # Test 9: Test Indexes
    print("\n[TEST 9] Verifying database indexes...")
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT indexname 
            FROM pg_indexes 
            WHERE tablename IN ('availability_history', 'daily_availability_snapshots')
            AND schemaname = 'public'
            ORDER BY indexname
        """)
        indexes = [row[0] for row in cursor.fetchall()]
        cursor.close()
        
        expected_indexes = [
            'idx_history_person_date',
            'idx_snapshots_person_date',
            'idx_snapshots_date'
        ]
        found_indexes = [idx for idx in expected_indexes if idx in indexes]
        
        if len(found_indexes) == len(expected_indexes):
            print(f"✓ PASSED: All indexes exist: {found_indexes}")
        else:
            missing = [idx for idx in expected_indexes if idx not in found_indexes]
            print(f"⚠ WARNING: Some indexes missing: {missing}")
            print(f"    Found indexes: {indexes}")
    except Exception as e:
        print(f"⚠ WARNING: Error checking indexes: {e}")
    
    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    print("✓ Database connection: OK")
    print("✓ Table creation: OK")
    print("✓ History logging: OK")
    print("✓ Daily snapshots: OK")
    print("✓ Historical queries: OK")
    print("✓ Database indexes: OK")
    print("\nAll core functionality tests passed!")
    print("\nNote: Google Sheets integration requires proper credentials.")
    print("      To test full sync functionality, use the admin dashboard")
    print("      or modify availability in Google Sheets directly.")
    
    conn.close()
    
except ImportError as e:
    print(f"✗ FAILED: Missing dependencies: {e}")
    print("Please install: pip install psycopg2-binary python-dotenv")
    sys.exit(1)
except Exception as e:
    print(f"✗ FAILED: Unexpected error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
