#!/usr/bin/env python3
"""
Script to update device configuration with new ZIMRA response data
"""

import json
import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import DeviceConfig, DeviceInfo

def update_device_config():
    """Update device configuration with new data"""
    
    # Create Flask app context
    app = create_app()
    
    with app.app_context():
        # Use an existing device ID instead of the serial number
        device_id = "26241"  # Using existing device ID
        
        # New configuration data based on your response
        new_config = {
            "certificate": "certs/client.crt",  # Keep existing certificate path
            "key": "certs/client.key",          # Keep existing key path
            "model_name": "Server",
            "model_version_number": "v1",
            
            # New data from your response
            "deviceBranchAddress": {
                "city": "Harare",
                "houseNo": "157",
                "province": "Harare",
                "street": "J.Chinamano"
            },
            "deviceBranchContacts": {
                "email": "innocentsm@synergycaglobal.com",
                "phoneNo": "0710373226"
            },
            "deviceBranchName": "Synergy Chartered Accountants (Pvt) Ltd",
            "deviceSerialNo": "H10S745243ZP0020",
            "qrUrl": "https://fdmstest.zimra.co.zw",
            "taxPayerName": "SYNERGY CHARTERED ACCOUNTANTS",
            "taxPayerTIN": "2000742784",
            "vatNumber": "220410348"
        }
        
        # Check if device exists in DeviceInfo
        device = DeviceInfo.query.filter_by(device_id=device_id).first()
        if not device:
            print(f"Error: Device {device_id} not found in DeviceInfo table")
            print("Available device IDs:")
            devices = DeviceInfo.query.all()
            for d in devices:
                print(f"- {d.device_id}")
            return
        else:
            print(f"Device {device_id} found and will be updated")
        
        # Check if device config exists
        device_config = DeviceConfig.query.filter_by(device_id=device_id).first()
        
        if device_config:
            print(f"Updating existing device configuration for {device_id}")
            device_config.config = json.dumps(new_config)
            device_config.updated_at = db.func.now()
        else:
            print(f"Creating new device configuration for {device_id}")
            device_config = DeviceConfig(
                device_id=device_id,
                config=json.dumps(new_config)
            )
            db.session.add(device_config)
        
        db.session.commit()
        print(f"Device configuration updated successfully for {device_id}")
        
        # Verify the update
        updated_config = DeviceConfig.query.filter_by(device_id=device_id).first()
        if updated_config:
            config_data = json.loads(updated_config.config)
            print("\nUpdated configuration:")
            print(f"Device ID: {device_id}")
            print(f"Tax Payer Name: {config_data.get('taxPayerName')}")
            print(f"Tax Payer TIN: {config_data.get('taxPayerTIN')}")
            print(f"VAT Number: {config_data.get('vatNumber')}")
            print(f"Branch Name: {config_data.get('deviceBranchName')}")
            print(f"QR URL: {config_data.get('qrUrl')}")
            print(f"Branch Address: {config_data.get('deviceBranchAddress')}")
            print(f"Branch Contact: {config_data.get('deviceBranchContacts')}")
        else:
            print("Error: Could not verify the update")

if __name__ == "__main__":
    update_device_config() 