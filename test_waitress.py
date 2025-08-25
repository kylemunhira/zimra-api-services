#!/usr/bin/env python3
"""
Test script for Waitress server
This script tests the Waitress server configuration before deploying as a Windows Service.
"""

import os
import sys
import time
import requests
import subprocess
import threading
from pathlib import Path
from sqlalchemy import text

def test_waitress_server():
    """Test the Waitress server configuration"""
    
    print("=== ZIMRA API Service - Waitress Test ===")
    print()
    
    # Check if required files exist
    required_files = [
        "waitress_server.py",
        "app/__init__.py",
        "app/config.py",
        "requirements.txt"
    ]
    
    print("Checking required files...")
    for file_path in required_files:
        if Path(file_path).exists():
            print(f"  ✓ {file_path}")
        else:
            print(f"  ✗ {file_path} - NOT FOUND")
            return False
    
    print()
    
    # Check Python dependencies
    print("Checking Python dependencies...")
    try:
        import waitress
        print("  ✓ waitress")
    except ImportError:
        print("  ✗ waitress - NOT INSTALLED")
        print("  Run: pip install waitress")
        return False
    
    try:
        import flask
        print("  ✓ flask")
    except ImportError:
        print("  ✗ flask - NOT INSTALLED")
        print("  Run: pip install flask")
        return False
    
    try:
        import psycopg2
        print("  ✓ psycopg2")
    except ImportError:
        print("  ✗ psycopg2 - NOT INSTALLED")
        print("  Run: pip install psycopg2-binary")
        return False
    
    print()
    
    # Test database connection
    print("Testing database connection...")
    try:
        from app import create_app
        app = create_app()
        with app.app_context():
            from app import db
            # Use SQLAlchemy 2.x compatible API
            with db.engine.connect() as connection:
                connection.execute(text("SELECT 1"))
        print("  ✓ Database connection successful")
    except Exception as e:
        print(f"  ✗ Database connection failed: {e}")
        print("  Please check your database configuration in app/__init__.py")
        return False
    
    print()
    
    # Start Waitress server in background
    print("Starting Waitress server for testing...")
    server_process = None
    
    try:
        # Set test environment variables
        os.environ['ZIMRA_HOST'] = '127.0.0.1'
        os.environ['ZIMRA_PORT'] = '5001'  # Use different port for testing
        os.environ['ZIMRA_THREADS'] = '2'
        os.environ['FLASK_ENV'] = 'production'
        
        # Start server in background
        server_process = subprocess.Popen([
            sys.executable, 'waitress_server.py'
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Wait for server to start with retries
        print("  Waiting for server to start...")
        base_url = 'http://127.0.0.1:5001/'
        max_wait_seconds = 30
        start_time = time.time()
        last_exception = None
        while time.time() - start_time < max_wait_seconds:
            try:
                response = requests.get(base_url, timeout=2)
                if response.status_code in (200, 301, 302, 404):
                    # Any HTTP response means server is up
                    print("  ✓ Server is accepting connections")
                    break
            except requests.exceptions.RequestException as e:
                last_exception = e
            time.sleep(1)
        else:
            print(f"  ✗ Server did not start within {max_wait_seconds} seconds")
            if last_exception:
                print(f"    Last error: {last_exception}")
            # Fall through to fetch logs and fail
            raise RuntimeError("Server startup timeout")
        
        # Test server response
        print("  Testing server response...")
        try:
            response = requests.get(base_url, timeout=5)
            if response.status_code == 200:
                print("  ✓ Server responding correctly")
            else:
                print(f"  ⚠ Server returned status code: {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"  ✗ Server not responding: {e}")
            return False
        
        # Test API endpoint
        print("  Testing API endpoint...")
        try:
            response = requests.get(base_url + 'api/', timeout=5)
            print(f"  ✓ API endpoint responding (status: {response.status_code})")
        except requests.exceptions.RequestException as e:
            print(f"  ✗ API endpoint not responding: {e}")
            return False
        
        print()
        print("=== Test Results ===")
        print("✓ All tests passed!")
        print("✓ Waitress server is working correctly")
        print("✓ Ready for Windows Service deployment")
        
        return True
        
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        # Try to print server logs for debugging
        if server_process:
            try:
                # Give the process a moment to flush buffers
                time.sleep(1)
                out, err = server_process.communicate(timeout=2)
                out_text = out.decode(errors='ignore') if out else ''
                err_text = err.decode(errors='ignore') if err else ''
                if out_text.strip():
                    print("  --- Server stdout ---")
                    print(out_text)
                if err_text.strip():
                    print("  --- Server stderr ---")
                    print(err_text)
            except Exception:
                pass
        return False
        
    finally:
        # Clean up
        if server_process:
            print("  Stopping test server...")
            server_process.terminate()
            try:
                server_process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                server_process.kill()
            print("  Test server stopped")

def test_windows_service_components():
    """Test Windows Service components"""
    
    print("=== Windows Service Component Test ===")
    print()
    
    # Check Windows Service dependencies
    print("Checking Windows Service dependencies...")
    
    try:
        import win32serviceutil
        import win32service
        import win32event
        print("  ✓ pywin32 (Windows Service support)")
    except ImportError:
        print("  ✗ pywin32 - NOT INSTALLED")
        print("  Run: pip install pywin32")
        return False
    
    # Check if running on Windows
    if os.name != 'nt':
        print("  ⚠ Not running on Windows - Windows Service tests skipped")
        return True
    
    # Check if running as administrator
    try:
        import ctypes
        is_admin = ctypes.windll.shell32.IsUserAnAdmin()
        if is_admin:
            print("  ✓ Running as Administrator")
        else:
            print("  ⚠ Not running as Administrator (required for service installation)")
    except:
        print("  ⚠ Unable to check administrator privileges")
    
    print()
    print("=== Windows Service Test Results ===")
    print("✓ Windows Service components are available")
    print("✓ Ready for Windows Service installation")
    
    return True

def main():
    """Main test function"""
    
    print("ZIMRA API Service - Pre-deployment Test")
    print("=" * 50)
    print()
    
    # Test Waitress server
    waitress_ok = test_waitress_server()
    
    print()
    
    # Test Windows Service components
    service_ok = test_windows_service_components()
    
    print()
    print("=" * 50)
    print("OVERALL TEST RESULTS:")
    
    if waitress_ok and service_ok:
        print("✓ ALL TESTS PASSED")
        print("✓ Ready for Windows Service deployment")
        print()
        print("Next steps:")
        print("1. Run: .\\install_windows_service.ps1 (as Administrator)")
        print("2. Check service status: .\\service_manager.ps1 -Action status")
        print("3. Start service: .\\service_manager.ps1 -Action start")
        return 0
    else:
        print("✗ SOME TESTS FAILED")
        print("✗ Please fix the issues above before deploying")
        return 1

if __name__ == "__main__":
    exit(main())
