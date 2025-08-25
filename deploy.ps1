# ZIMRA API Service - Windows Server Deployment Script
# Run this script as Administrator

param(
    [string]$AppPath = "C:\inetpub\wwwroot\zimra-api",
    [string]$PythonVersion = "3.8",
    [string]$DatabasePassword = "",
    [string]$ServerPort = "80"
)

Write-Host "Starting ZIMRA API Service Deployment..." -ForegroundColor Green

# Check if running as Administrator
if (-NOT ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    Write-Host "This script must be run as Administrator!" -ForegroundColor Red
    exit 1
}

# Step 1: Create application directory
Write-Host "Creating application directory..." -ForegroundColor Yellow
if (!(Test-Path $AppPath)) {
    New-Item -ItemType Directory -Path $AppPath -Force
}

# Step 2: Copy application files
Write-Host "Copying application files..." -ForegroundColor Yellow
$CurrentDir = Get-Location
Copy-Item -Path "$CurrentDir\*" -Destination $AppPath -Recurse -Force

# Step 3: Create virtual environment
Write-Host "Setting up Python virtual environment..." -ForegroundColor Yellow
Set-Location $AppPath
python -m venv venv

# Step 4: Activate virtual environment and install dependencies
Write-Host "Installing Python dependencies..." -ForegroundColor Yellow
& "$AppPath\venv\Scripts\Activate.ps1"
pip install --upgrade pip
pip install -r requirements.txt
pip install wfastcgi

# Step 5: Enable wfastcgi
Write-Host "Enabling wfastcgi..." -ForegroundColor Yellow
wfastcgi-enable

# Step 6: Create logs directory
Write-Host "Creating logs directory..." -ForegroundColor Yellow
if (!(Test-Path "$AppPath\logs")) {
    New-Item -ItemType Directory -Path "$AppPath\logs" -Force
}

# Step 7: Create .env file
Write-Host "Creating environment configuration..." -ForegroundColor Yellow
$EnvContent = @"
FLASK_ENV=production
FLASK_APP=run.py
DATABASE_URL=postgresql+psycopg2://postgres:$DatabasePassword@localhost/zimra_api_db
SECRET_KEY=$(New-Guid)
"@
$EnvContent | Out-File -FilePath "$AppPath\.env" -Encoding UTF8

# Step 8: Configure IIS
Write-Host "Configuring IIS..." -ForegroundColor Yellow

# Import IIS module
Import-Module WebAdministration

# Create application pool
$AppPoolName = "ZIMRA-API-Pool"
if (!(Get-IISAppPool -Name $AppPoolName -ErrorAction SilentlyContinue)) {
    New-WebAppPool -Name $AppPoolName
    Set-ItemProperty -Path "IIS:\AppPools\$AppPoolName" -Name "managedRuntimeVersion" -Value ""
    Set-ItemProperty -Path "IIS:\AppPools\$AppPoolName" -Name "processModel.identityType" -Value "ApplicationPoolIdentity"
}

# Create website
$SiteName = "ZIMRA API"
if (!(Get-Website -Name $SiteName -ErrorAction SilentlyContinue)) {
    New-Website -Name $SiteName -Port $ServerPort -PhysicalPath $AppPath -ApplicationPool $AppPoolName
} else {
    Set-ItemProperty -Path "IIS:\Sites\$SiteName" -Name "physicalPath" -Value $AppPath
    Set-ItemProperty -Path "IIS:\Sites\$SiteName" -Name "applicationPool" -Value $AppPoolName
}

# Step 9: Configure permissions
Write-Host "Configuring file permissions..." -ForegroundColor Yellow
$Acl = Get-Acl $AppPath
$AccessRule = New-Object System.Security.AccessControl.FileSystemAccessRule("IIS_IUSRS", "FullControl", "ContainerInherit,ObjectInherit", "None", "Allow")
$Acl.SetAccessRule($AccessRule)
Set-Acl $AppPath $Acl

# Step 10: Configure firewall
Write-Host "Configuring firewall..." -ForegroundColor Yellow
New-NetFirewallRule -DisplayName "ZIMRA API HTTP" -Direction Inbound -Protocol TCP -LocalPort $ServerPort -Action Allow -ErrorAction SilentlyContinue

# Step 11: Start services
Write-Host "Starting services..." -ForegroundColor Yellow
Start-Service -Name W3SVC
Start-Website -Name $SiteName

Write-Host "Deployment completed successfully!" -ForegroundColor Green
Write-Host "Application URL: http://localhost:$ServerPort" -ForegroundColor Cyan
Write-Host "API Endpoint: http://localhost:$ServerPort/api" -ForegroundColor Cyan

# Step 12: Database setup reminder
Write-Host "`nNext steps:" -ForegroundColor Yellow
Write-Host "1. Set up PostgreSQL database" -ForegroundColor White
Write-Host "2. Run database migrations: flask db upgrade" -ForegroundColor White
Write-Host "3. Test the application" -ForegroundColor White
Write-Host "4. Configure SSL certificate (recommended)" -ForegroundColor White

