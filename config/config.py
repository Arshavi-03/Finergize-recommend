import os
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

class Config:
    """Base configuration object"""
    # API settings
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    
    # OpenAI API configuration
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
    USE_OPENAI = os.environ.get('USE_OPENAI', 'True').lower() == 'true'
    
    # Model settings
    MODEL_PATH = os.environ.get('MODEL_PATH', 'models/finergize_recommender_agent_clean.joblib')
    
    # Debug settings
    DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'
    
    # Rate limiting
    RATE_LIMIT = int(os.environ.get('RATE_LIMIT', '100'))

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True

config_by_name = {
    'development': DevelopmentConfig,
    'production': ProductionConfig
}