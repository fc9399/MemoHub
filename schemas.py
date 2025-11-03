# schemas.py
from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import datetime

# File upload related
class FileUploadResponse(BaseModel):
    success: bool
    message: str
    data: dict

# Embedding related
class EmbeddingRequest(BaseModel):
    text: str
    input_type: str = "passage"  # "passage" or "query"

class EmbeddingResponse(BaseModel):
    embedding: List[float]
    dimension: int
    model: str

class BatchEmbeddingRequest(BaseModel):
    texts: List[str]
    input_type: str = "passage"

class BatchEmbeddingResponse(BaseModel):
    embeddings: List[List[float]]
    count: int
    dimension: int

# Search related
class SearchRequest(BaseModel):
    query: str
    limit: int = 10
    threshold: float = 0.2  # Lower default threshold to improve search recall (some words have lower similarity)

class MemoryUnit(BaseModel):
    id: str
    content: str
    memory_type: str  # text, image, audio, document
    embedding: Optional[List[float]] = None  # Optional field, not returned in search
    metadata: dict
    created_at: str
    updated_at: str
    source: Optional[str] = None
    summary: Optional[str] = None
    tags: List[str] = []

class SearchResult(BaseModel):
    memory: MemoryUnit
    similarity_score: float
    search_time: float

class SearchResponse(BaseModel):
    query: str
    results: List[SearchResult]
    total: int
    search_time: float

# AI Agent related
class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    use_memory: bool = True

class ChatResponse(BaseModel):
    response: str
    conversation_id: str
    relevant_memories: List[dict]
    context_used: int
    timestamp: str

# User authentication related
class UserBase(BaseModel):
    username: str
    email: EmailStr
    full_name: Optional[str] = None

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    password: Optional[str] = None

class UserInDB(UserBase):
    id: str
    hashed_password: str
    is_active: bool = True
    created_at: datetime
    updated_at: datetime

class User(UserBase):
    id: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

class UserLogin(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int

class TokenData(BaseModel):
    username: Optional[str] = None
    user_id: Optional[str] = None

# Health check
class HealthCheckResponse(BaseModel):
    status: str
    services: dict

# Integrations related
class IntegrationBase(BaseModel):
    provider: str  # 'google-drive' or 'notion'
    account: Optional[str] = None
    connected: bool = False
    last_sync: Optional[datetime] = None

class IntegrationCreate(IntegrationBase):
    user_id: str

class Integration(IntegrationBase):
    id: str
    user_id: str
    access_token: Optional[str] = None  # Stored encrypted
    refresh_token: Optional[str] = None  # Stored encrypted
    token_expires_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

class IntegrationAuthUrlRequest(BaseModel):
    redirect_uri: Optional[str] = None

class IntegrationAuthUrlResponse(BaseModel):
    auth_url: str
    state: str  # OAuth state parameter for CSRF prevention

class IntegrationConnectRequest(BaseModel):
    code: str
    state: str
    redirect_uri: Optional[str] = None  # Optional: must match the redirect_uri used during authorization

class IntegrationConnectResponse(BaseModel):
    success: bool
    integration: Integration
    message: str

class IntegrationListResponse(BaseModel):
    integrations: List[Integration]
    total: int

class IntegrationSyncResponse(BaseModel):
    success: bool
    message: str
    synced_items: int
    last_sync: datetime

# API Keys related
class ApiKeyBase(BaseModel):
    name: Optional[str] = None  # Optional name/description for the API key
    expires_at: Optional[datetime] = None  # Expiration time (optional)

class ApiKeyCreate(ApiKeyBase):
    pass

class ApiKey(ApiKeyBase):
    id: str
    user_id: str
    key_prefix: str  # Displayed prefix, e.g., "memo_sk_"
    key_hash: str  # Stores hash value, not the original key
    created_at: datetime
    last_used: Optional[datetime] = None
    expires_at: Optional[datetime] = None  # Expiration time
    is_active: bool = True

class ApiKeyResponse(BaseModel):
    id: str
    name: Optional[str] = None
    key: str  # Full key only returned on creation
    key_prefix: str
    created_at: datetime
    last_used: Optional[datetime] = None
    expires_at: Optional[datetime] = None  # Expiration time
    is_active: bool

class ApiKeyListResponse(BaseModel):
    keys: List[ApiKey]
    total: int