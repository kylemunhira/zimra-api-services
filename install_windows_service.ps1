# PowerShell script to install and configure ZIMRA API Service as Windows Service
# Run this script as Administrator

param(
    [string]$ServiceName = "ZimraAPIService",
    [string]$DisplayName = "ZIMRA API Service",
    [string]$Description = "ZIMRA API Service for fiscal device management and invoice processing",
    [string]$PythonPath = "",
    [string]$WorkingDirectory = "",
    [string]$ServerHost = "0.0.0.0",
    [int]$Port = 5000,
    [int]$Threads = 4
)

# Function to write colored output
function Write-ColorOutput {
    param(
        [string]$Message,
        [string]$Color = "White"
    )
    Write-Host $Message -ForegroundColor $Color
}

# Function to check if running as administrator
function Test-Administrator {
    $currentUser = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($currentUser)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

# Check if running as administrator
if (-not (Test-Administrator)) {
    Write-ColorOutput "This script must be run as Administrator!" "Red"
    Write-ColorOutput "Please right-click PowerShell and select 'Run as Administrator'" "Yellow"
    exit 1
}

Write-ColorOutput "=== ZIMRA API Service Windows Service Installer ===" "Cyan"
Write-ColorOutput ""

# Get current directory if not specified
if (-not $WorkingDirectory) {
    $WorkingDirectory = Get-Location
}

Write-ColorOutput "Working Directory: $WorkingDirectory" "Yellow"

# Find Python executable if not specified
if (-not $PythonPath) {
    $pythonCommands = @("python", "python3", "py")
    $PythonPath = $null
    
    foreach ($cmd in $pythonCommands) {
        try {
            $result = Get-Command $cmd -ErrorAction SilentlyContinue
            if ($result) {
                $PythonPath = $result.Source
                break
            }
        }
        catch {
            continue
        }
    }
    
    if (-not $PythonPath) {
        Write-ColorOutput "Python not found in PATH!" "Red"
        Write-ColorOutput "Please install Python or specify the PythonPath parameter" "Yellow"
        exit 1
    }
}

Write-ColorOutput "Python Path: $PythonPath" "Yellow"

# Check if required files exist
$requiredFiles = @(
    "windows_service.py",
    "waitress_server.py",
    "requirements.txt"
)

foreach ($file in $requiredFiles) {
    $filePath = Join-Path $WorkingDirectory $file
    if (-not (Test-Path $filePath)) {
        Write-ColorOutput "Required file not found: $file" "Red"
        exit 1
    }
}

Write-ColorOutput "All required files found" "Green"

# Install Python dependencies
Write-ColorOutput "Installing Python dependencies..." "Yellow"
try {
    $requirementsPath = Join-Path $WorkingDirectory "requirements.txt"
    & $PythonPath -m pip install -r $requirementsPath
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to install dependencies"
    }
    Write-ColorOutput "Dependencies installed successfully" "Green"
}
catch {
    Write-ColorOutput "Failed to install dependencies: $($_.Exception.Message)" "Red"
    exit 1
}

# Set environment variables
Write-ColorOutput "Setting environment variables..." "Yellow"
[Environment]::SetEnvironmentVariable("ZIMRA_HOST", $ServerHost, "Machine")
[Environment]::SetEnvironmentVariable("ZIMRA_PORT", $Port.ToString(), "Machine")
[Environment]::SetEnvironmentVariable("ZIMRA_THREADS", $Threads.ToString(), "Machine")
[Environment]::SetEnvironmentVariable("FLASK_ENV", "production", "Machine")

Write-ColorOutput "Environment variables set:" "Green"
Write-ColorOutput "  ZIMRA_HOST: $ServerHost" "White"
Write-ColorOutput "  ZIMRA_PORT: $Port" "White"
Write-ColorOutput "  ZIMRA_THREADS: $Threads" "White"
Write-ColorOutput "  FLASK_ENV: production" "White"

# Install Windows Service
Write-ColorOutput "Installing Windows Service..." "Yellow"
try {
    $serviceScriptPath = Join-Path $WorkingDirectory "windows_service.py"
    & $PythonPath $serviceScriptPath install
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to install service"
    }
    Write-ColorOutput "Windows Service installed successfully" "Green"
}
catch {
    Write-ColorOutput "Failed to install Windows Service: $($_.Exception.Message)" "Red"
    exit 1
}

# Configure service to start automatically
Write-ColorOutput "Configuring service startup..." "Yellow"
try {
    Set-Service -Name $ServiceName -StartupType Automatic
    Write-ColorOutput "Service configured to start automatically" "Green"
}
catch {
    Write-ColorOutput "Failed to configure service startup: $($_.Exception.Message)" "Red"
}

# Start the service
Write-ColorOutput "Starting Windows Service..." "Yellow"
try {
    Start-Service -Name $ServiceName
    Write-ColorOutput "Windows Service started successfully" "Green"
}
catch {
    Write-ColorOutput "Failed to start service: $($_.Exception.Message)" "Red"
    Write-ColorOutput "You can start it manually using: Start-Service -Name '$ServiceName'" "Yellow"
}

# Display service status
Write-ColorOutput ""
Write-ColorOutput "=== Service Status ===" "Cyan"
try {
    $service = Get-Service -Name $ServiceName
    Write-ColorOutput "Service Name: $($service.Name)" "White"
    Write-ColorOutput "Display Name: $($service.DisplayName)" "White"
    Write-ColorOutput "Status: $($service.Status)" "White"
    Write-ColorOutput "Startup Type: $($service.StartType)" "White"
}
catch {
    Write-ColorOutput "Failed to get service status: $($_.Exception.Message)" "Red"
}

Write-ColorOutput ""
Write-ColorOutput "=== Installation Complete ===" "Green"
Write-ColorOutput ""
Write-ColorOutput "Service Management Commands:" "Yellow"
Write-ColorOutput "  Start Service:   Start-Service -Name '$ServiceName'" "White"
Write-ColorOutput "  Stop Service:    Stop-Service -Name '$ServiceName'" "White"
Write-ColorOutput "  Restart Service: Restart-Service -Name '$ServiceName'" "White"
Write-ColorOutput "  Service Status:  Get-Service -Name '$ServiceName'" "White"
Write-ColorOutput ""
Write-ColorOutput "Uninstall Service:" "Yellow"
Write-ColorOutput "  Stop-Service -Name '$ServiceName'" "White"
Write-ColorOutput "  & '$PythonPath' '$serviceScriptPath' remove" "White"
Write-ColorOutput ""
Write-ColorOutput "Service will be available at: http://$ServerHost`:$Port" "Cyan"
Write-ColorOutput "Log files:" "Yellow"
Write-ColorOutput "  Service Log: $WorkingDirectory\zimra_windows_service.log" "White"
Write-ColorOutput "  Application Log: $WorkingDirectory\zimra_service.log" "White"

