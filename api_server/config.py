import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """
    Central configuration for Stockadoodle IMS
    """
    
    # Flask configuration
    SECRET_KEY = os.getenv('SECRET_KEY', 'stockadoodle-dev-2025')
    
    # Mongodb configuration
    MONGO_URI = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/')
    DATABASE_NAME = os.getenv('DATABASE_NAME', 'stockadoodle')
    
    # EMAIL/SMTP configuration (for mfa and notification)
    SMTP_HOST = os.getenv('SMTP', 'smtp.gmail.com')
    SMTP_PORT = int(os.getenv('SMTP_PORT', 587))
    SMTP_USERNAME = os.getenv('SMTP_USERNAME', '')
    SMTP_PASSWORD = os.getenv('SMTP_PASSWORD', '')
    SENDER_EMAIL = os.getenv('SENDER_EMAIL', 'noreply@stockadoodle.com')
    
    # MFA configuration
    MFA_CODE_LENGTH = int(os.getenv('MFA_CODE_LENGTH', 6))
    MFA_CODE_EXPIRY_MINUTES = int(os.getenv('MFA_CODE_EXPIRY_MINUTES', 5))
    
    # Manager email for alerts
    MANAGER_EMAIL = os.getenv('MANAGER_EMAIL', 'manager@example.com')
    
    DEBUG = os.getenv('DEBUG', 'True').lower() == 'true'
    TESTING = os.getenv('TESTING', 'False').lower() == 'true'