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




def generate_close_day_string(device_id: str, fiscal_day_no: str, date: str, receipt_close: dict) -> str:
    """
    Constructs the CloseDay signing string by extracting counters and 
    concatenating device-specific values for signing.

    Parameters:
        device_id (str): The unique device identifier (ZIMRA-assigned).
        fiscal_day_no (str): The fiscal day number to be closed.
        date (str): The fiscal close date in ISO format (e.g., '2025-07-24T06:00:00').
        receipt_close (dict): The full payload containing 'fiscalDayCounters'.

    Returns:
        str: Concatenated string ready to be signed with the device's private key.
    """
    if 'fiscalDayCounters' not in receipt_close:
        raise ValueError("Missing 'fiscalDayCounters' in receipt_close payload.")

    # Extract the required counters
    generated_dict = counters_extract_close_day(receipt_close['fiscalDayCounters'])

    # Concatenate values into the format required by ZIMRA
    concat_string = concat_helper_close_day(device_id, fiscal_day_no, date, generated_dict)

    return concat_string


def counters_extract_close_day(receipt_close: list) -> str:
    """
    Extracts and concatenates fiscal counter data from the ZIMRA 'fiscalDayCounters' list,
    formatting it into a single uppercase string used for signing.

    Parameters:
        receipt_close (list): List of fiscal counter dicts from the CloseDay payload.

    Returns:
        str: Concatenated string representing fiscal counters, ready for signing.
    """

    string_to_sign_ = ""

    for counter in receipt_close:
        fiscal_type = counter.get('fiscalCounterType')
        tax_percent = counter.get('fiscalCounterTaxPercent')
        tax_id = counter.get('fiscalCounterTaxID')
        currency = counter.get('fiscalCounterCurrency')
        value = counter.get('fiscalCounterValue')
        money_type = counter.get('fiscalCounterMoneyType')
        current_app.logger.debug(f"Ndasvika: {money_type}")
        # Defensive: skip if essential keys missing or value is None
        if fiscal_type is None or currency is None or value is None:
            continue

        # Multiply value by 100 and round
        value_str = str(round(float(value) * 100)).replace(".00", "").replace(".0", "")

        if fiscal_type != 'BalanceByMoneyType':

            if "TaxByTax" in fiscal_type and (tax_percent == 0 or tax_percent is None):
                # Skip this counter (empty string)
                continue
            else:
                if tax_percent is None or tax_id == 3:
                    string_to_sign_ += f"{fiscal_type}{currency}{value_str}"
                else:
                    tax_percent_str = add_zeros(tax_percent)
                    string_to_sign_ += f"{fiscal_type}{currency}{tax_percent_str}{value_str}"

        else:
            # BalanceByMoneyType case
            if money_type is None:
                money_type = ""
            string_to_sign_ += f"{fiscal_type}{currency}{money_type}{value_str}"

    return string_to_sign_.upper()

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
    concatenated_values = f"{device_id}{fiscal_day_no}{date}{counters}"
    return concatenated_values.upper()
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


