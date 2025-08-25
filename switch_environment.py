#!/usr/bin/env python3
"""
Environment Switcher for ZIMRA API Service

This script allows you to easily switch between test and production environments
by updating the configuration in app/config.py
"""

import os
import sys

def switch_environment(environment):
    """
    Switch the ZIMRA API service between test and production environments.
    
    Args:
        environment (str): Either 'test' or 'production'
    """
    config_file = 'app/config.py'
    
    if not os.path.exists(config_file):
        print(f"Error: Configuration file {config_file} not found!")
        return False
    
    # Read the current configuration
    with open(config_file, 'r') as f:
        content = f.read()
    
    if environment.lower() == 'test':
        # Switch to test mode
        new_content = content.replace(
            'zimra_config = ZimraConfig(test_mode=False)  # Change this to True for test mode',
            'zimra_config = ZimraConfig(test_mode=True)  # Test mode enabled'
        )
        print("✅ Switched to TEST environment")
        print("   - API URLs: https://fdmsapitest.zimra.co.zw")
        print("   - QR URLs: https://fdmstest.zimra.co.zw")
        print("   - Tax IDs: Test configuration")
        
    elif environment.lower() == 'production':
        # Switch to production mode
        new_content = content.replace(
            'zimra_config = ZimraConfig(test_mode=True)  # Test mode enabled',
            'zimra_config = ZimraConfig(test_mode=False)  # Production mode enabled'
        )
        new_content = new_content.replace(
            'zimra_config = ZimraConfig(test_mode=False)  # Change this to True for test mode',
            'zimra_config = ZimraConfig(test_mode=False)  # Production mode enabled'
        )
        print("✅ Switched to PRODUCTION environment")
        print("   - API URLs: https://fdmsapi.zimra.co.zw")
        print("   - QR URLs: https://fdms.zimra.co.zw")
        print("   - Tax IDs: Production configuration")
        
    else:
        print("❌ Invalid environment. Use 'test' or 'production'")
        return False
    
    # Write the updated configuration
    with open(config_file, 'w') as f:
        f.write(new_content)
    
    return True

def show_current_environment():
    """Show the current environment configuration"""
    config_file = 'app/config.py'
    
    if not os.path.exists(config_file):
        print("❌ Configuration file not found!")
        return
    
    with open(config_file, 'r') as f:
        content = f.read()
    
    if 'test_mode=True' in content:
        print("🔄 Current Environment: TEST")
        print("   - API URLs: https://fdmsapitest.zimra.co.zw")
        print("   - QR URLs: https://fdmstest.zimra.co.zw")
    elif 'test_mode=False' in content:
        print("🔄 Current Environment: PRODUCTION")
        print("   - API URLs: https://fdmsapi.zimra.co.zw")
        print("   - QR URLs: https://fdms.zimra.co.zw")
    else:
        print("❓ Unknown environment configuration")

def main():
    """Main function to handle command line arguments"""
    if len(sys.argv) < 2:
        print("ZIMRA API Service Environment Switcher")
        print("=====================================")
        print()
        show_current_environment()
        print()
        print("Usage:")
        print("  python switch_environment.py test        # Switch to test environment")
        print("  python switch_environment.py production  # Switch to production environment")
        print("  python switch_environment.py status      # Show current environment")
        return
    
    command = sys.argv[1].lower()
    
    if command == 'status':
        show_current_environment()
    elif command in ['test', 'production']:
        success = switch_environment(command)
        if success:
            print()
            print("🔄 Restart your application for changes to take effect!")
    else:
        print("❌ Invalid command. Use 'test', 'production', or 'status'")

if __name__ == "__main__":
    main()
