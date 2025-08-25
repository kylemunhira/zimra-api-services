#!/usr/bin/env python3
"""
Windows Service for ZIMRA API Service
This module provides Windows Service functionality using pywin32.
"""

import os
import sys
import time
import logging
import threading
from pathlib import Path
import win32serviceutil
import win32service
import win32event
import servicemanager
from waitress_server import run_waitress_server

# Configure logging for Windows Service
log_file = Path(__file__).parent / 'zimra_windows_service.log'
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

class ZimraWindowsService(win32serviceutil.ServiceFramework):
    """
    Windows Service class for ZIMRA API Service
    """
    
    _svc_name_ = "ZimraAPIService"
    _svc_display_name_ = "ZIMRA API Service"
    _svc_description_ = "ZIMRA API Service for fiscal device management and invoice processing"
    
    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.stop_event = win32event.CreateEvent(None, 0, 0, None)
        self.server_thread = None
        self.is_running = False
        
    def SvcStop(self):
        """
        Stop the Windows Service
        """
        logger.info("Stopping ZIMRA API Service...")
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.stop_event)
        self.is_running = False
        
    def SvcDoRun(self):
        """
        Run the Windows Service
        """
        logger.info("Starting ZIMRA API Service...")
        self.is_running = True
        self.main()
        
    def main(self):
        """
        Main service loop
        """
        try:
            # Change to the service directory
            service_dir = Path(__file__).parent
            os.chdir(service_dir)
            
            logger.info(f"Service directory: {service_dir}")
            logger.info("Initializing ZIMRA API Service...")
            
            # Start Waitress server in a separate thread
            self.server_thread = threading.Thread(
                target=self._run_waitress_server,
                daemon=True
            )
            self.server_thread.start()
            
            logger.info("ZIMRA API Service started successfully")
            
            # Keep the service running
            while self.is_running:
                time.sleep(1)
                
        except Exception as e:
            logger.error(f"Service error: {e}")
            self.is_running = False
            
    def _run_waitress_server(self):
        """
        Run the Waitress server
        """
        try:
            # Get configuration from environment or use defaults
            host = os.environ.get('ZIMRA_HOST', '0.0.0.0')
            port = int(os.environ.get('ZIMRA_PORT', '5000'))
            threads = int(os.environ.get('ZIMRA_THREADS', '4'))
            
            logger.info(f"Starting Waitress server on {host}:{port}")
            run_waitress_server(host=host, port=port, threads=threads)
            
        except Exception as e:
            logger.error(f"Waitress server error: {e}")
            self.is_running = False

def install_service():
    """
    Install the Windows Service
    """
    try:
        win32serviceutil.InstallService(
            ZimraWindowsService._svc_name_,
            ZimraWindowsService._svc_display_name_,
            ZimraWindowsService._svc_description_,
            startType=win32service.SERVICE_AUTO_START
        )
        print(f"Service '{ZimraWindowsService._svc_display_name_}' installed successfully")
    except Exception as e:
        print(f"Failed to install service: {e}")

def remove_service():
    """
    Remove the Windows Service
    """
    try:
        win32serviceutil.RemoveService(ZimraWindowsService._svc_name_)
        print(f"Service '{ZimraWindowsService._svc_display_name_}' removed successfully")
    except Exception as e:
        print(f"Failed to remove service: {e}")

if __name__ == '__main__':
    if len(sys.argv) == 1:
        servicemanager.Initialize()
        servicemanager.PrepareToHostSingle(ZimraWindowsService)
        servicemanager.StartServiceCtrlDispatcher()
    else:
        win32serviceutil.HandleCommandLine(ZimraWindowsService)
