# ZIMRA API Service Environment Configuration

This document explains the new environment configuration system that allows easy switching between test and production environments.

## Overview

The system now uses a centralized configuration class (`ZimraConfig`) that handles all environment-specific settings including:
- API URLs
- QR Code URLs  
- Tax ID mappings
- Environment-specific logic

## Configuration Class

### Location
`app/config.py`

### Key Features
- **Dynamic URL Management**: Automatically switches between test and production URLs
- **Tax ID Mapping**: Handles different tax ID configurations for each environment
- **Centralized Logic**: All environment-specific logic is in one place
- **Easy Switching**: Simple boolean flag to switch environments

## Environment Configurations

### Test Environment
```python
test_mode = True
base_url = 'https://fdmsapitest.zimra.co.zw/Device/v1/'
qr_url = 'https://fdmstest.zimra.co.zw/'
applicable_taxes = {
    'exempt': 1,  # Exempt items
    0: 2,         # Zero rate 0%
    5: 514,       # Non-VAT Withholding Tax
    15: 3         # Standard rated 15%
}
```

### Production Environment
```python
test_mode = False
base_url = 'https://fdmsapi.zimra.co.zw/Device/v1/'
qr_url = 'https://fdms.zimra.co.zw/'
applicable_taxes = {
    15: 1,        # Standard rated 15%
    0: 2,         # Zero rate 0%
    5: 514,       # Non-VAT Withholding Tax
    'exempt': 3   # Exempt items
}
```

## Tax ID Mapping Changes

| Tax Type | Test Tax ID | Production Tax ID | Description |
|----------|-------------|-------------------|-------------|
| Standard rated 15% | 3 | 1 | Standard VAT rate |
| Zero rate 0% | 2 | 2 | Zero-rated items |
| Exempt | 1 | 3 | Exempt from VAT |
| Non-VAT Withholding Tax | 514 | 514 | Withholding tax |

## Usage

### Switching Environments

#### Method 1: Using the Switch Script
```bash
# Switch to test environment
python switch_environment.py test

# Switch to production environment  
python switch_environment.py production

# Check current environment
python switch_environment.py status
```

#### Method 2: Manual Configuration
Edit `app/config.py` and change the last line:
```python
# For test environment
zimra_config = ZimraConfig(test_mode=True)

# For production environment
zimra_config = ZimraConfig(test_mode=False)
```

### Using the Configuration in Code

#### Getting API URLs
```python
from app.config import zimra_config

# Get URL for any endpoint
url = zimra_config.get_api_url(device_id, "GetStatus")
url = zimra_config.get_api_url(device_id, "OpenDay")
url = zimra_config.get_api_url(device_id, "CloseDay")
url = zimra_config.get_api_url(device_id, "SubmitReceipt")
url = zimra_config.get_api_url(device_id, "GetConfig")
```

#### Getting Tax Information
```python
# Get tax ID for a tax code
tax_id = zimra_config.get_tax_id('C')  # Returns 1 for production, 3 for test

# Get tax percentage for a tax code
tax_percent = zimra_config.get_tax_percentage('A')  # Returns None for exempt

# Check if a tax ID is exempt
is_exempt = zimra_config.is_exempt_tax_id(3)  # Returns True for production, False for test

# Get complete tax mapping
tax_mapping = zimra_config.get_tax_mapping()

# Get tax percent by ID mapping
tax_percent_by_id = zimra_config.get_tax_percent_by_id()
```

#### Getting QR URLs
```python
qr_url = zimra_config.qr_url
```

## Files Updated

The following files have been updated to use the new configuration system:

### Core Files
- `app/config.py` - New configuration class
- `app/routes.py` - All API endpoints and tax logic
- `utils/invoice_utils.py` - Tax calculations and QR generation
- `utils/generate_counters.py` - Fiscal counter generation
- `utils/update_closeday.py` - Fiscal counter updates

### Utility Files
- `switch_environment.py` - Environment switching script
- `ENVIRONMENT_CONFIGURATION.md` - This documentation

## Benefits

### 1. **Easy Environment Switching**
- Single command to switch between environments
- No need to manually update multiple files
- Reduces human error

### 2. **Centralized Configuration**
- All environment-specific settings in one place
- Easy to maintain and update
- Consistent across all modules

### 3. **Type Safety**
- Configuration class provides type hints
- Better IDE support and error detection
- Clear interface for all configuration options

### 4. **Maintainability**
- Changes to URLs or tax IDs only need to be made in one place
- Clear separation between test and production logic
- Easy to add new environment-specific features

## Testing

### Verify Configuration
```python
from app.config import zimra_config

# Check current environment
print(f"Test mode: {zimra_config.test_mode}")
print(f"Base URL: {zimra_config.base_url}")
print(f"QR URL: {zimra_config.qr_url}")

# Test tax ID mapping
print(f"Tax ID for 'C' (15%): {zimra_config.get_tax_id('C')}")
print(f"Tax ID for 'A' (exempt): {zimra_config.get_tax_id('A')}")
```

### Test Environment Switching
```bash
# Switch to test
python switch_environment.py test

# Verify URLs are test URLs
python -c "from app.config import zimra_config; print(zimra_config.base_url)"

# Switch to production
python switch_environment.py production

# Verify URLs are production URLs
python -c "from app.config import zimra_config; print(zimra_config.base_url)"
```

## Migration Notes

### From Old System
If you were previously using hardcoded URLs and tax IDs:

1. **Old Code:**
```python
url = f'https://fdmsapitest.zimra.co.zw/Device/v1/{device_id}/GetStatus'
tax_id = 3  # Hardcoded for 15% tax
```

2. **New Code:**
```python
from app.config import zimra_config
url = zimra_config.get_api_url(device_id, "GetStatus")
tax_id = zimra_config.get_tax_id('C')  # Gets correct tax ID for environment
```

### Backward Compatibility
The new system maintains the same external API - only the internal implementation has changed. All existing functionality should work exactly the same.

## Troubleshooting

### Common Issues

1. **Configuration Not Loading**
   - Ensure `app/config.py` exists and is properly formatted
   - Check that the `zimra_config` instance is created at the bottom of the file

2. **Wrong Environment Active**
   - Use `python switch_environment.py status` to check current environment
   - Restart your application after switching environments

3. **Tax ID Mismatches**
   - Verify that the tax ID mappings in the configuration match your environment
   - Check that all utility functions are using the configuration instead of hardcoded values

### Debug Mode
To debug configuration issues, you can add logging:
```python
import logging
from app.config import zimra_config

logging.basicConfig(level=logging.DEBUG)
logging.debug(f"Current environment: {'TEST' if zimra_config.test_mode else 'PRODUCTION'}")
logging.debug(f"Base URL: {zimra_config.base_url}")
logging.debug(f"Tax mapping: {zimra_config.applicable_taxes}")
```

## Future Enhancements

### Environment Variables
The system could be enhanced to support environment variables:
```python
import os
test_mode = os.getenv('ZIMRA_ENVIRONMENT', 'production').lower() == 'test'
zimra_config = ZimraConfig(test_mode=test_mode)
```

### Multiple Environments
The configuration class could be extended to support multiple environments:
```python
class ZimraConfig:
    def __init__(self, environment='production'):
        self.environment = environment
        # Load configuration based on environment
```

### Configuration Validation
Add validation to ensure configuration is correct:
```python
def validate_config(self):
    """Validate that the configuration is correct for the current environment"""
    # Add validation logic
    pass
```
