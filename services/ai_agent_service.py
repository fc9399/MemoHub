# AI Agent service
from typing import List, Dict, Any, Optional
from datetime import datetime
from services.database_service import database_service
from services.embedding_service import embedding_service
from services.llm_service import llm_service
from utils.text_utils import clean_text, extract_keywords, generate_summary
from utils.memory_utils import calculate_similarity
import json

class AIAgentService:
    """
    AI Agent service - Memory-based reasoning and conversation
    Uses NVIDIA NIM LLM for intelligent dialogue and memory retrieval
    """
    
    def __init__(self):
        self.conversation_history = {}  # Changed to dictionary to store conversation history
        self.max_context_memories = 5
        self.similarity_threshold = 0.1  # Lower threshold to find more relevant memories
    
    async def chat_with_memory(
        self,
        user_input: str,
        user_id: str,
        conversation_id: str = None,
        use_memory: bool = True
    ) -> Dict[str, Any]:
        """
        Memory-based conversation
        
        Args:
            user_input: User input
            user_id: User ID
            conversation_id: Conversation ID
            use_memory: Whether to use memory retrieval
            
        Returns:
            Dict: Conversation response
        """
        try:
            # Clean user input
            cleaned_input = clean_text(user_input)
            
            # If memory retrieval is enabled, search for relevant memories
            relevant_memories = []
            if use_memory:
                relevant_memories = await self._retrieve_relevant_memories(cleaned_input, user_id)
            
            # Build context
            context = self._build_context(relevant_memories, conversation_id)
            
            # Generate response (using NVIDIA NIM LLM)
            response = await self._generate_response(cleaned_input, context, conversation_id)
            
            # Save conversation turn
            self._save_conversation_turn(user_input, response, conversation_id)
            
            # If response contains new information, create memory
            if self._should_create_memory(response):
                await self._create_conversation_memory(user_input, response, user_id, conversation_id)
            
            return {
                'response': response,
                'conversation_id': conversation_id or f"conv_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
                'relevant_memories': relevant_memories,
                'context_used': len(relevant_memories),
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            print(f"❌ Chat failed: {e}")
            return {
                'response': "Sorry, I encountered some issues. Please try again later.",
                'conversation_id': conversation_id or f"conv_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
                'relevant_memories': [],
                'context_used': 0,
                'timestamp': datetime.utcnow().isoformat(),
                'error': str(e)
            }
    
    async def _retrieve_relevant_memories(self, query: str, user_id: str) -> List[Dict[str, Any]]:
        """Retrieve relevant memories"""
        try:
            # Generate query embedding
            query_embedding = embedding_service.generate_embedding(
                text=query,
                input_type="query"
            )
            
            # Search for relevant memories
            search_results = database_service.semantic_search(
                query_embedding=query_embedding,
                user_id=user_id,
                limit=self.max_context_memories,
                threshold=self.similarity_threshold
            )
            
            return search_results
            
        except Exception as e:
            print(f"❌ Memory retrieval failed: {e}")
            return []
    
    def _build_context(self, memories: List[Dict[str, Any]], conversation_id: str = None) -> str:
        """Build conversation context"""
        context_parts = []
        
        # Add relevant memories
        if memories:
            context_parts.append("Relevant memories:")
            for i, memory_data in enumerate(memories, 1):
                memory = memory_data.get('memory', {})
                similarity = memory_data.get('similarity_score', 0)
                
                context_parts.append(
                    f"{i}. {memory.get('summary', memory.get('content', ''))[:100]}... "
                    f"(similarity: {similarity:.2f})"
                )
        
        # Add conversation history
        if conversation_id and conversation_id in self.conversation_history:
            recent_turns = self.conversation_history[conversation_id][-3:]  # Last 3 turns
            if recent_turns:
                context_parts.append("\nRecent conversation:")
                for turn in recent_turns:
                    context_parts.append(f"User: {turn['user_input']}")
                    context_parts.append(f"Assistant: {turn['response']}")
        
        return "\n".join(context_parts)
    
    async def _generate_response(self, user_input: str, context: str, conversation_id: str = None) -> str:
        """Generate AI response (using NVIDIA NIM LLM)"""
        try:
            # Get conversation history
            conversation_history = []
            if conversation_id and conversation_id in self.conversation_history:
                conversation_history = self.conversation_history[conversation_id]
            
            # Use LLM to generate response
            response = llm_service.generate_response(
                user_input=user_input,
                context=context,
                conversation_history=conversation_history
            )
            
            return response
            
        except Exception as e:
            print(f"❌ LLM response generation failed: {e}")
            # Fallback to simplified response
            return await self._fallback_response(user_input, context)
    
    async def _fallback_response(self, user_input: str, context: str) -> str:
        """Fallback response (when LLM is unavailable)"""
        if context:
            return f"I understand what you said. Based on my memories:\n\n{context}\n\nWhat else would you like to know?"
        else:
            return "I hear you. Although I don't have relevant memories, I'm happy to help. You can tell me more."
    
    def _analyze_intent(self, user_input: str) -> str:
        """Analyze user intent"""
        user_input_lower = user_input.lower()
        
        # Search-related keywords
        search_keywords = ['搜索', '查找', '找', 'search', 'find', 'look for']
        if any(keyword in user_input_lower for keyword in search_keywords):
            return "search"
        
        # Question-related keywords
        question_keywords = ['什么', '怎么', '为什么', '如何', 'what', 'how', 'why', 'when', 'where']
        if any(keyword in user_input_lower for keyword in question_keywords):
            return "question"
        
        # Memory-related keywords
        memory_keywords = ['记得', '记忆', '之前', 'remember', 'memory', 'before']
        if any(keyword in user_input_lower for keyword in memory_keywords):
            return "memory"
        
        return "general"
    
    async def _handle_search_intent(self, user_input: str, context: str) -> str:
        """Handle search intent"""
        if context:
            return f"Based on my memories, I found the following relevant information:\n\n{context}\n\nThis information may be helpful."
        else:
            return "I didn't find any memories related to your search. You can upload documents or records to help me learn more."
    
    async def _handle_question_intent(self, user_input: str, context: str) -> str:
        """Handle question intent"""
        if context:
            return f"Based on my memories, I can answer your question:\n\n{context}\n\nIf you need more detailed information, please let me know."
        else:
            return "I don't currently have enough information to answer your question. You can provide more context or upload relevant documents."
    
    async def _handle_memory_intent(self, user_input: str, context: str) -> str:
        """Handle memory intent"""
        if context:
            return f"Yes, I remember this information:\n\n{context}\n\nThese are what I learned before."
        else:
            return "I didn't find relevant memories. You can tell me more information and I'll remember it."
    
    async def _handle_general_intent(self, user_input: str, context: str) -> str:
        """Handle general intent"""
        if context:
            return f"I understand what you said. Based on my memories:\n\n{context}\n\nWhat else would you like to know?"
        else:
            return "I hear you. Although I don't have relevant memories, I'm happy to help. You can tell me more."
    
    def _should_create_memory(self, response: str) -> bool:
        """Determine whether to create memory"""
        # Create memory if response contains new information or user provided valuable content
        return len(response) > 50 and "memory" not in response.lower()
    
    async def _create_conversation_memory(
        self,
        user_input: str,
        response: str,
        user_id: str,
        conversation_id: str = None
    ) -> str:
        """Create conversation memory"""
        try:
            # Combine user input and AI response
            conversation_text = f"User: {user_input}\nAssistant: {response}"
            
            # Generate embedding
            embedding = embedding_service.generate_embedding(
                text=conversation_text,
                input_type="passage"
            )
            
            # Create memory
            memory_id = database_service.create_memory(
                content=conversation_text,
                memory_type='conversation',
                embedding=embedding,
                user_id=user_id,
                metadata={
                    'conversation_id': conversation_id,
                    'user_input': user_input,
                    'ai_response': response,
                    'source': 'ai_agent'
                },
                source=f"conversation_{conversation_id}" if conversation_id else "ai_agent",
                summary=generate_summary(conversation_text, 100),
                tags=['conversation', 'ai_chat']
            )
            
            return memory_id
            
        except Exception as e:
            print(f"❌ Failed to create conversation memory: {e}")
            return None
    
    def _save_conversation_turn(
        self,
        user_input: str,
        response: str,
        conversation_id: str = None
    ):
        """Save conversation turn"""
        if not conversation_id:
            conversation_id = f"conv_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        
        if conversation_id not in self.conversation_history:
            self.conversation_history[conversation_id] = []
        
        self.conversation_history[conversation_id].append({
            'user_input': user_input,
            'response': response,
            'timestamp': datetime.utcnow().isoformat()
        })
        
        # Limit history length
        if len(self.conversation_history[conversation_id]) > 20:
            self.conversation_history[conversation_id] = self.conversation_history[conversation_id][-20:]
    
    async def get_conversation_history(self, conversation_id: str) -> List[Dict[str, Any]]:
        """Get conversation history"""
        return self.conversation_history.get(conversation_id, [])
    
    async def clear_conversation_history(self, conversation_id: str = None):
        """Clear conversation history"""
        if conversation_id:
            if conversation_id in self.conversation_history:
                del self.conversation_history[conversation_id]
        else:
            self.conversation_history.clear()
    
    def health_check(self) -> Dict[str, Any]:
        """Health check"""
        llm_health = llm_service.health_check()
        
        return {
            'status': 'healthy' if llm_health['status'] == 'healthy' else 'degraded',
            'active_conversations': len(self.conversation_history),
            'total_turns': sum(len(conv) for conv in self.conversation_history.values()),
            'max_context_memories': self.max_context_memories,
            'similarity_threshold': self.similarity_threshold,
            'llm_status': llm_health['status'],
            'llm_model': llm_health.get('model', 'unknown'),
            'llm_api_available': llm_health.get('api_available', False)
        }

# Global instance
ai_agent_service = AIAgentService()