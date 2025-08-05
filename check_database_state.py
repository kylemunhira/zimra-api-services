#!/usr/bin/env python3
"""
Check the current state of devices and fiscal days in the database.
"""

import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import DeviceInfo, FiscalDay, Invoice

def check_database_state():
    """Check the current state of the database."""
    print("Checking database state...")
    print("=" * 50)
    
    app = create_app()
    with app.app_context():
        # Check devices
        print("DEVICES:")
        devices = DeviceInfo.query.all()
        for device in devices:
            print(f"  - Device ID: {device.device_id}")
            print(f"    Model: {device.model_name}")
            print(f"    Version: {device.model_version}")
            print(f"    Certificate: {device.certificate_path}")
            print(f"    Key: {device.key_path}")
            print()
        
        # Check fiscal days
        print("FISCAL DAYS:")
        fiscal_days = FiscalDay.query.all()
        for fiscal_day in fiscal_days:
            print(f"  - Device: {fiscal_day.device_id}")
            print(f"    Fiscal Day No: {fiscal_day.fiscal_day_no}")
            print(f"    Is Open: {fiscal_day.is_open}")
            print(f"    Status: {fiscal_day.fiscal_status}")
            print(f"    Open Date: {fiscal_day.fiscal_day_open}")
            print()
        
        # Check invoices
        print("INVOICES:")
        invoices = Invoice.query.all()
        for invoice in invoices:
            print(f"  - Invoice ID: {invoice.id}")
            print(f"    Device: {invoice.device_id}")
            print(f"    Fiscal Day: {invoice.fiscal_day_number}")
            print(f"    Receipt Counter: {invoice.receipt_counter}")
            print(f"    Total Amount: {invoice.receipt_total}")
            print()
        
        # Summary
        print("SUMMARY:")
        print(f"  Total Devices: {len(devices)}")
        print(f"  Total Fiscal Days: {len(fiscal_days)}")
        print(f"  Open Fiscal Days: {len([fd for fd in fiscal_days if fd.is_open])}")
        print(f"  Total Invoices: {len(invoices)}")
        
        # Check for device 26428 specifically
        device_26428 = DeviceInfo.query.filter_by(device_id="26428").first()
        if device_26428:
            print(f"\nDevice 26428 found: {device_26428.model_name}")
            
            # Check fiscal days for this device
            fiscal_days_26428 = FiscalDay.query.filter_by(device_id="26428").all()
            print(f"Fiscal days for device 26428: {len(fiscal_days_26428)}")
            
            open_fiscal_days_26428 = [fd for fd in fiscal_days_26428 if fd.is_open]
            print(f"Open fiscal days for device 26428: {len(open_fiscal_days_26428)}")
            
            if open_fiscal_days_26428:
                print("Open fiscal days:")
                for fd in open_fiscal_days_26428:
                    print(f"  - Fiscal Day {fd.fiscal_day_no} (opened: {fd.fiscal_day_open})")
            else:
                print("No open fiscal days for device 26428")
                
            # Check invoices for device 26428
            invoices_26428 = Invoice.query.filter_by(device_id="26428").all()
            print(f"Invoices for device 26428: {len(invoices_26428)}")
            for invoice in invoices_26428:
                print(f"  - Invoice {invoice.id}: Fiscal Day {invoice.fiscal_day_number}, Receipt Counter {invoice.receipt_counter}")
        else:
            print("\nDevice 26428 not found!")

if __name__ == "__main__":
    check_database_state() 