# PowerShell script to manage ZIMRA API Service Windows Service
# Run this script as Administrator for start/stop operations

param(
    [Parameter(Mandatory=$true)]
    [ValidateSet("start", "stop", "restart", "status", "logs")]
    [string]$Action,
    
    [string]$ServiceName = "ZimraAPIService",
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

# Get current directory if not specified
if (-not $WorkingDirectory) {
    $WorkingDirectory = Get-Location
}

Write-ColorOutput "=== ZIMRA API Service Manager ===" "Cyan"
Write-ColorOutput ""

# Check if service exists
try {
    $service = Get-Service -Name $ServiceName -ErrorAction Stop
}
catch {
    Write-ColorOutput "Service '$ServiceName' not found!" "Red"
    Write-ColorOutput "Please install the service first using install_windows_service.ps1" "Yellow"
    exit 1
}

switch ($Action.ToLower()) {
    "start" {
        if (-not (Test-Administrator)) {
            Write-ColorOutput "Starting services requires Administrator privileges!" "Red"
            exit 1
        }
        
        if ($service.Status -eq "Running") {
            Write-ColorOutput "Service is already running" "Yellow"
        } else {
            Write-ColorOutput "Starting service..." "Yellow"
            try {
                Start-Service -Name $ServiceName
                Write-ColorOutput "Service started successfully" "Green"
                
                # Wait a moment and check status
                Start-Sleep -Seconds 2
                $service = Get-Service -Name $ServiceName
                Write-ColorOutput "Service Status: $($service.Status)" "White"
            }
            catch {
                Write-ColorOutput "Failed to start service: $($_.Exception.Message)" "Red"
                exit 1
            }
        }
    }
    
    "stop" {
        if (-not (Test-Administrator)) {
            Write-ColorOutput "Stopping services requires Administrator privileges!" "Red"
            exit 1
        }
        
        if ($service.Status -eq "Stopped") {
            Write-ColorOutput "Service is already stopped" "Yellow"
        } else {
            Write-ColorOutput "Stopping service..." "Yellow"
            try {
                Stop-Service -Name $ServiceName -Force
                Write-ColorOutput "Service stopped successfully" "Green"
                
                # Wait a moment and check status
                Start-Sleep -Seconds 2
                $service = Get-Service -Name $ServiceName
                Write-ColorOutput "Service Status: $($service.Status)" "White"
            }
            catch {
                Write-ColorOutput "Failed to stop service: $($_.Exception.Message)" "Red"
                exit 1
            }
        }
    }
    
    "restart" {
        if (-not (Test-Administrator)) {
            Write-ColorOutput "Restarting services requires Administrator privileges!" "Red"
            exit 1
        }
        
        Write-ColorOutput "Restarting service..." "Yellow"
        try {
            Restart-Service -Name $ServiceName -Force
            Write-ColorOutput "Service restarted successfully" "Green"
            
            # Wait a moment and check status
            Start-Sleep -Seconds 3
            $service = Get-Service -Name $ServiceName
            Write-ColorOutput "Service Status: $($service.Status)" "White"
        }
        catch {
            Write-ColorOutput "Failed to restart service: $($_.Exception.Message)" "Red"
            exit 1
        }
    }
    
    "status" {
        Write-ColorOutput "Service Information:" "Yellow"
        Write-ColorOutput "  Name: $($service.Name)" "White"
        Write-ColorOutput "  Display Name: $($service.DisplayName)" "White"
        Write-ColorOutput "  Status: $($service.Status)" "White"
        Write-ColorOutput "  Startup Type: $($service.StartType)" "White"
        Write-ColorOutput "  Service Type: $($service.ServiceType)" "White"
        
        # Show environment variables
        Write-ColorOutput ""
        Write-ColorOutput "Environment Variables:" "Yellow"
        $envVars = @("ZIMRA_HOST", "ZIMRA_PORT", "ZIMRA_THREADS", "FLASK_ENV")
        foreach ($var in $envVars) {
            $value = [Environment]::GetEnvironmentVariable($var, "Machine")
            if ($value) {
                Write-ColorOutput "  $var`: $value" "White"
            } else {
                Write-ColorOutput "  $var`: Not set" "Gray"
            }
        }
        
        # Show service URL if running
        if ($service.Status -eq "Running") {
            $serverHost = [Environment]::GetEnvironmentVariable("ZIMRA_HOST", "Machine")
            if (-not $serverHost) { $serverHost = "0.0.0.0" }
            $port = [Environment]::GetEnvironmentVariable("ZIMRA_PORT", "Machine")
            if (-not $port) { $port = "5000" }
            Write-ColorOutput ""
            Write-ColorOutput "Service URL: http://$serverHost`:$port" "Cyan"
        }
    }
    
    "logs" {
        Write-ColorOutput "Service Log Files:" "Yellow"
        
        $logFiles = @(
            @{Name="Service Log"; Path="zimra_windows_service.log"},
            @{Name="Application Log"; Path="zimra_service.log"}
        )
        
        foreach ($logFile in $logFiles) {
            $logPath = Join-Path $WorkingDirectory $logFile.Path
            if (Test-Path $logPath) {
                $fileInfo = Get-Item $logPath
                Write-ColorOutput "  $($logFile.Name): $($fileInfo.FullName)" "White"
                Write-ColorOutput "    Size: $([math]::Round($fileInfo.Length / 1KB, 2)) KB" "Gray"
                Write-ColorOutput "    Last Modified: $($fileInfo.LastWriteTime)" "Gray"
                
                # Show last 10 lines of the log
                Write-ColorOutput "    Last 10 lines:" "Gray"
                try {
                    $lastLines = Get-Content $logPath -Tail 10 -ErrorAction SilentlyContinue
                    foreach ($line in $lastLines) {
                        Write-ColorOutput "      $line" "Gray"
                    }
                }
                catch {
                    Write-ColorOutput "      Unable to read log file" "Red"
                }
            } else {
                Write-ColorOutput "  $($logFile.Name): Not found" "Red"
            }
            Write-ColorOutput ""
        }
        
        # Show Windows Event Log entries for the service
        Write-ColorOutput "Windows Event Log (last 5 entries):" "Yellow"
        try {
            $events = Get-WinEvent -FilterHashtable @{
                LogName = 'System'
                ProviderName = 'Service Control Manager'
                ID = 7036
            } -MaxEvents 20 | Where-Object { $_.Message -like "*$ServiceName*" } | Select-Object -First 5
            
            if ($events) {
                foreach ($event in $events) {
                    Write-ColorOutput "  $($event.TimeCreated): $($event.Message)" "White"
                }
            } else {
                Write-ColorOutput "  No recent service events found" "Gray"
            }
        }
        catch {
            Write-ColorOutput "  Unable to read Windows Event Log" "Red"
        }
    }
}

Write-ColorOutput ""
Write-ColorOutput "=== Management Complete ===" "Green"
