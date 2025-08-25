-- ZIMRA API Service - PostgreSQL Database Setup Script
-- Run this script as postgres user or superuser

-- Create database
CREATE DATABASE zimra_api_db;

-- Create application user
CREATE USER zimra_user WITH PASSWORD 'your_secure_password_here';

-- Grant privileges to the user
GRANT ALL PRIVILEGES ON DATABASE zimra_api_db TO zimra_user;

-- Connect to the zimra_api_db
\c zimra_api_db;

-- Grant schema privileges
GRANT ALL ON SCHEMA public TO zimra_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO zimra_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO zimra_user;

-- Set default privileges for future objects
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO zimra_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO zimra_user;

-- Create extensions if needed
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Verify setup
SELECT current_database(), current_user;

