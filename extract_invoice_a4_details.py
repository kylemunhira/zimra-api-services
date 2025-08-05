#!/usr/bin/env python3
"""
Script to extract detailed information about InvoiceA4 view from the API documentation
"""

import PyPDF2

def extract_invoice_a4_details():
    """Extract detailed information about InvoiceA4 view"""
    
    try:
        reader = PyPDF2.PdfReader('Fiscal Device Gateway API -Clients.pdf')
        
        print("=== InvoiceA4 View Details ===")
        
        # Focus on pages around 31 (InvoiceA4 section)
        target_pages = [30, 31, 32, 33, 34, 35]
        
        for page_num in target_pages:
            if page_num < len(reader.pages):
                page = reader.pages[page_num]
                text = page.extract_text()
                
                print(f"\n=== Page {page_num + 1} ===")
                print(text)
                print("=" * 80)
        
        # Also check for field descriptions
        print("\n=== Field Descriptions (Pages 32-34) ===")
        for page_num in range(32, 35):
            if page_num < len(reader.pages):
                page = reader.pages[page_num]
                text = page.extract_text()
                
                # Look for InvoiceA4 specific fields
                if "InvoiceA4" in text or "invoice" in text.lower():
                    print(f"\n--- Page {page_num + 1} ---")
                    print(text)
        
    except Exception as e:
        print(f"Error extracting details: {e}")

def search_for_invoice_fields():
    """Search for specific fields used in InvoiceA4 view"""
    
    try:
        reader = PyPDF2.PdfReader('Fiscal Device Gateway API -Clients.pdf')
        
        # Fields that are likely used in InvoiceA4 view
        invoice_fields = [
            "receiptNumber",
            "deviceId", 
            "dateTime",
            "taxPayerName",
            "taxPayerTin",
            "vatNumber",
            "deviceBranchName",
            "receiptTotal",
            "lineItems",
            "taxAmount",
            "salesAmountWithTax",
            "exclusive",
            "inclusive"
        ]
        
        print("\n=== InvoiceA4 Field Information ===")
        
        for page_num, page in enumerate(reader.pages):
            text = page.extract_text()
            
            for field in invoice_fields:
                if field.lower() in text.lower():
                    print(f"\nField '{field}' found on page {page_num + 1}")
                    # Extract context
                    lines = text.split('\n')
                    for i, line in enumerate(lines):
                        if field.lower() in line.lower():
                            start = max(0, i-1)
                            end = min(len(lines), i+2)
                            context = '\n'.join(lines[start:end])
                            print(f"Context: {context}")
                            break
        
    except Exception as e:
        print(f"Error searching fields: {e}")

if __name__ == "__main__":
    extract_invoice_a4_details()
    search_for_invoice_fields() 