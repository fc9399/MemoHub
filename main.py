# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from routers import upload_router, embedding_router, search_router, ai_agent_router, auth, integration, api_keys_router
from routers.memos import router as memos_router
from services.s3_service import s3_service
from services.embedding_service import embedding_service
from services.database_service import database_service
from services.ai_agent_service import ai_agent_service
from config import settings

# Configure FastAPI application with authentication persistence
app = FastAPI(
    title="Personal Memory Hub API",
    description="AWS & NVIDIA Hackathon Project - File Upload & Embedding Service",
    version="1.0.0",
    swagger_ui_parameters={
        "persistAuthorization": True,  # Keep users logged in across page refreshes
    }
)

# Custom OpenAPI schema with JWT Bearer authentication
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    
    # Define security schemes for Swagger UI
    openapi_schema["components"]["securitySchemes"] = {
        "HTTPBearer": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "Enter your JWT token in the format: Bearer <token>"
        }
    }
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(auth.router)  # Authentication routes
app.include_router(upload_router)
app.include_router(embedding_router)
app.include_router(search_router)
app.include_router(ai_agent_router)
app.include_router(integration.router)  # Integration routes
app.include_router(api_keys_router)  # API Keys routes
app.include_router(memos_router)  # Read-only Memos API routes

@app.get("/")
def root():
    """Root path - Service information"""
    return {
        "service": "Personal Memory Hub API",
        "version": "1.0.0",
        "environment": settings.ENVIRONMENT,
        "embedding_service": "NIM (Production)" if settings.ENVIRONMENT == "production" else "NVIDIA API (Development)",
        "endpoints": {
            "upload": "/api/upload",
            "upload_text": "/api/upload/text",
            "embedding": "/api/embeddings/generate",
            "batch_embedding": "/api/embeddings/batch",
            "search": "/api/search/semantic",
            "memories": "/api/search/memories",
            "chat": "/api/agent/chat",
            "conversations": "/api/agent/conversations",
            "api_keys": "/api/api-keys",
            "memos": "/api/memos",
            "memos_search": "/api/memos/search",
            "health": "/health",
            "docs": "/docs"
        }
    }

@app.get("/health")
async def health_check():
    """Overall health check"""
    
    # Check S3 service
    s3_health = s3_service.health_check()
    
    # Check Embedding service
    embedding_health = embedding_service.health_check()
    
    # Check Database service
    database_health = database_service.health_check()
    
    # Check AI Agent service
    ai_agent_health = ai_agent_service.health_check()
    
    # Determine overall status
    overall_status = "healthy" if (
        s3_health["status"] == "healthy" and 
        embedding_health["status"] == "healthy" and
        database_health["status"] in ["healthy", "degraded"] and  # Allow degraded status
        ai_agent_health["status"] in ["healthy", "degraded"]  # Allow degraded status
    ) else "unhealthy"
    
    return {
        "status": overall_status,
        "environment": settings.ENVIRONMENT,
        "services": {
            "s3": s3_health,
            "embedding": embedding_health,
            "database": database_health,
            "ai_agent": ai_agent_health
        }
    }

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting Personal Memory Hub API...")
    print(f"📦 S3 Bucket: {settings.S3_BUCKET_NAME}")
    print(f"🌍 AWS Region: {settings.AWS_REGION}")
    print(f"🔧 Environment: {settings.ENVIRONMENT}")
    print(f"🤖 Embedding Model: {settings.EMBEDDING_MODEL}")
    uvicorn.run(app, host="0.0.0.0", port=8012)












