"""
AWS S3 Manager for Bot Code and ML Models
Handles uploading, downloading, and managing bot files in S3
"""

import boto3
import os
import hashlib
import json
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from botocore.exceptions import ClientError, NoCredentialsError
import tempfile
import zipfile
from pathlib import Path
from dotenv import load_dotenv
import mimetypes

load_dotenv()
logger = logging.getLogger(__name__)

class S3Manager:
    """Manages bot code and ML models in AWS S3"""
    
    def __init__(self):
        """
        Initialize S3 manager using environment variables
        
        Environment Variables:
            AWS_ACCESS_KEY_ID: AWS access key ID
            AWS_SECRET_ACCESS_KEY: AWS secret access key
            AWS_DEFAULT_REGION: AWS region (default: us-east-1)
            AWS_S3_BUCKET_NAME: S3 bucket name for storing bot files
            AWS_S3_ENDPOINT_URL: Custom S3 endpoint URL (optional, for LocalStack/MinIO)
        """
        # Load configuration from environment variables
        self.aws_access_key_id = os.getenv('AWS_ACCESS_KEY_ID')
        self.aws_secret_access_key = os.getenv('AWS_SECRET_ACCESS_KEY')
        self.region = os.getenv('AWS_DEFAULT_REGION', 'us-east-1')
        self.bucket_name = os.getenv('AWS_S3_BUCKET_NAME', 'trading-bot-storage')
        self.endpoint_url = os.getenv('AWS_S3_ENDPOINT_URL')  # For LocalStack/MinIO
        
        # Validate required configuration
        if not self.bucket_name:
            raise ValueError("AWS_S3_BUCKET_NAME environment variable is required")
        
        # Initialize S3 client
        try:
            s3_config = {
                'region_name': self.region
            }
            
            # Add custom endpoint if provided (for LocalStack/MinIO)
            if self.endpoint_url:
                s3_config['endpoint_url'] = self.endpoint_url
            
            # Use explicit credentials if provided
            if self.aws_access_key_id and self.aws_secret_access_key:
                s3_config['aws_access_key_id'] = self.aws_access_key_id
                s3_config['aws_secret_access_key'] = self.aws_secret_access_key
                logger.info("Using explicit AWS credentials")
            else:
                logger.info("Using default AWS credentials (IAM role, profile, or instance metadata)")
            
            self.s3_client = boto3.client('s3', **s3_config)
            
            # Test connection and create bucket if needed
            self.initialize()
            
        except Exception as e:
            logger.error(f"Failed to initialize S3 client: {e}")
            raise
    
    def initialize(self):
        """Initialize S3 bucket and verify connection"""
        try:
            # Skip S3 initialization if no credentials available or using fake credentials
            if (not self.aws_access_key_id or not self.aws_secret_access_key or 
                self.aws_access_key_id == 'fake_access_key'):
                logger.warning("AWS credentials not configured or using fake credentials. S3 features will be disabled.")
                self.s3_client = None
                return
                
            # Test connection by listing buckets
            self.s3_client.list_buckets()
            logger.info("S3 connection successful")
            
            # Create bucket if it doesn't exist
            # self._create_bucket_if_not_exists()
            
            # Set bucket policy for bot storage
            self._setup_bucket_policy()
            
        except NoCredentialsError:
            logger.warning("AWS credentials not found. S3 features will be disabled.")
            self.s3_client = None
        except ClientError as e:
            logger.warning(f"AWS S3 client error: {e}. S3 features will be disabled.")
            self.s3_client = None
        except Exception as e:
            logger.warning(f"Failed to initialize S3: {e}. S3 features will be disabled.")
            self.s3_client = None
    
    def _create_bucket_if_not_exists(self):
        """Create S3 bucket if it doesn't exist"""
        try:
            # Check if bucket exists
            self.s3_client.head_bucket(Bucket=self.bucket_name)
            logger.info(f"Bucket '{self.bucket_name}' already exists")
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            
            if error_code == '404':
                # Bucket doesn't exist, create it
                try:
                    if self.region == 'us-east-1':
                        # us-east-1 doesn't need LocationConstraint
                        self.s3_client.create_bucket(Bucket=self.bucket_name)
                    else:
                        # Other regions need LocationConstraint
                        self.s3_client.create_bucket(
                            Bucket=self.bucket_name,
                            CreateBucketConfiguration={'LocationConstraint': self.region}
                        )
                    
                    logger.info(f"Created bucket '{self.bucket_name}' in region '{self.region}'")
                    
                    # Enable versioning
                    self.s3_client.put_bucket_versioning(
                        Bucket=self.bucket_name,
                        VersioningConfiguration={'Status': 'Enabled'}
                    )
                    
                    logger.info(f"Enabled versioning for bucket '{self.bucket_name}'")
                    
                except ClientError as create_error:
                    logger.error(f"Failed to create bucket: {create_error}")
                    raise
                    
            elif error_code == '403':
                logger.error(f"Access denied to bucket '{self.bucket_name}'. Check AWS permissions.")
                raise
            else:
                logger.error(f"Error checking bucket: {e}")
                raise
    
    def _setup_bucket_policy(self):
        """Setup bucket policy for bot storage"""
        try:
            # Basic bucket policy for bot storage
            bucket_policy = {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Principal": {"AWS": f"arn:aws:iam::{self._get_account_id()}:root"},
                        "Action": [
                            "s3:GetObject",
                            "s3:PutObject",
                            "s3:DeleteObject",
                            "s3:ListBucket"
                        ],
                        "Resource": [
                            f"arn:aws:s3:::{self.bucket_name}",
                            f"arn:aws:s3:::{self.bucket_name}/*"
                        ]
                    }
                ]
            }
            
            # Apply policy (only if we have permissions)
            try:
                self.s3_client.put_bucket_policy(
                    Bucket=self.bucket_name,
                    Policy=json.dumps(bucket_policy)
                )
                logger.info(f"Applied bucket policy to '{self.bucket_name}'")
            except ClientError as e:
                # It's okay if we can't set policy - might not have permissions
                logger.warning(f"Could not set bucket policy: {e}")
                
        except Exception as e:
            logger.warning(f"Could not setup bucket policy: {e}")
    
    def _get_account_id(self):
        """Get AWS account ID"""
        try:
            sts_client = boto3.client('sts', region_name=self.region)
            if self.aws_access_key_id and self.aws_secret_access_key:
                sts_client = boto3.client(
                    'sts',
                    aws_access_key_id=self.aws_access_key_id,
                    aws_secret_access_key=self.aws_secret_access_key,
                    region_name=self.region
                )
            
            response = sts_client.get_caller_identity()
            return response['Account']
        except Exception:
            return "*"  # Fallback for policy
    
    def health_check(self) -> bool:
        """Check if S3 connection is healthy"""
        try:
            # Simple health check by listing objects with limit
            self.s3_client.list_objects_v2(Bucket=self.bucket_name, MaxKeys=1)
            return True
        except Exception as e:
            logger.error(f"S3 health check failed: {e}")
            return False
    
    def get_config_info(self) -> Dict[str, Any]:
        """Get S3 configuration information"""
        return {
            "bucket_name": self.bucket_name,
            "region": self.region,
            "endpoint_url": self.endpoint_url,
            "credentials_configured": bool(self.aws_access_key_id and self.aws_secret_access_key),
            "using_custom_endpoint": bool(self.endpoint_url)
        }
    
    def upload_bot_code(self, bot_id: int, code_content: str, filename: str = "bot.py",
                        version: Optional[str] = None, file_type: str = "code") -> Dict[str, Any]:
        try:
            if not version:
                version = datetime.utcnow().strftime("%Y%m%d_%H%M%S")

            s3_key = f"bots/{bot_id}/{file_type}/{version}/{filename}"

            # Bytes for hashing / size / body
            body_bytes = code_content.encode('utf-8')
            file_hash = hashlib.sha256(body_bytes).hexdigest()
            file_size = str(len(body_bytes))

            # Guess content type from filename, fallback to octet-stream
            content_type = mimetypes.guess_type(filename)[0] or "application/octet-stream"
            # Optionally override for python files
            if filename.endswith('.py'):
                content_type = "text/x-python"
            elif filename.endswith('.robot'):
                content_type = "text/plain"

            metadata = {
                "bot_id": str(bot_id),
                "version": version,
                "filename": filename,
                "file_hash": file_hash,
                "upload_time": datetime.utcnow().isoformat(),
                "file_type": file_type,
                "file_size": file_size
            }

            # Upload code file
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=body_bytes,
                ContentType=content_type,
                Metadata={k: str(v) for k, v in metadata.items()}
            )

            # Store metadata under file_type-specific name
            metadata_key = f"bots/{bot_id}/metadata/{version}/{file_type}_metadata.json"
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=metadata_key,
                Body=json.dumps(metadata),
                ContentType="application/json"
            )

            logger.info(f"Uploaded bot file to S3: {s3_key}")

            return {
                "s3_key": s3_key,
                "version": version,
                "file_hash": file_hash,
                "metadata": metadata
            }

        except ClientError as e:
            logger.error(f"Error uploading bot file: {e}")
            raise
    
    def upload_ml_model(self, bot_id: int, model_data: bytes, filename: str, 
                       model_type: str, framework: str, version: Optional[str] = None) -> Dict[str, Any]:
        """
        Upload ML model to S3
        
        Args:
            bot_id: Bot ID
            model_data: Model data as bytes
            filename: Model filename
            model_type: Type of model (MODEL, WEIGHTS, CONFIG)
            framework: ML framework (tensorflow, pytorch, sklearn, etc.)
            version: Version identifier (optional)
            
        Returns:
            Dict with upload information
        """
        try:
            # Generate version if not provided
            if not version:
                version = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            
            # Create S3 key
            s3_key = f"bots/{bot_id}/models/{version}/{filename}"
            
            # Calculate file hash
            file_hash = hashlib.sha256(model_data).hexdigest()
            
            # Create metadata
            metadata = {
                "bot_id": str(bot_id),
                "version": version,
                "filename": filename,
                "model_type": model_type,
                "framework": framework,
                "file_hash": file_hash,
                "upload_time": datetime.utcnow().isoformat(),
                "file_size": str(len(model_data))
            }
            
            # Upload to S3
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=model_data,
                ContentType="application/octet-stream",
                Metadata=metadata
            )
            
            logger.info(f"Uploaded ML model: {s3_key}")
            
            return {
                "s3_key": s3_key,
                "version": version,
                "file_hash": file_hash,
                "metadata": metadata
            }
            
        except ClientError as e:
            logger.error(f"Error uploading ML model: {e}")
            raise
    
    def download_bot_code(self, bot_id: int, version: Optional[str] = None, filename: Optional[str] = None, file_type: str = "code") -> str:
        """
        Download bot code from S3
        
        Args:
            bot_id: Bot ID
            version: Version to download (latest if not specified)
            filename: Specific filename to download (auto-detect if not specified)
            
        Returns:
            Bot code content as string
        """
        if not self.s3_client:
            logger.warning("S3 client not available. Cannot download bot code.")
            raise Exception("S3 service not available")
            
        try:
            # Get version if not specified
            if not version:
                version = self.get_latest_version(bot_id, file_type)
                logger.info(f"Using latest version: {version}")
            
            # If filename not specified, find the Python file in the version directory
            if not filename:
                prefix = f"bots/{bot_id}/{file_type}/{version}/"
                response = self.s3_client.list_objects_v2(
                    Bucket=self.bucket_name,
                    Prefix=prefix
                )
                
                candidate_files = []
                for obj in response.get('Contents', []):
                    key = obj['Key']
                    if file_type == "code" and key.endswith('.py'):
                        candidate_files.append(key)
                    elif file_type == "rpa" and key.endswith('.robot'):
                        candidate_files.append(key)
                
                if not candidate_files:
                    raise FileNotFoundError(f"No {file_type} files found in {prefix}")

                # Use the first candidate file found
                s3_key = candidate_files[0]
                filename = s3_key.split('/')[-1]
                logger.info(f"Found file: {filename}")
            else:
                s3_key = f"bots/{bot_id}/{file_type}/{version}/{filename}"
            
            # Download file
            response = self.s3_client.get_object(Bucket=self.bucket_name, Key=s3_key)
            content = response['Body'].read().decode('utf-8')
            
            logger.info(f"Downloaded {file_type} file: {s3_key} ({len(content)} characters)")
            return content
            
        except ClientError as e:
            logger.error(f"Error downloading bot code: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error downloading bot code: {e}")
            raise
    
    def download_ml_model(self, bot_id: int, filename: str, version: Optional[str] = None) -> bytes:
        """
        Download ML model from S3
        
        Args:
            bot_id: Bot ID
            filename: Model filename
            version: Version to download (latest if not specified)
            
        Returns:
            Model data as bytes
        """
        try:
            # Get the S3 key
            if version:
                s3_key = f"bots/{bot_id}/models/{version}/{filename}"
            else:
                # Get latest version
                s3_key = self._get_latest_model_version_key(bot_id, filename)
                if not s3_key:
                    raise ValueError(f"No model found for bot {bot_id}, filename {filename}")
            
            # Download file
            response = self.s3_client.get_object(Bucket=self.bucket_name, Key=s3_key)
            model_data = response['Body'].read()
            
            logger.info(f"Downloaded ML model: {s3_key}")
            return model_data
            
        except ClientError as e:
            logger.error(f"Error downloading ML model: {e}")
            raise
    
    def download_bot_package(self, bot_id: int, version: Optional[str] = None) -> str:
        """
        Download complete bot package (code + models) as zip file
        
        Args:
            bot_id: Bot ID
            version: Version to download (latest if None)
            
        Returns:
            str: Path to downloaded zip file
        """
        try:
            # Get version if not specified
            if not version:
                version = self.get_latest_version(bot_id)
            
            # Create temporary directory
            temp_dir = tempfile.mkdtemp()
            bot_dir = Path(temp_dir) / f"bot_{bot_id}_{version}"
            bot_dir.mkdir(exist_ok=True)
            
            # Download code files
            try:
                code_content = self.download_bot_code(bot_id, version)
                (bot_dir / "bot.py").write_text(code_content)
            except FileNotFoundError:
                logger.warning(f"No code files found for bot {bot_id}")
            
            # Download model files
            models_dir = bot_dir / "models"
            models_dir.mkdir(exist_ok=True)
            
            for model_type in ["MODEL", "WEIGHTS", "CONFIG"]:
                try:
                    model_data = self.download_ml_model(bot_id, model_type, version)
                    model_files = self.list_files(bot_id, version, f"models/{model_type.lower()}")
                    if model_files:
                        (models_dir / model_files[0]).write_bytes(model_data)
                except FileNotFoundError:
                    continue
            
            # Create zip file
            zip_path = Path(temp_dir) / f"bot_{bot_id}_{version}.zip"
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for file_path in bot_dir.rglob('*'):
                    if file_path.is_file():
                        zipf.write(file_path, file_path.relative_to(bot_dir))
            
            logger.info(f"Created bot package: {zip_path}")
            return str(zip_path)
            
        except Exception as e:
            logger.error(f"Error creating bot package: {e}")
            raise
    
    def list_versions(self, bot_id: int) -> List[str]:
        """
        List all versions for a bot
        
        Args:
            bot_id: Bot ID
            
        Returns:
            List of version strings
        """
        try:
            prefix = f"bots/{bot_id}/"
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix,
                Delimiter='/'
            )
            
            versions = set()
            for obj in response.get('Contents', []):
                key_parts = obj['Key'].split('/')
                if len(key_parts) >= 4:  # bots/{bot_id}/type/{version}/
                    versions.add(key_parts[3])
            
            return sorted(list(versions), reverse=True)
            
        except ClientError as e:
            logger.error(f"Error listing versions: {e}")
            return []
    
    def get_latest_version(self, bot_id: int, file_type: str = None) -> str:
        try:
            prefix = f"bots/{bot_id}/"
            if file_type:
                prefix += f"{file_type}/"

            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix
            )

            versions = set()
            for obj in response.get('Contents', []):
                key_parts = obj['Key'].split('/')
                # bots/{bot_id}/{file_type}/{version}/filename
                if file_type:
                    version_index = 3
                else:
                    version_index = 2

                if len(key_parts) > version_index:
                    version = key_parts[version_index]
                    # Accept version folders (exclude filenames with extensions like .py, .json)
                    # Version can be "1.0.0", "v1", "latest", etc.
                    if not version.endswith(('.py', '.json', '.txt', '.md', '.yml', '.yaml')):
                        versions.add(version)

            if not versions:
                raise FileNotFoundError(f"No versions found for bot {bot_id} with file_type {file_type}")

            latest = max(versions)
            logger.info(f"Found versions for bot {bot_id}, file_type={file_type}: {sorted(versions)} -> using {latest}")
            return latest

        except ClientError as e:
            logger.error(f"Error getting latest version: {e}")
            raise
    
    def list_files(self, bot_id: int, version: str, file_type: str = None) -> List[str]:
        """
        List files for a specific bot version
        
        Args:
            bot_id: Bot ID
            version: Version string
            file_type: File type filter (code, models, etc.)
            
        Returns:
            List of filenames
        """
        try:
            prefix = f"bots/{bot_id}/"
            if file_type:
                prefix += f"{file_type}/{version}/"
            else:
                prefix += f"{version}/"
            
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix
            )
            
            files = []
            for obj in response.get('Contents', []):
                filename = obj['Key'].split('/')[-1]
                if filename:  # Not a directory
                    files.append(filename)
            
            return files
            
        except ClientError as e:
            logger.error(f"Error listing files: {e}")
            return []
    
    def delete_bot_version(self, bot_id: int, version: str) -> bool:
        """
        Delete a specific version of a bot
        
        Args:
            bot_id: Bot ID
            version: Version to delete
            
        Returns:
            bool: Success status
        """
        try:
            # List all objects for this version
            prefix = f"bots/{bot_id}/"
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix
            )
            
            # Find objects with this version
            objects_to_delete = []
            for obj in response.get('Contents', []):
                if f"/{version}/" in obj['Key']:
                    objects_to_delete.append({'Key': obj['Key']})
            
            if objects_to_delete:
                # Delete objects
                self.s3_client.delete_objects(
                    Bucket=self.bucket_name,
                    Delete={'Objects': objects_to_delete}
                )
                
                logger.info(f"Deleted {len(objects_to_delete)} objects for bot {bot_id} version {version}")
            
            return True
            
        except ClientError as e:
            logger.error(f"Error deleting bot version: {e}")
            return False
    
    def get_bot_metadata(self, bot_id: int, version: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Get metadata for a bot version
        
        Args:
            bot_id: Bot ID
            version: Version string
            
        Returns:
            Dict with bot metadata
        """
        try:
            metadata_prefix = f"bots/{bot_id}/metadata/{version}/"
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=metadata_prefix
            )
            
            metadata = {}
            for obj in response.get('Contents', []):
                key = obj['Key']
                if key.endswith('.json'):
                    response = self.s3_client.get_object(Bucket=self.bucket_name, Key=key)
                    content = json.loads(response['Body'].read().decode('utf-8'))
                    
                    metadata_type = key.split('/')[-1].replace('_metadata.json', '')
                    metadata[metadata_type] = content
            
            return metadata
            
        except ClientError as e:
            logger.error(f"Error getting bot metadata: {e}")
            return {}
    
    def get_storage_stats(self, bot_id: int = None) -> Dict[str, Any]:
        """
        Get storage statistics
        
        Args:
            bot_id: Bot ID (optional, for specific bot stats)
            
        Returns:
            Dict with storage statistics
        """
        try:
            prefix = f"bots/{bot_id}/" if bot_id else "bots/"
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix
            )
            
            stats = {
                "total_objects": 0,
                "total_size": 0,
                "file_types": {},
                "bot_count": 0 if bot_id else len(set()),
                "versions": {}
            }
            
            bot_ids = set()
            for obj in response.get('Contents', []):
                key = obj['Key']
                size = obj['Size']
                
                stats["total_objects"] += 1
                stats["total_size"] += size
                
                # Extract bot ID
                key_parts = key.split('/')
                if len(key_parts) >= 2:
                    bot_ids.add(key_parts[1])
                
                # File type stats
                if '/code/' in key:
                    file_type = 'code'
                elif '/models/' in key:
                    file_type = 'models'
                else:
                    file_type = 'metadata'
                
                if file_type not in stats["file_types"]:
                    stats["file_types"][file_type] = {"count": 0, "size": 0}
                
                stats["file_types"][file_type]["count"] += 1
                stats["file_types"][file_type]["size"] += size
            
            if not bot_id:
                stats["bot_count"] = len(bot_ids)
            
            return stats
            
        except ClientError as e:
            logger.error(f"Error getting storage stats: {e}")
            return {}

# Global S3 manager instance
s3_manager = None

def get_s3_manager() -> S3Manager:
    """Get global S3 manager instance"""
    global s3_manager
    if s3_manager is None:
        # Initialize with environment variables or default config
        s3_manager = S3Manager()
    
    return s3_manager 