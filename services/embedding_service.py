# Embedding Service
from openai import OpenAI
from typing import List
from config import settings

class EmbeddingService:
    """
    Embedding Service: supports development and production environments
    - Development environment: calls NVIDIA hosted API (for quick testing)
    - Production environment: calls NIM service deployed on AWS EKS
    """
    
    def __init__(self):
        # Check API key
        if not settings.NVIDIA_API_KEY or settings.NVIDIA_API_KEY == "your_nvidia_api_key_here":
            raise ValueError("NVIDIA API key not configured. Please set NVIDIA_API_KEY environment variable")
        
        # Choose different base_url based on environment
        if settings.ENVIRONMENT == "production":
            self.base_url = settings.NIM_EMBEDDING_URL
            print(f"🚀 Using production NIM: {self.base_url}")
        else:
            self.base_url = settings.NVIDIA_API_BASE_URL
            print(f"🔧 Using development API: {self.base_url}")
        
        self.client = OpenAI(
            base_url=self.base_url,
            api_key=settings.NVIDIA_API_KEY
        )
        self.model = settings.EMBEDDING_MODEL
    
    def generate_embedding(
        self, 
        text: str, 
        input_type: str = "passage"
    ) -> List[float]:
        """
        Generate embedding for single text
        
        Args:
            text: Input text
            input_type: "passage" (document) or "query" (query)
        
        Returns:
            List[float]: Embedding vector
        """
        try:
            response = self.client.embeddings.create(
                input=[text],
                model=self.model,
                encoding_format="float",
                extra_body={
                    "input_type": input_type,
                    "truncate": "NONE"
                }
            )
            embedding = response.data[0].embedding
            print(f"✅ Generated embedding, dimension: {len(embedding)}")
            return embedding
        except Exception as e:
            print(f"❌ Embedding generation failed: {str(e)}")
            raise
    
    def generate_embeddings_batch(
        self, 
        texts: List[str], 
        input_type: str = "passage"
    ) -> List[List[float]]:
        """
        Generate embeddings in batch
        
        Args:
            texts: List of texts
            input_type: "passage" or "query"
        
        Returns:
            List[List[float]]: List of embedding vectors
        """
        embeddings = []
        for i, text in enumerate(texts):
            print(f"🔄 Processing {i+1}/{len(texts)}")
            embedding = self.generate_embedding(text, input_type)
            embeddings.append(embedding)
        return embeddings
    
    def health_check(self) -> dict:
        """Health check: test if embedding service is working properly"""
        try:
            test_embedding = self.generate_embedding("health check test", "query")
            return {
                "status": "healthy",
                "environment": settings.ENVIRONMENT,
                "base_url": self.base_url,
                "model": self.model,
                "embedding_dimension": len(test_embedding)
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "environment": settings.ENVIRONMENT,
                "error": str(e)
            }

# Global instance
embedding_service = EmbeddingService()