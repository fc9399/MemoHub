# Integrations router
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
from services.integration_service import integration_service
from services.auth_service import auth_service
from schemas import (
    User, 
    IntegrationAuthUrlRequest, 
    IntegrationAuthUrlResponse,
    IntegrationConnectRequest,
    IntegrationConnectResponse,
    IntegrationListResponse,
    IntegrationSyncResponse
)
from routers.auth import get_current_active_user

router = APIRouter(prefix="/api/integrations", tags=["integrations"])
security = HTTPBearer()

@router.get("/{provider}/auth-url", response_model=IntegrationAuthUrlResponse)
async def get_auth_url(
    provider: str,
    redirect_uri: Optional[str] = None,
    current_user: User = Depends(get_current_active_user)
):
    """Get OAuth authorization URL"""
    if provider not in ['google-drive', 'notion']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported provider: {provider}. Supported: google-drive, notion"
        )
    
    try:
        result = integration_service.get_auth_url(
            user_id=current_user.id,
            provider=provider,
            redirect_uri=redirect_uri
        )
        return IntegrationAuthUrlResponse(**result)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate auth URL: {str(e)}"
        )

@router.post("/{provider}/connect", response_model=IntegrationConnectResponse)
async def connect_integration(
    provider: str,
    request: IntegrationConnectRequest,
    current_user: User = Depends(get_current_active_user)
):
    """Connect integration service (OAuth callback)"""
    if provider not in ['google-drive', 'notion']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported provider: {provider}"
        )
    
    try:
        print(f"🔄 Connecting integration: {provider}, user_id: {current_user.id}")
        integration = await integration_service.connect_integration(
            user_id=current_user.id,
            provider=provider,
            code=request.code,
            state=request.state,
            redirect_uri=request.redirect_uri
        )
        
        print(f"✅ Integration connected successfully: {provider}, integration_id: {integration.id}")
        
        # Don't return sensitive information (access_token, refresh_token)
        integration.access_token = None
        integration.refresh_token = None
        
        return IntegrationConnectResponse(
            success=True,
            integration=integration,
            message=f"{provider} connected successfully"
        )
    except ValueError as e:
        print(f"❌ Connection failed (ValueError): {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        print(f"❌ Connection failed (Exception): {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to connect integration: {str(e)}"
        )

@router.delete("/{provider}/disconnect")
async def disconnect_integration(
    provider: str,
    current_user: User = Depends(get_current_active_user)
):
    """Disconnect integration"""
    if provider not in ['google-drive', 'notion']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported provider: {provider}"
        )
    
    try:
        success = await integration_service.disconnect_integration(
            user_id=current_user.id,
            provider=provider
        )
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Integration not found"
            )
        return {"success": True, "message": f"{provider} disconnected successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to disconnect integration: {str(e)}"
        )

@router.post("/{provider}/sync", response_model=IntegrationSyncResponse)
async def sync_integration(
    provider: str,
    current_user: User = Depends(get_current_active_user)
):
    """Sync integration data"""
    if provider not in ['google-drive', 'notion']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported provider: {provider}"
        )
    
    try:
        result = await integration_service.sync_integration(
            user_id=current_user.id,
            provider=provider
        )
        return IntegrationSyncResponse(**result)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to sync integration: {str(e)}"
        )

@router.get("", response_model=IntegrationListResponse)
async def list_integrations(
    current_user: User = Depends(get_current_active_user)
):
    """Get all user integrations"""
    try:
        integrations = await integration_service.get_user_integrations(
            user_id=current_user.id
        )
        
        # Remove sensitive information
        for integration in integrations:
            integration.access_token = None
            integration.refresh_token = None
        
        return IntegrationListResponse(
            integrations=integrations,
            total=len(integrations)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list integrations: {str(e)}"
        )
