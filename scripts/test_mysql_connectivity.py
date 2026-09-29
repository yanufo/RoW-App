#!/usr/bin/env python3
"""
MySQL Connectivity Test Script
Tests the connection to the MySQL database from the Streamlit app
"""

import sys
import os

# Get database settings from environment variables
# Default to mysql-shared for Docker network, host.docker.internal for host mode
DB_HOST = os.getenv('DB_HOST', 'mysql-shared')
DB_PORT = os.getenv('DB_PORT', '3306')
DB_USER = os.getenv('DB_USER', 'streamlit_user')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'gve')
DB_NAME = os.getenv('DB_NAME', 'row_database')

print("=" * 60)
print("MySQL Connectivity Test")
print("=" * 60)
print(f"Host: {DB_HOST}")
print(f"Port: {DB_PORT}")
print(f"User: {DB_USER}")
print(f"Database: {DB_NAME}")
print("=" * 60)

try:
    import mysql.connector
    print("\n[OK] mysql.connector module imported successfully")
    
    # Try to connect
    conn = mysql.connector.connect(
        host=DB_HOST,
        port=int(DB_PORT),
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME
    )
    print("[OK] MySQL connection established successfully!")
    
    # Test a simple query
    cursor = conn.cursor()
    cursor.execute("SELECT VERSION()")
    version = cursor.fetchone()
    print(f"[OK] MySQL Server Version: {version[0]}")
    
    # List databases
    cursor.execute("SHOW DATABASES")
    databases = cursor.fetchall()
    print(f"\n[OK] Available databases:")
    for db in databases:
        print(f"   - {db[0]}")
    
    cursor.close()
    conn.close()
    print("\n" + "=" * 60)
    print("All connectivity tests PASSED!")
    print("=" * 60)
    sys.exit(0)
    
except ImportError as e:
    print(f"[ERROR] Failed to import mysql.connector: {e}")
    print("Please install: pip install mysql-connector-python")
    sys.exit(1)
    
except mysql.connector.Error as e:
    print(f"\n[ERROR] MySQL connection failed: {e}")
    print("\nTroubleshooting tips:")
    print("1. Check if MySQL server is running: docker ps | grep mysql")
    print("2. Verify MySQL credentials in .env file")
    print("3. Check network connectivity to host.docker.internal")
    print("4. Ensure MySQL port 3306 is accessible")
    sys.exit(1)
    
except Exception as e:
    print(f"\n[ERROR] Unexpected error: {e}")
    sys.exit(1)
