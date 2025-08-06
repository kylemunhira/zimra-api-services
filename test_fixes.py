#!/usr/bin/env python3
"""
Test script to verify the fixes for BalanceByMoneyType and latest fiscal day issues
"""

from app import create_app, db
from app.models import Invoice, FiscalDay, DeviceInfo
from utils.generate_counters import generate_counters
import os

def test_balance_by_money_type_fix():
    """Test that BalanceByMoneyType correctly calculates totals for each currency"""
    
    print("=== Testing BalanceByMoneyType Fix ===")
    
    # Create app context
    app = create_app()
    app.app_context().push()
    
    # Get device info
    device = DeviceInfo.query.filter_by(device_id='26799').first()
    if not device:
        print("❌ Device 26799 not found")
        return
    
    # Read private key
    with open(device.key_path, 'rb') as key_file:
        private_key_data = key_file.read()
    
    # Test fiscal day 2 (where we have invoices)
    fiscal_day_no = 2
    
    print(f"Testing fiscal day {fiscal_day_no} for device 26799")
    
    # Get invoices for this fiscal day
    invoices = Invoice.query.filter_by(
        device_id='26799',
        fiscal_day_number=str(fiscal_day_no)
    ).all()
    
    print(f"Found {len(invoices)} invoices:")
    for inv in invoices:
        print(f"  Invoice {inv.id}: Total={inv.receipt_total}, Currency={inv.receipt_currency}, MoneyType={inv.money_type}")
    
    # Generate counters
    try:
        counters_data = generate_counters(
            private_key=private_key_data,
            device_id='26799',
            date_string='2024-01-01',  # Dummy date
            close_day_date='2024-01-01',  # Dummy date
            fiscal_day_no=fiscal_day_no
        )
        
        print(f"\n✅ Generated {len(counters_data['fiscalDayCounters'])} counters")
        
        # Find BalanceByMoneyType counters
        balance_counters = [c for c in counters_data['fiscalDayCounters'] if c.get('fiscalCounterType') == 'BalanceByMoneyType']
        
        print(f"\nBalanceByMoneyType counters ({len(balance_counters)}):")
        for counter in balance_counters:
            currency = counter.get('fiscalCounterCurrency')
            money_type = counter.get('fiscalCounterMoneyType')
            value = counter.get('fiscalCounterValue')
            print(f"  {currency}/{money_type}: {value}")
            
            # Verify the values are correct
            if currency == 'USD' and money_type == 'CASH':
                expected = 20.0
                if value == expected:
                    print(f"    ✅ USD/CASH: {value} (correct)")
                else:
                    print(f"    ❌ USD/CASH: {value} (expected {expected})")
            elif currency == 'ZWG' and money_type == 'CASH':
                expected = 20.0
                if value == expected:
                    print(f"    ✅ ZWG/CASH: {value} (correct)")
                else:
                    print(f"    ❌ ZWG/CASH: {value} (expected {expected})")
        
    except Exception as e:
        print(f"❌ Error generating counters: {e}")

def test_latest_fiscal_day_fix():
    """Test that get_latest_fiscal_number returns the correct fiscal day"""
    
    print("\n=== Testing Latest Fiscal Day Fix ===")
    
    # Create app context
    app = create_app()
    app.app_context().push()
    
    # Import the function
    from app.routes import get_latest_fiscal_number, get_fiscal_number
    
    device_id = '26799'
    
    try:
        # Test the new function
        latest_fiscal_day = get_latest_fiscal_number(device_id)
        print(f"Latest fiscal day (highest number): {latest_fiscal_day}")
        
        # Test the old function for comparison
        open_fiscal_day = get_fiscal_number(device_id)
        print(f"Open fiscal day: {open_fiscal_day}")
        
        if latest_fiscal_day == 2 and open_fiscal_day == 1:
            print("✅ Latest fiscal day fix working correctly:")
            print(f"  - Latest (highest): {latest_fiscal_day}")
            print(f"  - Open: {open_fiscal_day}")
        else:
            print("❌ Latest fiscal day fix not working as expected")
            
    except Exception as e:
        print(f"❌ Error testing latest fiscal day: {e}")

def test_fiscal_day_status():
    """Test the fiscal day status in database"""
    
    print("\n=== Testing Fiscal Day Status ===")
    
    # Create app context
    app = create_app()
    app.app_context().push()
    
    # Get all fiscal days for device 26799
    fiscal_days = FiscalDay.query.filter_by(device_id='26799').order_by(FiscalDay.fiscal_day_no.desc()).all()
    
    print("Fiscal days for device 26799:")
    for fd in fiscal_days:
        print(f"  Day {fd.fiscal_day_no}: Open={fd.is_open}, Status={fd.fiscal_status}")

if __name__ == "__main__":
    test_balance_by_money_type_fix()
    test_latest_fiscal_day_fix()
    test_fiscal_day_status() 