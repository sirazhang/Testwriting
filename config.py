import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    DASHSCOPE_API_KEY = os.environ.get('DASHSCOPE_API_KEY')
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key'
    DEBUG = True
