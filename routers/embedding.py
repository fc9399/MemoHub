# Embedding router
from fastapi import APIRouter, HTTPException
from services.embedding_service import embedding_service
from schemas import (
    EmbeddingRequest, 
    EmbeddingResponse,
    BatchEmbeddingRequest,
    BatchEmbeddingResponse
)

router = APIRouter(prefix="/api/embeddings", tags=["embeddings"])

@router.post("/generate", response_model=EmbeddingResponse)
async def generate_embedding(request: EmbeddingRequest):
    """
    Generate embedding for single text
    
    Example:
        POST /api/embeddings/generate
        {
            "text": "What is the capital of France?",
            "input_type": "query"
        }
    """
    try:
        embedding = embedding_service.generate_embedding(
            text=request.text,
            input_type=request.input_type
        )
        return {
            "embedding": embedding,
            "dimension": len(embedding),
            "model": embedding_service.model
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/batch", response_model=BatchEmbeddingResponse)
async def generate_batch_embeddings(request: BatchEmbeddingRequest):
    """
    Generate embeddings in batch
    
    Example:
        POST /api/embeddings/batch
        {
            "texts": ["text1", "text2", "text3"],
            "input_type": "passage"
        }
    """
    try:
        embeddings = embedding_service.generate_embeddings_batch(
            texts=request.texts,
            input_type=request.input_type
        )
        return {
            "embeddings": embeddings,
            "count": len(embeddings),
            "dimension": len(embeddings[0]) if embeddings else 0
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def embedding_health_check():
    """Check Embedding service health status"""
    return embedding_service.health_check()