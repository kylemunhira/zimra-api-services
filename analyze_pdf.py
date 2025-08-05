#!/usr/bin/env python3
"""
Script to analyze the receiptA4.pdf structure and create an invoice template
"""

import PyPDF2
import re
from collections import defaultdict

def analyze_pdf_structure():
    """Analyze the PDF structure and extract layout information"""
    
    try:
        reader = PyPDF2.PdfReader('receiptA4.pdf')
        page = reader.pages[0]
        text = page.extract_text()
        
        print("=== PDF Analysis ===")
        print(f"Total pages: {len(reader.pages)}")
        print(f"Text length: {len(text)} characters")
        print("\n=== Extracted Text ===")
        print(text)
        
        # Analyze the structure
        lines = text.split('\n')
        print(f"\n=== Line Analysis ===")
        print(f"Total lines: {len(lines)}")
        
        # Group lines by content type
        sections = defaultdict(list)
        current_section = "header"
        
        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
                
            # Identify sections based on content patterns
            if any(keyword in line.lower() for keyword in ['invoice', 'receipt', 'bill']):
                current_section = "header"
            elif any(keyword in line.lower() for keyword in ['customer', 'client', 'bill to']):
                current_section = "customer"
            elif any(keyword in line.lower() for keyword in ['item', 'description', 'qty', 'quantity', 'price', 'amount']):
                current_section = "items"
            elif any(keyword in line.lower() for keyword in ['total', 'subtotal', 'tax', 'balance']):
                current_section = "totals"
            elif any(keyword in line.lower() for keyword in ['thank', 'note', 'terms']):
                current_section = "footer"
                
            sections[current_section].append((i, line))
        
        print(f"\n=== Section Analysis ===")
        for section, lines_list in sections.items():
            print(f"\n{section.upper()} ({len(lines_list)} lines):")
            for line_num, line_content in lines_list[:5]:  # Show first 5 lines
                print(f"  Line {line_num}: {line_content}")
            if len(lines_list) > 5:
                print(f"  ... and {len(lines_list) - 5} more lines")
        
        return text, sections
        
    except Exception as e:
        print(f"Error analyzing PDF: {e}")
        return None, None

def create_template_structure():
    """Create a template structure based on the analysis"""
    
    text, sections = analyze_pdf_structure()
    
    if not text:
        return
    
    print(f"\n=== Template Structure ===")
    
    # Create a template based on common invoice patterns
    template = {
        "header": {
            "company_info": {
                "name": "COMPANY NAME",
                "address": "COMPANY ADDRESS",
                "phone": "PHONE",
                "email": "EMAIL"
            },
            "invoice_info": {
                "title": "INVOICE",
                "number": "INVOICE #",
                "date": "DATE",
                "due_date": "DUE DATE"
            }
        },
        "customer": {
            "bill_to": "BILL TO:",
            "name": "CUSTOMER NAME",
            "address": "CUSTOMER ADDRESS",
            "phone": "CUSTOMER PHONE"
        },
        "items": {
            "headers": ["ITEM", "DESCRIPTION", "QTY", "UNIT PRICE", "AMOUNT"],
            "data": []
        },
        "totals": {
            "subtotal": "SUBTOTAL",
            "tax": "TAX",
            "total": "TOTAL",
            "balance": "BALANCE DUE"
        },
        "footer": {
            "notes": "NOTES:",
            "terms": "TERMS:",
            "thank_you": "THANK YOU FOR YOUR BUSINESS"
        }
    }
    
    print("Template structure created based on standard invoice format")
    return template

if __name__ == "__main__":
    analyze_pdf_structure()
    create_template_structure() 