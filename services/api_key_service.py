# API Key Service
import uuid
import secrets
import hashlib
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple
from fastapi import HTTPException, status
from config import settings
from schemas import ApiKey, ApiKeyCreate, ApiKeyResponse
import boto3
from botocore.exceptions import ClientError

class ApiKeyService:
    """
    API Key Service - Manages user API keys
    Uses DynamoDB to store API keys (stores hash values, not original keys)
    """
    
    def __init__(self):
        # Check if in test mode
        if settings.ENVIRONMENT == "test":
            self.dynamodb = None
            self.table_name = None
            self.dynamodb_disabled = True
            print("🧪 API Key service running in test mode")
            return
        
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
        
        # API Keys table name
        self.table_name = f"unimem-api-keys-{settings.ENVIRONMENT}"
        
        # Initialize table
        self._init_table()
    
    def _init_table(self):
        """Initialize API Keys table"""
        try:
            # Check if table exists
            try:
                self.dynamodb.Table(self.table_name).load()
                print(f"📋 API Keys table already exists: {self.table_name}")
            except ClientError as e:
                if e.response['Error']['Code'] == 'ResourceNotFoundException':
                    # Table doesn't exist, try to create
                    print(f"🔨 Creating API Keys table: {self.table_name}")
                    api_keys_table = self.dynamodb.create_table(
                        TableName=self.table_name,
                        KeySchema=[
                            {'AttributeName': 'id', 'KeyType': 'HASH'}
                        ],
                        AttributeDefinitions=[
                            {'AttributeName': 'id', 'AttributeType': 'S'},
                            {'AttributeName': 'user_id', 'AttributeType': 'S'},
                            {'AttributeName': 'key_hash', 'AttributeType': 'S'}
                        ],
                        GlobalSecondaryIndexes=[
                            {
                                'IndexName': 'user_id_index',
                                'KeySchema': [
                                    {'AttributeName': 'user_id', 'KeyType': 'HASH'},
                                    {'AttributeName': 'created_at', 'KeyType': 'RANGE'}
                                ],
                                'Projection': {'ProjectionType': 'ALL'}
                            },
                            {
                                'IndexName': 'key_hash_index',
                                'KeySchema': [
                                    {'AttributeName': 'key_hash', 'KeyType': 'HASH'}
                                ],
                                'Projection': {'ProjectionType': 'ALL'}
                            }
                        ],
                        BillingMode='PAY_PER_REQUEST'
                    )
                    print(f"✅ API Keys table created: {self.table_name}")
                else:
                    print(f"❌ Error checking API Keys table {self.table_name}: {e}")
                    raise
        except ClientError as e:
            if e.response['Error']['Code'] == 'AccessDeniedException':
                print(f"⚠️  Access denied accessing DynamoDB. Please ensure your AWS user has DynamoDB permissions.")
            else:
                print(f"❌ Error initializing API Keys table: {e}")
    
    def _generate_api_key(self) -> Tuple[str, str, str]:
        """
        Generate API key
        Returns: (complete key, key prefix, key hash)
        """
        # Generate random key
        random_part = secrets.token_urlsafe(32)  # Generate secure random string
        api_key = f"memo_sk_{random_part}"
        
        # Generate prefix (for display)
        key_prefix = f"memo_sk_{random_part[:8]}"
        
        # Generate hash (for storage and validation)
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        
        return api_key, key_prefix, key_hash
    
    def create_api_key(self, user_id: str, name: Optional[str] = None, expires_at: Optional[datetime] = None) -> ApiKeyResponse:
        """
        Create new API key
        
        Args:
            user_id: User ID
            name: Optional key name
        
        Returns:
            ApiKeyResponse: Response containing complete key (only returned on creation)
        """
        try:
            # Generate key
            api_key, key_prefix, key_hash = self._generate_api_key()
            
            # Create API key record
            api_key_id = str(uuid.uuid4())
            now = datetime.utcnow().isoformat()
            
            item = {
                'id': api_key_id,
                'user_id': user_id,
                'name': name,
                'key_prefix': key_prefix,
                'key_hash': key_hash,
                'created_at': now,
                'last_used': None,
                'expires_at': expires_at.isoformat() if expires_at else None,
                'is_active': True
            }
            
            # Store in DynamoDB
            table = self.dynamodb.Table(self.table_name)
            table.put_item(Item=item)
            
            print(f"✅ API Key created for user {user_id}: {key_prefix}")
            
            # Return response (includes complete key, only returned on creation)
            return ApiKeyResponse(
                id=api_key_id,
                name=name,
                key=api_key,  # Complete key, only returned on creation
                key_prefix=key_prefix,
                created_at=datetime.fromisoformat(now),
                last_used=None,
                expires_at=expires_at,
                is_active=True
            )
            
        except ClientError as e:
            print(f"❌ Error creating API key: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create API key: {str(e)}"
            )
    
    def list_api_keys(self, user_id: str) -> List[ApiKey]:
        """
        List all API keys for a user (does not return complete keys)
        
        Args:
            user_id: User ID
        
        Returns:
            List[ApiKey]: List of API keys
        """
        try:
            table = self.dynamodb.Table(self.table_name)
            
            # Query user's API keys using GSI
            response = table.query(
                IndexName='user_id_index',
                KeyConditionExpression='user_id = :user_id',
                ExpressionAttributeValues={
                    ':user_id': user_id
                },
                ScanIndexForward=False  # Descending order by creation time
            )
            
            api_keys = []
            for item in response.get('Items', []):
                api_keys.append(ApiKey(
                    id=item['id'],
                    user_id=item['user_id'],
                    name=item.get('name'),
                    key_prefix=item['key_prefix'],
                    key_hash=item['key_hash'],  # Note: returns hash, frontend should not use this
                    created_at=datetime.fromisoformat(item['created_at']),
                    last_used=datetime.fromisoformat(item['last_used']) if item.get('last_used') else None,
                    expires_at=datetime.fromisoformat(item['expires_at']) if item.get('expires_at') else None,
                    is_active=item.get('is_active', True)
                ))
            
            return api_keys
            
        except ClientError as e:
            print(f"❌ Error listing API keys: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to list API keys: {str(e)}"
            )
    
    def revoke_api_key(self, user_id: str, api_key_id: str) -> bool:
        """
        Revoke API key
        
        Args:
            user_id: User ID
            api_key_id: API key ID
        
        Returns:
            bool: Whether successful
        """
        try:
            table = self.dynamodb.Table(self.table_name)
            
            # First check if key exists and belongs to the user
            response = table.get_item(Key={'id': api_key_id})
            
            if 'Item' not in response:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="API key not found"
                )
            
            item = response['Item']
            if item['user_id'] != user_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You don't have permission to revoke this API key"
                )
            
            # Update key status
            table.update_item(
                Key={'id': api_key_id},
                UpdateExpression='SET is_active = :is_active',
                ExpressionAttributeValues={
                    ':is_active': False
                }
            )
            
            print(f"✅ API Key revoked: {api_key_id}")
            return True
            
        except HTTPException:
            raise
        except ClientError as e:
            print(f"❌ Error revoking API key: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to revoke API key: {str(e)}"
            )
    
    def validate_api_key(self, api_key: str) -> Optional[Dict[str, Any]]:
        """
        Validate API key and return user information
        
        Args:
            api_key: API key string
        
        Returns:
            Optional[Dict]: If valid, returns dictionary containing user_id; otherwise returns None
        """
        try:
            # Calculate key hash
            key_hash = hashlib.sha256(api_key.encode()).hexdigest()
            
            # Look up in DynamoDB
            table = self.dynamodb.Table(self.table_name)
            
            # Try to query using index
            items = []
            try:
                response = table.query(
                    IndexName='key_hash_index',
                    KeyConditionExpression='key_hash = :key_hash',
                    ExpressionAttributeValues={
                        ':key_hash': key_hash
                    }
                )
                items = response.get('Items', [])
            except ClientError as e:
                # If index doesn't exist, use scan method (slower but works)
                if e.response['Error']['Code'] == 'ValidationException':
                    print(f"⚠️  key_hash_index does not exist, using scan method")
                    response = table.scan(
                        FilterExpression='key_hash = :key_hash',
                        ExpressionAttributeValues={
                            ':key_hash': key_hash
                        }
                    )
                    items = response.get('Items', [])
                else:
                    raise
            
            if not items:
                return None
            
            # Check if key is active
            item = items[0]
            if not item.get('is_active', True):
                return None
            
            # Check if expired
            expires_at_str = item.get('expires_at')
            if expires_at_str:
                expires_at = datetime.fromisoformat(expires_at_str)
                if datetime.utcnow() > expires_at:
                    return None
            
            # Update last used time
            now = datetime.utcnow().isoformat()
            table.update_item(
                Key={'id': item['id']},
                UpdateExpression='SET last_used = :last_used',
                ExpressionAttributeValues={
                    ':last_used': now
                }
            )
            
            return {
                'user_id': item['user_id'],
                'api_key_id': item['id']
            }
            
        except Exception as e:
            print(f"❌ Error validating API key: {e}")
            return None
    
    def health_check(self) -> Dict[str, Any]:
        """Health check"""
        try:
            if self.dynamodb_disabled:
                return {
                    "status": "healthy",
                    "storage": "disabled (test mode)"
                }
            
            table = self.dynamodb.Table(self.table_name)
            table.load()
            return {
                "status": "healthy",
                "storage": "dynamodb",
                "table": self.table_name
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }

# Global instance
api_key_service = ApiKeyService()

