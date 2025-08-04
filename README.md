# ZIMRA API Service

A comprehensive Flask-based API service for managing ZIMRA fiscal devices and invoices with a modern web interface.

## Features

- **Fiscal Device Management**: Open/close fiscal days, get device status
- **Invoice Management**: Submit receipts, view invoices with modern UI
- **Real-time ZIMRA Integration**: Direct communication with ZIMRA fiscal device API
- **Modern Web Interface**: Beautiful, responsive UI for invoice management
- **Advanced Filtering**: Filter invoices by device, status, date range
- **Pagination**: Efficient handling of large invoice datasets
- **QR Code Support**: View QR codes for fiscalized invoices

## Quick Start

### Prerequisites

- Python 3.8+
- PostgreSQL database
- ZIMRA device certificates (placed in `certs/` directory)

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd zimra-api-service
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up the database:
```bash
# Configure your database connection in app/__init__.py
# Then run migrations:
flask db upgrade
```

5. Place your ZIMRA device certificates in the `certs/` directory:
```
certs/
├── 26428.pem
├── 26428.key
└── ... (other device certificates)
```

6. Run the application:
```bash
python run.py
```

The application will be available at `http://localhost:5000`

## Web Interface

### Main Dashboard
Visit `http://localhost:5000` to access the main dashboard with links to:
- Invoice Management UI
- API Status Check

### Invoice Management
Visit `http://localhost:5000/api/invoices-ui` to access the modern invoice listing interface featuring:

- **Advanced Filtering**: Filter by device ID, fiscalization status, and date range
- **Real-time Search**: Instant results as you type
- **Responsive Design**: Works perfectly on desktop and mobile devices
- **Invoice Details**: Click any invoice to view complete details including line items
- **QR Code Viewing**: View QR codes for fiscalized invoices
- **Pagination**: Navigate through large datasets efficiently

## API Endpoints

### Device Management
- `GET /api/getstatus/{device_id}` - Get device status
- `POST /api/openday/{device_id}` - Open fiscal day
- `POST /api/close_day/{device_id}` - Close fiscal day
- `GET /api/get_config/{device_id}` - Get device configuration

### Close Day Function Details

The `close_day` endpoint is a critical function for fiscal compliance that:

1. **Validates Input**: Checks for required fields (`fiscalDayNo`, `fiscalDayCounters`) and validates fiscal day number
2. **Device Verification**: Ensures the device exists and has proper certificates
3. **Fiscal Day Check**: Verifies there's an open fiscal day to close
4. **Signature Generation**: Creates a digital signature using the device's private key
5. **ZIMRA Integration**: Sends the signed request to ZIMRA's CloseDay API
6. **Database Update**: Updates the fiscal day status to 'FISCAL_DAY_CLOSED'

**Required Payload Structure:**
```json
{
  "fiscalDayNo": "123",
  "fiscalDayCounters": [
    {
      "fiscalCounterType": "TaxByTax",
      "fiscalCounterTaxPercent": 15.0,
      "fiscalCounterTaxID": 1,
      "fiscalCounterCurrency": "USD",
      "fiscalCounterValue": 100.00,
      "fiscalCounterMoneyType": "CASH"
    }
  ]
}
```

**Response Format:**
- **Success (200)**: Returns ZIMRA's response with fiscal day closure confirmation
- **Error (400)**: Missing required fields (`fiscalDayNo`, `fiscalDayCounters`) or fiscal day number mismatch
- **Error (404)**: Device not found or no open fiscal day
- **Error (500)**: Internal server error with detailed error information

### Invoice Management
- `GET /api/invoices` - List all invoices with filtering
- `GET /api/invoices/{invoice_id}` - Get specific invoice details
- `POST /api/submit_receipt/{device_id}` - Submit a new receipt

### Web Interface
- `GET /` - Main dashboard
- `GET /api/invoices-ui` - Invoice management interface
- `GET /static/{filename}` - Serve static files

## Invoice Filtering Options

The invoice listing API supports the following query parameters:

- `device_id` - Filter by specific device
- `status` - Filter by fiscalization status (`fiscalized` or `pending`)
- `date_from` - Filter invoices created from this date (YYYY-MM-DD)
- `date_to` - Filter invoices created until this date (YYYY-MM-DD)
- `page` - Page number for pagination (default: 1)
- `per_page` - Items per page (default: 10)

### Example API Calls

```bash
# Get all invoices
curl http://localhost:5000/api/invoices

# Get invoices for specific device
curl http://localhost:5000/api/invoices?device_id=26428

# Get fiscalized invoices only
curl http://localhost:5000/api/invoices?status=fiscalized

# Get invoices from date range
curl "http://localhost:5000/api/invoices?date_from=2024-01-01&date_to=2024-12-31"

# Get specific invoice details
curl http://localhost:5000/api/invoices/INV-001
```

## Database Schema

The application uses the following main models:

- **DeviceInfo**: Device configuration and certificates
- **FiscalDay**: Fiscal day tracking and status
- **Invoice**: Main invoice data with ZIMRA integration
- **InvoiceLineItem**: Individual line items within invoices
- **DeviceBranchAddress**: Branch address information
- **DeviceBranchContact**: Branch contact information

## Utility Functions

### Close Day Utilities (`utils/close_day_string_utilts.py`)

The close day functionality relies on several utility functions:

- **`generate_close_day_string()`**: Constructs the signing string by extracting counters and concatenating device-specific values
- **`counters_extract_close_day()`**: Extracts and formats fiscal counter data from ZIMRA's fiscalDayCounters list
- **`concat_helper_close_day()`**: Concatenates CloseDay data fields into a single string for signing
- **`add_zeros()`**: Formats tax percentages to two decimal places (e.g., 15 → '15.00')

### Date Utilities (`utils/date_utils.py`)

- **`get_close_day_string_date()`**: Returns current date in 'YYYY-MM-DD' format for fiscal day closure

## Configuration

### Database Configuration
Update the database connection in `app/__init__.py`:

```python
app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql+psycopg2://username:password@localhost/database_name"
```

### Certificate Configuration
Place your ZIMRA device certificates in the `certs/` directory with the naming convention:
- `{device_id}.pem` - Device certificate
- `{device_id}.key` - Device private key

## Development

### Running in Development Mode
```bash
python run.py
```

### Database Migrations
```bash
# Create a new migration
flask db migrate -m "Description of changes"

# Apply migrations
flask db upgrade
```

### Testing
The application includes comprehensive error handling and logging. Check the console output for detailed information about API requests and responses.

## Security Considerations

- Device certificates are stored securely in the `certs/` directory
- All API communications with ZIMRA use SSL/TLS encryption
- Private keys are used for digital signatures on receipts and fiscal day closures
- Database connections use secure PostgreSQL authentication
- Digital signatures ensure data integrity and authenticity for ZIMRA compliance

### Close Day Security Process

The close day function implements a comprehensive security workflow:

1. **Certificate Validation**: Verifies device certificates exist and are accessible
2. **Private Key Signing**: Uses the device's private key to create digital signatures
3. **String Construction**: Builds a secure signing string from fiscal counters and metadata
4. **Base64 Encoding**: Encodes the signature for transmission to ZIMRA
5. **SSL/TLS Communication**: All ZIMRA API calls use encrypted connections
6. **Database Integrity**: Updates fiscal day status only after successful ZIMRA response

## Troubleshooting

### Common Issues

1. **Certificate Errors**: Ensure device certificates are properly placed in the `certs/` directory
2. **Database Connection**: Verify PostgreSQL is running and credentials are correct
3. **ZIMRA API Errors**: Check device status and fiscal day status before submitting receipts
4. **UI Not Loading**: Ensure all static files are in the `static/` directory

### Close Day Specific Issues

1. **"No open fiscal day found"**: Ensure a fiscal day is opened before attempting to close
2. **"Missing required fields"**: Verify the payload contains `fiscalDayNo` and `fiscalDayCounters` (camelCase)
3. **"Fiscal day number mismatch"**: Ensure the provided fiscal day number matches the open fiscal day
4. **Signature Generation Errors**: Check that the device's private key is accessible and valid
5. **ZIMRA CloseDay API Errors**: Verify fiscal counters are correctly formatted and totals match
6. **Certificate Path Issues**: Ensure certificate and key paths in DeviceInfo table are correct

### Logs
The application provides detailed logging. Check the console output for:
- API request/response details
- Database operation logs
- ZIMRA integration status
- Error messages and stack traces

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions, please contact the development team or create an issue in the repository. 