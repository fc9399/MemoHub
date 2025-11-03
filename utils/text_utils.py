# Text processing utility functions
import re
import string
from typing import List, Dict, Any
from collections import Counter

def clean_text(text: str) -> str:
    """Clean text content"""
    if not text:
        return ""
    
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Remove special characters but keep basic punctuation
    text = re.sub(r'[^\w\s.,!?;:()\-]', '', text)
    
    # Strip leading and trailing whitespace
    text = text.strip()
    
    return text

def extract_keywords(text: str, max_keywords: int = 10) -> List[str]:
    """Extract keywords"""
    if not text:
        return []
    
    # Convert to lowercase
    text = text.lower()
    
    # Remove punctuation
    text = text.translate(str.maketrans('', '', string.punctuation))
    
    # Split into words
    words = text.split()
    
    # Filter stop words (simplified version)
    stop_words = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
        'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
        'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
        'should', 'may', 'might', 'must', 'can', 'this', 'that', 'these',
        'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him',
        'her', 'us', 'them', 'my', 'your', 'his', 'her', 'its', 'our', 'their'
    }
    
    # Filter words
    filtered_words = [
        word for word in words 
        if len(word) > 2 and word not in stop_words
    ]
    
    # Calculate word frequency
    word_counts = Counter(filtered_words)
    
    # Return most common words
    return [word for word, count in word_counts.most_common(max_keywords)]

def generate_summary(text: str, max_length: int = 200) -> str:
    """Generate text summary"""
    if not text:
        return ""
    
    # Clean text
    cleaned_text = clean_text(text)
    
    # If text length is less than max length, return directly
    if len(cleaned_text) <= max_length:
        return cleaned_text
    
    # Truncate to max length and add ellipsis
    summary = cleaned_text[:max_length].rstrip()
    
    # Ensure we don't truncate in the middle of a word
    last_space = summary.rfind(' ')
    if last_space > max_length * 0.8:  # If last space position is reasonable
        summary = summary[:last_space]
    
    return summary + "..."

def extract_entities(text: str) -> Dict[str, List[str]]:
    """Extract entities (simplified version)"""
    entities = {
        'emails': [],
        'urls': [],
        'phone_numbers': [],
        'dates': []
    }
    
    # Extract emails
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    entities['emails'] = re.findall(email_pattern, text)
    
    # Extract URLs
    url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
    entities['urls'] = re.findall(url_pattern, text)
    
    # Extract phone numbers (simplified version)
    phone_pattern = r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b'
    entities['phone_numbers'] = re.findall(phone_pattern, text)
    
    # Extract dates (simplified version)
    date_pattern = r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b'
    entities['dates'] = re.findall(date_pattern, text)
    
    return entities

def calculate_text_similarity(text1: str, text2: str) -> float:
    """Calculate similarity between two texts (based on word overlap)"""
    if not text1 or not text2:
        return 0.0
    
    # Clean text
    clean_text1 = clean_text(text1).lower()
    clean_text2 = clean_text(text2).lower()
    
    # Split into words
    words1 = set(clean_text1.split())
    words2 = set(clean_text2.split())
    
    # Calculate Jaccard similarity
    intersection = len(words1.intersection(words2))
    union = len(words1.union(words2))
    
    if union == 0:
        return 0.0
    
    return intersection / union

def format_text_for_embedding(text: str) -> str:
    """Format text for embedding generation"""
    # Clean text
    cleaned = clean_text(text)
    
    # Limit length (most embedding models have length limits)
    max_length = 8000  # Conservative estimate
    
    if len(cleaned) > max_length:
        cleaned = cleaned[:max_length]
    
    return cleaned
