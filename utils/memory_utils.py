# Memory-related utility functions
import uuid
import hashlib
from datetime import datetime
from typing import List, Dict, Any
import numpy as np

def generate_memory_id() -> str:
    """Generate unique memory ID"""
    return str(uuid.uuid4())

def generate_content_hash(content: str) -> str:
    """Generate content hash for deduplication"""
    return hashlib.md5(content.encode('utf-8')).hexdigest()

def format_timestamp(timestamp: datetime = None) -> str:
    """Format timestamp"""
    if timestamp is None:
        timestamp = datetime.utcnow()
    return timestamp.isoformat()

def calculate_similarity(embedding1: List[float], embedding2: List[float]) -> float:
    """Calculate cosine similarity between two vectors"""
    vec1 = np.array(embedding1)
    vec2 = np.array(embedding2)
    
    # Calculate cosine similarity
    similarity = np.dot(vec1, vec2) / (
        np.linalg.norm(vec1) * np.linalg.norm(vec2)
    )
    
    return float(similarity)

def create_memory_metadata(
    content: str,
    memory_type: str,
    source: str = None,
    tags: List[str] = None,
    **kwargs
) -> Dict[str, Any]:
    """Create memory metadata"""
    return {
        'content_hash': generate_content_hash(content),
        'memory_type': memory_type,
        'source': source,
        'tags': tags or [],
        'created_at': format_timestamp(),
        'updated_at': format_timestamp(),
        **kwargs
    }

def validate_memory_data(data: Dict[str, Any]) -> bool:
    """Validate memory data format"""
    required_fields = ['content', 'memory_type', 'embedding']
    
    for field in required_fields:
        if field not in data:
            return False
    
    # Verify embedding is a numeric list
    if not isinstance(data['embedding'], list) or not all(
        isinstance(x, (int, float)) for x in data['embedding']
    ):
        return False
    
    return True

def merge_memory_metadata(
    existing: Dict[str, Any],
    new: Dict[str, Any]
) -> Dict[str, Any]:
    """Merge memory metadata"""
    merged = existing.copy()
    
    # Update fields
    for key, value in new.items():
        if key == 'tags' and key in merged:
            # Merge tags
            merged[key] = list(set(merged[key] + value))
        elif key == 'updated_at':
            # Always update modification time
            merged[key] = value
        else:
            merged[key] = value
    
    return merged
