# User Authentication Service
import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from passlib.context import CryptContext
from jose import JWTError, jwt
from fastapi import HTTPException, status
from config import settings
from schemas import UserCreate, UserInDB, User, UserLogin, Token, TokenData
import boto3
from botocore.exceptions import ClientError

class AuthService:
    """
    User Authentication Service - handles user registration, login, JWT token management
    Uses DynamoDB to store user information
    """
    
    def __init__(self):
        # Password encryption context
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        
        # Check if in test mode
        if settings.ENVIRONMENT == "test":
            self.dynamodb = None
            self.users_table_name = None
            self.dynamodb_disabled = True
            print("🧪 Authentication service running in test mode")
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
        
        # Users table name
        self.users_table_name = f"unimem-users-{settings.ENVIRONMENT}"
        
        # Initialize users table
        self._init_users_table()
    
    def _init_users_table(self):
        """Initialize users table"""
        try:
            # Check if table exists
            try:
                self.dynamodb.Table(self.users_table_name).load()
                print(f"📋 Users table already exists: {self.users_table_name}")
            except ClientError as e:
                if e.response['Error']['Code'] == 'ResourceNotFoundException':
                    # Table doesn't exist, try to create
                    print(f"🔨 Creating users table: {self.users_table_name}")
                    users_table = self.dynamodb.create_table(
                        TableName=self.users_table_name,
                        KeySchema=[
                            {'AttributeName': 'id', 'KeyType': 'HASH'}
                        ],
                        AttributeDefinitions=[
                            {'AttributeName': 'id', 'AttributeType': 'S'},
                            {'AttributeName': 'username', 'AttributeType': 'S'},
                            {'AttributeName': 'email', 'AttributeType': 'S'}
                        ],
                        GlobalSecondaryIndexes=[
                            {
                                'IndexName': 'username_index',
                                'KeySchema': [
                                    {'AttributeName': 'username', 'KeyType': 'HASH'}
                                ],
                                'Projection': {'ProjectionType': 'ALL'}
                            },
                            {
                                'IndexName': 'email_index',
                                'KeySchema': [
                                    {'AttributeName': 'email', 'KeyType': 'HASH'}
                                ],
                                'Projection': {'ProjectionType': 'ALL'}
                            }
                        ],
                        BillingMode='PAY_PER_REQUEST'
                    )
                    print(f"✅ Users table created: {self.users_table_name}")
                else:
                    print(f"❌ Error checking users table {self.users_table_name}: {e}")
                    raise
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'AccessDeniedException':
                print(f"⚠️  Access denied accessing DynamoDB. Please ensure your AWS user has DynamoDB permissions.")
                print(f"   Required permissions: CreateTable, DescribeTable, PutItem, GetItem, UpdateItem, DeleteItem, Query, Scan")
                print(f"   Or manually create table: {self.users_table_name}")
                raise
            else:
                print(f"❌ Error with users table: {e}")
                raise
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password"""
        return self.pwd_context.verify(plain_password, hashed_password)
    
    def get_password_hash(self, password: str) -> str:
        """Generate password hash"""
        return self.pwd_context.hash(password)
    
    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Create access token"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({"exp": expire, "type": "access"})
        encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        return encoded_jwt
    
    def create_refresh_token(self, data: dict) -> str:
        """Create refresh token"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        to_encode.update({"exp": expire, "type": "refresh"})
        encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        return encoded_jwt
    
    def verify_token(self, token: str, token_type: str = "access") -> TokenData:
        """Verify token"""
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            username: str = payload.get("sub")
            user_id: str = payload.get("user_id")
            token_type_claim: str = payload.get("type")
            
            if username is None or user_id is None or token_type_claim != token_type:
                raise credentials_exception
            
            token_data = TokenData(username=username, user_id=user_id)
            return token_data
            
        except JWTError:
            raise credentials_exception
    
    async def create_user(self, user: UserCreate) -> User:
        """Create new user"""
        # Check if username already exists
        if await self.get_user_by_username(user.username):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already registered"
            )
        
        # Check if email already exists
        if await self.get_user_by_email(user.email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Create user ID
        user_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()
        
        # Prepare user data
        user_data = {
            'id': user_id,
            'username': user.username,
            'email': user.email,
            'full_name': user.full_name,
            'hashed_password': self.get_password_hash(user.password),
            'is_active': True,
            'created_at': now,
            'updated_at': now
        }
        
        try:
            # Store in DynamoDB
            table = self.dynamodb.Table(self.users_table_name)
            table.put_item(Item=user_data)
            
            print(f"✅ User created: {user.username} ({user_id})")
            
            # Return user info (without password)
            return User(
                id=user_id,
                username=user.username,
                email=user.email,
                full_name=user.full_name,
                is_active=True,
                created_at=datetime.fromisoformat(now),
                updated_at=datetime.fromisoformat(now)
            )
            
        except Exception as e:
            print(f"❌ Failed to create user: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create user"
            )
    
    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID"""
        try:
            table = self.dynamodb.Table(self.users_table_name)
            response = table.get_item(Key={'id': user_id})
            
            if 'Item' in response:
                item = response['Item']
                return User(
                    id=item['id'],
                    username=item['username'],
                    email=item['email'],
                    full_name=item.get('full_name'),
                    is_active=item.get('is_active', True),
                    created_at=datetime.fromisoformat(item['created_at']),
                    updated_at=datetime.fromisoformat(item['updated_at'])
                )
            return None
            
        except Exception as e:
            print(f"❌ Failed to get user by ID {user_id}: {e}")
            return None
    
    async def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username"""
        try:
            table = self.dynamodb.Table(self.users_table_name)
            response = table.query(
                IndexName='username_index',
                KeyConditionExpression='username = :username',
                ExpressionAttributeValues={':username': username}
            )
            
            if response['Items']:
                item = response['Items'][0]
                return User(
                    id=item['id'],
                    username=item['username'],
                    email=item['email'],
                    full_name=item.get('full_name'),
                    is_active=item.get('is_active', True),
                    created_at=datetime.fromisoformat(item['created_at']),
                    updated_at=datetime.fromisoformat(item['updated_at'])
                )
            return None
            
        except Exception as e:
            print(f"❌ Failed to get user by username {username}: {e}")
            return None
    
    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        try:
            table = self.dynamodb.Table(self.users_table_name)
            response = table.query(
                IndexName='email_index',
                KeyConditionExpression='email = :email',
                ExpressionAttributeValues={':email': email}
            )
            
            if response['Items']:
                item = response['Items'][0]
                return User(
                    id=item['id'],
                    username=item['username'],
                    email=item['email'],
                    full_name=item.get('full_name'),
                    is_active=item.get('is_active', True),
                    created_at=datetime.fromisoformat(item['created_at']),
                    updated_at=datetime.fromisoformat(item['updated_at'])
                )
            return None
            
        except Exception as e:
            print(f"❌ Failed to get user by email {email}: {e}")
            return None
    
    async def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """Authenticate user"""
        user = await self.get_user_by_username(username)
        if not user:
            return None
        
        # Get complete user info (including password hash)
        try:
            table = self.dynamodb.Table(self.users_table_name)
            response = table.get_item(Key={'id': user.id})
            
            if 'Item' in response:
                item = response['Item']
                if not self.verify_password(password, item['hashed_password']):
                    return None
                
                return User(
                    id=item['id'],
                    username=item['username'],
                    email=item['email'],
                    full_name=item.get('full_name'),
                    is_active=item.get('is_active', True),
                    created_at=datetime.fromisoformat(item['created_at']),
                    updated_at=datetime.fromisoformat(item['updated_at'])
                )
            
            return None
            
        except Exception as e:
            print(f"❌ Failed to authenticate user {username}: {e}")
            return None
    
    async def login_user(self, user_login: UserLogin) -> Token:
        """User login"""
        user = await self.authenticate_user(user_login.username, user_login.password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Inactive user"
            )
        
        # Create tokens
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = self.create_access_token(
            data={"sub": user.username, "user_id": user.id}, 
            expires_delta=access_token_expires
        )
        
        refresh_token = self.create_refresh_token(
            data={"sub": user.username, "user_id": user.id}
        )
        
        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )
    
    async def refresh_access_token(self, refresh_token: str) -> Token:
        """Refresh access token"""
        token_data = self.verify_token(refresh_token, "refresh")
        user = await self.get_user_by_username(token_data.username)
        
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        # Create new access token
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = self.create_access_token(
            data={"sub": user.username, "user_id": user.id}, 
            expires_delta=access_token_expires
        )
        
        return Token(
            access_token=access_token,
            refresh_token=refresh_token,  # Keep original refresh token
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )
    
    def health_check(self) -> Dict[str, Any]:
        """Health check"""
        try:
            # Check DynamoDB connection
            table = self.dynamodb.Table(self.users_table_name)
            self.dynamodb.meta.client.describe_table(TableName=self.users_table_name)
            
            return {
                'status': 'healthy',
                'service': 'auth',
                'dynamodb': 'connected',
                'table': self.users_table_name,
                'encryption': 'bcrypt'
            }
            
        except Exception as e:
            return {
                'status': 'unhealthy',
                'service': 'auth',
                'error': str(e)
            }

# Global instance
auth_service = AuthService()
