from flask import Blueprint, jsonify, request,current_app


"""def generate_close_day_string(device_id: str, fiscal_day_no: str, date: str, receipt_close: dict) -> str:

    Constructs the CloseDay signing string by extracting counters and 
    concatenating device-specific values for signing.

    Parameters:
        device_id (str): The unique device identifier (ZIMRA-assigned).
        fiscal_day_no (str): The fiscal day number to be closed.
        date (str): The fiscal close date in ISO format (e.g., '2025-07-24T06:00:00').
        receipt_close (dict): The full payload containing 'fiscalDayCounters'.

    Returns:
        str: Concatenated string ready to be signed with the device's private key.
    
    if 'fiscalDayCounters' not in receipt_close:
        raise ValueError("Missing 'fiscalDayCounters' in receipt_close payload.")

    # Extract the required counters
    generated_dict = counters_extract_close_day(receipt_close['fiscalDayCounters'])

    # Concatenate values into the format required by ZIMRA
    concat_string = concat_helper_close_day(device_id, fiscal_day_no, date, generated_dict)

    return concat_string"""




def generate_close_day_string(device_id: str, fiscal_day_no: str, date: str, receipt_close: dict, counters_for_string: dict = None) -> str:
    """
    Constructs the CloseDay signing string by extracting counters and 
    concatenating device-specific values for signing.

    Parameters:
        device_id (str): The unique device identifier (ZIMRA-assigned).
        fiscal_day_no (str): The fiscal day number to be closed.
        date (str): The fiscal close date in ISO format (e.g., '2025-07-24T06:00:00').
        receipt_close (dict): The full payload containing 'fiscalDayCounters'.
        counters_for_string (dict): Optional formatted counters data for dynamic string generation.

    Returns:
        str: Concatenated string ready to be signed with the device's private key.
    """
    # Debug logging to see input parameters
    from flask import current_app
    #current_app.logger.debug(f"generate_close_day_string - device_id: '{device_id}'")
    #current_app.logger.debug(f"generate_close_day_string - fiscal_day_no: '{fiscal_day_no}'")
    #current_app.logger.debug(f"generate_close_day_string - date: '{date}'")
    
    # Always extract fiscal counters from receipt_close first
    if 'fiscalDayCounters' not in receipt_close:
        raise ValueError("Missing 'fiscalDayCounters' in receipt_close payload.")
    generated_dict = counters_extract_close_day(receipt_close['fiscalDayCounters'])
    
    # Concatenate the fiscal counters with the Base64-encoded counters if provided
    if counters_for_string:
        fiscal_counters_string = generated_dict + counters_for_string
    else:
        fiscal_counters_string = generated_dict

    # Concatenate values into the format required by ZIMRA
    concat_string = concat_helper_close_day(device_id, fiscal_day_no, date, fiscal_counters_string)

    return concat_string


def counters_extract_close_day(receipt_close: list) -> str:
    """
    Extracts and concatenates fiscal counter data following ZIMRA specification:
    - Sort by fiscalCounterType (ascending), then currency (alphabetical), then tax_id/money_type (ascending)
    - Convert amounts to cents (multiply by 100)
    - Handle tax percent formatting (integer.fractional or empty for exempt)
    - Only include non-zero values
    - All text in uppercase

    Parameters:
        receipt_close (list): List of fiscal counter dicts from the CloseDay payload.

    Returns:
        str: Concatenated string representing fiscal counters, ready for signing.
    """
    
    # Filter out zero values and create sortable items
    valid_counters = []
    for counter in receipt_close:
        value = counter.get('fiscalCounterValue', 0)
        if value is not None and float(value) != 0:
            valid_counters.append(counter)
    
    # Sort according to tax ID:
    # 1. fiscalCounterTaxID (ascending) - primary sort key
    # 2. fiscalCounterType (ascending) - but BalanceByMoneyType should be last
    # 3. fiscalCounterCurrency (alphabetical ascending)
    def sort_key(counter):
        fiscal_type = counter.get('fiscalCounterType', '')
        currency = counter.get('fiscalCounterCurrency', '')
        
        # Get tax ID for sorting
        if counter.get('fiscalCounterType') == 'BalanceByMoneyType':
            # For BalanceByMoneyType, use a high tax ID to appear last
            tax_id = 999  # High value to ensure it appears last
        else:
            # For tax-related counters, use actual tax_id
            tax_id = counter.get('fiscalCounterTaxID', 0)
        
        # Give BalanceByMoneyType a higher priority to appear last within same tax_id
        if fiscal_type == 'BalanceByMoneyType':
            type_priority = 'ZZZ'  # This will sort after all other counter types
        else:
            type_priority = fiscal_type
        
        return (tax_id, type_priority, currency)
    
    sorted_counters = sorted(valid_counters, key=sort_key)
    
    string_to_sign_ = ""
    
    for counter in sorted_counters:
        fiscal_type = counter.get('fiscalCounterType', '').upper()
        currency = counter.get('fiscalCounterCurrency', '').upper()
        value = counter.get('fiscalCounterValue', 0)
        
        # Convert amount to cents (multiply by 100)
        value_cents = int(float(value) * 100)
        value_str = str(value_cents)
        
        if fiscal_type != 'BALANCEBYMONEYTYPE':
            # Tax-related counters
            tax_percent = counter.get('fiscalCounterTaxPercent')
            
            if tax_percent is None:
                # Exempt - use empty value
                tax_percent_str = ""
            else:
                # Format tax percent with two decimal places
                tax_percent_float = float(tax_percent)
                tax_percent_str = f"{tax_percent_float:.2f}"
            
            string_to_sign_ += f"{fiscal_type}{currency}{tax_percent_str}{value_str}"
        else:
            # BalanceByMoneyType
            money_type = counter.get('fiscalCounterMoneyType', '').upper()
            string_to_sign_ += f"{fiscal_type}{currency}{money_type}{value_str}"
    
    return string_to_sign_

def concat_helper_close_day(device_id: str, fiscal_day_no: str, date: str, counters: str) -> str:
    """
    Concatenates CloseDay data fields into a single string for signing.

    Parameters:
        device_id (str): Unique identifier of the fiscal device.
        fiscal_day_no (str): The fiscal day number (as string).
        date (str): The date string (ISO format recommended).
        counters (str): Extracted and formatted fiscal counters.

    Returns:
        str: Uppercase concatenated string used for signature generation.
    """
    # Debug logging to see what values are being concatenated
    from flask import current_app
    current_app.logger.debug(f"concat_helper_close_day - device_id: '{device_id}'")
    current_app.logger.debug(f"concat_helper_close_day - fiscal_day_no: '{fiscal_day_no}'")
    current_app.logger.debug(f"concat_helper_close_day - date: '{date}'")
    current_app.logger.debug(f"concat_helper_close_day - counters length: {len(counters)}")
    
    # Extract only the date part (YYYY-MM-DD) from the datetime string
    try:
        if 'T' in date:
            # If it's a datetime string like "2025-08-18T16:49:05", extract just the date part
            date_only = date.split('T')[0]
        else:
            # If it's already just a date, use it as is
            date_only = date
    except:
        # Fallback to original date if parsing fails
        date_only = date
    
    concatenated_values = f"{device_id}{fiscal_day_no}{date_only}{counters}"
    current_app.logger.debug(f"concat_helper_close_day - final string: '{concatenated_values}'")
    return concatenated_values
def add_zeros(value):
    """
    Converts an integer or float tax percentage to a two-decimal-place string.

    Examples:
        15   → '15.00'
        15.5 → '15.50'
        0    → '0.00'

    Parameters:
        value (int or float): Tax percentage.

    Returns:
        str: Tax percentage formatted to 2 decimal places.
    """
    try:
        return f"{float(value):.2f}"
    except (TypeError, ValueError):
        return str(value)
    
import datetime

def get_close_day_date_format(date_string: str) -> str:
    """
    Formats the close day date according to ZIMRA specifications.
    
    Parameters:
        date_string (str): DateTime string in ISO format.
        
    Returns:
        str: Formatted date string for close day operations.
    """
    try:
        # Parse the ISO datetime string
        date_object = datetime.datetime.strptime(date_string, "%Y-%m-%dT%H:%M:%S")
        # Return in the format expected by ZIMRA for close day
        # Use the same format as the input to ensure consistency
        return date_object.strftime("%Y-%m-%dT%H:%M:%S")
    except ValueError:
        try:
            # Try alternative format if the first one fails
            date_object = datetime.datetime.strptime(date_string, "%Y-%m-%d %H:%M:%S")
            return date_object.strftime("%Y-%m-%dT%H:%M:%S")
        except ValueError:
            # If parsing fails, return the original string
            return date_string


def get_date_only(date_string: str) -> str:
    """
    Extracts the date portion (YYYY-MM-DD) from an ISO 8601 datetime string.

    Parameters:
        date_string (str): DateTime string in the format 'YYYY-MM-DDTHH:MM:SS'.

    Returns:
        str: Date string in 'YYYY-MM-DD' format.

    Raises:
        ValueError: If the input format is incorrect.
    """
    try:
        date_object = datetime.datetime.strptime(date_string, "%Y-%m-%dT%H:%M:%S")
        return date_object.strftime("%Y-%m-%d")
    except ValueError as e:
        raise ValueError(f"Invalid date format for input '{date_string}': {e}")


def generate_dynamic_fiscal_string(counters_data: dict) -> str:
    """
    Generates a dynamic fiscal counter string based on provided data.
    
    Parameters:
        counters_data (dict): Dictionary containing fiscal counter data with structure:
            {
                'USD': {
                    'SaleByTax': [3200, 0.002000, 7200],
                    'SaleTaxByTax': [1080],
                    'BalanceByMoneyType': {'Cash': 13480}
                },
                'ZWG': {
                    'SaleByTax': [3200, 0.002000, 7200], 
                    'SaleTaxByTax': [1080],
                    'BalanceByMoneyType': {'Cash': 13480}
                }
            }
    
    Returns:
        str: The concatenated fiscal counter string (with uppercase counter types for signing)
    """
    fiscal_string = ""
    
    for currency in ['USD', 'ZWG']:
        if currency in counters_data:
            currency_data = counters_data[currency]
            
            # Add SaleByTax counters (convert to SALEBYTAX for signing)
            if 'SaleByTax' in currency_data:
                for value in currency_data['SaleByTax']:
                    fiscal_string += f"SALEBYTAX{currency}{value}"
            
            # Add SaleTaxByTax counters (convert to SALETAXBYTAX for signing)
            if 'SaleTaxByTax' in currency_data:
                for value in currency_data['SaleTaxByTax']:
                    fiscal_string += f"SALETAXBYTAX{currency}{value}"
            
            # Add BalanceByMoneyType counters (convert to BALANCEBYMONEYTYPE for signing)
            if 'BalanceByMoneyType' in currency_data:
                for money_type, value in currency_data['BalanceByMoneyType'].items():
                    fiscal_string += f"BALANCEBYMONEYTYPE{currency}{money_type}{value}"
    
    return fiscal_string





