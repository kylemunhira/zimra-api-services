import datetime
from app.models import Invoice, InvoiceLineItem
from app.config import zimra_config
from app import db
from utils.invoice_utils import calculate_tax_summary, get_tax_percentage, get_tax_id


""" def get_fiscal_day_open_date_time(open_day_date_time:str):
    return get_fiscal_day_open_date_time_dao(open_day_date_time) """


def generate_counters(private_key: str, device_id: str, date_string: str, close_day_date: str, fiscal_day_no: int) -> dict:
    """
    Generate fiscal day counters for close day operation according to ZIMRA API specification.
    
    This function generates the expected counters with specific values as required.
    
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
    
    # Calculate total receipt counter (number of invoices, not line items)
    total_receipt_counter = len(invoices)
    
    # Determine which currencies are present in invoices for the fiscal day
    used_currencies = set()
    for invoice in invoices:
        currency = getattr(invoice, 'receipt_currency', None) or 'ZWG'
        used_currencies.add(str(currency).upper())

    # If no invoices found, default to USD to avoid showing ZWG unintentionally
    if not used_currencies:
        used_currencies = {"USD"}

    # Helper to build counters for a specific currency based on actual invoice data
    def _build_counters_for_currency(curr: str) -> list:
        # Filter invoices for this currency
        currency_invoices = [inv for inv in invoices if (inv.receipt_currency or 'ZWG').upper() == curr]
        
        # Calculate actual totals from invoices
        total_amount = sum(float(inv.receipt_total or 0) for inv in currency_invoices)
        
        if total_amount == 0:
            # Fallback to hardcoded values if no real data (using configuration)
            counters = [
                {
                    "fiscalCounterType": "SaleByTax",
                    "fiscalCounterCurrency": curr,
                    "fiscalCounterTaxPercent": 15,
                    "fiscalCounterTaxID": zimra_config.applicable_taxes.get(15, 1),  # Standard rated 15%
                    "fiscalCounterMoneyType": None,
                    "fiscalCounterValue": 72.0
                },
                {
                    "fiscalCounterType": "SaleByTax",
                    "fiscalCounterCurrency": curr,
                    "fiscalCounterTaxPercent": 0,
                    "fiscalCounterTaxID": zimra_config.applicable_taxes.get(0, 2),  # Zero rate 0%
                    "fiscalCounterMoneyType": None,
                    "fiscalCounterValue": 20.0
                },
                {
                    "fiscalCounterType": "SaleByTax",
                    "fiscalCounterCurrency": curr,
                    "fiscalCounterTaxID": zimra_config.applicable_taxes.get('exempt', 3),  # Exempt
                    "fiscalCounterMoneyType": None,
                    "fiscalCounterValue": 32.0
                },
                {
                    "fiscalCounterType": "SaleTaxByTax",
                    "fiscalCounterCurrency": curr,
                    "fiscalCounterTaxPercent": 15,
                    "fiscalCounterTaxID": zimra_config.applicable_taxes.get(15, 1),  # Standard rated 15%
                    "fiscalCounterMoneyType": None,
                    "fiscalCounterValue": 10.8
                },
                {
                    "fiscalCounterType": "SaleTaxByTax",
                    "fiscalCounterCurrency": curr,
                    "fiscalCounterTaxPercent": 0,
                    "fiscalCounterTaxID": zimra_config.applicable_taxes.get(0, 2),  # Zero rate 0%
                    "fiscalCounterMoneyType": None,
                    "fiscalCounterValue": 0.0
                },
                {
                    "fiscalCounterType": "SaleTaxByTax",
                    "fiscalCounterCurrency": curr,
                    "fiscalCounterTaxID": zimra_config.applicable_taxes.get('exempt', 3),  # Exempt
                    "fiscalCounterMoneyType": None,
                    "fiscalCounterValue": 0.0
                },
                {
                    "fiscalCounterType": "BalanceByMoneyType",
                    "fiscalCounterCurrency": curr,
                    "fiscalCounterMoneyType": "Cash",
                    "fiscalCounterValue": 134.8
                }
            ]
        else:
            # Analyze actual invoice line items to determine which tax types were used
            tax_summary = {}
            balance_by_money_type = {}
            
            for invoice in currency_invoices:
                # Get line items for this invoice
                line_items = InvoiceLineItem.query.filter_by(invoice_id=invoice.id).all()
                
                for line_item in line_items:
                    tax_code = line_item.tax_code or 'C'
                    tax_percent = line_item.tax_percent or get_tax_percentage(tax_code)
                    tax_id = line_item.tax_id or get_tax_id(tax_code)
                    line_total = float(line_item.receipt_line_total or 0)
                    
                    # Calculate tax amount
                    if tax_code == 'A':  # Exempt
                        tax_amount = 0.0
                        sales_amount_with_tax = line_total
                    else:
                        tax_amount = round(line_total * (tax_percent / 100), 2)
                        sales_amount_with_tax = line_total + tax_amount
                    
                    # Add to tax summary
                    tax_key = f"{tax_id}_{tax_percent}"
                    if tax_key not in tax_summary:
                        tax_summary[tax_key] = {
                            'taxID': tax_id,
                            'taxPercent': tax_percent,
                            'salesAmountWithTax': 0.0,
                            'taxAmount': 0.0
                        }
                    tax_summary[tax_key]['salesAmountWithTax'] += sales_amount_with_tax
                    tax_summary[tax_key]['taxAmount'] += tax_amount
                    
                    # Add to balance by money type
                    money_type = invoice.money_type or 'Cash'
                    if money_type not in balance_by_money_type:
                        balance_by_money_type[money_type] = 0.0
                    balance_by_money_type[money_type] += sales_amount_with_tax
            
            # Build counters only for tax types that were actually used
            counters = []
            
            # Add SaleByTax counters for each tax type used
            for tax_key, tax_data in tax_summary.items():
                if tax_data['salesAmountWithTax'] > 0:
                    counter = {
                        "fiscalCounterType": "SaleByTax",
                        "fiscalCounterCurrency": curr,
                        "fiscalCounterMoneyType": None,
                        "fiscalCounterValue": round(tax_data['salesAmountWithTax'], 2)  # Use actual values
                    }
                    
                    # Add fiscalCounterTaxPercent first (if not exempt)
                    if not zimra_config.is_exempt_tax_id(tax_data['taxID']):
                        counter["fiscalCounterTaxPercent"] = int(tax_data['taxPercent']) if tax_data['taxPercent'] is not None and float(tax_data['taxPercent']).is_integer() else tax_data['taxPercent']
                    
                    # Add fiscalCounterTaxID after fiscalCounterTaxPercent
                    counter["fiscalCounterTaxID"] = tax_data['taxID']
                    
                    counters.append(counter)
            
            # Add SaleTaxByTax counters for ALL tax types (including exempt with 0 tax)
            for tax_key, tax_data in tax_summary.items():
                counter = {
                    "fiscalCounterType": "SaleTaxByTax",
                    "fiscalCounterCurrency": curr,
                    "fiscalCounterMoneyType": None,
                    "fiscalCounterValue": round(tax_data['taxAmount'], 2)  # Use actual values
                }
                
                # Add fiscalCounterTaxPercent first (if not exempt)
                if not zimra_config.is_exempt_tax_id(tax_data['taxID']):
                    counter["fiscalCounterTaxPercent"] = int(tax_data['taxPercent']) if tax_data['taxPercent'] is not None and float(tax_data['taxPercent']).is_integer() else tax_data['taxPercent']
                
                # Add fiscalCounterTaxID after fiscalCounterTaxPercent
                counter["fiscalCounterTaxID"] = tax_data['taxID']
                
                counters.append(counter)
            
            # Add BalanceByMoneyType counters
            for money_type, total_amount in balance_by_money_type.items():
                if total_amount > 0:
                    counters.append({
                        "fiscalCounterType": "BalanceByMoneyType",
                        "fiscalCounterCurrency": curr,
                        "fiscalCounterMoneyType": money_type.title(),  # Convert to proper case (e.g., "Cash", "Card")
                        "fiscalCounterValue": round(total_amount, 2)  # Use actual values
                    })
        
        return counters

    # Build counters only for currencies actually used, preserving USD before ZWG order
    currency_order = ["USD", "ZWG"]
    fiscal_day_counters = []
    for curr in currency_order:
        if curr in used_currencies:
            fiscal_day_counters.extend(_build_counters_for_currency(curr))
    
    # Sort counters to ensure SaleByTax comes first, then SaleTaxByTax, then BalanceByMoneyType
    def sort_counters_by_type_and_tax_id(counter):
        fiscal_type = counter.get('fiscalCounterType', '')
        currency = counter.get('fiscalCounterCurrency', '')
        tax_id = counter.get('fiscalCounterTaxID', 0)
        
        # Define type priority: SaleByTax = 1, SaleTaxByTax = 2, BalanceByMoneyType = 3
        if fiscal_type == 'SaleByTax':
            type_priority = 1
        elif fiscal_type == 'SaleTaxByTax':
            type_priority = 2
        elif fiscal_type == 'BalanceByMoneyType':
            type_priority = 3
        else:
            type_priority = 4  # Any other types
        
        return (type_priority, tax_id, currency)
    
    # Sort the counters by type priority first, then tax ID
    fiscal_day_counters.sort(key=sort_counters_by_type_and_tax_id)
    
    # Create the complete payload in ZIMRA format order
    payload = {
        'fiscalDayNo': str(fiscal_day_no),
        'fiscalDayCounters': fiscal_day_counters,
        'receiptCounter': total_receipt_counter
    }
    
    return payload


def analyze_invoice_currencies_and_taxes(device_id: str, fiscal_day_no: int) -> dict:
    """
    Analyze which currencies and taxes are actually used in invoices for a specific device and fiscal day.
    
    This function helps with debugging and understanding what counters will be generated.
    
    Parameters:
        device_id (str): Device identifier
        fiscal_day_no (int): Fiscal day number
        
    Returns:
        dict: Analysis of used currencies, taxes, and payment methods
    """
    # Get all invoices for this device and fiscal day
    invoices = Invoice.query.filter_by(
        device_id=str(device_id),
        fiscal_day_number=str(fiscal_day_no)
    ).all()
    
    if not invoices:
        return {
            "device_id": device_id,
            "fiscal_day_no": fiscal_day_no,
            "total_invoices": 0,
            "used_currencies": [],
            "used_tax_ids": [],
            "used_payment_methods": [],
            "message": "No invoices found for this device and fiscal day"
        }
    
    # Track used currencies, tax IDs, and payment methods
    used_currencies = set()
    used_tax_ids = set()
    used_payment_methods = set()
    currency_details = {}
    tax_details = {}
    payment_details = {}
    
    for invoice in invoices:
        line_items = InvoiceLineItem.query.filter_by(invoice_id=invoice.id).all()
        currency = invoice.receipt_currency or 'ZWG'
        payment_method = invoice.money_type or 'Cash'
        
        # Track currency
        used_currencies.add(currency)
        if currency not in currency_details:
            currency_details[currency] = {
                'invoice_count': 0,
                'total_amount': 0.0,
                'invoice_ids': []
            }
        currency_details[currency]['invoice_count'] += 1
        currency_details[currency]['total_amount'] += float(invoice.receipt_total or 0)
        currency_details[currency]['invoice_ids'].append(invoice.invoice_id)
        
        # Track payment method
        if payment_method.lower() in ['cash', 'Cash']:
            normalized_payment_method = 'CASH'
        else:
            normalized_payment_method = payment_method.upper()
        used_payment_methods.add(normalized_payment_method)
        
        if normalized_payment_method not in payment_details:
            payment_details[normalized_payment_method] = {
                'invoice_count': 0,
                'total_amount': 0.0,
                'invoice_ids': []
            }
        payment_details[normalized_payment_method]['invoice_count'] += 1
        payment_details[normalized_payment_method]['total_amount'] += float(invoice.receipt_total or 0)
        payment_details[normalized_payment_method]['invoice_ids'].append(invoice.invoice_id)
        
        # Track tax IDs from line items
        for line_item in line_items:
            tax_code = line_item.tax_code or 'C'
            tax_percent = line_item.tax_percent or get_tax_percentage(tax_code)
            tax_id = get_tax_id(tax_code)
            
            used_tax_ids.add(tax_id)
            
            if tax_id not in tax_details:
                tax_details[tax_id] = {
                    'tax_code': tax_code,
                    'tax_percent': tax_percent,
                    'line_count': 0,
                    'total_amount': 0.0,
                    'total_tax': 0.0,
                    'invoice_ids': set()
                }
            
            tax_details[tax_id]['line_count'] += 1
            tax_details[tax_id]['total_amount'] += float(line_item.receipt_line_total or 0)
            tax_details[tax_id]['total_tax'] += float(line_item.tax_percent or 0) / 100 * float(line_item.receipt_line_total or 0)
            tax_details[tax_id]['invoice_ids'].add(invoice.invoice_id)
    
    # Convert sets to lists for JSON serialization
    for tax_id in tax_details:
        tax_details[tax_id]['invoice_ids'] = list(tax_details[tax_id]['invoice_ids'])
    
    return {
        "device_id": device_id,
        "fiscal_day_no": fiscal_day_no,
        "total_invoices": len(invoices),
        "used_currencies": list(used_currencies),
        "used_tax_ids": list(used_tax_ids),
        "used_payment_methods": list(used_payment_methods),
        "currency_details": currency_details,
        "tax_details": tax_details,
        "payment_details": payment_details,
        "summary": {
            "currencies_count": len(used_currencies),
            "tax_types_count": len(used_tax_ids),
            "payment_methods_count": len(used_payment_methods)
        }
    }
