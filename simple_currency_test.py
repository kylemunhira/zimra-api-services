#!/usr/bin/env python3
"""
Simple test to verify the currency fix in fiscal counters
"""

from app import create_app, db
from app.models import Invoice
from utils.generate_counters import generate_counters

def test_currency_fix():
    """Test that both USD and ZWG currencies are included in fiscal counters"""
    app = create_app()
    app.app_context().push()
    
    print("=== Testing Currency Fix ===")
    
    # Test with device 26714 and fiscal day 1
    device_id = "26714"
    fiscal_day_no = 1
    
    try:
        # Read private key
        with open(f'certs/{device_id}.key', 'rb') as key_file:
            private_key_data = key_file.read()
        
        # Generate counters
        counters_data = generate_counters(
            private_key=private_key_data,
            device_id=device_id,
            date_string="2025-01-15T08:00:00",
            close_day_date="2025-01-15T08:00:00",
            fiscal_day_no=fiscal_day_no
        )
        
        # Check currencies in generated counters
        counter_currencies = set()
        for counter in counters_data.get('fiscalDayCounters', []):
            currency = counter.get('fiscalCounterCurrency')
            if currency:
                counter_currencies.add(currency)
        
        print(f"Currencies found: {counter_currencies}")
        print(f"Total counters: {len(counters_data.get('fiscalDayCounters', []))}")
        
        # Show counters by currency
        for currency in sorted(counter_currencies):
            currency_counters = [c for c in counters_data.get('fiscalDayCounters', []) if c.get('fiscalCounterCurrency') == currency]
            print(f"\n{currency} Currency ({len(currency_counters)} counters):")
            for i, counter in enumerate(currency_counters):
                print(f"  {i+1}. {counter.get('fiscalCounterType')}: {counter.get('fiscalCounterValue')}")
        
        # Verify both currencies are present
        expected_currencies = {'USD', 'ZWG'}
        if counter_currencies.issuperset(expected_currencies):
            print(f"\n✅ SUCCESS: Both USD and ZWG currencies are included!")
            return True
        else:
            print(f"\n❌ FAILURE: Missing currencies. Expected: {expected_currencies}, Found: {counter_currencies}")
            return False
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = test_currency_fix()
    if success:
        print("\n🎉 Currency fix is working correctly!")
    else:
        print("\n💥 Currency fix needs more work!") 