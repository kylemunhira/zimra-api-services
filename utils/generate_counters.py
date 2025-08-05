import datetime
from app.models import Invoice, InvoiceLineItem
from app import db
from utils.invoice_utils import calculate_tax_summary, get_tax_percentage, get_tax_id


""" def get_fiscal_day_open_date_time(open_day_date_time:str):
    return get_fiscal_day_open_date_time_dao(open_day_date_time) """


def generate_counters(private_key: str, device_id: str, date_string: str, close_day_date: str, fiscal_day_no: int) -> dict:
    """
    Generate fiscal day counters for close day operation.
    
    Parameters:
        private_key (str): Device private key
        device_id (str): Device identifier
        date_string (str): Fiscal day open date
        close_day_date (str): Close day date
        fiscal_day_no (int): Fiscal day number
        
    Returns:
        dict: Complete close day payload with counters
    """
    current_date = datetime.datetime.today().strftime("%Y-%m-%d")
    
    # Get all invoices for this device and fiscal day
    invoices = Invoice.query.filter_by(
        device_id=str(device_id),
        fiscal_day_number=str(fiscal_day_no)  # Use fiscal_day_number and convert to string
    ).all()
    
    if not invoices:
        raise ValueError(f"No invoices found for device {device_id} and fiscal day {fiscal_day_no}")
    
    # Calculate total receipt counter
    total_receipt_counter = sum(invoice.receipt_counter or 0 for invoice in invoices)
    
    # Generate fiscal day counters from invoice data
    fiscal_day_counters = []
    
    # Group invoices by tax type and calculate totals
    tax_summary = {}
    
    for invoice in invoices:
        line_items = InvoiceLineItem.query.filter_by(invoice_id=invoice.id).all()
        
        for line_item in line_items:
            tax_code = line_item.tax_code or 'C'  # Default to 15% tax
            tax_percent = get_tax_percentage(tax_code)
            tax_id = get_tax_id(tax_code)
            
            if tax_percent not in tax_summary:
                tax_summary[tax_percent] = {
                    'taxID': tax_id,
                    'taxAmount': 0.0,
                    'salesAmountWithTax': 0.0,
                    'salesAmount': 0.0
                }
            
            # Calculate tax amount
            line_total = float(line_item.receipt_line_total or 0)
            tax_amount = round(line_total * (tax_percent / 100), 2)
            
            tax_summary[tax_percent]['salesAmount'] += line_total
            tax_summary[tax_percent]['taxAmount'] += tax_amount
            tax_summary[tax_percent]['salesAmountWithTax'] += line_total + tax_amount
    
    # Convert tax summary to fiscal day counters
    for tax_percent, data in tax_summary.items():
        if data['salesAmount'] > 0:
            # Get the most common currency from invoices (default to ZWL)
            currency = 'ZWL'  # Default currency
            if invoices:
                # Use the currency from the first invoice as reference
                currency = invoices[0].receipt_currency or 'ZWL'
            
            # SaleByTax counter
            fiscal_day_counters.append({
                'fiscalCounterType': 'SaleByTax',
                'fiscalCounterTaxID': data['taxID'],
                'fiscalCounterTaxPercent': tax_percent,
                'fiscalCounterCurrency': currency,
                'fiscalCounterValue': round(data['salesAmount'], 2)
            })
            
            # SaleTaxByTax counter
            fiscal_day_counters.append({
                'fiscalCounterType': 'SaleTaxByTax',
                'fiscalCounterTaxID': data['taxID'],
                'fiscalCounterTaxPercent': tax_percent,
                'fiscalCounterCurrency': currency,
                'fiscalCounterValue': round(data['taxAmount'], 2)
            })
    
    # Add BalanceByMoneyType counter (total sales with tax)
    total_sales_with_tax = sum(data['salesAmountWithTax'] for data in tax_summary.values())
    if total_sales_with_tax > 0:
        # Get the most common money type from invoices (default to Cash)
        money_type = 'Cash'  # Default money type
        if invoices:
            # Use the money type from the first invoice as reference
            money_type = invoices[0].money_type or 'Cash'
        
        fiscal_day_counters.append({
            'fiscalCounterType': 'BalanceByMoneyType',
            'fiscalCounterCurrency': currency,
            'fiscalCounterMoneyType': money_type.upper(),
            'fiscalCounterValue': round(total_sales_with_tax, 2)
        })
    
    # Create the complete payload
    payload = {
        'fiscalDayNo': str(fiscal_day_no),
        'fiscalDayCounters': fiscal_day_counters,
        'receiptCounter': total_receipt_counter
    }
    
    return payload 
    