# Database Service
import json
import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
from config import settings
import boto3
from botocore.exceptions import ClientError
import numpy as np
from schemas import MemoryUnit, SearchResult

class DatabaseService:
    """
    Database Service - manages storage and retrieval of memory units
    Uses DynamoDB for metadata storage, S3 for large files, local storage for vectors (production can integrate Pinecone/Weaviate)
    """
    
    def __init__(self):
        # Check AWS configuration
        if (not settings.AWS_ACCESS_KEY_ID or 
            settings.AWS_ACCESS_KEY_ID == "your_aws_access_key_here" or
            not settings.S3_BUCKET_NAME or
            settings.S3_BUCKET_NAME == "your-s3-bucket-name"):
            raise ValueError("AWS configuration incomplete. Please set AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, and S3_BUCKET_NAME environment variables")
        
        # DynamoDB client
        self.dynamodb = boto3.resource(
            'dynamodb',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_REGION
        )
        
        # Table names
        self.memories_table_name = f"unimem-memories-{settings.ENVIRONMENT}"
        self.embeddings_table_name = f"unimem-embeddings-{settings.ENVIRONMENT}"
        
        # Initialize tables
        self.dynamodb_disabled = False
        self._init_tables()
        
        # In-memory vector store (for fast search)
        self.vector_store = {}
        
        # Load existing vectors from DynamoDB to memory
        self._load_vectors_to_memory()
    
    def _init_tables(self):
        """Initialize DynamoDB tables"""
        try:
            # Check if table exists
            try:
                self.dynamodb.Table(self.memories_table_name).load()
                print(f"📋 Table already exists: {self.memories_table_name}")
            except ClientError as e:
                if e.response['Error']['Code'] == 'ResourceNotFoundException':
                    # Table doesn't exist, try to create
                    print(f"🔨 Creating table: {self.memories_table_name}")
                    memories_table = self.dynamodb.create_table(
                        TableName=self.memories_table_name,
                        KeySchema=[
                            {'AttributeName': 'id', 'KeyType': 'HASH'}
                        ],
                        AttributeDefinitions=[
                            {'AttributeName': 'id', 'AttributeType': 'S'},
                            {'AttributeName': 'created_at', 'AttributeType': 'S'},
                            {'AttributeName': 'memory_type', 'AttributeType': 'S'}
                        ],
                        GlobalSecondaryIndexes=[
                            {
                                'IndexName': 'created_at_index',
                                'KeySchema': [
                                    {'AttributeName': 'created_at', 'KeyType': 'HASH'}
                                ],
                                'Projection': {'ProjectionType': 'ALL'}
                            },
                            {
                                'IndexName': 'memory_type_index',
                                'KeySchema': [
                                    {'AttributeName': 'memory_type', 'KeyType': 'HASH'},
                                    {'AttributeName': 'created_at', 'KeyType': 'RANGE'}
                                ],
                                'Projection': {'ProjectionType': 'ALL'}
                            }
                        ],
                        BillingMode='PAY_PER_REQUEST'
                    )
                    print(f"✅ Table created: {self.memories_table_name}")
                else:
                    print(f"❌ Error checking table {self.memories_table_name}: {e}")
                    raise
            
            # Check vector storage table
            try:
                self.dynamodb.Table(self.embeddings_table_name).load()
                print(f"📋 Table already exists: {self.embeddings_table_name}")
            except ClientError as e:
                if e.response['Error']['Code'] == 'ResourceNotFoundException':
                    # Table doesn't exist, try to create
                    print(f"🔨 Creating table: {self.embeddings_table_name}")
                    embeddings_table = self.dynamodb.create_table(
                        TableName=self.embeddings_table_name,
                        KeySchema=[
                            {'AttributeName': 'id', 'KeyType': 'HASH'}
                        ],
                        AttributeDefinitions=[
                            {'AttributeName': 'id', 'AttributeType': 'S'}
                        ],
                        BillingMode='PAY_PER_REQUEST'
                    )
                    print(f"✅ Table created: {self.embeddings_table_name}")
                else:
                    print(f"❌ Error checking table {self.embeddings_table_name}: {e}")
                    raise
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'AccessDeniedException':
                print(f"⚠️  Access denied accessing DynamoDB. Please ensure your AWS user has DynamoDB permissions.")
                print(f"   Required permissions: CreateTable, DescribeTable, PutItem, GetItem, UpdateItem, DeleteItem, Query, Scan")
                print(f"   Or manually create tables: {self.memories_table_name}, {self.embeddings_table_name}")
                print(f"   Continuing without DynamoDB functionality...")
                self.dynamodb = None
                self.dynamodb_disabled = True
            else:
                print(f"❌ Error with tables: {e}")
                raise
    
    def _load_vectors_to_memory(self):
        """Load vectors from DynamoDB to memory"""
        if self.dynamodb_disabled:
            print("⚠️  DynamoDB disabled, skipping vector loading")
            return
            
        try:
            vectors_table = self.dynamodb.Table(self.embeddings_table_name)
            response = vectors_table.scan()
            
            loaded_count = 0
            for item in response.get('Items', []):
                memory_id = item['id']
                decimal_embedding = item['embedding']
                
                # Convert Decimal back to float
                float_embedding = [float(x) for x in decimal_embedding]
                
                # Store in memory vector store
                self.vector_store[memory_id] = {
                    'embedding': np.array(float_embedding),
                    'memory_id': memory_id,
                    'user_id': item.get('user_id')  # ✅ Add this line!
                }
                loaded_count += 1
            
            print(f"✅ Loaded {loaded_count} vectors from DynamoDB to memory")
            
        except Exception as e:
            print(f"⚠️  Failed to load vectors from DynamoDB: {e}")
            # Don't throw exception, allow system to continue
    
    def create_memory(
        self,
        content: str,
        memory_type: str,
        embedding: List[float],
        user_id: str,
        metadata: Dict[str, Any] = None,
        source: str = None,
        summary: str = None,
        tags: List[str] = None
    ) -> str:
        """
        Create new memory unit
        
        Args:
            content: Memory content
            memory_type: Memory type (text, image, audio, document)
            embedding: Vector embedding
            user_id: User ID
            metadata: Metadata
            source: Source
            summary: Summary
            tags: Tags
            
        Returns:
            str: Memory ID
        """
        if self.dynamodb_disabled:
            print("⚠️  DynamoDB disabled, memory not persisted")
            return None
            
        memory_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()
        
        # Prepare memory data
        memory_data = {
            'id': memory_id,
            'user_id': user_id,
            'content': content,
            'memory_type': memory_type,
            'metadata': metadata or {},
            'created_at': now,
            'updated_at': now,
            'source': source,
            'summary': summary,
            'tags': tags or []
        }
        
        # Prepare vector data - convert float to Decimal
        from decimal import Decimal
        
        # Convert floats in embedding to Decimal
        decimal_embedding = [Decimal(str(float(x))) for x in embedding]
        
        vector_data = {
            'id': memory_id,
            'user_id': user_id,
            'embedding': decimal_embedding,  # Store Decimal type vector
            'memory_id': memory_id,
            'created_at': now
        }
        
        # Store to database
        try:
            # Store memory metadata in DynamoDB
            memories_table = self.dynamodb.Table(self.memories_table_name)
            memories_table.put_item(Item=memory_data)
            
            # Store vector data in DynamoDB
            vectors_table = self.dynamodb.Table(self.embeddings_table_name)
            vectors_table.put_item(Item=vector_data)
            
            # Also store in memory (for fast search)
            self.vector_store[memory_id] = {
                'embedding': np.array(embedding),
                'memory_id': memory_id,
                'user_id': user_id 
            }
            
            print(f"✅ Memory created: {memory_id}")
            print(f"✅ Vector stored: {len(embedding)} dimensions")
            return memory_id
            
        except Exception as e:
            print(f"❌ Failed to create memory: {e}")
            raise
    
    def semantic_search(
        self,
        query_embedding: List[float],
        user_id: str,
        limit: int = 10,
        threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        """
        Semantic search
        
        Args:
            query_embedding: Query vector
            user_id: User ID
            limit: Result limit
            threshold: Similarity threshold
            
        Returns:
            List[Dict]: Search results
        """
        import time
        start_time = time.time()
        
        query_vector = np.array(query_embedding)
        results = []
        
        # Calculate similarity (using cosine similarity)
        print(f"🔍 Searching in {len(self.vector_store)} vectors with threshold {threshold} for user {user_id}")
        
        for memory_id, vector_data in self.vector_store.items():
            # Check if belongs to current user
            if vector_data.get('user_id') != user_id:
                continue
                
            embedding = vector_data['embedding']
            
            # Calculate cosine similarity
            similarity = np.dot(query_vector, embedding) / (
                np.linalg.norm(query_vector) * np.linalg.norm(embedding)
            )
            
            print(f"📊 Memory {memory_id[:8]}... similarity: {similarity:.4f}")
            
            if similarity >= threshold:
                # Get memory metadata
                memory = self.get_memory_by_id(memory_id)
                if memory and memory.get('user_id') == user_id:
                    results.append({
                        'memory': memory,
                        'similarity_score': float(similarity),
                        'search_time': time.time() - start_time
                    })
                    print(f"✅ Added result: {memory_id[:8]}... (similarity: {similarity:.4f})")
                else:
                    print(f"⚠️  Memory not found or not owned by user for {memory_id[:8]}...")
        
        # Sort by similarity
        results.sort(key=lambda x: x['similarity_score'], reverse=True)
        
        return results[:limit]
    
    def get_memory_by_id(self, memory_id: str) -> Optional[Dict[str, Any]]:
        """Get memory by ID"""
        if self.dynamodb_disabled:
            return None
            
        try:
            table = self.dynamodb.Table(self.memories_table_name)
            response = table.get_item(Key={'id': memory_id})
            
            if 'Item' in response:
                return response['Item']
            return None
            
        except Exception as e:
            print(f"❌ Failed to get memory {memory_id}: {e}")
            return None
    
    def get_memories(
        self,
        user_id: str,
        limit: int = 20,
        offset: int = 0,
        memory_type: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get memory list"""
        if self.dynamodb_disabled:
            return []
            
        try:
            table = self.dynamodb.Table(self.memories_table_name)
            
            # Build query parameters
            if memory_type:
                # Use GSI query
                response = table.query(
                    IndexName='memory_type_index',
                    KeyConditionExpression='memory_type = :mt',
                    FilterExpression='user_id = :user_id',
                    ExpressionAttributeValues={
                        ':mt': memory_type,
                        ':user_id': user_id
                    },
                    Limit=limit,
                    ScanIndexForward=False  # Descending order by time
                )
            else:
                # Scan table
                filter_expression = 'user_id = :user_id'
                expression_values = {':user_id': user_id}
                
                if start_date and end_date:
                    filter_expression += ' AND created_at BETWEEN :start AND :end'
                    expression_values[':start'] = start_date
                    expression_values[':end'] = end_date
                
                response = table.scan(
                    Limit=limit,
                    FilterExpression=filter_expression,
                    ExpressionAttributeValues=expression_values
                )
            
            memories = response.get('Items', [])
            
            # Sort by time
            memories.sort(key=lambda x: x['created_at'], reverse=True)
            
            return memories[offset:offset + limit]
            
        except Exception as e:
            print(f"❌ Failed to get memories: {e}")
            return []
    
    def get_related_memories(
        self,
        memory_id: str,
        user_id: str,  # ✅ Add user_id parameter
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Get related memories"""
        try:
            # 1. Get current memory's vector
            if memory_id not in self.vector_store:
                print(f"⚠️  Memory {memory_id} not found in vector store")
                return []
            
            vector_data = self.vector_store[memory_id]
            
            # 2. Verify user permission
            if vector_data.get('user_id') != user_id:
                print(f"⚠️  Memory {memory_id} does not belong to user {user_id}")
                return []
            
            current_embedding = vector_data['embedding']
            
            # 3. ✅ Search related memories (pass user_id)
            results = self.semantic_search(
                query_embedding=current_embedding.tolist(),
                user_id=user_id,  # ✅ Add user_id parameter
                limit=limit + 1,
                threshold=0.5
            )
            
            # 4. Filter out itself
            related = [r for r in results if r['memory']['id'] != memory_id]
            
            print(f"✅ Found {len(related)} related memories for {memory_id}")
            return related[:limit]
            
        except Exception as e:
            print(f"❌ Failed to get related memories: {e}")
            import traceback
            traceback.print_exc()
            return []

    def delete_memory(self, memory_id: str) -> bool:
        """Delete memory"""
        try:
            # Delete memory metadata
            memories_table = self.dynamodb.Table(self.memories_table_name)
            memories_table.delete_item(Key={'id': memory_id})
            
            # Delete vector data
            vectors_table = self.dynamodb.Table(self.embeddings_table_name)
            vectors_table.delete_item(Key={'id': memory_id})
            
            # Delete from memory vector store
            if memory_id in self.vector_store:
                del self.vector_store[memory_id]
            
            print(f"✅ Memory deleted: {memory_id}")
            print(f"✅ Vector deleted: {memory_id}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to delete memory {memory_id}: {e}")
            return False
    
    def get_search_stats(self) -> Dict[str, Any]:
        """Get search statistics"""
        try:
            # DynamoDB storage mode
            table = self.dynamodb.Table(self.memories_table_name)
            response = table.scan(Select='COUNT')
            
            total_memories = response['Count']
            vector_count = len(self.vector_store)
            
            # Statistics by type
            type_stats = {}
            for memory_id in self.vector_store.keys():
                memory = self.get_memory_by_id(memory_id)
                if memory:
                    memory_type = memory.get('memory_type', 'unknown')
                    type_stats[memory_type] = type_stats.get(memory_type, 0) + 1
            
            return {
                'total_memories': total_memories,
                'vector_count': vector_count,
                'type_distribution': type_stats,
                'storage_mode': 'dynamodb',
                'last_updated': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            print(f"❌ Failed to get stats: {e}")
            return {
                'total_memories': 0,
                'vector_count': 0,
                'type_distribution': {},
                'storage_mode': 'dynamodb',
                'error': str(e)
            }
    
    def health_check(self) -> Dict[str, Any]:
        """Health check"""
        if self.dynamodb_disabled:
            return {
                'status': 'degraded',
                'storage': 'disabled',
                'dynamodb': 'disabled',
                'vector_store': 'active',
                'total_memories': len(self.vector_store),
                'message': 'DynamoDB disabled due to permissions'
            }
            
        try:
            # Check DynamoDB connection
            table = self.dynamodb.Table(self.memories_table_name)
            self.dynamodb.meta.client.describe_table(TableName=self.memories_table_name)
            
            return {
                'status': 'healthy',
                'storage': 'dynamodb',
                'dynamodb': 'connected',
                'vector_store': 'active',
                'total_memories': len(self.vector_store),
                'persistent_storage': 'enabled',
                'memory_type': 'long_term'
            }
            
        except Exception as e:
            return {
                'status': 'unhealthy',
                'storage': 'dynamodb',
                'error': str(e)
            }

# Global instance
database_service = DatabaseService()
