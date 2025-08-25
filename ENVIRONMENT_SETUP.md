# Environment Configuration Guide

## SECRET_KEY Setup

The `SECRET_KEY` is a critical security configuration for your Flask application. Here's how to set it up properly:

### 1. Generate a Secure SECRET_KEY

**Option A: Using Python (Recommended)**
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

**Option B: Using OpenSSL**
```bash
openssl rand -hex 32
```

### 2. Set Environment Variable

**Windows (PowerShell):**
```powershell
$env:SECRET_KEY="your-generated-secret-key-here"
```

**Windows (Command Prompt):**
```cmd
set SECRET_KEY=your-generated-secret-key-here
```

**Linux/Mac:**
```bash
export SECRET_KEY="your-generated-secret-key-here"
```

### 3. Create .env File (Recommended)

Create a `.env` file in your project root:
```env
# Flask Configuration
FLASK_ENV=production
FLASK_APP=run.py

# Security - CHANGE THIS IN PRODUCTION!
SECRET_KEY=your-generated-secret-key-here

# Database Configuration
DATABASE_URL=postgresql+psycopg2://postgres:your_password@localhost/zimra_api_db

# ZIMRA API Configuration
ZIMRA_API_BASE_URL=https://fdmsapitest.zimra.co.zw

# Logging Configuration
LOG_LEVEL=INFO

# Development Settings (set to False in production)
DEBUG=False
```

### 4. Production Deployment

For production deployment, set the SECRET_KEY as an environment variable in your deployment script:

**Windows Service:**
```batch
set SECRET_KEY=your-production-secret-key
python run.py
```

**IIS Configuration:**
Add to your `web.config`:
```xml
<environmentVariables>
    <add name="SECRET_KEY" value="your-production-secret-key" />
</environmentVariables>
```

## Security Best Practices

1. **Never commit SECRET_KEY to version control**
2. **Use different keys for development and production**
3. **Make the key at least 32 characters long**
4. **Use random, unpredictable values**
5. **Rotate keys periodically in production**

## Current Configuration

Your Flask app is now configured to:
- Use the `SECRET_KEY` environment variable if set
- Fall back to a default value (change this in production)
- Properly secure sessions, cookies, and CSRF protection

## Testing the Configuration

After setting up your SECRET_KEY, test that it's working:

```bash
python -c "from app import create_app; app = create_app(); print('SECRET_KEY configured:', bool(app.config.get('SECRET_KEY')))"
```

This should output: `SECRET_KEY configured: True`

