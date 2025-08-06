#!/usr/bin/env python3
"""
Test script to demonstrate querying fiscal counters by device ID and fiscal day number
"""

import requests
import json

def test_fiscal_counters_query():
    """Test the fiscal counters query by device ID and fiscal day number"""
    
    # Configuration
    BASE_URL = "http://localhost:5000"
    DEVICE_ID = "26799"
    FISCAL_DAY_NO = 2
    
    print("=== Testing Fiscal Counters Query by Device ID and Fiscal Day ===")
    print(f"Base URL: {BASE_URL}")
    print(f"Device ID: {DEVICE_ID}")
    print(f"Fiscal Day No: {FISCAL_DAY_NO}")
    
    # Test 1: Query with explicit device ID and fiscal day number
    print(f"\n=== Test 1: Query by Device ID and Fiscal Day ===")
    url = f"{BASE_URL}/fiscal_counters/{DEVICE_ID}/{FISCAL_DAY_NO}"
    print(f"GET {url}")
    
    try:
        response = requests.get(url)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Success! Fiscal counters retrieved:")
            
            # Display query info
            query_info = data.get('query_info', {})
            print(f"\n📋 Query Information:")
            print(f"   Device ID: {query_info.get('device_id')}")
            print(f"   Fiscal Day No: {query_info.get('fiscal_day_no')}")
            print(f"   Total Counters: {query_info.get('total_counters')}")
            print(f"   Currencies: {query_info.get('currencies')}")
            
            # Display fiscal day info
            print(f"\n📅 Fiscal Day Information:")
            print(f"   Fiscal Day No: {data.get('fiscal_day_no')}")
            print(f"   Fiscal Day Open: {data.get('fiscal_day_open')}")
            print(f"   Fiscal Day Status: {data.get('fiscal_day_status')}")
            
            # Display summary
            print(f"\n📊 Summary:")
            print(f"   Total Receipts: {data.get('total_receipts')}")
            print(f"   Total Amount: {data.get('total_amount')}")
            print(f"   Receipt Counter: {data.get('receipt_counter')}")
            
            summary = data.get('summary', {})
            print(f"\n📈 Counter Summary:")
            print(f"   Sale Counters: {summary.get('sale_counters', 0)}")
            print(f"   Tax Counters: {summary.get('tax_counters', 0)}")
            print(f"   Balance Counters: {summary.get('balance_counters', 0)}")
            print(f"   Credit Note Counters: {summary.get('credit_note_counters', 0)}")
            print(f"   Debit Note Counters: {summary.get('debit_note_counters', 0)}")
            
            # Display counters by currency
            counters_by_currency = data.get('counters_by_currency', {})
            print(f"\n💰 Counters by Currency:")
            for currency, counters in counters_by_currency.items():
                print(f"   {currency}: {len(counters)} counters")
                for i, counter in enumerate(counters[:3]):  # Show first 3
                    counter_type = counter.get('fiscalCounterType', 'Unknown')
                    value = counter.get('fiscalCounterValue', 0)
                    print(f"     {i+1}. {counter_type}: {value}")
                if len(counters) > 3:
                    print(f"     ... and {len(counters) - 3} more")
            
            # Display counters by type
            counters_by_type = data.get('counters_by_type', {})
            print(f"\n📊 Counters by Type:")
            for counter_type, counters in counters_by_type.items():
                print(f"   {counter_type}: {len(counters)} counters")
                for i, counter in enumerate(counters[:2]):  # Show first 2
                    currency = counter.get('fiscalCounterCurrency', 'Unknown')
                    value = counter.get('fiscalCounterValue', 0)
                    print(f"     {i+1}. {currency}: {value}")
                if len(counters) > 2:
                    print(f"     ... and {len(counters) - 2} more")
            
        else:
            print(f"❌ Error: {response.status_code}")
            try:
                error_data = response.json()
                print(f"Error Details: {json.dumps(error_data, indent=2)}")
            except:
                print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Exception: {e}")
    
    # Test 2: Query with latest fiscal day (NEW)
    print(f"\n=== Test 2: Query with Latest Fiscal Day ===")
    url2 = f"{BASE_URL}/fiscal_counters/{DEVICE_ID}/latest"
    print(f"GET {url2}")
    
    try:
        response2 = requests.get(url2)
        print(f"Status Code: {response2.status_code}")
        
        if response2.status_code == 200:
            data2 = response2.json()
            print("✅ Success! Latest fiscal counters retrieved:")
            
            # Display query info
            query_info = data2.get('query_info', {})
            print(f"\n📋 Query Information:")
            print(f"   Device ID: {query_info.get('device_id')}")
            print(f"   Fiscal Day No: {query_info.get('fiscal_day_no')}")
            print(f"   Total Counters: {query_info.get('total_counters')}")
            print(f"   Currencies: {query_info.get('currencies')}")
            print(f"   Is Latest: {query_info.get('is_latest')}")
            print(f"   Note: {query_info.get('note')}")
            
            # Display fiscal day info
            print(f"\n📅 Latest Fiscal Day Information:")
            print(f"   Fiscal Day No: {data2.get('fiscal_day_no')}")
            print(f"   Fiscal Day Open: {data2.get('fiscal_day_open')}")
            print(f"   Fiscal Day Status: {data2.get('fiscal_day_status')}")
            
            # Display summary
            print(f"\n📊 Summary:")
            print(f"   Total Receipts: {data2.get('total_receipts')}")
            print(f"   Total Amount: {data2.get('total_amount')}")
            print(f"   Receipt Counter: {data2.get('receipt_counter')}")
            
            summary = data2.get('summary', {})
            print(f"\n📈 Counter Summary:")
            print(f"   Sale Counters: {summary.get('sale_counters', 0)}")
            print(f"   Tax Counters: {summary.get('tax_counters', 0)}")
            print(f"   Balance Counters: {summary.get('balance_counters', 0)}")
            print(f"   Credit Note Counters: {summary.get('credit_note_counters', 0)}")
            print(f"   Debit Note Counters: {summary.get('debit_note_counters', 0)}")
            
        else:
            print(f"❌ Error: {response2.status_code}")
            try:
                error_data = response2.json()
                print(f"Error Details: {json.dumps(error_data, indent=2)}")
            except:
                print(f"Response: {response2.text}")
                
    except Exception as e:
        print(f"❌ Exception: {e}")
    
    # Test 3: Query with different fiscal day number
    print(f"\n=== Test 3: Query with Different Fiscal Day ===")
    FISCAL_DAY_NO_3 = 1
    url3 = f"{BASE_URL}/fiscal_counters/{DEVICE_ID}/{FISCAL_DAY_NO_3}"
    print(f"GET {url3}")
    
    try:
        response3 = requests.get(url3)
        print(f"Status Code: {response3.status_code}")
        
        if response3.status_code == 200:
            data3 = response3.json()
            print("✅ Success! Fiscal counters retrieved for fiscal day 1:")
            print(f"   Total Counters: {data3.get('query_info', {}).get('total_counters', 0)}")
            print(f"   Currencies: {data3.get('query_info', {}).get('currencies', [])}")
        else:
            print(f"❌ Error: {response3.status_code}")
            try:
                error_data = response3.json()
                print(f"Error Details: {json.dumps(error_data, indent=2)}")
            except:
                print(f"Response: {response3.text}")
                
    except Exception as e:
        print(f"❌ Exception: {e}")
    
    # Test 4: Query with invalid device ID
    print(f"\n=== Test 4: Query with Invalid Device ID ===")
    INVALID_DEVICE_ID = "99999"
    url4 = f"{BASE_URL}/fiscal_counters/{INVALID_DEVICE_ID}/latest"
    print(f"GET {url4}")
    
    try:
        response4 = requests.get(url4)
        print(f"Status Code: {response4.status_code}")
        
        if response4.status_code == 404:
            print("✅ Correctly handled invalid device ID")
        else:
            print(f"❌ Unexpected response: {response4.status_code}")
            
    except Exception as e:
        print(f"❌ Exception: {e}")

def test_curl_commands():
    """Show curl commands for testing"""
    print(f"\n=== cURL Commands for Testing ===")
    print(f"# Query fiscal counters by device ID and specific fiscal day number")
    print(f"curl -X GET 'http://localhost:5000/fiscal_counters/26799/2'")
    print(f"")
    print(f"# Query fiscal counters by device ID using latest fiscal day")
    print(f"curl -X GET 'http://localhost:5000/fiscal_counters/26799/latest'")
    print(f"")
    print(f"# Query with different fiscal day")
    print(f"curl -X GET 'http://localhost:5000/fiscal_counters/26799/1'")
    print(f"")
    print(f"# Query with invalid device ID")
    print(f"curl -X GET 'http://localhost:5000/fiscal_counters/99999/latest'")

if __name__ == "__main__":
    test_fiscal_counters_query()
    test_curl_commands() 