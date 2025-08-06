#!/usr/bin/env python3
"""
Test script for Fiscal Counters functionality

This script demonstrates the fiscal counters endpoints that implement
section 6. FISCAL COUNTERS from the ZIMRA API specification.
"""

import requests
import json
import sys

# Configuration
BASE_URL = "http://localhost:5000"
DEVICE_ID = "26428"  # Replace with your actual device ID

def test_fiscal_counters():
    """Test the basic fiscal counters endpoint"""
    print("=== Testing Basic Fiscal Counters ===")
    
    # Test 1: Get fiscal counters for current open fiscal day
    url = f"{BASE_URL}/fiscal_counters/{DEVICE_ID}"
    print(f"GET {url}")
    
    try:
        response = requests.get(url)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Success! Fiscal counters retrieved:")
            print(f"   Device ID: {data.get('device_id')}")
            print(f"   Fiscal Day No: {data.get('fiscal_day_no')}")
            print(f"   Fiscal Day Status: {data.get('fiscal_day_status')}")
            print(f"   Total Receipts: {data.get('total_receipts')}")
            print(f"   Total Amount: {data.get('total_amount')}")
            print(f"   Receipt Counter: {data.get('receipt_counter')}")
            print(f"   Number of Fiscal Counters: {len(data.get('fiscal_counters', []))}")
            
            # Display summary
            summary = data.get('summary', {})
            print(f"   Summary:")
            print(f"     - Sale Counters: {summary.get('sale_counters', 0)}")
            print(f"     - Tax Counters: {summary.get('tax_counters', 0)}")
            print(f"     - Balance Counters: {summary.get('balance_counters', 0)}")
            print(f"     - Credit Note Counters: {summary.get('credit_note_counters', 0)}")
            print(f"     - Debit Note Counters: {summary.get('debit_note_counters', 0)}")
            
            # Display counters by type
            counters_by_type = data.get('counters_by_type', {})
            print(f"   Counters by Type:")
            for counter_type, counters in counters_by_type.items():
                print(f"     - {counter_type}: {len(counters)} counters")
                for i, counter in enumerate(counters[:3]):  # Show first 3
                    print(f"       {i+1}. {counter}")
                if len(counters) > 3:
                    print(f"       ... and {len(counters) - 3} more")
            
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Exception: {e}")

def test_detailed_fiscal_counters():
    """Test the detailed fiscal counters endpoint"""
    print("\n=== Testing Detailed Fiscal Counters ===")
    
    # Test 2: Get detailed fiscal counters
    url = f"{BASE_URL}/fiscal_counters/{DEVICE_ID}/detailed"
    print(f"GET {url}")
    
    try:
        response = requests.get(url)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Success! Detailed fiscal counters retrieved:")
            print(f"   Device ID: {data.get('device_id')}")
            print(f"   Fiscal Day No: {data.get('fiscal_day_no')}")
            print(f"   Fiscal Day Status: {data.get('fiscal_day_status')}")
            print(f"   Total Invoices: {data.get('total_invoices')}")
            
            # Display detailed breakdown
            breakdown = data.get('detailed_breakdown', {})
            
            # Currency breakdown
            print(f"   Currency Breakdown:")
            for currency, details in breakdown.get('by_currency', {}).items():
                print(f"     - {currency}: ${details['total_amount']:.2f} ({details['invoice_count']} invoices)")
            
            # Tax type breakdown
            print(f"   Tax Type Breakdown:")
            for tax_type, details in breakdown.get('by_tax_type', {}).items():
                print(f"     - {tax_type}: ${details['total_amount']:.2f} tax: ${details['total_tax']:.2f} ({details['line_count']} lines)")
            
            # Payment method breakdown
            print(f"   Payment Method Breakdown:")
            for method, details in breakdown.get('by_payment_method', {}).items():
                print(f"     - {method}: ${details['total_amount']:.2f} ({details['invoice_count']} invoices)")
            
            # Receipt type breakdown
            print(f"   Receipt Type Breakdown:")
            for receipt_type, details in breakdown.get('by_receipt_type', {}).items():
                print(f"     - {receipt_type}: ${details['total_amount']:.2f} ({details['invoice_count']} invoices)")
            
            # Show first few invoice details
            invoice_details = breakdown.get('invoice_details', [])
            if invoice_details:
                print(f"   Invoice Details (showing first 3):")
                for i, invoice in enumerate(invoice_details[:3]):
                    print(f"     {i+1}. {invoice['invoice_id']}: ${invoice['receipt_total']:.2f} ({invoice['receipt_type']})")
                if len(invoice_details) > 3:
                    print(f"     ... and {len(invoice_details) - 3} more invoices")
            
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Exception: {e}")

def test_fiscal_counters_with_specific_day():
    """Test fiscal counters with a specific fiscal day number"""
    print("\n=== Testing Fiscal Counters with Specific Day ===")
    
    # Test 3: Get fiscal counters for a specific fiscal day
    fiscal_day_no = 1  # Replace with an actual fiscal day number
    url = f"{BASE_URL}/fiscal_counters/{DEVICE_ID}?fiscal_day_no={fiscal_day_no}"
    print(f"GET {url}")
    
    try:
        response = requests.get(url)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Success! Fiscal counters for specific day retrieved:")
            print(f"   Device ID: {data.get('device_id')}")
            print(f"   Fiscal Day No: {data.get('fiscal_day_no')}")
            print(f"   Fiscal Day Status: {data.get('fiscal_day_status')}")
            print(f"   Total Receipts: {data.get('total_receipts')}")
            print(f"   Total Amount: {data.get('total_amount')}")
            
        elif response.status_code == 404:
            print(f"ℹ️  No data found for fiscal day {fiscal_day_no}")
            data = response.json()
            print(f"   Error: {data.get('error')}")
            
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Exception: {e}")

def main():
    """Main test function"""
    print("🚀 Testing Fiscal Counters API Endpoints")
    print("=" * 50)
    
    # Check if server is running
    try:
        health_check = requests.get(f"{BASE_URL}/")
        if health_check.status_code != 200:
            print("❌ Server is not responding properly")
            print("Please make sure the Flask server is running on http://localhost:5000")
            return
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server")
        print("Please make sure the Flask server is running on http://localhost:5000")
        return
    
    print("✅ Server is running")
    
    # Run tests
    test_fiscal_counters()
    test_detailed_fiscal_counters()
    test_fiscal_counters_with_specific_day()
    
    print("\n" + "=" * 50)
    print("🎉 Fiscal Counters testing completed!")
    print("\nAPI Endpoints Summary:")
    print(f"  GET {BASE_URL}/fiscal_counters/{{device_id}}")
    print(f"  GET {BASE_URL}/fiscal_counters/{{device_id}}?fiscal_day_no={{day_number}}")
    print(f"  GET {BASE_URL}/fiscal_counters/{{device_id}}/detailed")
    print(f"  GET {BASE_URL}/fiscal_counters/{{device_id}}/detailed?fiscal_day_no={{day_number}}")

if __name__ == "__main__":
    main() 