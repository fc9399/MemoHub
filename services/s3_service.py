# S3 Service
import boto3
from fastapi import UploadFile, HTTPException
from datetime import datetime
from urllib.parse import quote
from config import settings

class S3Service:
    """S3 file upload service"""
    
    def __init__(self):
        # Check AWS configuration
        if (not settings.AWS_ACCESS_KEY_ID or 
            settings.AWS_ACCESS_KEY_ID == "your_aws_access_key_here" or
            not settings.S3_BUCKET_NAME or
            settings.S3_BUCKET_NAME == "your-s3-bucket-name"):
            raise ValueError("S3 configuration incomplete. Please set AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, and S3_BUCKET_NAME environment variables")
        
        self.client = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_REGION
        )
        self.bucket_name = settings.S3_BUCKET_NAME
    
    def validate_file(self, file: UploadFile) -> bool:
        """Validate file format and size"""
        if not file.filename:
            raise HTTPException(status_code=400, detail="Filename cannot be empty")
        
        extension = file.filename.split(".")[-1].lower()
        if extension not in settings.ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file format. Allowed: {', '.join(settings.ALLOWED_EXTENSIONS)}"
            )
        return True
    
    async def upload_file(self, file: UploadFile) -> dict:
        """
        Upload file to S3
        
        Args:
            file: File to upload
            
        Returns:
            dict: File information
        """
        # Validate file
        self.validate_file(file)
        
        try:
            # Generate filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            original_filename = file.filename
            s3_key = f"uploads/{timestamp}_{original_filename}"
            
            print(f"📤 Starting upload: {original_filename}")
            
            # Read file content
            file_content = await file.read()
            file_size = len(file_content)
            
            print(f"📊 File size: {file_size / 1024:.2f} KB")
            
            # Upload to S3
            self.client.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=file_content,
                ContentType=file.content_type or 'application/octet-stream',
                Metadata={
                    'original_filename': quote(original_filename),
                    'upload_timestamp': timestamp
                }
            )
            file_url = f"s3://{self.bucket_name}/{s3_key}"
            
            print(f"✅ Upload successful: {s3_key}")
            
            return {
                "original_filename": original_filename,
                "s3_key": s3_key,
                "file_url": file_url,
                "file_size": file_size,
                "file_extension": original_filename.split(".")[-1].lower(),
                "upload_time": timestamp
            }
            
        except Exception as e:
            error_msg = str(e)
            print(f"❌ Upload failed: {error_msg}")
            
            # Provide more detailed error information
            if "Access Denied" in error_msg:
                raise HTTPException(
                    status_code=403, 
                    detail=f"S3 access denied. Please ensure your AWS user has write permissions to S3 bucket '{self.bucket_name}'."
                )
            elif "NoSuchBucket" in error_msg:
                raise HTTPException(
                    status_code=404,
                    detail=f"S3 bucket '{self.bucket_name}' does not exist. Please check bucket name or create the bucket."
                )
            else:
                raise HTTPException(status_code=500, detail=f"Upload failed: {error_msg}")
    
    def upload_text_content(self, text_content: str, filename: str, user_id: str = None, metadata: dict = None) -> dict:
        """
        Upload text content to S3
        
        Args:
            text_content: Text content
            filename: Filename (used to generate S3 key)
            user_id: User ID (optional, for organizing files)
            metadata: Additional metadata (optional)
            
        Returns:
            dict: File information (s3_key, file_url, file_size, etc.)
        """
        try:
            # Generate filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            # Clean filename, keep only safe characters
            safe_filename = "".join(c for c in filename if c.isalnum() or c in (' ', '-', '_', '.')).strip()
            safe_filename = safe_filename.replace(' ', '_')[:100]  # Limit length
            
            # Build S3 key, organize by user if user_id provided
            if user_id:
                s3_key = f"integrations/{user_id}/{timestamp}_{safe_filename}.txt"
            else:
                s3_key = f"integrations/{timestamp}_{safe_filename}.txt"
            
            print(f"📤 Uploading text content to S3: {s3_key}")
            
            # Encode text content as bytes
            file_content = text_content.encode('utf-8')
            file_size = len(file_content)
            
            print(f"📊 Content size: {file_size / 1024:.2f} KB")
            
            # Prepare metadata
            s3_metadata = {
                'upload_timestamp': timestamp,
                'content_type': 'text/plain',
                'source': 'integration'
            }
            if metadata:
                # Convert metadata values to strings (S3 metadata must be strings)
                for key, value in metadata.items():
                    s3_metadata[str(key)] = str(value)[:1000]  # S3 metadata value limit is 2KB
            
            # Upload to S3
            self.client.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=file_content,
                ContentType='text/plain; charset=utf-8',
                Metadata=s3_metadata
            )
            file_url = f"s3://{self.bucket_name}/{s3_key}"
            
            print(f"✅ Text content uploaded successfully: {s3_key}")
            
            return {
                "original_filename": safe_filename,
                "s3_key": s3_key,
                "file_url": file_url,
                "file_size": file_size,
                "file_extension": "txt",
                "upload_time": timestamp
            }
            
        except Exception as e:
            error_msg = str(e)
            print(f"❌ Text upload failed: {error_msg}")
            
            # Provide more detailed error information
            if "Access Denied" in error_msg:
                raise ValueError(f"S3 access denied. Please ensure your AWS user has write permissions to S3 bucket '{self.bucket_name}'.")
            elif "NoSuchBucket" in error_msg:
                raise ValueError(f"S3 bucket '{self.bucket_name}' does not exist. Please check bucket name or create the bucket.")
            else:
                raise ValueError(f"Text upload failed: {error_msg}")
    
    def health_check(self) -> dict:
        """Check if S3 connection is working properly"""
        try:
            self.client.head_bucket(Bucket=self.bucket_name)
            return {
                "status": "healthy",
                "bucket": self.bucket_name
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }

# Global instance
s3_service = S3Service()