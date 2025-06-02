from flask_pymongo import PyMongo
import logging

mongo = PyMongo()

def init_db(app):
    """Initialize MongoDB connection with the Flask app"""
    try:
        mongo.init_app(app, uri=app.config["MONGODB_URI"])
        logging.info("MongoDB connection initialized successfully")
        return True
    except Exception as e:
        logging.error(f"Failed to initialize MongoDB connection: {e}")
        return False

def get_db():
    """Get database instance"""
    return mongo.db
