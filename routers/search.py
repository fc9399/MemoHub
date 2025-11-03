# Search router
from fastapi import APIRouter, HTTPException, Query, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import List, Optional
from services.database_service import database_service
from services.embedding_service import embedding_service
from services.auth_service import auth_service
from schemas import SearchRequest, SearchResponse, MemoryUnit, User
import json

router = APIRouter(prefix="/api/search", tags=["search"])

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

@router.post("/semantic", response_model=SearchResponse)
async def semantic_search(request: SearchRequest, current_user: User = Depends(get_current_user)):
    """
    Semantic search - Search for relevant content in memory repository
    
    Example:
        POST /api/search/semantic
        {
            "query": "What was discussed in last week's meeting?",
            "limit": 10,
            "threshold": 0.3
        }
    """
    try:
        # Generate query embedding
        # Fixed! For the same text, passage and query similarity is only 0.3992, so change input_type to passage
        query_embedding = embedding_service.generate_embedding(
            text=request.query,
            input_type="passage" # ← Changed to passage
        )
        
        # Search in vector database
        search_results = database_service.semantic_search(
            query_embedding=query_embedding,
            user_id=current_user.id,
            limit=request.limit,
            threshold=request.threshold
        )
        
        # Calculate total search time
        total_search_time = 0
        if search_results:
            total_search_time = search_results[0].get("search_time", 0)
        
        return {
            "query": request.query,
            "results": search_results,
            "total": len(search_results),
            "search_time": total_search_time
        }
        
    except Exception as e:
        import traceback
        error_detail = f"Search failed: {str(e)}\nTraceback: {traceback.format_exc()}"
        print(f"❌ Search error: {error_detail}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@router.get("/memories")
async def get_memories(
    current_user: User = Depends(get_current_user),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    memory_type: Optional[str] = Query(None, description="Filter by memory type"),
    start_date: Optional[str] = Query(None, description="Start date YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="End date YYYY-MM-DD")
):
    """
    Get memory list - Supports pagination and filtering
    
    Parameters:
        limit: Limit of returned items
        offset: Offset
        memory_type: Memory type filter (text, image, audio, document)
        start_date: Start date
        end_date: End date
    """
    try:
        memories = database_service.get_memories(
            user_id=current_user.id,
            limit=limit,
            offset=offset,
            memory_type=memory_type,
            start_date=start_date,
            end_date=end_date
        )
        
        return {
            "memories": memories,
            "total": len(memories),
            "limit": limit,
            "offset": offset
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get memories: {str(e)}")

@router.get("/memories/{memory_id}")
async def get_memory_by_id(memory_id: str):
    """
    Get specific memory details by ID
    """
    try:
        memory = database_service.get_memory_by_id(memory_id)
        if not memory:
            raise HTTPException(status_code=404, detail="Memory not found")
        
        return memory
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get memory: {str(e)}")

@router.post("/memories/{memory_id}/related")
async def get_related_memories(
    memory_id: str,
    limit: int = Query(5, ge=1, le=20),
    current_user: User = Depends(get_current_user)  # ✅ Add user authentication
):
    """
    Get related memories - Based on semantic similarity
    
    Parameters:
        memory_id: Memory ID
        limit: Limit of returned items
        
    Returns:
        List of related memories
    """
    try:
        # 1. Verify memory exists and belongs to current user
        memory = database_service.get_memory_by_id(memory_id)
        if not memory:
            raise HTTPException(status_code=404, detail="Memory not found")
        
        if memory.get('user_id') != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # 2. ✅ Get related memories (pass user_id)
        related_memories = database_service.get_related_memories(
            memory_id=memory_id,
            user_id=current_user.id,  # ✅ Pass user_id
            limit=limit
        )
        
        return {
            "memory_id": memory_id,
            "related_memories": related_memories,
            "count": len(related_memories)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_detail = f"Failed to get related memories: {str(e)}\nTraceback: {traceback.format_exc()}"
        print(f"❌ {error_detail}")
        raise HTTPException(status_code=500, detail=f"Failed to get related memories: {str(e)}")

@router.delete("/memories/{memory_id}")
async def delete_memory(memory_id: str):
    """
    Delete memory
    """
    try:
        success = database_service.delete_memory(memory_id)
        if not success:
            raise HTTPException(status_code=404, detail="Memory not found")
        
        return {
            "success": True,
            "message": f"Memory {memory_id} deleted successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete memory: {str(e)}")

@router.get("/stats")
async def get_search_stats():
    """
    Get search statistics
    """
    try:
        stats = database_service.get_search_stats()
        return stats
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")

@router.get("/health")
async def search_health_check():
    """Check search service health status"""
    return database_service.health_check()
