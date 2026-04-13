"""
Database connection and operations for Gmail scraper
Handles PostgreSQL connection and email insertion with duplicate prevention
"""

import psycopg2
from psycopg2.extras import execute_values
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database configuration
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': os.getenv('DB_PORT', '5432'),
    'database': os.getenv('DB_NAME', 'email_analytics'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', '')
}


def get_connection():
    """
    Create and return a PostgreSQL database connection
    """
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except psycopg2.Error as e:
        print(f"Error connecting to database: {e}")
        raise


def create_table():
    """
    Create the emails table if it doesn't exist
    Includes unique constraint to prevent duplicates
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # Create table with proper schema
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS emails (
                id SERIAL PRIMARY KEY,
                sender TEXT NOT NULL,
                subject TEXT,
                timestamp TIMESTAMP NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(sender, subject, timestamp)
            );
        """)
        
        # Create indexes for better query performance
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_timestamp ON emails(timestamp);
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_sender ON emails(sender);
        """)
        
        conn.commit()
        print("✓ Database table created successfully")
        
    except psycopg2.Error as e:
        print(f"Error creating table: {e}")
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()


def insert_email(sender, subject, timestamp):
    """
    Insert a single email into the database
    Handles duplicate prevention using ON CONFLICT
    
    Args:
        sender (str): Email sender
        subject (str): Email subject
        timestamp (datetime): Email timestamp
    
    Returns:
        bool: True if inserted, False if duplicate
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO emails (sender, subject, timestamp)
            VALUES (%s, %s, %s)
            ON CONFLICT (sender, subject, timestamp) DO NOTHING
            RETURNING id;
        """, (sender, subject, timestamp))
        
        result = cursor.fetchone()
        conn.commit()
        
        # Return True if a new row was inserted
        return result is not None
        
    except psycopg2.Error as e:
        print(f"Error inserting email: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()


def insert_emails_batch(emails):
    """
    Insert multiple emails in a single transaction for better performance
    
    Args:
        emails (list): List of tuples (sender, subject, timestamp)
    
    Returns:
        int: Number of emails inserted (excluding duplicates)
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # Use execute_values for efficient batch insert
        execute_values(
            cursor,
            """
            INSERT INTO emails (sender, subject, timestamp)
            VALUES %s
            ON CONFLICT (sender, subject, timestamp) DO NOTHING
            """,
            emails
        )
        
        inserted_count = cursor.rowcount
        conn.commit()
        return inserted_count
        
    except psycopg2.Error as e:
        print(f"Error inserting emails batch: {e}")
        conn.rollback()
        return 0
    finally:
        cursor.close()
        conn.close()


def get_email_count():
    """
    Get the total number of emails in the database
    
    Returns:
        int: Total email count
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT COUNT(*) FROM emails;")
        count = cursor.fetchone()[0]
        return count
    except psycopg2.Error as e:
        print(f"Error getting email count: {e}")
        return 0
    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    # Test database connection and table creation
    print("Testing database connection...")
    try:
        create_table()
        count = get_email_count()
        print(f"✓ Database connection successful")
        print(f"✓ Current email count: {count}")
    except Exception as e:
        print(f"✗ Database test failed: {e}")
