#!/usr/bin/env python3
"""
Debug script to investigate currency issue in fiscal counters
"""

from app import create_app, db
from app.models import Invoice, FiscalDay, InvoiceLineItem
from collections import defaultdict

def debug_currency_issue():
    """Debug the currency issue in fiscal counters"""
    app = create_app()
    app.app_context().push()
    
    print("=== Debugging Currency Issue in Fiscal Counters ===")
    
    # Get all invoices
    invoices = Invoice.query.all()
    print(f"Total invoices: {len(invoices)}")
    
    # Check currencies in database
    currencies = set(i.receipt_currency for i in invoices if i.receipt_currency)
    print(f"Unique currencies in database: {currencies}")
    
    # Count invoices by currency
    from collections import Counter
    currency_counts = Counter(i.receipt_currency for i in invoices if i.receipt_currency)
    print("Invoices by currency:")
    for curr, count in currency_counts.items():
        print(f"  {curr}: {count} invoices")
    
    # Check invoices by fiscal day and device
    print("\nInvoices by fiscal day, device, and currency:")
    day_device_currency = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
    for invoice in invoices:
        if invoice.fiscal_day_number:
            day_device_currency[invoice.fiscal_day_number][invoice.device_id][invoice.receipt_currency] += 1
    
    for day in sorted(day_device_currency.keys()):
        print(f"  Day {day}:")
        for device_id, currencies in day_device_currency[day].items():
            print(f"    Device {device_id}: {dict(currencies)}")
    
    # Check which device has fiscal day 1
    print(f"\n=== Checking Device IDs for Fiscal Day 1 ===")
    day_1_invoices = [i for i in invoices if i.fiscal_day_number == '1']
    print(f"Invoices in fiscal day 1: {len(day_1_invoices)}")
    
    if day_1_invoices:
        day_1_devices = set(i.device_id for i in day_1_invoices)
        print(f"Device IDs in day 1: {day_1_devices}")
        
        for device_id in day_1_devices:
            device_invoices = [i for i in day_1_invoices if i.device_id == device_id]
            print(f"  Device {device_id}: {len(device_invoices)} invoices")
            
            device_currencies = set(i.receipt_currency for i in device_invoices if i.receipt_currency)
            print(f"    Currencies: {device_currencies}")
            
            for currency in device_currencies:
                currency_invoices = [i for i in device_invoices if i.receipt_currency == currency]
                print(f"      {currency}: {len(currency_invoices)} invoices")
                for inv in currency_invoices[:3]:  # Show first 3
                    print(f"        - {inv.invoice_id}: ${inv.receipt_total}")
    
    # Test the generate_counters function with the correct device
    print(f"\n=== Testing generate_counters function with correct device ===")
    from utils.generate_counters import generate_counters
    
    # Find a device that has invoices in fiscal day 1
    if day_1_invoices:
        test_device_id = day_1_invoices[0].device_id
        print(f"Testing with device ID: {test_device_id}")
        
        # Debug the invoices for this device and fiscal day
        device_fiscal_day_invoices = [i for i in invoices if i.device_id == test_device_id and i.fiscal_day_number == '1']
        print(f"Found {len(device_fiscal_day_invoices)} invoices for device {test_device_id} in fiscal day 1")
        
        for inv in device_fiscal_day_invoices:
            print(f"  Invoice {inv.invoice_id}: Currency={inv.receipt_currency}, Total={inv.receipt_total}")
            
            # Check line items
            line_items = InvoiceLineItem.query.filter_by(invoice_id=inv.id).all()
            print(f"    Line items: {len(line_items)}")
            for line in line_items:
                print(f"      - {line.receipt_line_name}: {line.receipt_line_total} (tax: {line.tax_code})")
        
        try:
            # Read a private key for testing
            with open(f'certs/{test_device_id}.key', 'rb') as key_file:
                private_key_data = key_file.read()
            
            # Test with fiscal day 1 and the correct device
            counters_data = generate_counters(
                private_key=private_key_data,
                device_id=str(test_device_id),
                date_string="2025-01-15T08:00:00",
                close_day_date="2025-01-15T08:00:00",
                fiscal_day_no=1
            )
            
            print(f"Generated counters for day 1, device {test_device_id}:")
            print(f"  Total counters: {len(counters_data.get('fiscalDayCounters', []))}")
            
            # Check currencies in generated counters
            counter_currencies = set()
            for counter in counters_data.get('fiscalDayCounters', []):
                currency = counter.get('fiscalCounterCurrency')
                if currency:
                    counter_currencies.add(currency)
            
            print(f"  Currencies in counters: {counter_currencies}")
            
            # Show all counters grouped by currency
            print(f"  All counters by currency:")
            counters_by_currency = defaultdict(list)
            for counter in counters_data.get('fiscalDayCounters', []):
                currency = counter.get('fiscalCounterCurrency', 'Unknown')
                counters_by_currency[currency].append(counter)
            
            for currency, counters in counters_by_currency.items():
                print(f"    {currency}: {len(counters)} counters")
                for i, counter in enumerate(counters):
                    print(f"      {i+1}. {counter}")
            
        except Exception as e:
            print(f"Error testing generate_counters: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    debug_currency_issue() 