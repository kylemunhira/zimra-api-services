@echo off
REM ZIMRA API Service - Manual Start Script
REM This script can be used to start the service manually or as a Windows Service

cd /d C:\inetpub\wwwroot\zimra-api

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Set environment variables
set FLASK_ENV=production
set FLASK_APP=run.py

REM Start the application
python run.py

pause

