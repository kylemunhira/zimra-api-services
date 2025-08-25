# ZIMRA API Service - Deployment Checklist

## Pre-Deployment Checklist

### Server Requirements
- [ ] Windows Server 2016 or later
- [ ] PowerShell 5.1 or later
- [ ] Administrator access
- [ ] Internet connection for downloads

### Software Installation
- [ ] Python 3.8+ installed
- [ ] PostgreSQL 12+ installed and configured
- [ ] IIS installed and configured
- [ ] URL Rewrite Module installed
- [ ] Application Request Routing (ARR) installed

### Database Setup
- [ ] PostgreSQL service running
- [ ] Database `zimra_api_db` created
- [ ] User `zimra_user` created with proper permissions
- [ ] Database connection string configured

## Deployment Steps

### Step 1: Application Deployment
- [ ] Copy application files to `C:\inetpub\wwwroot\zimra-api`
- [ ] Run `deploy.ps1` script as Administrator
- [ ] Verify virtual environment created
- [ ] Verify all Python packages installed

### Step 2: Database Migration
- [ ] Activate virtual environment: `.\venv\Scripts\Activate.ps1`
- [ ] Run database migrations: `flask db upgrade`
- [ ] Verify database tables created

### Step 3: IIS Configuration
- [ ] Verify `web.config` file in application root
- [ ] Verify application pool created and configured
- [ ] Verify website created and bound to correct port
- [ ] Verify file permissions set correctly

### Step 4: Service Installation (Optional)
- [ ] Run `install_windows_service.ps1` as Administrator
- [ ] Verify service installed and running
- [ ] Set service to start automatically

### Step 5: Testing
- [ ] Test local access: `http://localhost`
- [ ] Test API endpoint: `http://localhost/api`
- [ ] Test external access: `http://your-server-ip`
- [ ] Check application logs for errors

### Step 6: Security Configuration
- [ ] Configure firewall rules
- [ ] Install SSL certificate (recommended)
- [ ] Set up HTTPS binding
- [ ] Configure backup strategy

## Post-Deployment Verification

### Application Health
- [ ] Application responds to HTTP requests
- [ ] API endpoints return expected responses
- [ ] Database connections working
- [ ] Static files served correctly

### Performance Monitoring
- [ ] Monitor CPU and memory usage
- [ ] Monitor database performance
- [ ] Set up logging and monitoring
- [ ] Configure alerts for critical issues

### Security Verification
- [ ] Firewall rules configured correctly
- [ ] SSL certificate installed (if applicable)
- [ ] File permissions set correctly
- [ ] Database access secured

## Troubleshooting

### Common Issues
- [ ] 500 Internal Server Error - Check application logs
- [ ] Database connection failed - Verify connection string
- [ ] Permission denied - Check file permissions
- [ ] Module not found - Verify virtual environment

### Useful Commands
```powershell
# Check service status
Get-Service -Name "ZIMRA-API-Service"

# Check IIS status
Get-Service -Name W3SVC

# Check PostgreSQL status
Get-Service -Name postgresql*

# Restart IIS
iisreset

# View application logs
Get-Content "C:\inetpub\wwwroot\zimra-api\logs\wsgi.log" -Tail 50
```

## Support Information

### Log Locations
- Application logs: `C:\inetpub\wwwroot\zimra-api\logs\`
- IIS logs: `C:\inetpub\logs\LogFiles\`
- Event Viewer: Windows Logs → Application

### Configuration Files
- Web.config: `C:\inetpub\wwwroot\zimra-api\web.config`
- Environment variables: `C:\inetpub\wwwroot\zimra-api\.env`
- Database configuration: In application code

### Contact Information
- System Administrator: [Your Contact Info]
- Database Administrator: [Your Contact Info]
- Application Support: [Your Contact Info]

