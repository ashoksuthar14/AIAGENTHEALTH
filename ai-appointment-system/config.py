import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-here'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///healthcare.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    GEMINI_API_KEY = 'AIzaSyBj4bKJRjfgw2euZObmbK18pIp_TCtKqyw'
    FLASK_DEBUG = True
    TEMPLATES_AUTO_RELOAD = True
    DEEPSEEK_API_KEY = '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'
    DEEPSEEK_MODEL = 'deepseek/deepseek-r1-distill-llama-70b:free'