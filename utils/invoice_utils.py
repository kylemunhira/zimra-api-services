import json
import hashlib
import base64
from datetime import datetime
from app.models import Invoice, InvoiceLineItem, DeviceBranchAddress, DeviceBranchContact, DeviceConfig, FiscalDay
from app import db


def invoice_exists(device_id: str, invoice_id: str) -> bool:
    """Check if an invoice already exists"""
    return Invoice.query.filter_by(device_id=device_id, invoice_id=invoice_id).first() is not None


def get_fiscal_day_counter(device_id: str, fiscal_open_date_time: str) -> int:
    """Get the current fiscal day counter for a device"""
    # This is a simplified version - you might need to implement based on your business logic
    return Invoice.query.filter_by(device_id=device_id).count()


def get_global_number(device_id: str) -> int:
    """Get the global number for a device"""
    # This is a simplified version - you might need to implement based on your business logic
    latest_invoice = Invoice.query.filter_by(device_id=device_id).order_by(Invoice.receipt_global_no.desc()).first()
    return latest_invoice.receipt_global_no if latest_invoice else 0


def get_fiscal_day_open_date_time(open_day_date_time: str) -> str:
    """Get fiscal day open date time in the required format"""
    # Convert the fiscal day open date time to the format expected by counter functions
    try:
        date_obj = datetime.fromisoformat(open_day_date_time.replace('Z', '+00:00'))
        return date_obj.strftime('%Y-%m-%d %H:%M:%S')
    except:
        return open_day_date_time


def get_previous_hash(device_id: str, fiscal_open_date_time: str) -> str:
    """Get the previous receipt hash for chaining"""
    # Get the most recent invoice for this device and fiscal day
    latest_invoice = Invoice.query.filter_by(device_id=device_id).order_by(Invoice.receipt_counter.desc()).first()
    if latest_invoice and latest_invoice.hash_string:
        return latest_invoice.hash_string
    return ''


def calculate_tax_summary(receipt_lines: list) -> dict:
    """Calculate tax summary from receipt lines with enhanced logic like Django"""
    tax_summary = {
        '15': {'taxCode': '15', 'taxPercent': 15.0, 'taxID': 1, 'taxAmount': 0, 'salesAmountWithTax': 0},
        '0': {'taxCode': '0', 'taxPercent': 0.0, 'taxID': 2, 'taxAmount': 0, 'salesAmountWithTax': 0},
        '-1': {'taxCode': None, 'taxPercent': 0.0, 'taxID': None, 'taxAmount': 0, 'salesAmountWithTax': 0},  # Exempt
        '5': {'taxCode': '5', 'taxPercent': 5.0, 'taxID': 3, 'taxAmount': 0, 'salesAmountWithTax': 0}
    }
    
    for line in receipt_lines:
        tax_code = str(line.get('taxCode', '15'))
        tax_percent = float(line.get('taxPercent', 15.0))
        line_total = float(line.get('receiptLineTotal', 0))
        
        # Map tax codes to the summary structure
        if tax_code in tax_summary:
            tax_summary[tax_code]['taxAmount'] += line_total * (tax_percent / 100)
            tax_summary[tax_code]['salesAmountWithTax'] += line_total
        else:
            # Default to 15% if tax code not found
            tax_summary['15']['taxAmount'] += line_total * 0.15
            tax_summary['15']['salesAmountWithTax'] += line_total
    
    return tax_summary


def calculate_total_sales_amount_with_tax(tax_summary: list) -> float:
    """Calculate total sales amount with tax"""
    total = 0
    for tax in tax_summary:
        total += float(tax.get('salesAmountWithTax', 0))
    return total


def get_tax_percentage(tax_code: str) -> float:
    """Get tax percentage for a tax code"""
    tax_percentages = {
        'A': 0.0,
        'B': 0.0,
        'C': 15.0,
        'D': 0.0,
        '15': 15.0,
        '0': 0.0,
        '5': 5.0
    }
    return tax_percentages.get(tax_code.upper(), 15.0)


def get_tax_id(tax_code: str) -> int:
    """Get tax ID for a tax code"""
    tax_ids = {
        'A': 1,
        'B': 2,
        'C': 3,
        'D': 4,
        '15': 1,
        '0': 2,
        '5': 3
    }
    return tax_ids.get(tax_code.upper(), 1)


def create_invoice_line_items(invoice_id: int, receipt_lines: list) -> list:
    """Create invoice line items from receipt lines"""
    line_items = []
    
    for i, line in enumerate(receipt_lines, 1):
        line_item = InvoiceLineItem(
            invoice_id=invoice_id,
            receipt_line_type=line.get('receiptLineType', 'Sale'),
            receipt_line_no=i,
            receipt_line_hs_code=line.get('receiptLineHSCode', '12345'),
            receipt_line_name=line.get('receiptLineName'),
            receipt_line_price=float(line.get('receiptLinePrice', 0)),
            receipt_line_quantity=float(line.get('receiptLineQuantity', 0)),
            receipt_line_total=float(line.get('receiptLineTotal', 0)),
            tax_code=line.get('taxCode', '15'),
            tax_percent=get_tax_percentage(line.get('taxCode', '15')),
            tax_id=get_tax_id(line.get('taxCode', '15'))
        )
        line_items.append(line_item)
        db.session.add(line_item)
    
    return line_items


def create_invoice(invoice_data: dict) -> Invoice:
    """Create a new invoice"""
    invoice = Invoice(
        invoice_id=invoice_data['invoice_id'],
        device_id=invoice_data['device_id'],
        receipt_currency=invoice_data['receipt_currency'],
        money_type=invoice_data['money_type'],
        receipt_type=invoice_data['receipt_type'],
        receipt_total=invoice_data['receipt_total']
    )
    
    db.session.add(invoice)
    db.session.commit()
    
    # Create line items
    if 'line_items' in invoice_data:
        create_invoice_line_items(invoice.id, invoice_data['line_items'])
    
    return invoice


def update_fiscalized_invoice(update_data: dict) -> Invoice:
    """Update invoice with fiscalization data"""
    invoice = Invoice.query.filter_by(invoice_id=update_data['invoice_id']).first()
    
    if not invoice:
        raise ValueError(f"Invoice {update_data['invoice_id']} not found")
    
    # Update ZIMRA response data
    invoice.zimra_receipt_number = update_data.get('zimra_receipt_number')
    invoice.operation_id = update_data.get('operation_id')
    invoice.qr_code_string = update_data.get('qr_code_string')
    invoice.verification_number = update_data.get('verification_number')
    invoice.hash_string = update_data.get('hash_string')
    invoice.is_fiscalized = update_data.get('is_fiscalized', True)
    
    # Update receipt details
    invoice.receipt_counter = update_data.get('receipt_counter')
    invoice.receipt_global_no = update_data.get('receipt_global_no')
    invoice.fiscal_day_number = update_data.get('fiscal_day_number')
    invoice.receipt_notes = update_data.get('receipt_notes', '')
    
    # Update tax payer information
    invoice.tax_payer_name = update_data.get('tax_payer_name')
    invoice.tax_payer_tin = update_data.get('tax_payer_tin')
    invoice.vat_number = update_data.get('vat_number')
    invoice.device_branch_name = update_data.get('device_branch_name')
    
    # Update credit/debit note information
    invoice.debit_credit_note_invoice_ref = update_data.get('debit_credit_note_invoice_ref')
    invoice.debit_credit_note_invoice_ref_date = update_data.get('debit_credit_note_invoice_ref_date')
    
    # Create or update device branch address
    if 'device_branch_address' in update_data:
        address_data = update_data['device_branch_address']
        address = DeviceBranchAddress.query.filter_by(invoice_id=invoice.id).first()
        if not address:
            address = DeviceBranchAddress(invoice_id=invoice.id)
            db.session.add(address)
        
        address.city = address_data.get('city')
        address.house_no = address_data.get('house_no')
        address.province = address_data.get('province')
        address.street = address_data.get('street')
    
    # Create or update device branch contact
    if 'device_branch_contact' in update_data:
        contact_data = update_data['device_branch_contact']
        contact = DeviceBranchContact.query.filter_by(invoice_id=invoice.id).first()
        if not contact:
            contact = DeviceBranchContact(invoice_id=invoice.id)
            db.session.add(contact)
        
        contact.email = contact_data.get('email')
        contact.phone_number = contact_data.get('phone_number')
    
    db.session.commit()
    return invoice


def qr_string_generator(device_id: str, qr_url: str, receipt_date: str, 
                       reciept_global_no: int, reciept_signature: str) -> str:
    """
    Generate QR code string in the correct ZIMRA format.
    
    Expected format:
    https://fdmstest.zimra.co.zw/Receipt/Result?DeviceId=0000026241&ReceiptDate=07%2F30%2F2025%2000%3A00%3A00&ReceiptGlobalNo=0000000013&ReceiptQrData=A4CA-3605-FF81-F1BA
    """
    import urllib.parse
    
    # Pad device ID with zeros to 10 digits
    padded_device_id = device_id.zfill(10)
    
    # Pad receipt global number with zeros to 10 digits
    padded_receipt_global_no = str(reciept_global_no).zfill(10)
    
    # Format receipt date as MM/DD/YYYY HH:MM:SS and URL encode it
    # receipt_date should be in format like "2025-07-30"
    try:
        date_obj = datetime.strptime(receipt_date, '%Y-%m-%d')
        formatted_date = date_obj.strftime('%m/%d/%Y 00:00:00')
    except:
        # Fallback to current date if parsing fails
        formatted_date = datetime.now().strftime('%m/%d/%Y 00:00:00')
    
    # URL encode the date
    encoded_date = urllib.parse.quote(formatted_date)
    
    # Convert signature to hex format (like Django implementation)
    # The signature should be in base64 format, convert to hex
    try:
        signature_bytes = base64.b64decode(reciept_signature)
        hex_signature = signature_bytes.hex().upper()
        # Format as 4-character groups separated by hyphens
        formatted_signature = '-'.join([hex_signature[i:i+4] for i in range(0, len(hex_signature), 4)])
    except:
        # Fallback if signature conversion fails
        formatted_signature = "0000-0000-0000-0000"
    
    # Build the QR URL with query parameters
    qr_string = f"{qr_url}Receipt/Result?DeviceId={padded_device_id}&ReceiptDate={encoded_date}&ReceiptGlobalNo={padded_receipt_global_no}&ReceiptQrData={formatted_signature}"
    
    return qr_string


def base64_to_hex_md5(base64_signature: str) -> str:
    """Convert base64 signature to hex MD5"""
    # Decode base64 signature
    signature_bytes = base64.b64decode(base64_signature)
    # Generate MD5 hash
    md5_hash = hashlib.md5(signature_bytes).hexdigest()
    return md5_hash


def get_device_config(device_id: str) -> dict:
    """Get device configuration"""
    device_config = DeviceConfig.query.filter_by(device_id=device_id).first()
    if device_config:
        return json.loads(device_config.config)
    return {}


def qr_date() -> str:
    """Get current date for QR code in YYYY-MM-DD format"""
    return datetime.now().strftime('%Y-%m-%d')


def receipt_date_print() -> str:
    """Get formatted receipt date for printing"""
    return datetime.now().strftime('%d/%m/%Y %H:%M:%S')


def get_credit_debit_note_invoice(device_id: str, receipt_id: str) -> Invoice:
    """Get the invoice referenced in a credit/debit note"""
    return Invoice.query.filter_by(device_id=device_id, zimra_receipt_number=receipt_id).first() 