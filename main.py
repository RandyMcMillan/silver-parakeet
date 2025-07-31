from app import app, db

# Import all models to ensure they're registered
from models import *  # noqa: F401, F403

# Import and register distance cache model
from distance_cache import DistanceCache  # noqa: F401

# Create database tables
with app.app_context():
    db.create_all()
