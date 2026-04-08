import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-change-in-production'
    GOOGLE_MAPS_API_KEY = os.environ.get('GOOGLE_MAPS_API_KEY')
    
    # Validate required env vars
    @staticmethod
    def check_config():
        required = ['GOOGLE_MAPS_API_KEY']
        missing = [key for key in required if not getattr(Config, key)]
        if missing:
            raise ValueError(f"Missing env vars: {missing}")
