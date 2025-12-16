#!/usr/bin/env python3
"""
Initialize history tables in the database.
"""

import os
import sys
from dotenv import load_dotenv
import psycopg2

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

def init_history_tables():
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        
        # Create availability_history table for tracking all changes
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS availability_history (
                id SERIAL PRIMARY KEY,
                person_id INTEGER REFERENCES persons(id),
                name VARCHAR(255),
                office_number VARCHAR(100),
                is_available BOOLEAN,
                changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                change_source VARCHAR(50)
            )
        """)
        
        # Create daily_availability_snapshots table for daily snapshots
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS daily_availability_snapshots (
                id SERIAL PRIMARY KEY,
                person_id INTEGER REFERENCES persons(id),
                name VARCHAR(255),
                office_number VARCHAR(100),
                is_available BOOLEAN,
                snapshot_date DATE NOT NULL,
                snapshot_time TIME DEFAULT CURRENT_TIME,
                UNIQUE(person_id, snapshot_date)
            )
        """)
        
        # Create indexes for better query performance
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_history_person_date 
            ON availability_history(person_id, changed_at)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_snapshots_person_date 
            ON daily_availability_snapshots(person_id, snapshot_date)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_snapshots_date 
            ON daily_availability_snapshots(snapshot_date)
        """)
        
        conn.commit()
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"Database initialization error: {e}")
        conn.rollback()
        cursor.close()
        conn.close()
        return False

if __name__ == "__main__":
    print("Initializing history tables...")
    if init_history_tables():
        print("✓ Successfully created history tables")
    else:
        print("✗ Failed to create history tables")
        sys.exit(1)
