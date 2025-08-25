from flask import Flask, send_from_directory
import logging
from flask_sqlalchemy import SQLAlchemy  # ✅ This import is required
from flask_migrate import Migrate

db = SQLAlchemy()
migrate = Migrate()
def create_app():
    app = Flask(__name__, static_folder='static', static_url_path='/static')

    # Configure Logging
    logging.basicConfig(level=logging.DEBUG, 
                        format='[%(asctime)s] %(levelname)s in %(module)s: %(message)s')  # or INFO, ERROR
    app.logger.setLevel(logging.DEBUG)

    # Configure SECRET_KEY for security
    import os
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or 'your-secret-key-here-change-in-production'

        # Example for SQLite
   # app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///zimra.db'
    #app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    app.config['SQLALCHEMY_DATABASE_URI'] =  "postgresql+psycopg2://postgres:%40gr1ff1n%23@localhost/zimra_api_db"
#'postgresql://postgres:@gr1ff1n#@localhost:5432/zimra_api_db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)
    migrate.init_app(app,db)
    
    # Register API blueprint
    from .routes import api
    app.register_blueprint(api, url_prefix='/api')

    # Add root route to serve index.html
    @app.route('/')
    def index():
        """Serve the main index page"""
        try:
            with open('static/index.html', 'r', encoding='utf-8') as f:
                html_content = f.read()
            return html_content, 200, {'Content-Type': 'text/html'}
        except FileNotFoundError:
            return {"error": "Index file not found"}, 404
        except Exception as e:
            return {"error": "Failed to load index", "details": str(e)}, 500

    # Add route to serve invoices.html directly
    @app.route('/invoices')
    def invoices():
        """Serve the invoices page"""
        try:
            with open('static/invoices.html', 'r', encoding='utf-8') as f:
                html_content = f.read()
            return html_content, 200, {'Content-Type': 'text/html'}
        except FileNotFoundError:
            return {"error": "Invoices file not found"}, 404
        except Exception as e:
            return {"error": "Failed to load invoices", "details": str(e)}, 500

    # Add route to serve static files from static_files directory
    @app.route('/static_files/<path:filename>')
    def serve_static_files(filename):
        """Serve static files from static_files directory"""
        import os
        static_files_dir = os.path.join(os.getcwd(), 'static_files')
        return send_from_directory(static_files_dir, filename)

    from .models import FiscalDay 
    from .models import DeviceInfo
    from .models import DeviceConfiguration 

    with app.app_context():
        db.create_all()  # create tables here
   
   
    return app
