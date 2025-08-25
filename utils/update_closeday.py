from app.config import zimra_config

def update_fiscal_counter_data(data: list) -> list:
    """
    Ensure 'fiscalCounterTaxPercent' and 'fiscalCounterMoneyType' are properly set for all counters.

    - For tax-related counters (SaleByTax, SaleTaxByTax):
      - If missing, derive tax percent from TaxID: 1 -> None (Exempt), 2 -> 0.0, 3 -> 15.0, 514 -> 5.0
      - Set fiscalCounterMoneyType to null
    - For 'BalanceByMoneyType':
      - Remove fiscalCounterTaxPercent if present
      - Keep fiscalCounterMoneyType as is

    Parameters:
        data (list): List of fiscal counter dictionaries.

    Returns:
        list: Updated list with adjusted counters in the correct field order.
    """
    updated_data = []

    tax_percent_by_id = zimra_config.get_tax_percent_by_id()

    for item in data:
        counter_type = str(item.get("fiscalCounterType", ""))
        
        if counter_type == "BalanceByMoneyType":
            # For BalanceByMoneyType, create with correct field order
            updated_item = {
                "fiscalCounterType": item.get("fiscalCounterType"),
                "fiscalCounterCurrency": item.get("fiscalCounterCurrency"),
                "fiscalCounterMoneyType": item.get("fiscalCounterMoneyType"),
                "fiscalCounterValue": item.get("fiscalCounterValue")
            }
        else:
            # For tax-related counters (SaleByTax, SaleTaxByTax), create with correct field order
            tax_id = item.get("fiscalCounterTaxID")
            
            # Start with base fields in correct order
            updated_item = {
                "fiscalCounterType": item.get("fiscalCounterType"),
                "fiscalCounterCurrency": item.get("fiscalCounterCurrency")
            }
            
            # Add fiscalCounterTaxPercent if not exempt (before fiscalCounterTaxID)
            if not zimra_config.is_exempt_tax_id(tax_id):
                tax_percent = item.get("fiscalCounterTaxPercent")
                if tax_percent is None:
                    tax_percent = tax_percent_by_id.get(tax_id)
                if tax_percent is not None:
                    updated_item["fiscalCounterTaxPercent"] = tax_percent
            
            # Add fiscalCounterTaxID after fiscalCounterTaxPercent (for all tax-related counters)
            updated_item["fiscalCounterTaxID"] = tax_id
            
            # Add remaining fields
            updated_item["fiscalCounterMoneyType"] = None
            updated_item["fiscalCounterValue"] = item.get("fiscalCounterValue")
        
        updated_data.append(updated_item)

    return updated_data
