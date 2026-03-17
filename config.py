import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'a-very-strong-secret-key-in-case-env-is-not-set'
    MYSQL_HOST = os.environ.get('MYSQL_HOST') or 'localhost'
    # 加上默认的用户名 xgy
    MYSQL_USER = os.environ.get('MYSQL_USER') or 'xgy'
    # 加上默认的密码
    MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD') or '197111226716'
    MYSQL_DB = os.environ.get('MYSQL_DB') or 'recipe_website'
    
    SQLALCHEMY_DATABASE_URI = f'mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}/{MYSQL_DB}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # 加上默认的百炼 API Key
    DASHSCOPE_API_KEY = os.environ.get('DASHSCOPE_API_KEY') or 'sk-10da423f54e44c3ea22f28bb60b1f920'