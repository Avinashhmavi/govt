#!/usr/bin/env python3
"""
Test the complete sync flow to verify everything works correctly
"""

from google_sheets_sync import GoogleSheetsSync
from app import get_db_connection
from psycopg2.extras import RealDictCursor

print("=" * 60)
print("Testing Complete Sync Flow")
print("=" * 60)

gs = GoogleSheetsSync('gcp.json', '1XT3A8iW5gbWl76qSeSQZ-6BG2hUluGbx24VYxwr1HkE', 'Sheet1')

# Step 1: Check current state
print("\n1. Current State:")
sheet_data = gs.read_availability_data()
sheet_available = sum(1 for d in sheet_data if d['is_available'])

conn = get_db_connection()
cursor = conn.cursor(cursor_factory=RealDictCursor)
cursor.execute("SELECT COUNT(*) as total, SUM(CASE WHEN is_available THEN 1 ELSE 0 END) as available FROM persons")
db_stats = cursor.fetchone()

print(f"   Sheet: {sheet_available}/{len(sheet_data)} available")
print(f"   Database: {db_stats['available']}/{db_stats['total']} available")
print(f"   Match: {'✓ YES' if db_stats['available'] == sheet_available else '✗ NO'}")

# Step 2: Test sync
print("\n2. Running Sync...")
updated, errors, msgs = gs.sync_sheet_to_db(get_db_connection)
print(f"   Updated: {updated} rows")
print(f"   Errors: {errors}")

# Step 3: Verify after sync
cursor.execute("SELECT COUNT(*) as total, SUM(CASE WHEN is_available THEN 1 ELSE 0 END) as available FROM persons")
db_after = cursor.fetchone()

print(f"\n3. After Sync:")
print(f"   Database: {db_after['available']}/{db_after['total']} available")
print(f"   Match: {'✓ YES' if db_after['available'] == sheet_available else '✗ NO'}")

# Step 4: Test specific person matching
print("\n4. Testing Person Matching:")
test_cases = [
    ("", "रूम नं.-627"),  # Empty name
    ("---", "रूम नं. 203 ते 210"),  # Dash name
    ("डॉ. गणेश धुमाळ", "जी-14-15"),  # Full name
]

for name, office in test_cases:
    # Find in sheet
    sheet_person = [d for d in sheet_data if d['office_number'] == office]
    if sheet_person:
        sheet_status = sheet_person[0]['is_available']
        # Find in DB
        if name:
            cursor.execute("SELECT is_available FROM persons WHERE office_number = %s AND name = %s", (office, name))
        else:
            cursor.execute("SELECT is_available FROM persons WHERE office_number = %s AND (name IS NULL OR name = '' OR name = '---')", (office,))
        db_result = cursor.fetchone()
        if db_result:
            db_status = db_result['is_available']
            match = "✓" if sheet_status == db_status else "✗"
            print(f"   {match} {name[:20] if name else 'EMPTY':20} | {office[:25]:25} | Sheet={sheet_status}, DB={db_status}")

cursor.close()
conn.close()

print("\n" + "=" * 60)
print("Test Complete!")
print("=" * 60)

