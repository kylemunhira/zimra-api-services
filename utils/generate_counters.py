import datetime
from app.models import Invoice, InvoiceLineItem
from app import db
from utils.invoice_utils import calculate_tax_summary, get_tax_percentage, get_tax_id


""" def get_fiscal_day_open_date_time(open_day_date_time:str):
    return get_fiscal_day_open_date_time_dao(open_day_date_time) """


def generate_counters(private_key: str, device_id: str, date_string: str, close_day_date: str, fiscal_day_no: int) -> dict:
    """
    Generate fiscal day counters for close day operation according to ZIMRA API specification.
    
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
    
    # Calculate total receipt counter
    total_receipt_counter = sum(invoice.receipt_counter or 0 for invoice in invoices)
    
    # Initialize fiscal day counters list
    fiscal_day_counters = []
    
    # Define all supported currencies
    supported_currencies = ['ZWG', 'USD']
    
    # Define all supported tax IDs and their details
    tax_configs = {
        1: {'tax_code': 'A', 'tax_percent': None, 'description': 'Exempt'},
        2: {'tax_code': 'B', 'tax_percent': 0.0, 'description': 'Zero-rate'},
        3: {'tax_code': 'C', 'tax_percent': 15.0, 'description': 'Standard rate'}
    }
    
    # Define supported money type (CASH only)
    supported_money_types = ['CASH']
    
    # Group invoices by receipt type, currency, and tax type
    # Structure: {receipt_type: {currency: {tax_id: {taxID, taxAmount, salesAmount, salesAmountWithTax, taxPercent}}}}
    receipt_type_summary = {}
    
    for invoice in invoices:
        line_items = InvoiceLineItem.query.filter_by(invoice_id=invoice.id).all()
        currency = invoice.receipt_currency or 'ZWG'
        receipt_type = invoice.receipt_type or 'SALE'
        
        # Normalize receipt type - treat FiscalInvoice as SALE
        if receipt_type in ['FiscalInvoice', 'SALE']:
            normalized_receipt_type = 'SALE'
        elif receipt_type in ['CREDIT_NOTE', 'CreditNote']:
            normalized_receipt_type = 'CREDIT_NOTE'
        elif receipt_type in ['DEBIT_NOTE', 'DebitNote']:
            normalized_receipt_type = 'DEBIT_NOTE'
        else:
            normalized_receipt_type = receipt_type
        
        if normalized_receipt_type not in receipt_type_summary:
            receipt_type_summary[normalized_receipt_type] = {}
        
        if currency not in receipt_type_summary[normalized_receipt_type]:
            receipt_type_summary[normalized_receipt_type][currency] = {}
        
        for line_item in line_items:
            tax_code = line_item.tax_code or 'C'  # Default to 15% tax
            tax_percent = line_item.tax_percent or get_tax_percentage(tax_code)
            tax_id = get_tax_id(tax_code)
            
            # Use tax_id as the key to properly separate exempt (tax_id=1), zero-rate (tax_id=2), and standard (tax_id=3)
            if tax_id not in receipt_type_summary[normalized_receipt_type][currency]:
                receipt_type_summary[normalized_receipt_type][currency][tax_id] = {
                    'taxID': tax_id,
                    'taxAmount': 0.0,
                    'salesAmountWithTax': 0.0,
                    'salesAmount': 0.0,
                    'taxPercent': tax_percent
                }
            
            # Calculate tax amount
            line_total = float(line_item.receipt_line_total or 0)
            # For exempt items (tax_percent is None or 0), tax amount is 0
            if tax_percent is None or tax_percent == 0:
                tax_amount = 0.0
            else:
                tax_amount = round(line_total * (tax_percent / 100), 2)
            
            receipt_type_summary[normalized_receipt_type][currency][tax_id]['salesAmount'] += line_total
            receipt_type_summary[normalized_receipt_type][currency][tax_id]['taxAmount'] += tax_amount
            receipt_type_summary[normalized_receipt_type][currency][tax_id]['salesAmountWithTax'] += line_total + tax_amount
    
    # Generate fiscal counters for each receipt type, currency, and tax type
    for receipt_type in ['SALE', 'CREDIT_NOTE', 'DEBIT_NOTE']:
        for currency in supported_currencies:
            for tax_id, tax_config in tax_configs.items():
                # Get actual data if it exists
                actual_data = receipt_type_summary.get(receipt_type, {}).get(currency, {}).get(tax_id, {
                    'taxID': tax_id,
                    'taxAmount': 0.0,
                    'salesAmount': 0.0,
                    'taxPercent': tax_config['tax_percent']
                })
                
                # Determine counter type based on receipt type
                if receipt_type == 'SALE':
                    # SaleByTax counter - for all tax types
                    fiscal_day_counters.append({
                        'fiscalCounterType': 'SaleByTax',
                        'fiscalCounterTaxID': tax_id,
                        'fiscalCounterTaxPercent': tax_config['tax_percent'],
                        'fiscalCounterCurrency': currency,
                        'fiscalCounterValue': round(actual_data['salesAmount'], 2)
                    })
                    
                    # SaleTaxByTax counter - only for 15% tax (tax_id == 3)
                    if tax_id == 3:
                        fiscal_day_counters.append({
                            'fiscalCounterType': 'SaleTaxByTax',
                            'fiscalCounterTaxID': tax_id,
                            'fiscalCounterTaxPercent': tax_config['tax_percent'],
                            'fiscalCounterCurrency': currency,
                            'fiscalCounterValue': round(actual_data['taxAmount'], 2)
                        })
                
                elif receipt_type == 'CREDIT_NOTE':
                    # CreditNoteByTax counter
                    fiscal_day_counters.append({
                        'fiscalCounterType': 'CreditNoteByTax',
                        'fiscalCounterTaxID': tax_id,
                        'fiscalCounterTaxPercent': tax_config['tax_percent'],
                        'fiscalCounterCurrency': currency,
                        'fiscalCounterValue': round(actual_data['salesAmount'], 2)
                    })
                    
                    # CreditNoteTaxByTax counter - only for 15% tax (tax_id == 3)
                    if tax_id == 3:
                        fiscal_day_counters.append({
                            'fiscalCounterType': 'CreditNoteTaxByTax',
                            'fiscalCounterTaxID': tax_id,
                            'fiscalCounterTaxPercent': tax_config['tax_percent'],
                            'fiscalCounterCurrency': currency,
                            'fiscalCounterValue': round(actual_data['taxAmount'], 2)
                        })
                
                elif receipt_type == 'DEBIT_NOTE':
                    # DebitNoteByTax counter
                    fiscal_day_counters.append({
                        'fiscalCounterType': 'DebitNoteByTax',
                        'fiscalCounterTaxID': tax_id,
                        'fiscalCounterTaxPercent': tax_config['tax_percent'],
                        'fiscalCounterCurrency': currency,
                        'fiscalCounterValue': round(actual_data['salesAmount'], 2)
                    })
                    
                    # DebitNoteTaxByTax counter - only for 15% tax (tax_id == 3)
                    if tax_id == 3:
                        fiscal_day_counters.append({
                            'fiscalCounterType': 'DebitNoteTaxByTax',
                            'fiscalCounterTaxID': tax_id,
                            'fiscalCounterTaxPercent': tax_config['tax_percent'],
                            'fiscalCounterCurrency': currency,
                            'fiscalCounterValue': round(actual_data['taxAmount'], 2)
                        })
    
    # Add BalanceByMoneyType counter for each currency and payment method
    # Group invoices by currency and payment method for actual data
    currency_payment_summary = {}
    
    for invoice in invoices:
        currency = invoice.receipt_currency or 'ZWG'
        payment_method = invoice.money_type or 'Cash'
        
        # Normalize payment method - treat 'Cash' as 'CASH'
        if payment_method.lower() in ['cash', 'Cash']:
            normalized_payment_method = 'CASH'
        else:
            normalized_payment_method = payment_method.upper()
        
        if currency not in currency_payment_summary:
            currency_payment_summary[currency] = {}
        
        if normalized_payment_method not in currency_payment_summary[currency]:
            currency_payment_summary[currency][normalized_payment_method] = 0.0
        
        # Add invoice total to payment method total
        invoice_total = float(invoice.receipt_total or 0)
        currency_payment_summary[currency][normalized_payment_method] += invoice_total
    
    # Create BalanceByMoneyType counters for all currencies and payment methods
    for currency in supported_currencies:
        for payment_method in supported_money_types:
            # Get actual total if it exists, otherwise use 0
            actual_total = currency_payment_summary.get(currency, {}).get(payment_method, 0.0)
            
            fiscal_day_counters.append({
                'fiscalCounterType': 'BalanceByMoneyType',
                'fiscalCounterCurrency': currency,
                'fiscalCounterMoneyType': payment_method,
                'fiscalCounterValue': round(actual_total, 2)
            })
    
    # Create the complete payload
    payload = {
        'fiscalDayNo': str(fiscal_day_no),
        'fiscalDayCounters': fiscal_day_counters,
        'receiptCounter': total_receipt_counter
    }
    
    return payload
    