#!/usr/bin/env python3
"""
Test script to verify updated fiscal counters with ZWG currency and CASH money type
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import Invoice, InvoiceLineItem, DeviceInfo, FiscalDay
from utils.generate_counters import generate_counters
from utils.update_closeday import update_fiscal_counter_data
import json

def test_currency_fix():
    """Test the updated fiscal counters with ZWG currency and CASH money type"""
    app = create_app()
    app.app_context().push()
    
    device_id = "26799"
    fiscal_day_no = 2
    
    print("=== Testing Updated Fiscal Counters (ZWG + CASH) ===")
    print(f"Device ID: {device_id}")
    print(f"Fiscal Day: {fiscal_day_no}")
    
    try:
        # Get device info
        device = DeviceInfo.query.filter_by(device_id=str(device_id)).first()
        if not device:
            print("❌ Device not found")
            return
        
        print(f"✅ Device found: {device.device_id}")
        
        # Get fiscal day info
        fiscal_day = FiscalDay.query.filter_by(
            device_id=device.device_id,
            fiscal_day_no=fiscal_day_no
        ).first()
        
        if not fiscal_day:
            print("❌ Fiscal day not found")
            return
        
        print(f"✅ Fiscal day found: {fiscal_day.fiscal_day_no}")
        
        # Generate counters
        print(f"\n=== Generating Updated Counters ===")
        with open(device.key_path, 'rb') as key_file:
            private_key_data = key_file.read()
        
        close_data = generate_counters(
            private_key=private_key_data,
            device_id=str(device_id),
            date_string=fiscal_day.fiscal_day_open,
            close_day_date=fiscal_day.fiscal_day_open,
            fiscal_day_no=fiscal_day_no
        )
        
        print("✅ Counters generated:")
        print(f"   Fiscal Day No: {close_data.get('fiscalDayNo')}")
        print(f"   Receipt Counter: {close_data.get('receiptCounter')}")
        print(f"   Number of Counters: {len(close_data.get('fiscalDayCounters', []))}")
        
        # Update fiscal counter data
        updated_counters = update_fiscal_counter_data(close_data['fiscalDayCounters'])
        close_data['fiscalDayCounters'] = updated_counters
        
        # Display all counters organized by type
        print(f"\n=== Updated Fiscal Counters ===")
        
        # Group counters by type
        counters_by_type = {}
        for counter in updated_counters:
            counter_type = counter.get('fiscalCounterType', 'Unknown')
            if counter_type not in counters_by_type:
                counters_by_type[counter_type] = []
            counters_by_type[counter_type].append(counter)
        
        # Display each counter type
        for counter_type, counters in counters_by_type.items():
            print(f"\n📊 {counter_type} Counters ({len(counters)}):")
            for i, counter in enumerate(counters, 1):
                currency = counter.get('fiscalCounterCurrency', 'Unknown')
                value = counter.get('fiscalCounterValue', 0)
                tax_id = counter.get('fiscalCounterTaxID', 'N/A')
                tax_percent = counter.get('fiscalCounterTaxPercent', 'N/A')
                money_type = counter.get('fiscalCounterMoneyType', 'N/A')
                
                print(f"   {i}. Currency: {currency}, Value: {value}, Tax ID: {tax_id}, Tax %: {tax_percent}, Money Type: {money_type}")
        
        # Summary statistics
        print(f"\n=== Summary Statistics ===")
        currencies_found = set(c.get('fiscalCounterCurrency') for c in updated_counters)
        print(f"Currencies: {currencies_found}")
        
        # Count by currency
        for currency in ['ZWG', 'USD']:
            currency_counters = [c for c in updated_counters if c.get('fiscalCounterCurrency') == currency]
            print(f"{currency} counters: {len(currency_counters)}")
        
        # Count by counter type
        for counter_type in ['SaleByTax', 'SaleTaxByTax', 'CreditNoteByTax', 'CreditNoteTaxByTax', 'DebitNoteByTax', 'DebitNoteTaxByTax', 'BalanceByMoneyType']:
            type_counters = [c for c in updated_counters if c.get('fiscalCounterType') == counter_type]
            print(f"{counter_type}: {len(type_counters)} counters")
        
        # Verify we have all expected counters
        expected_counter_types = ['SaleByTax', 'SaleTaxByTax', 'CreditNoteByTax', 'CreditNoteTaxByTax', 'DebitNoteByTax', 'DebitNoteTaxByTax', 'BalanceByMoneyType']
        expected_currencies = ['ZWG', 'USD']
        
        print(f"\n=== Verification ===")
        for counter_type in expected_counter_types:
            for currency in expected_currencies:
                matching_counters = [c for c in updated_counters if c.get('fiscalCounterType') == counter_type and c.get('fiscalCounterCurrency') == currency]
                if matching_counters:
                    print(f"✅ {counter_type} - {currency}: {len(matching_counters)} counter(s)")
                else:
                    print(f"❌ {counter_type} - {currency}: Missing")
        
        # Check for CASH money type only
        balance_counters = [c for c in updated_counters if c.get('fiscalCounterType') == 'BalanceByMoneyType']
        money_types_found = set(c.get('fiscalCounterMoneyType') for c in balance_counters)
        print(f"\n💰 Money Types in BalanceByMoneyType: {money_types_found}")
        
        # Display final payload structure
        print(f"\n=== Final Payload Structure ===")
        print(json.dumps(close_data, indent=2))
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_currency_fix() 