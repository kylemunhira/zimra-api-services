# Fiscal Counters API Documentation

## Overview

This document describes the implementation of **Section 6. FISCAL COUNTERS** from the ZIMRA Fiscal Device Gateway API specification. The fiscal counters functionality provides comprehensive reporting and analysis capabilities for fiscal day operations.

## Implementation Details

### Core Components

1. **Fiscal Counter Generation** (`utils/generate_counters.py`)
   - Generates fiscal day counters from invoice data
   - Supports multiple counter types: SaleByTax, SaleTaxByTax, BalanceByMoneyType
   - Handles credit/debit note counters
   - Processes tax calculations and currency conversions

2. **Fiscal Counter Processing** (`utils/update_closeday.py`)
   - Applies ZIMRA-specific formatting rules
   - Removes tax percentage for specific counter types
   - Ensures compliance with ZIMRA API requirements

3. **String Generation** (`utils/close_day_string_utilts.py`)
   - Creates signing strings from fiscal counters
   - Implements ZIMRA signature requirements
   - Handles counter concatenation for digital signatures

### Supported Counter Types

| Counter Type | Description | Tax ID Support | Currency Support |
|--------------|-------------|----------------|------------------|
| `SaleByTax` | Sales amounts by tax type | All tax IDs | All currencies |
| `SaleTaxByTax` | Tax amounts by tax type | Tax ID 3 (15%) | All currencies |
| `BalanceByMoneyType` | Balance by payment method | N/A | All currencies |
| `CreditNoteByTax` | Credit note amounts by tax | All tax IDs | All currencies |
| `CreditNoteTaxByTax` | Credit note tax amounts | Tax ID 3 (15%) | All currencies |
| `DebitNoteByTax` | Debit note amounts by tax | All tax IDs | All currencies |
| `DebitNoteTaxByTax` | Debit note tax amounts | Tax ID 3 (15%) | All currencies |

## API Endpoints

### 1. Basic Fiscal Counters

**Endpoint:** `GET /fiscal_counters/{device_id}`

**Description:** Retrieves fiscal counters for a specific device and fiscal day.

**Parameters:**
- `device_id` (path): Device identifier
- `fiscal_day_no` (query, optional): Specific fiscal day number. If not provided, uses current open fiscal day.

**Response Format:**
```json
{
  "device_id": "26428",
  "fiscal_day_no": 1,
  "fiscal_day_open": "2025-01-15T08:00:00",
  "fiscal_day_status": "OPEN",
  "total_receipts": 25,
  "total_amount": 1250.75,
  "receipt_counter": 25,
  "fiscal_counters": [
    {
      "fiscalCounterType": "SaleByTax",
      "fiscalCounterTaxID": 3,
      "fiscalCounterTaxPercent": 15.0,
      "fiscalCounterCurrency": "USD",
      "fiscalCounterValue": 1000.00
    },
    {
      "fiscalCounterType": "SaleTaxByTax",
      "fiscalCounterTaxID": 3,
      "fiscalCounterCurrency": "USD",
      "fiscalCounterValue": 150.00
    },
    {
      "fiscalCounterType": "BalanceByMoneyType",
      "fiscalCounterCurrency": "USD",
      "fiscalCounterMoneyType": "CASH",
      "fiscalCounterValue": 1150.00
    }
  ],
  "counters_by_type": {
    "SaleByTax": [...],
    "SaleTaxByTax": [...],
    "BalanceByMoneyType": [...]
  },
  "summary": {
    "sale_counters": 3,
    "tax_counters": 1,
    "balance_counters": 1,
    "credit_note_counters": 0,
    "debit_note_counters": 0
  }
}
```

### 2. Detailed Fiscal Counters

**Endpoint:** `GET /fiscal_counters/{device_id}/detailed`

**Description:** Provides detailed breakdown of fiscal counters by currency, tax type, payment method, and receipt type.

**Parameters:**
- `device_id` (path): Device identifier
- `fiscal_day_no` (query, optional): Specific fiscal day number

**Response Format:**
```json
{
  "device_id": "26428",
  "fiscal_day_no": 1,
  "fiscal_day_open": "2025-01-15T08:00:00",
  "fiscal_day_status": "OPEN",
  "total_invoices": 25,
  "detailed_breakdown": {
    "by_currency": {
      "USD": {
        "total_amount": 1000.00,
        "total_tax": 150.00,
        "invoice_count": 20
      },
      "ZWL": {
        "total_amount": 250.75,
        "total_tax": 37.61,
        "invoice_count": 5
      }
    },
    "by_tax_type": {
      "C_15.0%": {
        "tax_code": "C",
        "tax_percent": 15.0,
        "tax_id": 3,
        "total_amount": 1000.00,
        "total_tax": 150.00,
        "line_count": 50
      },
      "E_0.0%": {
        "tax_code": "E",
        "tax_percent": 0.0,
        "tax_id": 2,
        "total_amount": 250.75,
        "total_tax": 0.00,
        "line_count": 10
      }
    },
    "by_payment_method": {
      "Cash": {
        "total_amount": 800.00,
        "invoice_count": 16
      },
      "Card": {
        "total_amount": 450.75,
        "invoice_count": 9
      }
    },
    "by_receipt_type": {
      "SALE": {
        "total_amount": 1200.00,
        "invoice_count": 24
      },
      "CREDIT_NOTE": {
        "total_amount": 50.75,
        "invoice_count": 1
      }
    },
    "invoice_details": [
      {
        "invoice_id": "INV001",
        "zimra_receipt_number": "ZR123456",
        "receipt_type": "SALE",
        "receipt_total": 100.00,
        "receipt_currency": "USD",
        "money_type": "Cash",
        "is_fiscalized": true,
        "created_at": "2025-01-15T10:30:00",
        "line_items_count": 3
      }
    ]
  }
}
```

## Usage Examples

### Python Requests

```python
import requests

# Get fiscal counters for current open fiscal day
response = requests.get("http://localhost:5000/fiscal_counters/26428")
counters = response.json()

# Get fiscal counters for specific fiscal day
response = requests.get("http://localhost:5000/fiscal_counters/26428?fiscal_day_no=1")
counters = response.json()

# Get detailed breakdown
response = requests.get("http://localhost:5000/fiscal_counters/26428/detailed")
detailed = response.json()
```

### cURL Commands

```bash
# Basic fiscal counters
curl -X GET "http://localhost:5000/fiscal_counters/26428"

# Fiscal counters for specific day
curl -X GET "http://localhost:5000/fiscal_counters/26428?fiscal_day_no=1"

# Detailed breakdown
curl -X GET "http://localhost:5000/fiscal_counters/26428/detailed"
```

## Error Handling

### Common Error Responses

**404 - Device Not Found:**
```json
{
  "error": "Device not found"
}
```

**404 - Fiscal Day Not Found:**
```json
{
  "error": "Fiscal day 1 not found for device 26428"
}
```

**404 - No Invoices Found:**
```json
{
  "error": "No invoices found for device 26428 and fiscal day 1",
  "fiscal_day_no": 1,
  "fiscal_day_open": "2025-01-15T08:00:00",
  "is_open": true,
  "fiscal_counters": []
}
```

**500 - Internal Server Error:**
```json
{
  "error_type": "ValueError",
  "error_message": "No open fiscal day found for device_id: 26428",
  "traceback": "..."
}
```

## Integration with ZIMRA API

### Close Day Integration

The fiscal counters are automatically generated and used during the close day operation:

1. **Counter Generation**: Uses `generate_counters()` to create fiscal day counters from invoice data
2. **Counter Processing**: Applies `update_fiscal_counter_data()` for ZIMRA compliance
3. **String Generation**: Creates signing string using `generate_close_day_string()`
4. **API Submission**: Sends to ZIMRA CloseDay endpoint with proper formatting

### Signature Generation

Fiscal counters are included in the digital signature generation process:

```python
# Generate counters
counters_data = generate_counters(private_key, device_id, date_string, close_day_date, fiscal_day_no)

# Update for ZIMRA compliance
updated_counters = update_fiscal_counter_data(counters_data['fiscalDayCounters'])

# Generate signing string
string_to_sign = generate_close_day_string(device_id, fiscal_day_no, date, updated_counters)
```

## Testing

### Test Script

Run the provided test script to verify functionality:

```bash
python test_fiscal_counters.py
```

### Manual Testing

1. **Start the server:**
   ```bash
   python run.py
   ```

2. **Open a fiscal day:**
   ```bash
   curl -X POST "http://localhost:5000/openday/26428"
   ```

3. **Submit some receipts:**
   ```bash
   curl -X POST "http://localhost:5000/submit_receipt/26428" \
        -H "Content-Type: application/json" \
        -d '{"receipt": {...}}'
   ```

4. **Get fiscal counters:**
   ```bash
   curl -X GET "http://localhost:5000/fiscal_counters/26428"
   ```

## Compliance Notes

### ZIMRA API Requirements

1. **Counter Types**: All supported counter types match ZIMRA specifications
2. **Tax Handling**: Proper handling of exempt (tax_id=1), zero-rate (tax_id=2), and standard (tax_id=3) taxes
3. **Currency Support**: Multi-currency support with proper formatting
4. **Signature Integration**: Counters included in digital signature generation
5. **Data Validation**: Proper validation of fiscal day numbers and device IDs

### Data Accuracy

- **Real-time Calculation**: Counters are calculated from actual invoice data
- **Tax Compliance**: Proper tax calculations and exemptions
- **Currency Handling**: Accurate multi-currency support
- **Audit Trail**: Complete audit trail through invoice records

## Performance Considerations

1. **Database Queries**: Optimized queries for large datasets
2. **Caching**: Consider implementing caching for frequently accessed counters
3. **Pagination**: For large datasets, consider pagination in detailed endpoints
4. **Indexing**: Ensure proper database indexing on fiscal_day_number and device_id

## Future Enhancements

1. **Real-time Updates**: WebSocket support for real-time counter updates
2. **Export Functionality**: PDF/Excel export of counter reports
3. **Advanced Filtering**: Date range filtering and advanced search
4. **Dashboard Integration**: Real-time dashboard with counter visualizations
5. **Batch Processing**: Support for bulk counter operations

## Troubleshooting

### Common Issues

1. **No Counters Found**: Ensure invoices exist for the specified fiscal day
2. **Device Not Found**: Verify device ID exists in the database
3. **Fiscal Day Issues**: Check if fiscal day is properly opened
4. **Tax Calculation Errors**: Verify tax codes and percentages are correct

### Debug Information

Enable debug logging to see detailed counter generation:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Database Queries

Check fiscal day and invoice data:

```sql
-- Check fiscal days
SELECT * FROM fiscal_day WHERE device_id = '26428';

-- Check invoices
SELECT * FROM invoice WHERE device_id = '26428' AND fiscal_day_number = '1';

-- Check line items
SELECT * FROM invoice_line_item WHERE invoice_id IN (
    SELECT id FROM invoice WHERE device_id = '26428' AND fiscal_day_number = '1'
);
```

## Conclusion

The fiscal counters implementation provides a comprehensive solution for ZIMRA compliance, offering both basic and detailed reporting capabilities. The system integrates seamlessly with existing fiscal day operations and provides accurate, real-time counter data for regulatory reporting and business intelligence. 