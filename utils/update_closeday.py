def update_fiscal_counter_data(data: list) -> list:
    """
    Removes 'fiscalCounterTaxPercent' from counters where TaxID is 3 and type is tax-related.

    Parameters:
        data (list): List of fiscal counter dictionaries.

    Returns:
        list: Updated list with adjusted tax-related counters.
    """
    updated_data = []

    tax_counter_types = {
        "SaleByTax", "SaleTaxByTax",
        "CreditNoteByTax", "CreditNoteTaxByTax",
        "DebitNoteByTax", "DebitNoteTaxByTax"
    }

    for item in data:
        if (
            item.get("fiscalCounterType") in tax_counter_types and
            item.get("fiscalCounterTaxID") == 3
        ):
            # Shallow copy, then remove the tax percent key
            updated_item = dict(item)
            updated_item.pop("fiscalCounterTaxPercent", None)
            updated_data.append(updated_item)
        else:
            updated_data.append(item)

    return updated_data
