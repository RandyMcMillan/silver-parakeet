import os
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix
import json

# Set up logging
logging.basicConfig(level=logging.DEBUG)

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

# create the app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET") or os.urandom(24)
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# configure the database with error handling
database_url = os.environ.get("DATABASE_URL", "sqlite:///route_optimizer.db")
app.config["SQLALCHEMY_DATABASE_URI"] = database_url
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
    "pool_timeout": 30,  # Add timeout for connections
    "max_overflow": 10,  # Handle connection overflow
}

# Add database connection error handling
try:
    # Test database connection
    from sqlalchemy import create_engine
    test_engine = create_engine(database_url)
    test_connection = test_engine.connect()
    test_connection.close()
    logging.info(f"Database connection successful: {database_url}")
except Exception as e:
    logging.error(f"Database connection failed: {e}")
    # Don't fail startup, but log the error

# initialize the app with the extension
db.init_app(app)

# Add security headers to all responses
from security_enhancements import add_security_headers

@app.after_request 
def after_request(response):
    return add_security_headers(response)

with app.app_context():
    # Import models to ensure tables are created
    import models
    db.create_all()

# Add custom Jinja2 filter
def from_json(value):
    """Convert JSON string to Python object"""
    try:
        return json.loads(value)
    except (json.JSONDecodeError, TypeError):
        return []

app.jinja_env.filters['from_json'] = from_json

# Register routes after app initialization to avoid circular imports
with app.app_context():
    from routes import main
    app.register_blueprint(main)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
