# Upload router
from fastapi import APIRouter, UploadFile, File, HTTPException, Query, Depends
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from services.s3_service import s3_service
from services.parser_service import parser_service
from services.auth_service import auth_service
from schemas import FileUploadResponse, User
from typing import Optional

router = APIRouter(prefix="/api", tags=["upload"])

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer())) -> User:
    """Get current user"""
    token = credentials.credentials
    token_data = auth_service.verify_token(token)
    user = await auth_service.get_user_by_username(token_data.username)
    
    if user is None:
        raise HTTPException(
            status_code=401,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user

@router.post("/upload", response_model=FileUploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    parse_and_store: bool = True,
    current_user: User = Depends(get_current_user)
):
    """
    Upload file to S3 and optionally parse and store as memory
    
    Parameters:
        file: Uploaded file
        parse_and_store: Whether to parse and store as memory unit
    
    Returns:
        JSON response containing file information and memory ID
    """
    try:
        # Upload to S3
        file_data = await s3_service.upload_file(file)
        
        response_data = {
            "success": True,
            "message": "File uploaded successfully",
            "data": file_data
        }
        
        # If parsing is enabled, parse file and create memory
        if parse_and_store:
            try:
                parse_result = await parser_service.parse_file(file, file_data, current_user.id)
                response_data["memory"] = {
                    "memory_id": parse_result["memory_id"],
                    "parsed_content": parse_result["parsed_content"],
                    "embedding_dimension": parse_result["embedding_dimension"]
                }
                response_data["message"] = "File uploaded and parsed successfully"
            except Exception as parse_error:
                # Parse failure doesn't affect upload, but log the error
                response_data["parse_error"] = str(parse_error)
                response_data["message"] = "File uploaded but parsing failed"
        
        return JSONResponse(
            status_code=200,
            content=response_data
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@router.post("/upload/text")
async def upload_text(
    text: str = Query(..., description="Text content to upload"),
    source: Optional[str] = Query(None, description="Source identifier"),
    current_user: User = Depends(get_current_user)
):
    """
    Upload text content directly and create memory
    
    Parameters:
        text: Text content
        source: Source identifier
    
    Returns:
        JSON response containing memory ID
    """
    try:
        parse_result = await parser_service.parse_text_input(text, source, current_user.id)
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": "Text uploaded and stored as memory",
                "memory_id": parse_result["memory_id"],
                "content": parse_result["content"],
                "embedding_dimension": parse_result["embedding_dimension"]
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Text upload failed: {str(e)}")

@router.get("/upload/supported-types")
async def get_supported_types():
    """
    Get list of supported file types
    """
    try:
        supported_types = parser_service.get_supported_types()
        
        return {
            "supported_types": supported_types,
            "total": len(supported_types)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get supported types: {str(e)}")

@router.get("/upload/health")
async def upload_health_check():
    """Check upload and parse service health status"""
    try:
        s3_health = s3_service.health_check()
        parser_health = parser_service.health_check()
        
        overall_status = "healthy" if (
            s3_health["status"] == "healthy" and 
            parser_health["status"] == "healthy"
        ) else "unhealthy"
        
        return {
            "status": overall_status,
            "services": {
                "s3": s3_health,
                "parser": parser_health
            }
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }