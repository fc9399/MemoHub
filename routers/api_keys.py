# API Keys router
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import List
from schemas import ApiKey, ApiKeyCreate, ApiKeyResponse, ApiKeyListResponse
from services.api_key_service import api_key_service
from services.auth_service import auth_service

router = APIRouter(prefix="/api/api-keys", tags=["API Keys"])
security = HTTPBearer()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """
    Get current user (via JWT token)
    """
    token = credentials.credentials
    try:
        token_data = auth_service.verify_token(token)
        # verify_token returns TokenData, containing username and user_id
        if not token_data.user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return {"user_id": token_data.user_id}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

@router.post("", response_model=ApiKeyResponse, status_code=status.HTTP_201_CREATED)
async def create_api_key(
    key_data: ApiKeyCreate,
    current_user: dict = Depends(get_current_user)
):
    """
    Create new API key
    Note: The complete API key will only be returned once at creation, please keep it safe
    
    You can set an expiration time (expires_at), if not set it will never expire
    """
    user_id = current_user["user_id"]
    response = api_key_service.create_api_key(
        user_id=user_id, 
        name=key_data.name,
        expires_at=key_data.expires_at
    )
    return response

@router.get("", response_model=ApiKeyListResponse)
async def list_api_keys(current_user: dict = Depends(get_current_user)):
    """
    List all API keys for current user
    Note: The returned key list does not include complete keys, only prefixes and metadata
    """
    user_id = current_user["user_id"]
    keys = api_key_service.list_api_keys(user_id=user_id)
    return ApiKeyListResponse(keys=keys, total=len(keys))

@router.delete("/{api_key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_api_key(
    api_key_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Revoke (delete) API key
    """
    user_id = current_user["user_id"]
    api_key_service.revoke_api_key(user_id=user_id, api_key_id=api_key_id)
    return None