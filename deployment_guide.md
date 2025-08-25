# ZIMRA API Service - Windows Service Deployment Guide

This guide provides step-by-step instructions for deploying the ZIMRA API Service as a Windows Service using Waitress.

## Prerequisites

### System Requirements
- Windows Server 2016 or later (or Windows 10/11 for development)
- Python 3.8 or later
- PostgreSQL database server
- Administrator privileges for service installation

### Software Dependencies
- Python 3.8+
- pip (Python package manager)
- PostgreSQL client libraries

## Installation Steps

### 1. Prepare the Environment

1. **Clone or download the project** to your Windows server
2. **Open PowerShell as Administrator**
3. **Navigate to the project directory**:
   ```powershell
   cd "C:\path\to\zimra-api-service"
   ```

### 2. Install Python Dependencies

The installation script will automatically install all required dependencies, but you can also install them manually:

```powershell
# Install dependencies
python -m pip install -r requirements.txt
```

### 3. Configure Database

Ensure your PostgreSQL database is running and accessible. Update the database connection string in `app/__init__.py` if needed:

```python
app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql+psycopg2://username:password@localhost/database_name"
```

### 4. Configure Environment

The service uses the following environment variables (automatically set by the installer):

- `ZIMRA_HOST`: Host to bind to (default: 0.0.0.0)
- `ZIMRA_PORT`: Port to bind to (default: 5000)
- `ZIMRA_THREADS`: Number of worker threads (default: 4)
- `FLASK_ENV`: Environment mode (set to 'production')

### 5. Install Windows Service

Run the installation script as Administrator:

```powershell
# Basic installation with default settings
.\install_windows_service.ps1

# Custom installation with specific parameters
.\install_windows_service.ps1 -Host "127.0.0.1" -Port 8080 -Threads 8
```

The installer will:
- Install Python dependencies
- Set environment variables
- Create and configure the Windows Service
- Start the service automatically

## Service Management

### Using PowerShell Scripts

The project includes several PowerShell scripts for service management:

#### Check Service Status
```powershell
.\service_manager.ps1 -Action status
```

#### Start Service
```powershell
.\service_manager.ps1 -Action start
```

#### Stop Service
```powershell
.\service_manager.ps1 -Action stop
```

#### Restart Service
```powershell
.\service_manager.ps1 -Action restart
```

#### View Logs
```powershell
.\service_manager.ps1 -Action logs
```

### Using Windows Service Manager

You can also manage the service through Windows Services:

1. Press `Win + R`, type `services.msc`, and press Enter
2. Find "ZIMRA API Service" in the list
3. Right-click to start, stop, or restart the service

### Using Command Line

```powershell
# Start service
Start-Service -Name "ZimraAPIService"

# Stop service
Stop-Service -Name "ZimraAPIService"

# Check status
Get-Service -Name "ZimraAPIService"

# Restart service
Restart-Service -Name "ZimraAPIService"
```

## Configuration

### Service Configuration

The service configuration is stored in the following files:

- **`windows_service.py`**: Windows Service wrapper
- **`waitress_server.py`**: Waitress server configuration
- **`app/config.py`**: Application configuration

### Environment Variables

You can modify environment variables after installation:

```powershell
# Set custom host and port
[Environment]::SetEnvironmentVariable("ZIMRA_HOST", "127.0.0.1", "Machine")
[Environment]::SetEnvironmentVariable("ZIMRA_PORT", "8080", "Machine")

# Restart service to apply changes
Restart-Service -Name "ZimraAPIService"
```

### Database Configuration

Update the database connection in `app/__init__.py`:

```python
app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql+psycopg2://username:password@host:port/database"
```

## Monitoring and Logging

### Log Files

The service creates two main log files:

- **`zimra_windows_service.log`**: Windows Service wrapper logs
- **`zimra_service.log`**: Application logs

### Viewing Logs

```powershell
# View service logs
.\service_manager.ps1 -Action logs

# View specific log file
Get-Content zimra_service.log -Tail 50

# Monitor logs in real-time
Get-Content zimra_service.log -Wait
```

### Windows Event Log

The service also logs to Windows Event Log:

1. Open Event Viewer (`eventvwr.msc`)
2. Navigate to Windows Logs > System
3. Filter by Source: "Service Control Manager"

## Troubleshooting

### Common Issues

#### Service Won't Start
1. Check if Python is in PATH
2. Verify all dependencies are installed
3. Check log files for errors
4. Ensure database is accessible

#### Port Already in Use
```powershell
# Check what's using the port
netstat -ano | findstr :5000

# Change port in environment variables
[Environment]::SetEnvironmentVariable("ZIMRA_PORT", "8080", "Machine")
Restart-Service -Name "ZimraAPIService"
```

#### Database Connection Issues
1. Verify PostgreSQL is running
2. Check connection string in `app/__init__.py`
3. Ensure database exists and is accessible
4. Check firewall settings

#### Permission Issues
- Ensure the service account has necessary permissions
- Check file permissions on the project directory
- Verify database user permissions

### Debug Mode

For troubleshooting, you can run the application directly:

```powershell
# Stop the service
Stop-Service -Name "ZimraAPIService"

# Run directly with debug output
python waitress_server.py
```

## Uninstallation

### Remove Windows Service

```powershell
# Run uninstaller as Administrator
.\uninstall_windows_service.ps1
```

The uninstaller will:
- Stop the service
- Remove the Windows Service
- Clean up environment variables
- Remove log files

### Manual Removal

If the uninstaller fails, you can remove manually:

```powershell
# Stop and remove service
Stop-Service -Name "ZimraAPIService" -Force
sc.exe delete ZimraAPIService

# Remove environment variables
[Environment]::SetEnvironmentVariable("ZIMRA_HOST", $null, "Machine")
[Environment]::SetEnvironmentVariable("ZIMRA_PORT", $null, "Machine")
[Environment]::SetEnvironmentVariable("ZIMRA_THREADS", $null, "Machine")
[Environment]::SetEnvironmentVariable("FLASK_ENV", $null, "Machine")
```

## Security Considerations

### Firewall Configuration

Configure Windows Firewall to allow the service port:

```powershell
# Allow inbound connections on service port
New-NetFirewallRule -DisplayName "ZIMRA API Service" -Direction Inbound -Protocol TCP -LocalPort 5000 -Action Allow
```

### Service Account

The service runs under the Local System account by default. For production environments, consider:

1. Creating a dedicated service account
2. Granting minimal required permissions
3. Using Windows Authentication for database connections

### SSL/TLS Configuration

For production deployments, configure SSL/TLS:

1. Obtain SSL certificates
2. Configure Waitress for HTTPS
3. Update firewall rules for HTTPS port

## Performance Tuning

### Waitress Configuration

Adjust Waitress settings in `waitress_server.py`:

```python
serve(
    app,
    host=host,
    port=port,
    threads=threads,           # Increase for more concurrent requests
    connection_limit=1000,     # Maximum concurrent connections
    cleanup_interval=30,       # Connection cleanup interval
    channel_timeout=120,       # Request timeout
    max_request_body_size=1073741824,  # 1GB max request size
    buffer_size=16384,         # Buffer size for requests
    url_scheme='http'
)
```

### Database Optimization

1. Configure PostgreSQL for production workloads
2. Set appropriate connection pool sizes
3. Optimize database queries
4. Monitor database performance

## Backup and Recovery

### Database Backup

```powershell
# Create database backup
pg_dump -h localhost -U username -d zimra_api_db > backup.sql

# Restore database
psql -h localhost -U username -d zimra_api_db < backup.sql
```

### Service Configuration Backup

Backup the following files:
- `app/config.py`
- `app/__init__.py`
- Environment variables
- Log files

## Support

For issues and support:

1. Check the log files for error messages
2. Review this deployment guide
3. Check Windows Event Logs
4. Verify all prerequisites are met

## File Structure

```
zimra-api-service/
├── app/                          # Flask application
│   ├── __init__.py              # App factory and configuration
│   ├── config.py                # ZIMRA configuration
│   ├── models.py                # Database models
│   └── routes.py                # API routes
├── static/                      # Static files
├── waitress_server.py           # Waitress server configuration
├── windows_service.py           # Windows Service wrapper
├── install_windows_service.ps1  # Service installer
├── uninstall_windows_service.ps1 # Service uninstaller
├── service_manager.ps1          # Service management
├── requirements.txt             # Python dependencies
└── DEPLOYMENT_GUIDE.md          # This guide
```
