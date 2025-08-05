#!/usr/bin/env python3
"""
Script to extract information from Fiscal Device Gateway API -Clients.pdf
Specifically looking for section 10.2 InvoiceA4 view
"""

import PyPDF2
import re

def extract_api_documentation():
    """Extract information from the API documentation PDF"""
    
    try:
        reader = PyPDF2.PdfReader('Fiscal Device Gateway API -Clients.pdf')
        
        print("=== API Documentation Analysis ===")
        print(f"Total pages: {len(reader.pages)}")
        
        # Search for section 10.2 InvoiceA4 view
        invoice_a4_content = []
        section_found = False
        
        for page_num, page in enumerate(reader.pages):
            text = page.extract_text()
            
            # Look for section 10.2
            if "10.2" in text and "InvoiceA4" in text:
                section_found = True
                print(f"\n=== Found Section 10.2 InvoiceA4 on page {page_num + 1} ===")
                invoice_a4_content.append(f"Page {page_num + 1}: {text}")
            
            # Also look for any invoice-related content
            elif "InvoiceA4" in text or "invoice" in text.lower():
                print(f"\n=== Invoice-related content on page {page_num + 1} ===")
                invoice_a4_content.append(f"Page {page_num + 1}: {text}")
        
        if not section_found:
            print("Section 10.2 InvoiceA4 not found. Searching for any invoice-related content...")
            
            # Search all pages for invoice content
            for page_num, page in enumerate(reader.pages):
                text = page.extract_text()
                if "invoice" in text.lower() or "receipt" in text.lower():
                    print(f"\n=== Invoice/Receipt content on page {page_num + 1} ===")
                    print(text[:500] + "..." if len(text) > 500 else text)
        
        return invoice_a4_content
        
    except Exception as e:
        print(f"Error analyzing API documentation: {e}")
        return []

def search_for_specific_patterns():
    """Search for specific patterns in the API documentation"""
    
    try:
        reader = PyPDF2.PdfReader('Fiscal Device Gateway API -Clients.pdf')
        
        patterns = [
            "10.2",
            "InvoiceA4",
            "invoice format",
            "A4 format",
            "receipt format",
            "fiscal receipt",
            "ZIMRA receipt"
        ]
        
        print("\n=== Searching for specific patterns ===")
        
        for page_num, page in enumerate(reader.pages):
            text = page.extract_text()
            
            for pattern in patterns:
                if pattern.lower() in text.lower():
                    print(f"\nPattern '{pattern}' found on page {page_num + 1}")
                    # Extract context around the pattern
                    lines = text.split('\n')
                    for i, line in enumerate(lines):
                        if pattern.lower() in line.lower():
                            start = max(0, i-2)
                            end = min(len(lines), i+3)
                            context = '\n'.join(lines[start:end])
                            print(f"Context:\n{context}")
                            break
        
    except Exception as e:
        print(f"Error searching patterns: {e}")

if __name__ == "__main__":
    extract_api_documentation()
    search_for_specific_patterns() 