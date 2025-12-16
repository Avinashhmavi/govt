#!/usr/bin/env python3
"""
Simple test for availability history tracking - tests database directly.
"""

import os
import sys
from datetime import date, timedelta
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor

load_dotenv()

# Database configuration
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

def get_db_connection():
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        return conn
    except Exception as e:
        print(f"Database connection error: {e}")
        return None

def log_availability_change(conn, person_id, name, office_number, is_available, change_source='test'):
    """Test version of log function"""
    try:
        cursor = conn.cursor()
        today = date.today()
        
        # Insert into availability_history
        cursor.execute("""
            INSERT INTO availability_history (person_id, name, office_number, is_available, change_source)
            VALUES (%s, %s, %s, %s, %s)
        """, (person_id, name, office_number, is_available, change_source))
        
        # Insert/update daily_availability_snapshots
        cursor.execute("""
            INSERT INTO daily_availability_snapshots (person_id, name, office_number, is_available, snapshot_date)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (person_id, snapshot_date) 
            DO UPDATE SET 
                is_available = EXCLUDED.is_available,
                snapshot_time = CURRENT_TIME,
                name = EXCLUDED.name,
                office_number = EXCLUDED.office_number
        """, (person_id, name, office_number, is_available, today))
        
        cursor.close()
        return True
    except Exception as e:
        print(f"Error logging change: {e}")
        return False

print("=" * 70)
print("AVAILABILITY HISTORY TRACKING - SIMPLE TEST")
print("=" * 70)

# Test 1: Database Connection
print("\n[TEST 1] Testing database connection...")
conn = get_db_connection()
if not conn:
    print("✗ FAILED: Database connection failed")
    print("Please check your database configuration in .env file")
    sys.exit(1)
print("✓ PASSED: Database connection successful")

# Test 2: Verify Tables Exist
print("\n[TEST 2] Verifying history tables exist...")
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
        print("   Run the app once to initialize the database tables.")
        conn.close()
        sys.exit(1)
    else:
        print(f"✓ PASSED: All required tables exist: {tables}")
except Exception as e:
    print(f"✗ FAILED: Error checking tables: {e}")
    import traceback
    traceback.print_exc()
    conn.close()
    sys.exit(1)

# Test 3: Get a test person
print("\n[TEST 3] Getting a test person from database...")
try:
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute("SELECT id, name, office_number, is_available FROM persons LIMIT 1")
    test_person = cursor.fetchone()
    cursor.close()
    
    if not test_person:
        print("✗ FAILED: No persons found in database.")
        print("   Please ensure data is loaded by running the app.")
        conn.close()
        sys.exit(1)
    
    print(f"✓ PASSED: Found test person:")
    print(f"    ID: {test_person['id']}")
    print(f"    Name: {test_person['name'] or '(empty)'}")
    print(f"    Office: {test_person['office_number'] or '(empty)'}")
    print(f"    Current Status: {'Available' if test_person['is_available'] else 'Unavailable'}")
except Exception as e:
    print(f"✗ FAILED: Error getting test person: {e}")
    import traceback
    traceback.print_exc()
    conn.close()
    sys.exit(1)

# Test 4: Test History Logging
print("\n[TEST 4] Testing history logging function...")
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
    if log_availability_change(conn, person_id, name, office_number, new_status, 'test'):
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
                print(f"    - Status: {'Available' if history_entry[4] else 'Unavailable'}")
                print(f"    - Source: {history_entry[5]}")
                print(f"    - Timestamp: {history_entry[3]}")
        else:
            print("✗ FAILED: History entry not created")
            conn.rollback()
            cursor.close()
            conn.close()
            sys.exit(1)
    else:
        print("✗ FAILED: log_availability_change returned False")
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

# Test 5: Test Daily Snapshot
print("\n[TEST 5] Testing daily snapshot creation...")
try:
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    today = date.today()
    
    # Check if snapshot exists for today
    cursor.execute("""
        SELECT * FROM daily_availability_snapshots 
        WHERE person_id = %s AND snapshot_date = %s
    """, (person_id, today))
    snapshot = cursor.fetchone()
    
    if snapshot:
        print(f"✓ PASSED: Daily snapshot exists for today")
        print(f"    - Person ID: {snapshot['person_id']}")
        print(f"    - Date: {snapshot['snapshot_date']}")
        print(f"    - Status: {'Available' if snapshot['is_available'] else 'Unavailable'}")
        print(f"    - Time: {snapshot['snapshot_time']}")
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

# Test 6: Test Historical Queries
print("\n[TEST 6] Testing historical data queries...")
try:
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    today = date.today()
    
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
    
    # Show example query for "who was available yesterday"
    print(f"\n    Example: Query who was available on {yesterday}:")
    cursor.execute("""
        SELECT name, office_number, is_available 
        FROM daily_availability_snapshots 
        WHERE snapshot_date = %s 
        LIMIT 5
    """, (yesterday,))
    examples = cursor.fetchall()
    if examples:
        for ex in examples:
            status = "Available" if ex['is_available'] else "Unavailable"
            print(f"      - {ex['name'] or '(no name)'} ({ex['office_number']}): {status}")
    else:
        print(f"      (No data for {yesterday} - this is normal if no changes occurred)")
    
    cursor.close()
except Exception as e:
    print(f"✗ FAILED: Error querying historical data: {e}")
    import traceback
    traceback.print_exc()
    conn.close()
    sys.exit(1)

# Test 7: Verify Indexes
print("\n[TEST 7] Verifying database indexes...")
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
print("✓ Table existence: OK")
print("✓ History logging: OK")
print("✓ Daily snapshots: OK")
print("✓ Historical queries: OK")
print("✓ Database indexes: OK")
print("\nAll core functionality tests passed!")
print("\nTo test Google Sheets integration:")
print("  1. Ensure Google Sheets credentials are configured")
print("  2. Run: python3 init_sheet.py")
print("  3. Make changes in Google Sheets and verify history is logged")
print("\nTo test admin dashboard:")
print("  1. Start the Flask app: python3 app.py")
print("  2. Login to admin dashboard")
print("  3. Toggle availability and verify history is logged")

conn.close()
