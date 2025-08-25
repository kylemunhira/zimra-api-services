#!/usr/bin/env python3
"""
Database connection test script
This script tests the PostgreSQL connection separately from the main application.
"""

import psycopg2
from urllib.parse import quote_plus

def test_direct_psycopg2():
    """Test direct psycopg2 connection"""
    print("=== Testing Direct psycopg2 Connection ===")
    
    try:
        # Test with direct psycopg2 connection
        conn = psycopg2.connect(
            host="localhost",
            database="zimra_api_db",
            user="postgres",
            password="@gr1ff1n#"
        )
        
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        result = cursor.fetchone()
        print(f"  ✓ Direct psycopg2 connection successful: {result}")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"  ✗ Direct psycopg2 connection failed: {e}")
        return False

def test_sqlalchemy_connection():
    """Test SQLAlchemy connection"""
    print("\n=== Testing SQLAlchemy Connection ===")
    
    try:
        from app import create_app, db
        
        app = create_app()
        with app.app_context():
            # Test SQLAlchemy connection
            with db.engine.connect() as connection:
                result = connection.execute(db.text("SELECT 1"))
                row = result.fetchone()
                print(f"  ✓ SQLAlchemy connection successful: {row}")
        
        return True
        
    except Exception as e:
        print(f"  ✗ SQLAlchemy connection failed: {e}")
        return False

def test_database_url():
    """Test database URL parsing"""
    print("\n=== Testing Database URL ===")
    
    # Original URL from config
    original_url = "postgresql+psycopg2://postgres:%40gr1ff1n%23@localhost/zimra_api_db"
    print(f"  Original URL: {original_url}")
    
    # Decoded URL
    decoded_url = "postgresql+psycopg2://postgres:@gr1ff1n#@localhost/zimra_api_db"
    print(f"  Decoded URL: {decoded_url}")
    
    # Test URL encoding
    password = "@gr1ff1n#"
    encoded_password = quote_plus(password)
    print(f"  Password: {password}")
    print(f"  Encoded password: {encoded_password}")
    
    # Reconstructed URL
    reconstructed_url = f"postgresql+psycopg2://postgres:{encoded_password}@localhost/zimra_api_db"
    print(f"  Reconstructed URL: {reconstructed_url}")

def main():
    """Main test function"""
    print("Database Connection Test")
    print("=" * 50)
    
    # Test database URL parsing
    test_database_url()
    
    # Test direct psycopg2 connection
    direct_ok = test_direct_psycopg2()
    
    # Test SQLAlchemy connection
    sqlalchemy_ok = test_sqlalchemy_connection()
    
    print("\n" + "=" * 50)
    print("TEST RESULTS:")
    
    if direct_ok and sqlalchemy_ok:
        print("✓ All database tests passed!")
        print("✓ Database connection is working correctly")
    else:
        print("✗ Some database tests failed")
        print("\nTroubleshooting steps:")
        print("1. Check if PostgreSQL is running")
        print("2. Verify database 'zimra_api_db' exists")
        print("3. Check username and password")
        print("4. Verify PostgreSQL is listening on localhost:5432")

if __name__ == "__main__":
    main()
