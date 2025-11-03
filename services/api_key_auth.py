# API Key authentication - for read-only API
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional, Dict, Any
from services.api_key_service import api_key_service

security = HTTPBearer()

async def get_user_from_api_key(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Dict[str, Any]:
    """
    Get user information through API Key (read-only permission)
    
    Only allows GET requests, ensuring read-only permission
    """
    api_key = credentials.credentials
    
    # Validate API Key
    api_key_info = api_key_service.validate_api_key(api_key)
    if not api_key_info:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired API key",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return {
        'user_id': api_key_info['user_id'],
        'api_key_id': api_key_info['api_key_id']
    }

