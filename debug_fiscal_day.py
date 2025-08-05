#!/usr/bin/env python3
"""
Debug script for fiscal day signature generation.
This script helps identify issues with the fiscal day close operation.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import DeviceInfo, FiscalDay, Invoice, InvoiceLineItem
from utils.close_day_string_utilts import generate_close_day_string, get_close_day_date_format
from utils.generate_counters import generate_counters
from utils.update_closeday import update_fiscal_counter_data
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
import base64
import hashlib
import json

def debug_fiscal_day_signature(device_id):
    """Debug the fiscal day signature generation process"""
    
    app = create_app()
    with app.app_context():
        try:
            # 1. Load device config
            device = DeviceInfo.query.filter_by(device_id=str(device_id)).first()
            if not device:
                print(f"❌ Device {device_id} not found")
                return
            
            print(f"✅ Device found: {device.device_id}")
            print(f"   Certificate: {device.certificate_path}")
            print(f"   Key: {device.key_path}")
            
            # 2. Get fiscal day number
            from app.routes import get_fiscal_number
            fiscal_day_number = str(get_fiscal_number(device_id))
            print(f"✅ Fiscal day number: {fiscal_day_number}")
            
            # 3. Get the open fiscal day
            open_fiscal_day = FiscalDay.query.filter_by(
                device_id=device.device_id, 
                fiscal_day_no=int(fiscal_day_number),
                is_open=True
            ).first()
            
            if not open_fiscal_day:
                print(f"❌ No open fiscal day {fiscal_day_number} found for device {device_id}")
                return
            
            print(f"✅ Open fiscal day found:")
            print(f"   Open date: {open_fiscal_day.fiscal_day_open}")
            print(f"   Status: {open_fiscal_day.fiscal_status}")
            
            # 4. Generate counters
            try:
                with open(device.key_path, 'rb') as key_file:
                    private_key_data = key_file.read()
                
                close_data = generate_counters(
                    private_key=private_key_data,
                    device_id=str(device_id),
                    date_string=open_fiscal_day.fiscal_day_open,
                    close_day_date=open_fiscal_day.fiscal_day_open,
                    fiscal_day_no=int(fiscal_day_number)
                )
                
                print(f"✅ Generated close data:")
                print(f"   Fiscal day no: {close_data['fiscalDayNo']}")
                print(f"   Receipt counter: {close_data['receiptCounter']}")
                print(f"   Number of counters: {len(close_data['fiscalDayCounters'])}")
                
                # Print counter details
                for i, counter in enumerate(close_data['fiscalDayCounters']):
                    print(f"   Counter {i+1}: {counter}")
                
            except ValueError as e:
                print(f"❌ Error generating counters: {e}")
                return
            
            # 5. Update fiscal counter data
            updated_counters = update_fiscal_counter_data(close_data['fiscalDayCounters'])
            close_data['fiscalDayCounters'] = updated_counters
            
            print(f"✅ Updated counters:")
            for i, counter in enumerate(updated_counters):
                print(f"   Updated Counter {i+1}: {counter}")
            
            # 6. Format close date
            formatted_close_date = get_close_day_date_format(open_fiscal_day.fiscal_day_open)
            print(f"✅ Formatted close date: {formatted_close_date}")
            
            # 7. Generate string to sign
            string_to_sign = generate_close_day_string(
                device_id=str(device_id),
                fiscal_day_no=fiscal_day_number,
                date=formatted_close_date,
                receipt_close=close_data
            )
            
            print(f"✅ String to sign:")
            print(f"   Length: {len(string_to_sign)}")
            print(f"   Content: {string_to_sign}")
            
            # 8. Generate signature
            with open(device.key_path, 'rb') as key_file:
                private_key = serialization.load_pem_private_key(
                    key_file.read(),
                    password=None
                )
            
            signature = private_key.sign(
                string_to_sign.encode('utf-8'),
                padding.PKCS1v15(),
                hashes.SHA256()
            )
            
            fiscal_day_device_signature = base64.b64encode(signature).decode('utf-8')
            
            # Generate MD5 hash
            signature_bytes = base64.b64decode(fiscal_day_device_signature)
            md5_hash = hashlib.md5(signature_bytes).hexdigest().upper()
            signature_hash = md5_hash[:16]
            
            print(f"✅ Generated signature:")
            print(f"   Hash: {signature_hash}")
            print(f"   Signature length: {len(fiscal_day_device_signature)}")
            print(f"   Signature (first 100 chars): {fiscal_day_device_signature[:100]}...")
            
            # 9. Create final payload
            close_data['fiscalDayDeviceSignature'] = {
                "hash": signature_hash,
                "signature": fiscal_day_device_signature
            }
            
            print(f"✅ Final payload:")
            print(json.dumps(close_data, indent=2))
            
        except Exception as e:
            print(f"❌ Error during debug: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python debug_fiscal_day.py <device_id>")
        sys.exit(1)
    
    device_id = sys.argv[1]
    debug_fiscal_day_signature(device_id) 