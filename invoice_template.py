#!/usr/bin/env python3
"""
Invoice Template based on A4 receipt format - Updated to match ZIMRA InvoiceA4 view specification
"""

from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, mm
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
import io
import qrcode
from datetime import datetime

def create_qr_code(data, size=100):
    """Create QR code image"""
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Convert PIL image to bytes
    img_buffer = io.BytesIO()
    img.save(img_buffer, format='PNG')
    img_buffer.seek(0)
    return img_buffer

def generate_invoice_pdf_a4_format(invoice_data):
    """Generate invoice PDF using A4 template format matching ZIMRA InvoiceA4 view specification"""
    
    # Create PDF document with A4 size and proper margins
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, 
        pagesize=A4, 
        rightMargin=15*mm, 
        leftMargin=15*mm, 
        topMargin=15*mm, 
        bottomMargin=15*mm
    )
    
    # Create custom styles
    styles = getSampleStyleSheet()
    
    # Title style for "FISCAL TAX INVOICE"
    title_style = ParagraphStyle(
        'TitleStyle',
        parent=styles['Heading1'],
        fontSize=18,
        fontName='Helvetica-Bold',
        alignment=TA_CENTER,
        spaceAfter=20
    )
    
    # Section header style
    section_style = ParagraphStyle(
        'SectionStyle',
        parent=styles['Heading2'],
        fontSize=12,
        fontName='Helvetica-Bold',
        spaceAfter=6
    )
    
    # Normal text style
    normal_style = ParagraphStyle(
        'NormalStyle',
        parent=styles['Normal'],
        fontSize=10,
        fontName='Helvetica',
        spaceAfter=3
    )
    
    # Small text style
    small_style = ParagraphStyle(
        'SmallStyle',
        parent=styles['Normal'],
        fontSize=8,
        fontName='Helvetica',
        spaceAfter=2
    )
    
    # Story elements
    story = []
    
    # ===== HEADER SECTION =====
    # FISCAL TAX INVOICE title
    story.append(Paragraph("FISCAL TAX INVOICE", title_style))
    story.append(Spacer(1, 10))
    
    # ===== VERIFICATION SECTION =====
    if invoice_data.get('verification_number'):
        verification_style = ParagraphStyle(
            'VerificationStyle',
            parent=styles['Normal'],
            fontSize=10,
            fontName='Helvetica',
            alignment=TA_CENTER,
            spaceAfter=6
        )
        story.append(Paragraph(f"Verification code", verification_style))
        story.append(Paragraph(f"{invoice_data.get('verification_number')}", verification_style))
        story.append(Paragraph("You can verify this receipt manually at", verification_style))
        story.append(Paragraph("https://receipt.zimra.org/", verification_style))
        story.append(Spacer(1, 15))
    
    # ===== SELLER/BUYER SECTION =====
    # Create a table with SELLER and BUYER columns
    seller_buyer_data = []
    
    # Seller information
    seller_info = []
    seller_info.append(Paragraph("SELLER", section_style))
    seller_info.append(Paragraph(f"Company legal name: {invoice_data.get('tax_payer_name', 'N/A')}", normal_style))
    seller_info.append(Paragraph(f"TIN: {invoice_data.get('tax_payer_tin', 'N/A')}", normal_style))
    if invoice_data.get('vat_number'):
        seller_info.append(Paragraph(f"VAT No: {invoice_data.get('vat_number')}", normal_style))
    if invoice_data.get('device_branch_name'):
        seller_info.append(Paragraph(f"{invoice_data.get('device_branch_name')}", normal_style))
    if invoice_data.get('branch_address'):
        seller_info.append(Paragraph(f"{invoice_data.get('branch_address')}", normal_style))
    if invoice_data.get('branch_contact'):
        contact_parts = invoice_data.get('branch_contact', '').split(', ')
        for contact in contact_parts:
            if contact.strip():
                seller_info.append(Paragraph(contact.strip(), normal_style))
    
    # Buyer information (if available)
    buyer_info = []
    buyer_info.append(Paragraph("BUYER", section_style))
    # Note: Buyer information would come from invoice_data if available
    # For now, we'll use placeholder or leave empty
    buyer_info.append(Paragraph("Company ABC, Ltd.", normal_style))
    buyer_info.append(Paragraph("Food Market ABC", normal_style))
    buyer_info.append(Paragraph("TIN: 19870123", normal_style))
    buyer_info.append(Paragraph("12 Southgate Hwange", normal_style))
    buyer_info.append(Paragraph("john.smith@email.com", normal_style))
    buyer_info.append(Paragraph("(081) 20875", normal_style))
    
    # Add seller and buyer to table
    seller_buyer_data.append([seller_info, buyer_info])
    
    seller_buyer_table = Table(seller_buyer_data, colWidths=[3*inch, 3*inch])
    seller_buyer_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
    ]))
    story.append(seller_buyer_table)
    story.append(Spacer(1, 15))
    
    # ===== RECEIPT INFORMATION SECTION =====
    receipt_info_data = []
    
    # Receipt details
    receipt_info_data.append([
        Paragraph("Receipt No:", normal_style),
        Paragraph(f"{invoice_data.get('receipt_counter', 'N/A')}/{invoice_data.get('receipt_global_no', 'N/A')}", normal_style),
        Paragraph("Fiscal day No:", normal_style),
        Paragraph(f"{invoice_data.get('fiscal_day_number', 'N/A')}", normal_style)
    ])
    
    receipt_info_data.append([
        Paragraph("Invoice No:", normal_style),
        Paragraph(f"{invoice_data.get('zimra_receipt_number', 'N/A')}", normal_style),
        Paragraph("Date:", normal_style),
        Paragraph(f"{invoice_data.get('created_at', 'N/A')}", normal_style)
    ])
    
    receipt_info_data.append([
        Paragraph("Device Serial No:", normal_style),
        Paragraph(f"{invoice_data.get('device_id', 'N/A')}", normal_style),
        Paragraph("Fiscal device ID:", normal_style),
        Paragraph(f"{invoice_data.get('device_id', 'N/A')}", normal_style)
    ])
    
    # Add credit/debit note information if available
    if invoice_data.get('debit_credit_note_invoice_ref_date'):
        receipt_info_data.append([
            Paragraph("Receipt No:", normal_style),
            Paragraph(f"{invoice_data.get('receipt_counter', 'N/A')}", normal_style),
            Paragraph("Date:", normal_style),
            Paragraph(f"{invoice_data.get('debit_credit_note_invoice_ref_date')}", normal_style)
        ])
        receipt_info_data.append([
            Paragraph("Invoice No:", normal_style),
            Paragraph(f"{invoice_data.get('zimra_receipt_number', 'N/A')}", normal_style),
            Paragraph("", normal_style),
            Paragraph("", normal_style)
        ])
        receipt_info_data.append([
            Paragraph("Device Serial No:", normal_style),
            Paragraph(f"{invoice_data.get('device_id', 'N/A')}", normal_style),
            Paragraph("", normal_style),
            Paragraph("", normal_style)
        ])
    
    receipt_info_table = Table(receipt_info_data, colWidths=[1.5*inch, 2*inch, 1.5*inch, 1.5*inch])
    receipt_info_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
        ('ALIGN', (2, 0), (2, -1), 'LEFT'),
        ('ALIGN', (3, 0), (3, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
    ]))
    story.append(receipt_info_table)
    story.append(Spacer(1, 15))
    
    # ===== LINE ITEMS SECTION =====
    if invoice_data.get('line_items'):
        # Table headers matching the format from the API documentation
        headers = ['Code', 'Description', 'Qty', 'Price', 'VAT', 'Amount (excl. tax)']
        table_data = [headers]
        
        # Add line items
        for item in invoice_data['line_items']:
            # Format tax information
            tax_info = f"{item.get('tax_percent', 0)}%"
            if item.get('tax_code'):
                tax_info = f"{item.get('tax_code')} {item.get('tax_percent', 0)}%"
            
            table_data.append([
                item.get('receipt_line_hs_code', 'N/A'),
                item.get('receipt_line_name', ''),
                str(item.get('receipt_line_quantity', 1)),
                f"{item.get('receipt_line_price', 0):.2f}",
                tax_info,
                f"{item.get('receipt_line_total', 0):.2f}"
            ])
        
        # Add total row
        table_data.append([
            'Total', '', '', '', '', 
            f"{invoice_data.get('receipt_total', 0):.2f}"
        ])
        
        # Calculate column widths
        col_widths = [0.8*inch, 2.2*inch, 0.6*inch, 0.8*inch, 0.8*inch, 1.2*inch]
        
        items_table = Table(table_data, colWidths=col_widths)
        items_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (2, 1), (2, -2), 'CENTER'),  # Center quantities
            ('ALIGN', (3, 1), (5, -1), 'RIGHT'),  # Right align prices and amounts
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),  # Bold headers
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),  # Bold totals
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ('TOPPADDING', (0, 0), (-1, -1), 2),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey),
        ]))
        story.append(items_table)
        story.append(Spacer(1, 15))
    
    # ===== TAX SUMMARY SECTION =====
    # Calculate tax summary if line items are available
    if invoice_data.get('line_items'):
        tax_summary = {}
        for item in invoice_data['line_items']:
            tax_percent = item.get('tax_percent', 0)
            if tax_percent not in tax_summary:
                tax_summary[tax_percent] = {
                    'amount': 0,
                    'tax_amount': 0,
                    'total_with_tax': 0
                }
            amount = item.get('receipt_line_total', 0)
            tax_amount = amount * (tax_percent / 100)
            tax_summary[tax_percent]['amount'] += amount
            tax_summary[tax_percent]['tax_amount'] += tax_amount
            tax_summary[tax_percent]['total_with_tax'] += amount + tax_amount
        
        if tax_summary:
            tax_data = []
            total_tax = 0
            total_amount = 0
            
            for tax_percent, data in sorted(tax_summary.items(), reverse=True):
                if tax_percent > 0:
                    tax_data.append([
                        f"Total {tax_percent}%",
                        f"{data['amount']:.2f}",
                        f"VAT {data['tax_amount']:.2f}"
                    ])
                    total_tax += data['tax_amount']
                    total_amount += data['total_with_tax']
            
            if tax_data:
                tax_data.append([
                    "Invoice total, ZWL",
                    f"{total_amount:.2f}",
                    ""
                ])
                
                tax_table = Table(tax_data, colWidths=[2*inch, 1.5*inch, 1.5*inch])
                tax_table.setStyle(TableStyle([
                    ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                    ('ALIGN', (1, 0), (2, -1), 'RIGHT'),
                    ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
                    ('TOPPADDING', (0, 0), (-1, -1), 2),
                ]))
                story.append(tax_table)
                story.append(Spacer(1, 15))
    
    # ===== QR CODE SECTION =====
    if invoice_data.get('qr_code_url'):
        try:
            qr_buffer = create_qr_code(invoice_data.get('qr_code_url'))
            qr_image = Image(qr_buffer, width=1*inch, height=1*inch)
            story.append(qr_image)
        except Exception as e:
            story.append(Paragraph(f"QR Code: {invoice_data.get('qr_code_url')}", normal_style))
    
    # ===== FOOTER SECTION =====
    story.append(Spacer(1, 20))
    story.append(Paragraph("Thank you for your business!", normal_style))
    story.append(Paragraph("This is a fiscal receipt generated by ZIMRA compliant system", small_style))
    
    # Build PDF
    doc.build(story)
    buffer.seek(0)
    return buffer

def test_template():
    """Test the template with sample data"""
    sample_data = {
        'invoice_id': 'INV-001',
        'zimra_receipt_number': 'ZIMRA-2024-001',
        'device_id': 'DEVICE-001',
        'created_at': '2024-01-15 14:30:00',
        'is_fiscalized': True,
        'receipt_type': 'SALE',
        'money_type': 'Cash',
        'receipt_counter': 1,
        'receipt_global_no': 1001,
        'fiscal_day_number': 'FD-2024-001',
        'operation_id': 'OP-001',
        'verification_number': 'VER-001',
        'hash_string': 'ABC123DEF456',
        'tax_payer_name': 'Sample Company Ltd',
        'tax_payer_tin': '123456789',
        'vat_number': 'VAT123456',
        'device_branch_name': 'Main Branch',
        'branch_address': '123 Main Street, Harare',
        'branch_contact': '+263 4 123456',
        'receipt_total': 150.00,
        'notes': 'Sample invoice for testing',
        'qr_code_url': 'https://example.com/verify/INV-001',
        'line_items': [
            {
                'receipt_line_name': 'Product A',
                'receipt_line_quantity': 2,
                'receipt_line_price': 50.00,
                'receipt_line_total': 100.00,
                'tax_code': 'VAT',
                'tax_percent': 15,
                'receipt_line_hs_code': 'HS001',
                'tax_id': 1
            },
            {
                'receipt_line_name': 'Product B',
                'receipt_line_quantity': 1,
                'receipt_line_price': 50.00,
                'receipt_line_total': 50.00,
                'tax_code': 'VAT',
                'tax_percent': 15,
                'receipt_line_hs_code': 'HS002',
                'tax_id': 1
            }
        ]
    }
    
    pdf_buffer = generate_invoice_pdf_a4_format(sample_data)
    
    # Save test PDF
    with open('test_invoice_template.pdf', 'wb') as f:
        f.write(pdf_buffer.getvalue())
    
    print("Test invoice template generated: test_invoice_template.pdf")

if __name__ == "__main__":
    test_template() 