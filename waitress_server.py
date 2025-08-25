#!/usr/bin/env python3
"""
Waitress Server Configuration for ZIMRA API Service
This file configures Waitress as a production WSGI server for Windows deployment.
"""

import os
import sys
import logging
from waitress import serve
from app import create_app

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
    handlers=[
        logging.FileHandler('zimra_service.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

def create_waitress_app():
    """Create and configure the Flask application for Waitress"""
    try:
        app = create_app()
        logger.info("Flask application created successfully")
        return app
    except Exception as e:
        logger.error(f"Failed to create Flask application: {e}")
        raise

def run_waitress_server(host='0.0.0.0', port=5000, threads=4):
    """
    Run the Waitress server with production settings
    
    Args:
        host (str): Host to bind to (default: 0.0.0.0 for all interfaces)
        port (int): Port to bind to (default: 5000)
        threads (int): Number of threads (default: 4)
    """
    app = create_waitress_app()
    
    logger.info(f"Starting Waitress server on {host}:{port}")
    logger.info(f"Server configuration: threads={threads}")
    
    # Waitress configuration for production
    serve(
        app,
        host=host,
        port=port,
        threads=threads,
        connection_limit=1000,
        cleanup_interval=30,
        channel_timeout=120,
        log_socket_errors=True,
        max_request_body_size=1073741824,  # 1GB
        url_scheme='http'
    )

if __name__ == "__main__":
    # Get configuration from environment variables or use defaults
    host = os.environ.get('ZIMRA_HOST', '0.0.0.0')
    port = int(os.environ.get('ZIMRA_PORT', '5000'))
    threads = int(os.environ.get('ZIMRA_THREADS', '4'))
    
    logger.info("ZIMRA API Service starting...")
    logger.info(f"Environment: {os.environ.get('FLASK_ENV', 'production')}")
    
    try:
        run_waitress_server(host=host, port=port, threads=threads)
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}")
        sys.exit(1)
