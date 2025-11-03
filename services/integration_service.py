# Integrations Service
import json
import uuid
import hmac
import hashlib
import base64
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from urllib.parse import urlencode, urlparse, parse_qs
import requests
from config import settings
import boto3
from botocore.exceptions import ClientError
from cryptography.fernet import Fernet
from schemas import Integration, IntegrationCreate

class IntegrationService:
    """
    Integrations Service - manages external service integrations (Google Drive, Notion)
    Handles OAuth authorization, token management, and data synchronization
    """
    
    def __init__(self):
        # Check AWS configuration
        if (not settings.AWS_ACCESS_KEY_ID or 
            settings.AWS_ACCESS_KEY_ID == "your_aws_access_key_here"):
            raise ValueError("AWS configuration incomplete")
        
        # DynamoDB client
        self.dynamodb = boto3.resource(
            'dynamodb',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_REGION
        )
        
        # Table name
        self.table_name = f"unimem-integrations-{settings.ENVIRONMENT}"
        
        # Initialize table
        self._init_table()
        
        # Initialize encryption key (generated using SECRET_KEY)
        self._init_encryption()
    
    def _init_table(self):
        """Initialize DynamoDB table"""
        try:
            try:
                self.dynamodb.Table(self.table_name).load()
                print(f"📋 Integrations table already exists: {self.table_name}")
            except ClientError as e:
                if e.response['Error']['Code'] == 'ResourceNotFoundException':
                    print(f"🔨 Creating integrations table: {self.table_name}")
                    table = self.dynamodb.create_table(
                        TableName=self.table_name,
                        KeySchema=[
                            {'AttributeName': 'id', 'KeyType': 'HASH'}
                        ],
                        AttributeDefinitions=[
                            {'AttributeName': 'id', 'AttributeType': 'S'},
                            {'AttributeName': 'user_id', 'AttributeType': 'S'},
                            {'AttributeName': 'provider', 'AttributeType': 'S'}
                        ],
                        GlobalSecondaryIndexes=[
                            {
                                'IndexName': 'user_provider_index',
                                'KeySchema': [
                                    {'AttributeName': 'user_id', 'KeyType': 'HASH'},
                                    {'AttributeName': 'provider', 'KeyType': 'RANGE'}
                                ],
                                'Projection': {'ProjectionType': 'ALL'}
                            }
                        ],
                        BillingMode='PAY_PER_REQUEST'
                    )
                    print(f"✅ Integrations table created: {self.table_name}")
                else:
                    print(f"⚠️  Error checking integrations table: {e}")
        except ClientError as e:
            print(f"⚠️  DynamoDB access error: {e}")
    
    def _init_encryption(self):
        """Initialize encryption key"""
        # Generate Fernet key using SECRET_KEY
        key = hashlib.sha256(settings.SECRET_KEY.encode()).digest()
        key_b64 = base64.urlsafe_b64encode(key)
        self.cipher = Fernet(key_b64)
    
    def _encrypt_token(self, token: str) -> str:
        """Encrypt token"""
        if not token:
            return ""
        return self.cipher.encrypt(token.encode()).decode()
    
    def _decrypt_token(self, encrypted_token: str) -> str:
        """Decrypt token"""
        if not encrypted_token:
            return ""
        try:
            return self.cipher.decrypt(encrypted_token.encode()).decode()
        except Exception:
            return ""
    
    def _generate_oauth_state(self, user_id: str, provider: str) -> str:
        """Generate OAuth state parameter (prevent CSRF)"""
        timestamp = str(int(datetime.now().timestamp()))
        message = f"{user_id}:{provider}:{timestamp}"
        signature = hmac.new(
            settings.OAUTH_STATE_SECRET.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()
        state_data = {
            'user_id': user_id,
            'provider': provider,
            'timestamp': timestamp,
            'signature': signature
        }
        return base64.urlsafe_b64encode(json.dumps(state_data).encode()).decode()
    
    def _verify_oauth_state(self, state: str, provider: str) -> Optional[str]:
        """Verify OAuth state and return user_id"""
        try:
            state_data = json.loads(base64.urlsafe_b64decode(state.encode()).decode())
            user_id = state_data.get('user_id')
            state_provider = state_data.get('provider')
            timestamp = state_data.get('timestamp')
            signature = state_data.get('signature')
            
            # Verify provider matches
            if state_provider != provider:
                return None
            
            # Verify timestamp (prevent replay attacks, valid within 5 minutes)
            state_time = datetime.fromtimestamp(int(timestamp))
            if datetime.now() - state_time > timedelta(minutes=5):
                return None
            
            # Verify signature
            message = f"{user_id}:{provider}:{timestamp}"
            expected_sig = hmac.new(
                settings.OAUTH_STATE_SECRET.encode(),
                message.encode(),
                hashlib.sha256
            ).hexdigest()
            
            if signature != expected_sig:
                return None
            
            return user_id
        except Exception:
            return None
    
    def get_auth_url(self, user_id: str, provider: str, redirect_uri: Optional[str] = None) -> Dict[str, str]:
        """Generate OAuth authorization URL"""
        state = self._generate_oauth_state(user_id, provider)
        
        if provider == 'google-drive':
            if not settings.GOOGLE_CLIENT_ID:
                raise ValueError("Google OAuth not configured, please set GOOGLE_CLIENT_ID")
            
            redirect = redirect_uri or settings.GOOGLE_REDIRECT_URI
            params = {
                'client_id': settings.GOOGLE_CLIENT_ID,
                'redirect_uri': redirect,
                'response_type': 'code',
                'scope': 'https://www.googleapis.com/auth/drive.readonly https://www.googleapis.com/auth/userinfo.email https://www.googleapis.com/auth/userinfo.profile',
                'access_type': 'offline',
                'prompt': 'consent',
                'state': state
            }
            auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"
            
        elif provider == 'notion':
            if not settings.NOTION_CLIENT_ID:
                raise ValueError("Notion OAuth not configured, please set NOTION_CLIENT_ID")
            
            redirect = redirect_uri or settings.NOTION_REDIRECT_URI
            params = {
                'client_id': settings.NOTION_CLIENT_ID,
                'redirect_uri': redirect,
                'response_type': 'code',
                'owner': 'user',
                'state': state
            }
            auth_url = f"https://api.notion.com/v1/oauth/authorize?{urlencode(params)}"
            
        else:
            raise ValueError(f"Unsupported provider: {provider}")
        
        return {
            'auth_url': auth_url,
            'state': state
        }
    
    async def connect_integration(self, user_id: str, provider: str, code: str, state: str, redirect_uri: Optional[str] = None) -> Integration:
        """Connect integration service (OAuth callback handler)"""
        print(f"🔄 Starting integration connection: provider={provider}, user_id={user_id[:8]}...")
        print(f"   - Received redirect_uri parameter: {redirect_uri}")
        print(f"   - Default redirect_uri: {settings.GOOGLE_REDIRECT_URI if provider == 'google-drive' else settings.NOTION_REDIRECT_URI}")
        
        # Verify state
        verified_user_id = self._verify_oauth_state(state, provider)
        if not verified_user_id or verified_user_id != user_id:
            raise ValueError("Invalid OAuth state")
        
        # Exchange code for token
        try:
            if provider == 'google-drive':
                token_data = self._exchange_google_code(code, redirect_uri)
            elif provider == 'notion':
                token_data = self._exchange_notion_code(code, redirect_uri)
            else:
                raise ValueError(f"Unsupported provider: {provider}")
        except ValueError as e:
            error_msg = str(e)
            print(f"❌ Token exchange failed: {error_msg}")
            # If invalid_grant, provide more detailed hints
            if "invalid_grant" in error_msg:
                print(f"💡 Common causes of invalid_grant:")
                print(f"   1. redirect_uri mismatch (during authorization vs token exchange)")
                print(f"   2. Authorization code expired (usually valid for a few minutes)")
                print(f"   3. Authorization code reused (each code can only be used once)")
                print(f"   4. Please re-authorize to get a new code")
            raise
        
        # Get account info
        account_info = await self._get_account_info(provider, token_data['access_token'])
        
        # Determine account identifier (prefer email, otherwise use name)
        account_identifier = account_info.get('email') or account_info.get('name')
        print(f"📝 Saving integration info, account identifier: {account_identifier}")
        
        # Store or update integration info
        integration = await self._save_integration(
            user_id=user_id,
            provider=provider,
            access_token=token_data['access_token'],
            refresh_token=token_data.get('refresh_token'),
            expires_in=token_data.get('expires_in'),
            account=account_identifier
        )
        
        print(f"✅ Integration info saved, account field: {integration.account}")
        
        return integration
    
    def _exchange_google_code(self, code: str, redirect_uri: Optional[str] = None) -> Dict[str, Any]:
        """Exchange Google OAuth code for token"""
        if not settings.GOOGLE_CLIENT_SECRET:
            raise ValueError("Google OAuth not configured")
        
        token_url = "https://oauth2.googleapis.com/token"
        redirect = redirect_uri or settings.GOOGLE_REDIRECT_URI
        
        print(f"🔄 Google token exchange:")
        print(f"   - Using redirect_uri: {redirect}")
        print(f"   - Passed redirect_uri parameter: {redirect_uri}")
        print(f"   - Default redirect_uri: {settings.GOOGLE_REDIRECT_URI}")
        
        data = {
            'client_id': settings.GOOGLE_CLIENT_ID,
            'client_secret': settings.GOOGLE_CLIENT_SECRET,
            'code': code,
            'grant_type': 'authorization_code',
            'redirect_uri': redirect
        }
        
        response = requests.post(token_url, data=data)
        if response.status_code != 200:
            error_text = response.text
            print(f"❌ Google token exchange failed:")
            print(f"   Status code: {response.status_code}")
            print(f"   Error details: {error_text}")
            print(f"   Used redirect_uri: {redirect}")
            raise ValueError(f"Google token exchange failed: {error_text}")
        
        print(f"✅ Google token exchange successful")
        return response.json()
    
    def _exchange_notion_code(self, code: str, redirect_uri: Optional[str] = None) -> Dict[str, Any]:
        """Exchange Notion OAuth code for token"""
        if not settings.NOTION_CLIENT_SECRET:
            raise ValueError("Notion OAuth not configured")
        
        token_url = "https://api.notion.com/v1/oauth/token"
        redirect = redirect_uri or settings.NOTION_REDIRECT_URI
        data = {
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': redirect
        }
        headers = {
            'Authorization': f'Basic {base64.b64encode(f"{settings.NOTION_CLIENT_ID}:{settings.NOTION_CLIENT_SECRET}".encode()).decode()}',
            'Content-Type': 'application/json'
        }
        
        response = requests.post(token_url, json=data, headers=headers)
        if response.status_code != 200:
            error_detail = response.text
            try:
                error_json = response.json()
                error_detail = error_json.get('error_description', error_json.get('error', error_detail))
            except:
                pass
            print(f"❌ Notion token exchange failed: {response.status_code} - {error_detail}")
            raise ValueError(f"Notion token exchange failed: {error_detail}")
        
        return response.json()
    
    async def _get_account_info(self, provider: str, access_token: str) -> Dict[str, Any]:
        """Get account information"""
        print(f"🔍 Getting account info: provider={provider}")
        
        if provider == 'google-drive':
            try:
                response = requests.get(
                    'https://www.googleapis.com/oauth2/v2/userinfo',
                    headers={'Authorization': f'Bearer {access_token}'}
                )
                print(f"   Google userinfo response status: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    email = data.get('email')
                    name = data.get('name')
                    print(f"   ✅ Got account info: email={email}, name={name}")
                    return {'email': email, 'name': name}
                else:
                    print(f"   ⚠️  Google userinfo request failed: {response.status_code} - {response.text}")
            except Exception as e:
                print(f"   ❌ Exception getting Google account info: {e}")
        
        elif provider == 'notion':
            try:
                response = requests.get(
                    'https://api.notion.com/v1/users/me',
                    headers={'Authorization': f'Bearer {access_token}', 'Notion-Version': '2022-06-28'}
                )
                print(f"   Notion users/me response status: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    email = data.get('person', {}).get('email')
                    name = data.get('name')
                    print(f"   ✅ Got account info: email={email}, name={name}")
                    return {'email': email, 'name': name}
                else:
                    print(f"   ⚠️  Notion users/me request failed: {response.status_code} - {response.text}")
            except Exception as e:
                print(f"   ❌ Exception getting Notion account info: {e}")
        
        print(f"   ⚠️  Did not get account info, returning empty dict")
        return {}
    
    async def _save_integration(
        self, 
        user_id: str, 
        provider: str, 
        access_token: str,
        refresh_token: Optional[str] = None,
        expires_in: Optional[int] = None,
        account: Optional[str] = None
    ) -> Integration:
        """Save or update integration info"""
        table = self.dynamodb.Table(self.table_name)
        
        # Check if already exists
        existing = await self.get_integration_by_user_provider(user_id, provider)
        
        now = datetime.now()
        expires_at = None
        if expires_in:
            expires_at = now + timedelta(seconds=expires_in)
        
        if existing:
            # Update existing integration
            item = {
                'id': existing.id,
                'user_id': user_id,
                'provider': provider,
                'account': account or existing.account,
                'connected': True,
                'access_token': self._encrypt_token(access_token),
                'refresh_token': self._encrypt_token(refresh_token) if refresh_token else existing.refresh_token or "",
                'token_expires_at': expires_at.isoformat() if expires_at else None,
                'updated_at': now.isoformat(),
                'created_at': existing.created_at.isoformat()
            }
            table.put_item(Item=item)
            # Create Integration object for return (use original tokens, not encrypted)
            return Integration(
                id=existing.id,
                user_id=user_id,
                provider=provider,
                account=account or existing.account,
                connected=True,
                access_token=access_token,  # Original token
                refresh_token=refresh_token,  # Original token
                token_expires_at=expires_at,
                created_at=existing.created_at,
                updated_at=now
            )
        else:
            # Create new integration
            integration_id = str(uuid.uuid4())
            item = {
                'id': integration_id,
                'user_id': user_id,
                'provider': provider,
                'account': account,
                'connected': True,
                'access_token': self._encrypt_token(access_token),
                'refresh_token': self._encrypt_token(refresh_token) if refresh_token else "",
                'token_expires_at': expires_at.isoformat() if expires_at else None,
                'created_at': now.isoformat(),
                'updated_at': now.isoformat()
            }
            table.put_item(Item=item)
            # Create Integration object for return (use original tokens, not encrypted)
            return Integration(
                id=integration_id,
                user_id=user_id,
                provider=provider,
                account=account,
                connected=True,
                access_token=access_token,  # Original token
                refresh_token=refresh_token,  # Original token
                token_expires_at=expires_at,
                created_at=now,
                updated_at=now
            )
    
    async def get_integration_by_user_provider(self, user_id: str, provider: str) -> Optional[Integration]:
        """Get integration by user_id and provider"""
        table = self.dynamodb.Table(self.table_name)
        
        try:
            response = table.query(
                IndexName='user_provider_index',
                KeyConditionExpression='user_id = :uid AND provider = :p',
                ExpressionAttributeValues={
                    ':uid': user_id,
                    ':p': provider
                }
            )
            
            if response['Items']:
                item = response['Items'][0]
                # Decrypt tokens
                item['access_token'] = self._decrypt_token(item.get('access_token', ''))
                item['refresh_token'] = self._decrypt_token(item.get('refresh_token', ''))
                return Integration(**item)
            return None
        except ClientError as e:
            print(f"Error getting integration: {e}")
            return None
    
    async def get_user_integrations(self, user_id: str) -> List[Integration]:
        """Get all user integrations"""
        table = self.dynamodb.Table(self.table_name)
        
        try:
            response = table.query(
                IndexName='user_provider_index',
                KeyConditionExpression='user_id = :uid',
                ExpressionAttributeValues={':uid': user_id}
            )
            
            integrations = []
            for item in response['Items']:
                # Decrypt tokens (for internal use only)
                item['access_token'] = self._decrypt_token(item.get('access_token', ''))
                item['refresh_token'] = self._decrypt_token(item.get('refresh_token', ''))
                integrations.append(Integration(**item))
            
            return integrations
        except ClientError as e:
            print(f"Error getting user integrations: {e}")
            return []
    
    async def disconnect_integration(self, user_id: str, provider: str) -> bool:
        """Disconnect integration"""
        integration = await self.get_integration_by_user_provider(user_id, provider)
        if not integration:
            return False
        
        table = self.dynamodb.Table(self.table_name)
        table.delete_item(Key={'id': integration.id})
        return True
    
    async def sync_integration(self, user_id: str, provider: str) -> Dict[str, Any]:
        """Sync integration data"""
        integration = await self.get_integration_by_user_provider(user_id, provider)
        if not integration or not integration.connected:
            raise ValueError("Integration not connected")
        
        # Check if token expired, refresh if necessary
        access_token = integration.access_token
        
        # Handle token_expires_at: could be string or datetime object
        if integration.token_expires_at:
            if isinstance(integration.token_expires_at, str):
                expires_at = datetime.fromisoformat(integration.token_expires_at)
            elif isinstance(integration.token_expires_at, datetime):
                expires_at = integration.token_expires_at
            else:
                expires_at = None
            
            if expires_at and expires_at < datetime.now():
                if integration.refresh_token:
                    access_token = await self._refresh_token(provider, integration.refresh_token)
                else:
                    raise ValueError("Token expired and no refresh token available")
        
        # Execute sync logic (based on provider)
        synced_items = 0
        if provider == 'google-drive':
            synced_items = await self._sync_google_drive(user_id, access_token)
        elif provider == 'notion':
            synced_items = await self._sync_notion(user_id, access_token)
        
        # Update last_sync
        table = self.dynamodb.Table(self.table_name)
        table.update_item(
            Key={'id': integration.id},
            UpdateExpression='SET last_sync = :sync, updated_at = :now',
            ExpressionAttributeValues={
                ':sync': datetime.now().isoformat(),
                ':now': datetime.now().isoformat()
            }
        )
        
        return {
            'success': True,
            'message': f'Successfully synced {synced_items} items from {provider}',
            'synced_items': synced_items,
            'last_sync': datetime.now()
        }
    
    async def _refresh_token(self, provider: str, refresh_token: str) -> str:
        """Refresh access token"""
        if provider == 'google-drive':
            token_url = "https://oauth2.googleapis.com/token"
            data = {
                'client_id': settings.GOOGLE_CLIENT_ID,
                'client_secret': settings.GOOGLE_CLIENT_SECRET,
                'refresh_token': refresh_token,
                'grant_type': 'refresh_token'
            }
            response = requests.post(token_url, data=data)
            if response.status_code == 200:
                return response.json()['access_token']
        # Notion typically doesn't need refresh token
        raise ValueError(f"Token refresh not supported for {provider}")
    
    async def _sync_google_drive(self, user_id: str, access_token: str) -> int:
        """Sync Google Drive files"""
        try:
            from services.parser_service import parser_service
            from services.database_service import database_service
            from services.embedding_service import embedding_service
            from services.s3_service import s3_service
            from fastapi import UploadFile
            import io
            
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Accept': 'application/json'
            }
            
            synced_count = 0
            
            # Supported MIME types
            supported_mime_types = {
                'application/pdf': 'pdf',
                'application/vnd.google-apps.document': 'docx',  # Google Docs
                'application/vnd.openxmlformats-officedocument.wordprocessingml.document': 'docx',
                'application/vnd.openxmlformats-officedocument.presentationml.presentation': 'pptx',  # PowerPoint
                'application/vnd.ms-powerpoint.presentation.macroEnabled.12': 'pptx',  # PowerPoint (macro-enabled)
                'application/vnd.google-apps.presentation': 'pptx',  # Google Slides
                'text/plain': 'txt',
                'text/markdown': 'md',
                'image/png': 'png',
                'image/jpeg': 'jpg',
                'image/jpg': 'jpg',
                'image/gif': 'gif'
            }
            
            # 1. Get Google Drive file list
            files_url = "https://www.googleapis.com/drive/v3/files"
            
            # Build query: only get supported file types, exclude folders and deleted files
            # Note: Google Apps types (like Google Slides) need special handling
            mime_type_filters = [
                f"mimeType='{mime}'" for mime in supported_mime_types.keys()
            ]
            query = f"({' or '.join(mime_type_filters)}) and trashed=false"
            
            params = {
                'q': query,
                'fields': 'files(id,name,mimeType,size,modifiedTime,webViewLink)',
                'pageSize': 100
            }
            
            print(f"🔍 Searching Google Drive files...")
            response = requests.get(files_url, headers=headers, params=params)
            
            if response.status_code != 200:
                print(f"❌ Google Drive API request failed: {response.status_code} - {response.text}")
                return 0
            
            files = response.json().get('files', [])
            print(f"📋 Found {len(files)} supported files")
            
            # 2. For each file, download and process
            for file_info in files:
                try:
                    file_id = file_info.get('id')
                    file_name = file_info.get('name', 'Untitled')
                    mime_type = file_info.get('mimeType', '')
                    file_size = int(file_info.get('size', 0))
                    modified_time = file_info.get('modifiedTime', '')
                    
                    # Check file type
                    file_extension = supported_mime_types.get(mime_type)
                    if not file_extension:
                        print(f"⚠️  Skipping unsupported file type: {file_name} ({mime_type})")
                        continue
                    
                    # Check if already exists (identified by source)
                    source_id = f"googledrive_{file_id}"
                    
                    print(f"📥 Processing file: {file_name} (ID: {file_id[:8]}...)")
                    
                    # Download file content
                    download_url = f"https://www.googleapis.com/drive/v3/files/{file_id}"
                    
                    # Google Docs need to use export endpoint
                    if mime_type == 'application/vnd.google-apps.document':
                        download_url += '?exportFormat=docx&mimeType=application/vnd.openxmlformats-officedocument.wordprocessingml.document'
                    elif mime_type == 'application/vnd.google-apps.presentation':
                        # Export Google Slides as PPTX
                        download_url += '?exportFormat=pptx&mimeType=application/vnd.openxmlformats-officedocument.presentationml.presentation'
                    else:
                        download_url += '?alt=media'
                    
                    download_response = requests.get(download_url, headers=headers, stream=True)
                    
                    if download_response.status_code != 200:
                        print(f"⚠️  Download failed: {file_name} (status: {download_response.status_code})")
                        continue
                    
                    # Read file content
                    file_content = download_response.content
                    
                    # Create UploadFile object for subsequent use
                    file_obj = io.BytesIO(file_content)
                    
                    # First upload to S3 (following Notion implementation)
                    try:
                        upload_file_for_s3 = UploadFile(
                            filename=f"{file_name}.{file_extension}",
                            file=file_obj
                        )
                        upload_file_for_s3.content_type = mime_type
                        s3_data = await s3_service.upload_file(upload_file_for_s3)
                        print(f"📤 File uploaded to S3: {s3_data['s3_key']}")
                    except Exception as s3_error:
                        print(f"⚠️  S3 upload failed, but continuing with parsing: {s3_error}")
                        s3_data = None
                    
                    # Reset file pointer, create new UploadFile for parsing
                    file_obj = io.BytesIO(file_content)
                    upload_file = UploadFile(
                        filename=f"{file_name}.{file_extension}",
                        file=file_obj
                    )
                    upload_file.content_type = mime_type
                    
                    # Add Google Drive specific info to s3_data metadata
                    # parser_service will merge s3_data.metadata into memory metadata
                    if s3_data:
                        if 'metadata' not in s3_data:
                            s3_data['metadata'] = {}
                        s3_data['metadata'].update({
                            'source': 'google-drive',
                            'google_drive_file_id': file_id,
                            'google_drive_file_name': file_name,
                            'google_drive_file_url': file_info.get('webViewLink', ''),
                            'modified_time': modified_time,
                            'synced_at': datetime.now().isoformat()
                        })
                    else:
                        # If no s3_data, create a dict containing metadata
                        s3_data = {
                            'metadata': {
                                'source': 'google-drive',
                                'google_drive_file_id': file_id,
                                'google_drive_file_name': file_name,
                                'google_drive_file_url': file_info.get('webViewLink', ''),
                                'modified_time': modified_time,
                                'synced_at': datetime.now().isoformat()
                            }
                        }
                    
                    # Parse file content (parser_service.parse_file automatically creates memory)
                    try:
                        parse_result = await parser_service.parse_file(upload_file, s3_data or {}, user_id)
                        
                        # parse_result already contains memory_id, meaning memory was created
                        if parse_result.get('memory_id'):
                            # Update memory metadata to add Google Drive specific info
                            # Note: parser_service already created the memory
                            # To include Google Drive info, we need to update metadata
                            # But for simplicity, we can deduplicate on next sync, or update metadata now
                            
                            # Get created memory_id
                            memory_id = parse_result.get('memory_id')
                            
                            # Update memory metadata to add Google Drive info (optional)
                            # Since parser_service already created memory, metadata should already contain basic info
                            # Google Drive info can be identified through source field
                            
                            synced_count += 1
                            if s3_data:
                                print(f"✅ Synced Google Drive file: {file_name} (ID: {memory_id}, S3: {s3_data['s3_key']})")
                            else:
                                print(f"✅ Synced Google Drive file: {file_name} (ID: {memory_id})")
                        else:
                            print(f"⚠️  File parsed successfully but no memory created: {file_name}")
                    
                    except Exception as parse_error:
                        print(f"⚠️  File parsing failed: {file_name} - {parse_error}")
                        import traceback
                        traceback.print_exc()
                        continue
                
                except Exception as e:
                    print(f"⚠️  File processing failed: {file_name} - {e}")
                    import traceback
                    traceback.print_exc()
                    continue
            
            print(f"✅ Google Drive sync complete, synced {synced_count} files")
            return synced_count
            
        except Exception as e:
            print(f"❌ Google Drive sync failed: {e}")
            import traceback
            traceback.print_exc()
            return 0
    
    async def _sync_notion(self, user_id: str, access_token: str) -> int:
        """Sync Notion pages"""
        try:
            from services.parser_service import parser_service
            from services.database_service import database_service
            from services.embedding_service import embedding_service
            from services.s3_service import s3_service
            
            # Get Notion databases and pages
            # First search all accessible pages
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Notion-Version': '2022-06-28',
                'Content-Type': 'application/json'
            }
            
            synced_count = 0
            
            # 1. Search all accessible pages
            search_url = "https://api.notion.com/v1/search"
            search_data = {
                "filter": {
                    "property": "object",
                    "value": "page"
                },
                "page_size": 100
            }
            
            response = requests.post(search_url, json=search_data, headers=headers)
            if response.status_code != 200:
                print(f"❌ Notion search failed: {response.status_code} - {response.text}")
                return 0
            
            results = response.json().get('results', [])
            
            # 2. For each page, get its content and save as memory
            for page in results:
                try:
                    page_id = page.get('id')
                    page_title = self._extract_page_title(page)
                    
                    # Get page block content
                    blocks_url = f"https://api.notion.com/v1/blocks/{page_id}/children"
                    blocks_response = requests.get(blocks_url, headers=headers)
                    
                    if blocks_response.status_code == 200:
                        blocks = blocks_response.json().get('results', [])
                        page_content = self._extract_text_from_blocks(blocks)
                        
                        if page_content:
                            # Build complete page content
                            full_content = f"Title: {page_title}\n\nContent:\n{page_content}"
                            
                            # Check if already exists (identified by source)
                            source_id = f"notion_{page_id}"
                            
                            # First upload document content to S3
                            try:
                                s3_data = s3_service.upload_text_content(
                                    text_content=full_content,
                                    filename=f"notion_{page_title}",
                                    user_id=user_id,
                                    metadata={
                                        'notion_page_id': page_id,
                                        'notion_page_url': page.get('url', ''),
                                        'notion_page_title': page_title,
                                        'source': 'notion'
                                    }
                                )
                                print(f"📤 Notion page uploaded to S3: {s3_data['s3_key']}")
                            except Exception as s3_error:
                                print(f"⚠️  S3 upload failed, but continuing to create memory: {s3_error}")
                                s3_data = None
                            
                            # Generate embedding
                            embedding = embedding_service.generate_embedding(
                                text=full_content,
                                input_type="passage"
                            )
                            
                            # Prepare metadata, including S3 info
                            memory_metadata = {
                                'source': 'notion',
                                'notion_page_id': page_id,
                                'notion_page_url': page.get('url', ''),
                                'notion_page_title': page_title,
                                'synced_at': datetime.now().isoformat()
                            }
                            
                            # If S3 upload successful, add S3 info to metadata
                            if s3_data:
                                memory_metadata['s3_key'] = s3_data.get('s3_key')
                                memory_metadata['s3_url'] = s3_data.get('file_url')
                                memory_metadata['file_size'] = s3_data.get('file_size')
                            
                            # Create memory, source points to S3 URL (if exists) or use source_id
                            source_url = s3_data.get('file_url') if s3_data else source_id
                            
                            memory_id = database_service.create_memory(
                                content=full_content,
                                memory_type='text',
                                embedding=embedding,
                                user_id=user_id,
                                metadata=memory_metadata,
                                source=source_url,
                                summary=page_content[:200] + "..." if len(page_content) > 200 else page_content,
                                tags=['notion', 'synced']
                            )
                            
                            if memory_id:
                                synced_count += 1
                                if s3_data:
                                    print(f"✅ Synced Notion page: {page_title} (ID: {memory_id}, S3: {s3_data['s3_key']})")
                                else:
                                    print(f"✅ Synced Notion page: {page_title} (ID: {memory_id}, S3 upload failed)")
                    
                except Exception as e:
                    print(f"⚠️  Page sync failed (ID: {page_id}): {e}")
                    import traceback
                    traceback.print_exc()
                    continue
            
            print(f"✅ Notion sync complete, synced {synced_count} pages")
            return synced_count
            
        except Exception as e:
            print(f"❌ Notion sync failed: {e}")
            import traceback
            traceback.print_exc()
            return 0
    
    def _extract_page_title(self, page: Dict[str, Any]) -> str:
        """Extract title from Notion page object"""
        try:
            properties = page.get('properties', {})
            # Look for title property
            for prop_name, prop_value in properties.items():
                prop_type = prop_value.get('type')
                if prop_type == 'title':
                    title_parts = prop_value.get('title', [])
                    if title_parts:
                        return ''.join([part.get('plain_text', '') for part in title_parts])
            
            # If no title property found, try other names
            for prop_name in ['Name', 'name', 'Title', 'title']:
                if prop_name in properties:
                    prop = properties[prop_name]
                    if prop.get('type') == 'title':
                        title_parts = prop.get('title', [])
                        if title_parts:
                            return ''.join([part.get('plain_text', '') for part in title_parts])
            
            # Finally try to get from URL
            url = page.get('url', '')
            if url:
                return url.split('/')[-1] or 'Untitled Page'
            
            return 'Untitled Page'
        except Exception as e:
            return 'Untitled Page'
    
    def _extract_text_from_blocks(self, blocks: List[Dict[str, Any]]) -> str:
        """Extract text content from Notion blocks"""
        texts = []
        
        for block in blocks:
            block_type = block.get('type')
            block_content = block.get(block_type, {})
            
            if block_type == 'paragraph':
                rich_text = block_content.get('rich_text', [])
                para_text = ''.join([rt.get('plain_text', '') for rt in rich_text])
                if para_text:
                    texts.append(para_text)
            
            elif block_type == 'heading_1':
                rich_text = block_content.get('rich_text', [])
                heading_text = ''.join([rt.get('plain_text', '') for rt in rich_text])
                if heading_text:
                    texts.append(f"# {heading_text}")
            
            elif block_type == 'heading_2':
                rich_text = block_content.get('rich_text', [])
                heading_text = ''.join([rt.get('plain_text', '') for rt in rich_text])
                if heading_text:
                    texts.append(f"## {heading_text}")
            
            elif block_type == 'heading_3':
                rich_text = block_content.get('rich_text', [])
                heading_text = ''.join([rt.get('plain_text', '') for rt in rich_text])
                if heading_text:
                    texts.append(f"### {heading_text}")
            
            elif block_type == 'bulleted_list_item':
                rich_text = block_content.get('rich_text', [])
                item_text = ''.join([rt.get('plain_text', '') for rt in rich_text])
                if item_text:
                    texts.append(f"• {item_text}")
            
            elif block_type == 'numbered_list_item':
                rich_text = block_content.get('rich_text', [])
                item_text = ''.join([rt.get('plain_text', '') for rt in rich_text])
                if item_text:
                    texts.append(f"1. {item_text}")
            
            elif block_type == 'to_do':
                rich_text = block_content.get('rich_text', [])
                item_text = ''.join([rt.get('plain_text', '') for rt in rich_text])
                checked = block_content.get('checked', False)
                checkbox = '✓' if checked else '☐'
                if item_text:
                    texts.append(f"{checkbox} {item_text}")
            
            elif block_type == 'quote':
                rich_text = block_content.get('rich_text', [])
                quote_text = ''.join([rt.get('plain_text', '') for rt in rich_text])
                if quote_text:
                    texts.append(f"> {quote_text}")
            
            elif block_type == 'code':
                rich_text = block_content.get('rich_text', [])
                code_text = ''.join([rt.get('plain_text', '') for rt in rich_text])
                language = block_content.get('language', '')
                if code_text:
                    texts.append(f"```{language}\n{code_text}\n```")
            
            elif block_type == 'callout':
                rich_text = block_content.get('rich_text', [])
                callout_text = ''.join([rt.get('plain_text', '') for rt in rich_text])
                if callout_text:
                    texts.append(f"💡 {callout_text}")
        
        return '\n\n'.join(texts)

# Create service instance
integration_service = IntegrationService()
