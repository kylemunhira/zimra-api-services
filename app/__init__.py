from flask import Flask
import logging
from flask_sqlalchemy import SQLAlchemy  # ✅ This import is required
from flask_migrate import Migrate

db = SQLAlchemy()
migrate = Migrate()
def create_app():
    app = Flask(__name__)

    # Configure Logging
    logging.basicConfig(level=logging.DEBUG, 
                        format='[%(asctime)s] %(levelname)s in %(module)s: %(message)s')  # or INFO, ERROR
    app.logger.setLevel(logging.DEBUG)


        # Example for SQLite
   # app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///zimra.db'
    #app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    app.config['SQLALCHEMY_DATABASE_URI'] =  "postgresql+psycopg2://postgres:%40gr1ff1n%23@localhost/zimra_api_db"
#'postgresql://postgres:@gr1ff1n#@localhost:5432/zimra_api_db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)
    migrate.init_app(app,db)
    
    from .routes import api
    app.register_blueprint(api, url_prefix='/api')

    from .models import FiscalDay 
    from .models import DeviceInfo
    from .models import DeviceConfiguration 

    with app.app_context():
        db.create_all()  # create tables here
   
   
    return app
