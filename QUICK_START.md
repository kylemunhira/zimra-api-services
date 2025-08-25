# ZIMRA API Service - Quick Start Guide

This guide will help you quickly deploy the ZIMRA API Service as a Windows Service using Waitress.

## Prerequisites

- Windows Server 2016+ or Windows 10/11
- Python 3.8+
- PostgreSQL database
- Administrator privileges

## Quick Deployment Steps

### 1. Install Dependencies

```powershell
# Install Python dependencies
pip install -r requirements.txt
```

### 2. Test the Setup

```powershell
# Run pre-deployment tests
python test_waitress.py
```

### 3. Install Windows Service

```powershell
# Run as Administrator
.\install_windows_service.ps1
```

### 4. Verify Installation

```powershell
# Check service status
.\service_manager.ps1 -Action status

# View logs
.\service_manager.ps1 -Action logs
```

### 5. Access the Service

The service will be available at: `http://localhost:5000`

## Service Management

### Start/Stop/Restart
```powershell
.\service_manager.ps1 -Action start
.\service_manager.ps1 -Action stop
.\service_manager.ps1 -Action restart
```

### Check Status
```powershell
.\service_manager.ps1 -Action status
```

### View Logs
```powershell
.\service_manager.ps1 -Action logs
```

## Uninstall

```powershell
# Run as Administrator
.\uninstall_windows_service.ps1
```

## Troubleshooting

### Service Won't Start
1. Check if Python is in PATH
2. Verify database connection
3. Check log files: `zimra_service.log` and `zimra_windows_service.log`

### Port Issues
```powershell
# Change port
[Environment]::SetEnvironmentVariable("ZIMRA_PORT", "8080", "Machine")
Restart-Service -Name "ZimraAPIService"
```

### Database Issues
Update the connection string in `app/__init__.py`:
```python
app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql+psycopg2://username:password@localhost/database"
```

## Configuration

### Environment Variables
- `ZIMRA_HOST`: Server host (default: 0.0.0.0)
- `ZIMRA_PORT`: Server port (default: 5000)
- `ZIMRA_THREADS`: Worker threads (default: 4)
- `FLASK_ENV`: Environment (set to 'production')

### Custom Installation
```powershell
.\install_windows_service.ps1 -Host "127.0.0.1" -Port 8080 -Threads 8
```

## Log Files

- **Service Log**: `zimra_windows_service.log`
- **Application Log**: `zimra_service.log`

## Support

For detailed information, see `DEPLOYMENT_GUIDE.md`
