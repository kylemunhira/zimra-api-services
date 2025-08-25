class ZimraConfig:
    """
    Configuration class for ZIMRA API service.
    Handles both test and production environments with dynamic URL and tax ID mappings.
    """
    
    def __init__(self, test_mode: bool = True):
        """
        Initialize ZIMRA configuration.
        
        Args:
            test_mode (bool): If True, use test environment. If False, use production environment.
        """
        if test_mode:
            self.test_mode = True
            self.base_url: str = 'https://fdmsapitest.zimra.co.zw/Device/v1/'
            self.qr_url: str = 'https://fdmstest.zimra.co.zw/'
            # Test environment tax ID mapping
            self.applicable_taxes: dict = {
                'exempt': 1,  # Exempt items
                0: 2,         # Zero rate 0%
                5: 514,       # Non-VAT Withholding Tax
                15: 3         # Standard rated 15%
            }
        else:
            self.test_mode = False
            self.base_url: str = 'https://fdmsapi.zimra.co.zw/Device/v1/'
            self.qr_url: str = 'https://fdms.zimra.co.zw/'
            # Production environment tax ID mapping
            self.applicable_taxes: dict = {
                15: 1,        # Standard rated 15%
                0: 2,         # Zero rate 0%
                5: 514,       # Non-VAT Withholding Tax
                'exempt': 3   # Exempt items
            }
    
    def get_api_url(self, device_id: str, endpoint: str) -> str:
        """
        Get the full API URL for a specific endpoint.
        
        Args:
            device_id (str): Device identifier
            endpoint (str): API endpoint (e.g., 'GetStatus', 'OpenDay', 'CloseDay', 'SubmitReceipt', 'GetConfig')
            
        Returns:
            str: Complete API URL
        """
        return f"{self.base_url}{device_id}/{endpoint}"
    
    def get_tax_id(self, tax_code: str) -> int:
        """
        Get tax ID for a given tax code.
        
        Args:
            tax_code (str): Tax code ('A' for exempt, 'B' for 0%, 'C' for 15%, 'D' for 5%)
            
        Returns:
            int: Tax ID for the given tax code
        """
        tax_code_mapping = {
            'A': 'exempt',  # Exempt
            'B': 0,         # Zero rate 0%
            'C': 15,        # Standard rated 15%
            'D': 5          # Non-VAT Withholding Tax
        }
        
        tax_value = tax_code_mapping.get(tax_code.upper(), 15)  # Default to 15%
        return self.applicable_taxes.get(tax_value, 1)  # Default to tax ID 1
    
    def get_tax_percentage(self, tax_code: str) -> float:
        """
        Get tax percentage for a given tax code.
        
        Args:
            tax_code (str): Tax code ('A' for exempt, 'B' for 0%, 'C' for 15%, 'D' for 5%)
            
        Returns:
            float: Tax percentage (None for exempt items)
        """
        tax_percentages = {
            'A': None,  # Exempt items - should be None/null
            'B': 0.0,   # 0% tax items
            'C': 15.0,  # 15% tax items
            'D': 5.0,   # 5% tax items
        }
        return tax_percentages.get(tax_code.upper(), 15.0)
    
    def is_exempt_tax_id(self, tax_id: int) -> bool:
        """
        Check if a tax ID represents exempt items.
        
        Args:
            tax_id (int): Tax ID to check
            
        Returns:
            bool: True if the tax ID represents exempt items
        """
        exempt_tax_id = self.applicable_taxes.get('exempt', 3)
        return tax_id == exempt_tax_id
    
    def get_tax_mapping(self) -> dict:
        """
        Get the complete tax mapping for the current environment.
        
        Returns:
            dict: Tax mapping with tax codes, percentages, and IDs
        """
        return {
            '15': {
                'taxCode': 'C', 
                'taxPercent': 15.0, 
                'taxID': self.applicable_taxes.get(15, 1), 
                'taxAmount': 0.0, 
                'salesAmountWithTax': 0.0
            },
            '0': {
                'taxCode': 'B', 
                'taxPercent': 0.0, 
                'taxID': self.applicable_taxes.get(0, 2), 
                'taxAmount': 0.0, 
                'salesAmountWithTax': 0.0
            },
            '-1': {
                'taxCode': "A", 
                'taxPercent': 0.0, 
                'taxID': self.applicable_taxes.get('exempt', 3), 
                'taxAmount': 0.0, 
                'salesAmountWithTax': 0.0
            },
            '5': {
                'taxCode': 'D', 
                'taxPercent': 5.0, 
                'taxID': self.applicable_taxes.get(5, 514), 
                'taxAmount': 0.0, 
                'salesAmountWithTax': 0.0
            }
        }
    
    def get_tax_percent_by_id(self) -> dict:
        """
        Get tax percent mapping by tax ID for the current environment.
        
        Returns:
            dict: Mapping of tax ID to tax percentage
        """
        return {
            self.applicable_taxes.get(15, 1): 15,      # Standard rated 15%
            self.applicable_taxes.get(0, 2): 0,        # Zero rate 0%
            self.applicable_taxes.get('exempt', 3): None,  # Exempt
            self.applicable_taxes.get(5, 514): 5       # Non-VAT Withholding Tax
        }


# Global configuration instance
# Set test_mode=True for test environment, False for production
zimra_config = ZimraConfig(test_mode=True)  # Production mode enabled
