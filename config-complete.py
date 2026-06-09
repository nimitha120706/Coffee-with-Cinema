"""
Coffee-with-Cinema Configuration System
Centralized configuration management using environment variables
"""

import os
from datetime import timedelta
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Base configuration class"""
    
    # Flask Configuration
    SECRET_KEY = os.getenv('SECRET_KEY', 'coffee-cinema-secret-key-change-in-production-2026')
    DEBUG = os.getenv('DEBUG', 'True').lower() == 'true'
    
    # Session Configuration
    SESSION_TYPE = 'filesystem'
    SESSION_PERMANENT = False
    SESSION_USE_SIGNER = True
    SESSION_COOKIE_SECURE = os.getenv('SESSION_COOKIE_SECURE', 'False').lower() == 'true'
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = timedelta(hours=int(os.getenv('SESSION_LIFETIME_HOURS', '2')))
    
    # Database Configuration
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///coffee_cinema.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = DEBUG
    
    # Ollama Configuration
    OLLAMA_BASE_URL = os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')
    OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'granite3.2:8b')
    OLLAMA_TIMEOUT = int(os.getenv('OLLAMA_TIMEOUT', '120'))
    
    # Feature Flags
    ENABLE_TONE_ANALYSIS = os.getenv('ENABLE_TONE_ANALYSIS', 'True').lower() == 'true'
    ENABLE_COSTUME_DETAILS = os.getenv('ENABLE_COSTUME_DETAILS', 'True').lower() == 'true'
    ENABLE_CHARACTER_ARC_SEPARATION = os.getenv('ENABLE_CHARACTER_ARC_SEPARATION', 'True').lower() == 'true'
    ENABLE_CONSISTENCY_TRACKING = os.getenv('ENABLE_CONSISTENCY_TRACKING', 'True').lower() == 'true'
    ENABLE_TEMPLATE_LIBRARY = os.getenv('ENABLE_TEMPLATE_LIBRARY', 'True').lower() == 'true'
    
    # Generation Parameters
    SCREENPLAY_MAX_TOKENS = int(os.getenv('SCREENPLAY_MAX_TOKENS', '3500'))
    CHARACTER_MAX_TOKENS = int(os.getenv('CHARACTER_MAX_TOKENS', '2500'))
    SOUND_MAX_TOKENS = int(os.getenv('SOUND_MAX_TOKENS', '2500'))
    TONE_MAX_TOKENS = int(os.getenv('TONE_MAX_TOKENS', '800'))
    COSTUME_MAX_TOKENS = int(os.getenv('COSTUME_MAX_TOKENS', '1500'))
    CHARACTER_ARC_MAX_TOKENS = int(os.getenv('CHARACTER_ARC_MAX_TOKENS', '2000'))
    
    # Temperature Settings
    TEMPERATURE_CREATIVE = float(os.getenv('TEMPERATURE_CREATIVE', '0.7'))
    TEMPERATURE_ANALYTICAL = float(os.getenv('TEMPERATURE_ANALYTICAL', '0.4'))
    
    # File & Folder Configuration
    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', 'uploads')
    EXPORT_FOLDER = os.getenv('EXPORT_FOLDER', 'exports')
    LOG_FILE = os.getenv('LOG_FILE', 'logs/app.log')
    MAX_CONTENT_LENGTH = int(os.getenv('MAX_CONTENT_LENGTH', '16777216'))  # 16MB
    ALLOWED_EXPORT_FORMATS = os.getenv('ALLOWED_EXPORT_FORMATS', 'txt,pdf,docx').split(',')
    
    @staticmethod
    def init_app(app):
        """Initialize application with configuration"""
        pass

class DevelopmentConfig(Config):
    """Development environment configuration"""
    DEBUG = True
    TESTING = False

class ProductionConfig(Config):
    """Production environment configuration"""
    DEBUG = False
    SESSION_COOKIE_SECURE = True
    
    @classmethod
    def init_app(cls, app):
        Config.init_app(app)
        
        # Log to stderr in production
        import logging
        from logging import StreamHandler
        file_handler = StreamHandler()
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)

class TestingConfig(Config):
    """Testing environment configuration"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'

# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
