# PowerShell script to uninstall ZIMRA API Service Windows Service
# Run this script as Administrator

param(
    [string]$ServiceName = "ZimraAPIService",
    [string]$PythonPath = "",
    [string]$WorkingDirectory = ""
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

Write-ColorOutput "=== ZIMRA API Service Windows Service Uninstaller ===" "Cyan"
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

# Check if service exists
try {
    $service = Get-Service -Name $ServiceName -ErrorAction Stop
    Write-ColorOutput "Found service: $($service.DisplayName)" "Yellow"
}
catch {
    Write-ColorOutput "Service '$ServiceName' not found!" "Red"
    exit 1
}

# Stop the service if it's running
if ($service.Status -eq "Running") {
    Write-ColorOutput "Stopping service..." "Yellow"
    try {
        Stop-Service -Name $ServiceName -Force
        Write-ColorOutput "Service stopped successfully" "Green"
        
        # Wait a moment for the service to fully stop
        Start-Sleep -Seconds 3
    }
    catch {
        Write-ColorOutput "Failed to stop service: $($_.Exception.Message)" "Red"
        Write-ColorOutput "Attempting to continue with uninstallation..." "Yellow"
    }
}

# Remove the Windows Service
Write-ColorOutput "Removing Windows Service..." "Yellow"
try {
    $serviceScriptPath = Join-Path $WorkingDirectory "windows_service.py"
    if (Test-Path $serviceScriptPath) {
        & $PythonPath $serviceScriptPath remove
        if ($LASTEXITCODE -eq 0) {
            Write-ColorOutput "Windows Service removed successfully" "Green"
        } else {
            throw "Service removal failed"
        }
    } else {
        Write-ColorOutput "Service script not found, attempting manual removal..." "Yellow"
        # Manual removal using sc.exe
        & sc.exe delete $ServiceName
        if ($LASTEXITCODE -eq 0) {
            Write-ColorOutput "Service removed manually" "Green"
        } else {
            throw "Manual service removal failed"
        }
    }
}
catch {
    Write-ColorOutput "Failed to remove Windows Service: $($_.Exception.Message)" "Red"
    exit 1
}

# Remove environment variables
Write-ColorOutput "Removing environment variables..." "Yellow"
try {
    [Environment]::SetEnvironmentVariable("ZIMRA_HOST", $null, "Machine")
    [Environment]::SetEnvironmentVariable("ZIMRA_PORT", $null, "Machine")
    [Environment]::SetEnvironmentVariable("ZIMRA_THREADS", $null, "Machine")
    [Environment]::SetEnvironmentVariable("FLASK_ENV", $null, "Machine")
    Write-ColorOutput "Environment variables removed" "Green"
}
catch {
    Write-ColorOutput "Failed to remove environment variables: $($_.Exception.Message)" "Red"
}

# Clean up log files (optional)
$logFiles = @(
    "zimra_windows_service.log",
    "zimra_service.log"
)

Write-ColorOutput "Cleaning up log files..." "Yellow"
foreach ($logFile in $logFiles) {
    $logPath = Join-Path $WorkingDirectory $logFile
    if (Test-Path $logPath) {
        try {
            Remove-Item $logPath -Force
            Write-ColorOutput "Removed: $logFile" "Green"
        }
        catch {
            Write-ColorOutput "Failed to remove $logFile: $($_.Exception.Message)" "Yellow"
        }
    }
}

Write-ColorOutput ""
Write-ColorOutput "=== Uninstallation Complete ===" "Green"
Write-ColorOutput ""
Write-ColorOutput "The ZIMRA API Service has been successfully uninstalled." "White"
Write-ColorOutput ""
Write-ColorOutput "Note: Python packages installed via pip are still available." "Yellow"
Write-ColorOutput "To remove them, run: $PythonPath -m pip uninstall -r requirements.txt" "White"
