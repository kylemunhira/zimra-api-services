# ZIMRA QR String Format Specification

## Overview
The QR string is generated according to ZIMRA (Zimbabwe Revenue Authority) specifications for fiscal device management. This document outlines the exact format and components required.

## QR String Components

The QR string is constructed from these components in order:

1. **Base URL**: `https://fdmstest.zimra.co.zw/` (ZIMRA's fiscal device management system)
2. **Device ID**: 10-digit zero-padded device identifier
3. **Receipt Date**: Date in format DDMMYYYY (e.g., "02232024" for February 23, 2024)
4. **Global Receipt Number**: 10-digit zero-padded sequential receipt number
5. **Signature Hash**: MD5 hash of the digital signature (16 characters, uppercase)

## Format
```
BaseURL + DeviceID + ReceiptDate + GlobalReceiptNumber + SignatureHash
```

## Example Breakdown

### Input Values:
- Device ID: `26428`
- Receipt Date: `2024-02-23` (YYYY-MM-DD format)
- Global Receipt Number: `13`
- Signature: Base64 encoded signature from ZIMRA

### Generated Components:
1. **Base URL**: `https://fdmstest.zimra.co.zw/`
2. **Device ID (10-digit)**: `0000026428`
3. **Receipt Date (DDMMYYYY)**: `23022024`
4. **Global Receipt Number (10-digit)**: `0000000013`
5. **Signature Hash (16 chars)**: `970F9B28F924FB6D`

### Final QR String:
```
https://fdmstest.zimra.co.zw/0000026428230220240000000013970F9B28F924FB6D
```

## Implementation Details

### Function Signature
```python
def qr_string_generator(device_id: str, qr_url: str, receipt_date: str, 
                       reciept_global_no: int, reciept_signature: str) -> str:
```

### Parameters
- `device_id`: Device identifier (will be zero-padded to 10 digits)
- `qr_url`: Base URL for ZIMRA's fiscal device management system
- `receipt_date`: Date in YYYY-MM-DD format
- `reciept_global_no`: Sequential receipt number
- `reciept_signature`: Base64 encoded digital signature

### Processing Steps

1. **Base URL Processing**:
   - Ensures URL ends with `/`
   - Example: `https://fdmstest.zimra.co.zw/`

2. **Device ID Processing**:
   - Zero-pads to exactly 10 digits
   - Example: `26428` → `0000026428`

3. **Receipt Date Processing**:
   - Converts from YYYY-MM-DD to DDMMYYYY format
   - Example: `2024-02-23` → `23022024`

4. **Global Receipt Number Processing**:
   - Zero-pads to exactly 10 digits
   - Example: `13` → `0000000013`

5. **Signature Hash Processing**:
   - Decodes base64 signature
   - Generates MD5 hash
   - Takes first 16 characters (uppercase)
   - Example: `dGVzdF9zaWduYXR1cmVfZm9yX3Rlc3Rpbmc=` → `970F9B28F924FB6D`

## Usage in Application

The QR string is generated in the `submit_receipt` function:

```python
# Generate QR code using stored QR URL from device config
qr_url = device_config.qr_url if device_config and device_config.qr_url else "https://fdmstest.zimra.co.zw/"
qr_string = qr_string_generator(
    device_id=str(device_id),
    qr_url=qr_url,
    receipt_date=qr_date(),
    reciept_global_no=global_number + 1,
    reciept_signature=receipt_device_signature_obj.sign_data()
)
```

## Validation

The generated QR string should:
- Be exactly 73 characters long (29 + 10 + 8 + 10 + 16)
- Start with the base URL
- Contain only alphanumeric characters and forward slashes
- Have proper zero-padding for device ID and global receipt number
- Have uppercase signature hash

## Error Handling

The function includes fallback mechanisms:
- If date parsing fails, uses current date
- If signature processing fails, uses default hash
- Ensures all components are properly formatted

## Testing

Use the provided test script to verify QR string generation:

```bash
python simple_qr_test.py
```

This will output a complete breakdown of the QR string components and the final generated string. 