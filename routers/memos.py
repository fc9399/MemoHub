# Read-only Memos API - For external tools like Claude
from fastapi import APIRouter, Query, HTTPException, status, Depends
from typing import List, Optional
from services.database_service import database_service
from services.embedding_service import embedding_service
from services.api_key_auth import get_user_from_api_key
from schemas import MemoryUnit
from datetime import datetime

router = APIRouter(prefix="/api/memos", tags=["Memos (Read-Only)"])

@router.get("", response_model=List[MemoryUnit])
async def list_memos(
    limit: int = Query(20, ge=1, le=100, description="Limit of returned items"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    memory_type: Optional[str] = Query(None, description="Filter by memory type (text, image, audio, document)"),
    user_info: dict = Depends(get_user_from_api_key)
):
    """
    List all memos (read-only)
    
    Uses API Key authentication, only returns current user's memos
    """
    user_id = user_info['user_id']
    
    try:
        memories = database_service.get_memories(
            user_id=user_id,
            limit=limit,
            offset=offset,
            memory_type=memory_type
        )
        
        # Convert to MemoryUnit format
        result = []
        for mem in memories:
            result.append(MemoryUnit(
                id=mem.get('id', ''),
                content=mem.get('content', ''),
                memory_type=mem.get('memory_type', 'text'),
                metadata=mem.get('metadata', {}),
                created_at=mem.get('created_at', datetime.utcnow().isoformat()),
                updated_at=mem.get('updated_at', datetime.utcnow().isoformat()),
                source=mem.get('source'),
                summary=mem.get('summary'),
                tags=mem.get('tags', [])
            ))
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list memos: {str(e)}"
        )

@router.get("/search")
async def search_memos(
    q: str = Query(..., description="Search keyword"),
    limit: int = Query(10, ge=1, le=50, description="Limit of returned items"),
    user_info: dict = Depends(get_user_from_api_key)
):
    """
    Search memos (read-only)
    
    Uses semantic search, returns most relevant memos
    """
    user_id = user_info['user_id']
    
    try:
        # Generate query embedding
        query_embedding = embedding_service.generate_embedding(
            text=q,
            input_type="passage"
        )
        
        # Search in vector database (use lower threshold to ensure results)
        search_results = database_service.semantic_search(
            query_embedding=query_embedding,
            user_id=user_id,
            limit=limit,
            threshold=0.2  # Use lower threshold
        )
        
        # Convert to simplified format
        result = []
        for item in search_results:
            memory = item.get('memory', {})
            result.append({
                'id': memory.get('id', ''),
                'content': memory.get('content', ''),
                'memory_type': memory.get('memory_type', 'text'),
                'metadata': memory.get('metadata', {}),
                'similarity_score': item.get('similarity_score', 0),
                'created_at': memory.get('created_at', ''),
                'source': memory.get('source'),
                'summary': memory.get('summary'),
                'tags': memory.get('tags', [])
            })
        
        return {
            'query': q,
            'results': result,
            'total': len(result)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to search memos: {str(e)}"
        )

@router.get("/{memo_id}")
async def get_memo(
    memo_id: str,
    user_info: dict = Depends(get_user_from_api_key)
):
    """
    Get single memo details (read-only)
    """
    user_id = user_info['user_id']
    
    try:
        memory = database_service.get_memory_by_id(memo_id)
        
        if not memory:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Memo not found"
            )
        
        # Verify memo belongs to current user
        if memory.get('user_id') != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        # Convert to MemoryUnit format
        return MemoryUnit(
            id=memory.get('id', ''),
            content=memory.get('content', ''),
            memory_type=memory.get('memory_type', 'text'),
            metadata=memory.get('metadata', {}),
            created_at=memory.get('created_at', datetime.utcnow().isoformat()),
            updated_at=memory.get('updated_at', datetime.utcnow().isoformat()),
            source=memory.get('source'),
            summary=memory.get('summary'),
            tags=memory.get('tags', [])
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get memo: {str(e)}"
        )