# AI Agent router
from fastapi import APIRouter, HTTPException, Query, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional, List
from services.ai_agent_service import ai_agent_service
from services.auth_service import auth_service
from schemas import ChatRequest, ChatResponse, User
from pydantic import BaseModel

router = APIRouter(prefix="/api/agent", tags=["ai_agent"])

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

@router.post("/chat", response_model=ChatResponse)
async def chat_with_agent(request: ChatRequest, current_user: User = Depends(get_current_user)):
    """
    Chat with AI Agent
    
    Example:
        POST /api/agent/chat
        {
            "message": "What did we discuss last week?",
            "conversation_id": "conv_123",
            "use_memory": true
        }
    """
    try:
        result = await ai_agent_service.chat_with_memory(
            user_input=request.message,
            user_id=current_user.id,
            conversation_id=request.conversation_id,
            use_memory=request.use_memory
        )
        
        return ChatResponse(
            response=result['response'],
            conversation_id=result['conversation_id'],
            relevant_memories=result.get('relevant_memories', []),
            context_used=result.get('context_used', 0),
            timestamp=result['timestamp']
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat failed: {str(e)}")

@router.get("/conversations")
async def get_all_conversations():
    """
    Get all conversation list
    """
    try:
        conversations = []
        for conv_id, history in ai_agent_service.conversation_history.items():
            conversations.append({
                "conversation_id": conv_id,
                "turn_count": len(history),
                "last_activity": history[-1]["timestamp"] if history else None
            })
        
        return {
            "conversations": conversations,
            "total": len(conversations)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get conversations: {str(e)}")

@router.get("/conversations/{conversation_id}/history")
async def get_conversation_history(conversation_id: str):
    """
    Get conversation history
    """
    try:
        history = await ai_agent_service.get_conversation_history(conversation_id)
        
        return {
            "conversation_id": conversation_id,
            "history": history,
            "total_turns": len(history)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get history: {str(e)}")

@router.delete("/conversations/{conversation_id}")
async def clear_conversation(conversation_id: str):
    """
    Clear specific conversation history
    """
    try:
        await ai_agent_service.clear_conversation_history(conversation_id)
        
        return {
            "success": True,
            "message": f"Conversation {conversation_id} cleared"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clear conversation: {str(e)}")

@router.delete("/conversations")
async def clear_all_conversations():
    """
    Clear all conversation history
    """
    try:
        await ai_agent_service.clear_conversation_history()
        
        return {
            "success": True,
            "message": "All conversations cleared"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clear conversations: {str(e)}")

@router.get("/conversations")
async def list_conversations():
    """
    List all conversations
    """
    try:
        conversations = list(ai_agent_service.conversation_history.keys())
        
        return {
            "conversations": conversations,
            "total": len(conversations)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list conversations: {str(e)}")

@router.get("/health")
async def agent_health_check():
    """Check AI Agent service health status"""
    return ai_agent_service.health_check()
