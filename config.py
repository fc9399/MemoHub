# config.py
import os
from dotenv import load_dotenv

# Load from .env file first, override=True ensures .env file overrides system environment variables
load_dotenv(override=True)

class Settings:
    # AWS Configuration
    AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
    AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')
    S3_BUCKET_NAME = os.getenv('S3_BUCKET_NAME')
    
    # NVIDIA NIM Configuration
    ENVIRONMENT = os.getenv('ENVIRONMENT', 'development')  # development or production
    NVIDIA_API_KEY = os.getenv('NVIDIA_API_KEY')
    
    # Development environment: use NVIDIA hosted API
    NVIDIA_API_BASE_URL = "https://integrate.api.nvidia.com/v1"
    
    # Production environment: use self-deployed NIM
    NIM_EMBEDDING_URL = os.getenv('NIM_EMBEDDING_URL', 'http://embedding-nim.nim-service:8000/v1')
    
    # Embedding model configuration
    EMBEDDING_MODEL = "nvidia/llama-3.2-nv-embedqa-1b-v2"
    EMBEDDING_DIMENSION = 2048
    
    # File upload configuration
    ALLOWED_EXTENSIONS = {'pdf', 'docx', 'txt', 'png', 'jpg', 'jpeg', 'gif', 'md'}
    MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB
    
    # User authentication configuration
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-here-change-in-production')
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 30
    REFRESH_TOKEN_EXPIRE_DAYS = 7
    
    # Integrations OAuth configuration
    # Frontend base URL (used to dynamically build redirect_uri)
    FRONTEND_URL = os.getenv('FRONTEND_URL', 'http://localhost:3001')
    
    # Google Drive OAuth
    GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID', '')
    GOOGLE_CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET', '')
    # Prioritize FRONTEND_URL, use GOOGLE_REDIRECT_URI if set
    _google_redirect = os.getenv('GOOGLE_REDIRECT_URI')
    if _google_redirect:
        GOOGLE_REDIRECT_URI = _google_redirect
    else:
        GOOGLE_REDIRECT_URI = f"{FRONTEND_URL}/api/integrations/google-drive/callback"
    
    # Notion OAuth
    NOTION_CLIENT_ID = os.getenv('NOTION_CLIENT_ID', '')
    NOTION_CLIENT_SECRET = os.getenv('NOTION_CLIENT_SECRET', '')
    # Prioritize FRONTEND_URL, use NOTION_REDIRECT_URI if set
    _notion_redirect = os.getenv('NOTION_REDIRECT_URI')
    if _notion_redirect:
        NOTION_REDIRECT_URI = _notion_redirect
    else:
        NOTION_REDIRECT_URI = f"{FRONTEND_URL}/api/integrations/notion/callback"
    
    # OAuth base configuration
    OAUTH_STATE_SECRET = os.getenv('OAUTH_STATE_SECRET', SECRET_KEY)  # Used to generate OAuth state

settings = Settings()