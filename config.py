import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-here'
    MYSQL_HOST = 'localhost'
    MYSQL_USER = 'xgy'
    MYSQL_PASSWORD = '197111226716'
    MYSQL_DB = 'recipe_website'
    SQLALCHEMY_DATABASE_URI = f'mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}/{MYSQL_DB}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # 阿里云百炼 API Key (建议生产环境中仍使用环境变量)
    DASHSCOPE_API_KEY = os.environ.get('DASHSCOPE_API_KEY') or 'sk-10da423f54e44c3ea22f28bb60b1f920'
