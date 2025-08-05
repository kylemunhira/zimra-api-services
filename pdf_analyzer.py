#!/usr/bin/env python3
"""
Enhanced PDF analyzer for receiptA4.pdf
"""

import fitz  # PyMuPDF
import re
from collections import defaultdict

def analyze_pdf_with_pymupdf():
    """Analyze PDF using PyMuPDF for better text extraction"""
    
    try:
        # Try to install PyMuPDF if not available
        import subprocess
        import sys
        subprocess.check_call([sys.executable, "-m", "pip", "install", "PyMuPDF"])
        
        doc = fitz.open("receiptA4.pdf")
        page = doc[0]
        
        # Extract text with positioning
        text_dict = page.get_text("dict")
        
        print("=== PDF Analysis with PyMuPDF ===")
        print(f"Total pages: {len(doc)}")
        print(f"Page size: {page.rect}")
        
        # Extract text blocks
        blocks = text_dict["blocks"]
        print(f"\n=== Text Blocks ===")
        print(f"Total blocks: {len(blocks)}")
        
        # Analyze each block
        for i, block in enumerate(blocks):
            if "lines" in block:
                print(f"\nBlock {i}:")
                print(f"  Bounds: {block['bbox']}")
                print(f"  Type: {block.get('type', 'unknown')}")
                
                for line in block["lines"]:
                    for span in line["spans"]:
                        text = span["text"]
                        font = span["font"]
                        size = span["size"]
                        bbox = span["bbox"]
                        
                        if text.strip():
                            print(f"    Text: '{text}'")
                            print(f"    Font: {font}, Size: {size}")
                            print(f"    Position: {bbox}")
        
        # Extract all text
        text = page.get_text()
        print(f"\n=== Full Text ===")
        print(text)
        
        doc.close()
        return text, blocks
        
    except ImportError:
        print("PyMuPDF not available, trying alternative method...")
        return None, None
    except Exception as e:
        print(f"Error analyzing PDF: {e}")
        return None, None

def create_invoice_template():
    """Create an invoice template based on standard A4 receipt format"""
    
    template = {
        "page_size": "A4",
        "margins": {
            "top": 20,
            "bottom": 20,
            "left": 20,
            "right": 20
        },
        "sections": {
            "header": {
                "position": "top",
                "height": 80,
                "elements": [
                    {"type": "company_logo", "position": (20, 20), "size": (60, 60)},
                    {"type": "company_name", "position": (100, 20), "font": "Helvetica-Bold", "size": 16},
                    {"type": "company_address", "position": (100, 40), "font": "Helvetica", "size": 10},
                    {"type": "company_contact", "position": (100, 55), "font": "Helvetica", "size": 10},
                    {"type": "invoice_title", "position": (400, 20), "font": "Helvetica-Bold", "size": 18},
                    {"type": "invoice_number", "position": (400, 40), "font": "Helvetica", "size": 12},
                    {"type": "invoice_date", "position": (400, 55), "font": "Helvetica", "size": 12}
                ]
            },
            "customer_info": {
                "position": "below_header",
                "height": 60,
                "elements": [
                    {"type": "bill_to_label", "position": (20, 100), "font": "Helvetica-Bold", "size": 12},
                    {"type": "customer_name", "position": (20, 115), "font": "Helvetica", "size": 12},
                    {"type": "customer_address", "position": (20, 130), "font": "Helvetica", "size": 10},
                    {"type": "customer_contact", "position": (20, 145), "font": "Helvetica", "size": 10}
                ]
            },
            "items_table": {
                "position": "middle",
                "start_y": 180,
                "headers": ["Item", "Description", "Qty", "Unit Price", "Amount"],
                "column_widths": [80, 200, 60, 80, 80],
                "row_height": 20
            },
            "totals": {
                "position": "bottom",
                "start_y": 500,
                "elements": [
                    {"type": "subtotal", "position": (400, 500), "font": "Helvetica", "size": 12},
                    {"type": "tax", "position": (400, 520), "font": "Helvetica", "size": 12},
                    {"type": "total", "position": (400, 540), "font": "Helvetica-Bold", "size": 14},
                    {"type": "balance_due", "position": (400, 560), "font": "Helvetica-Bold", "size": 14}
                ]
            },
            "footer": {
                "position": "bottom",
                "start_y": 600,
                "elements": [
                    {"type": "notes", "position": (20, 600), "font": "Helvetica", "size": 10},
                    {"type": "terms", "position": (20, 620), "font": "Helvetica", "size": 10},
                    {"type": "thank_you", "position": (300, 600), "font": "Helvetica-Bold", "size": 12},
                    {"type": "qr_code", "position": (500, 600), "size": (60, 60)}
                ]
            }
        }
    }
    
    return template

def generate_template_code():
    """Generate Python code for the invoice template"""
    
    template = create_invoice_template()
    
    code = '''
def generate_invoice_pdf(invoice_data):
    """Generate invoice PDF using A4 template format"""
    
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch, mm
    from reportlab.lib import colors
    import io
    
    # Create PDF document
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=20*mm, leftMargin=20*mm, 
                           topMargin=20*mm, bottomMargin=20*mm)
    
    # Styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        spaceAfter=30,
        alignment=1  # Center alignment
    )
    
    # Story elements
    story = []
    
    # Header Section
    story.append(Paragraph("COMPANY NAME", title_style))
    story.append(Paragraph("Company Address Line 1", styles['Normal']))
    story.append(Paragraph("Phone: +123 456 7890 | Email: info@company.com", styles['Normal']))
    story.append(Spacer(1, 20))
    
    # Invoice Info
    invoice_info = [
        ['Invoice #:', invoice_data.get('invoice_id', 'N/A')],
        ['Date:', invoice_data.get('created_at', 'N/A')],
        ['Status:', 'Fiscalized' if invoice_data.get('is_fiscalized') else 'Pending']
    ]
    
    invoice_table = Table(invoice_info, colWidths=[1*inch, 3*inch])
    invoice_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(invoice_table)
    story.append(Spacer(1, 20))
    
    # Customer Information
    story.append(Paragraph("Bill To:", styles['Heading2']))
    story.append(Paragraph("Customer Name", styles['Normal']))
    story.append(Paragraph("Customer Address", styles['Normal']))
    story.append(Spacer(1, 20))
    
    # Items Table
    if invoice_data.get('line_items'):
        story.append(Paragraph("Items", styles['Heading2']))
        
        # Table headers
        headers = ['Item', 'Description', 'Qty', 'Unit Price', 'Amount']
        table_data = [headers]
        
        # Add items
        for item in invoice_data['line_items']:
            table_data.append([
                item.get('receipt_line_name', ''),
                item.get('description', ''),
                str(item.get('receipt_line_quantity', 0)),
                f"${item.get('receipt_line_price', 0):.2f}",
                f"${item.get('receipt_line_total', 0):.2f}"
            ])
        
        # Add totals row
        table_data.append(['', '', '', 'TOTAL:', f"${invoice_data.get('receipt_total', 0):.2f}"])
        
        items_table = Table(table_data, colWidths=[1.5*inch, 2*inch, 0.8*inch, 1*inch, 1*inch])
        items_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (2, 1), (-1, -1), 'RIGHT'),  # Right align numbers
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),  # Bold headers
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),  # Bold totals
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ]))
        story.append(items_table)
    
    story.append(Spacer(1, 20))
    
    # Footer
    story.append(Paragraph("Thank you for your business!", styles['Normal']))
    story.append(Paragraph("Terms: Payment due within 30 days", styles['Normal']))
    
    # Build PDF
    doc.build(story)
    buffer.seek(0)
    return buffer
'''
    
    return code

if __name__ == "__main__":
    print("=== PDF Analysis ===")
    text, blocks = analyze_pdf_with_pymupdf()
    
    print("\n=== Template Generation ===")
    template = create_invoice_template()
    print("Invoice template structure created")
    
    print("\n=== Generated Code ===")
    code = generate_template_code()
    print(code) 