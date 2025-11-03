# Authentication helper functions - supports JWT Token and API Key
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
from services.auth_service import auth_service
from services.api_key_service import api_key_service
from schemas import User

security = HTTPBearer(auto_error=False)

async def get_current_user_any(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> User:
    """
    Get current user - supports JWT Token or API Key
    
    Authentication priority:
    1. First try JWT Token (usually starts with 'eyJ')
    2. If not JWT, try to validate as API Key
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = credentials.credentials
    
    # Strategy 1: Try to validate as JWT Token
    if token.startswith('eyJ'):  # JWT usually starts with 'eyJ'
        try:
            token_data = auth_service.verify_token(token)
            user = await auth_service.get_user_by_username(token_data.username)
            if user:
                return user
        except:
            pass  # JWT validation failed, continue to try API Key
    
    # Strategy 2: Try to validate as API Key
    api_key_info = api_key_service.validate_api_key(token)
    if api_key_info:
        user = await auth_service.get_user_by_id(api_key_info['user_id'])
        if user:
            return user
    
    # Both methods failed
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

