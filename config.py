import os
from urllib.parse import urlparse

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'ckv_college_cep_secret_key_2026_amravati'
    
    # Database Settings (Supports individual env vars or cloud database URL)
    db_url = os.environ.get('MYSQL_URL') or os.environ.get('DATABASE_URL')
    if db_url:
        parsed = urlparse(db_url)
        MYSQL_HOST = parsed.hostname or 'localhost'
        MYSQL_USER = parsed.username or 'root'
        MYSQL_PASSWORD = parsed.password or ''
        MYSQL_DB = parsed.path.lstrip('/') or 'community_knowledge_vault'
        MYSQL_PORT = parsed.port or 3306
    else:
        MYSQL_HOST = os.environ.get('MYSQL_HOST', 'localhost')
        MYSQL_USER = os.environ.get('MYSQL_USER', 'root')
        MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD', 'yash123')
        MYSQL_DB = os.environ.get('MYSQL_DB', 'community_knowledge_vault')
        MYSQL_PORT = int(os.environ.get('MYSQL_PORT', 3306))

    # File Uploads Configuration
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
    ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'webp'}
    MAX_CONTENT_LENGTH = 25 * 1024 * 1024  # 25 MB max limit
