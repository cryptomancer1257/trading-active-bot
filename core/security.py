# file: security.py

import os
import sys
from datetime import datetime, timedelta
from typing import Optional, Annotated

from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status, Header
from fastapi.security import OAuth2PasswordBearer, APIKeyHeader
from sqlalchemy.orm import Session

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core import crud, models, schemas
from core.database import get_db

# Lấy các biến từ .env hoặc dùng giá trị mặc định
SECRET_KEY = os.getenv("SECRET_KEY", "a_super_secret_key_for_dev")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 # 24 giờ

# Cấu hình mã hóa mật khẩu
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Cấu hình OAuth2
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Kiểm tra mật khẩu thô với mật khẩu đã mã hóa."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Mã hóa mật khẩu."""
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Tạo một JWT access token mới."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# --- Dependencies để bảo vệ Endpoints ---

async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)], db: Session = Depends(get_db)) -> models.User:
    """
    Giải mã token, lấy user_id và truy xuất thông tin user từ DB.
    Đây là dependency cơ bản nhất để xác thực.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = crud.get_user(db, user_id=int(user_id))
    if user is None:
        raise credentials_exception
    return user

async def get_current_active_user(current_user: Annotated[models.User, Depends(get_current_user)]) -> models.User:
    """Kiểm tra xem user có bị vô hiệu hóa hay không (nếu có trường is_active)."""
    # if current_user.disabled:
    #     raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

async def get_current_active_developer(current_user: Annotated[models.User, Depends(get_current_active_user)]) -> models.User:
    """Yêu cầu người dùng phải có vai trò là DEVELOPER hoặc ADMIN."""
    if current_user.role.value not in ["DEVELOPER", "ADMIN"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Operation not permitted for your role"
        )
    return current_user

async def get_current_active_admin(current_user: Annotated[models.User, Depends(get_current_active_user)]) -> models.User:
    """Yêu cầu người dùng phải có vai trò là ADMIN."""
    if current_user.role.value != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You must be an admin to perform this action"
        )
    return current_user

# --- API Key Authentication for Marketplace ---
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

async def get_user_by_api_key(api_key: str = Depends(api_key_header), db: Session = Depends(get_db)) -> models.User:
    """
    Authenticate user by API key for marketplace integration.
    This allows external systems to authenticate using API keys.
    """
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key is required",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    
    # Find user by API key
    user = crud.get_user_by_api_key(db, api_key=api_key)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is inactive"
        )
    
    return user

# Get marketplace API key from environment or use default for development
MARKETPLACE_API_KEY = os.getenv("MARKETPLACE_API_KEY", "marketplace_dev_api_key_12345")

async def validate_marketplace_api_key(api_key: str = Depends(api_key_header)) -> bool:
    """
    Validate marketplace API key from header (dynamic from environment).
    No user object needed.
    """
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key is required",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    
    # Check against environment variable API key
    if api_key != MARKETPLACE_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid marketplace API key",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    
    return True  # Just return True, no user object needed

async def get_marketplace_user(current_user: Annotated[models.User, Depends(get_user_by_api_key)]) -> models.User:
    """
    Dependency for marketplace endpoints that require API key authentication.
    """
    return current_user

# ========================
# Encryption/Decryption for sensitive data
# ========================

import base64
from cryptography.fernet import Fernet

# Generate or get encryption key (in production, store this securely)
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY", Fernet.generate_key())
if isinstance(ENCRYPTION_KEY, str):
    ENCRYPTION_KEY = ENCRYPTION_KEY.encode()
    
fernet = Fernet(ENCRYPTION_KEY)

def encrypt_sensitive_data(data: str) -> str:
    """Encrypt sensitive data like API keys"""
    if not data:
        return data
    
    encrypted_data = fernet.encrypt(data.encode())
    return base64.b64encode(encrypted_data).decode()

def decrypt_sensitive_data(encrypted_data: str) -> str:
    """Decrypt sensitive data like API keys"""
    if not encrypted_data:
        return encrypted_data
    
    try:
        decoded_data = base64.b64decode(encrypted_data.encode())
        decrypted_data = fernet.decrypt(decoded_data)
        return decrypted_data.decode()
    except Exception:
        # If decryption fails, return original data (for backward compatibility)
        return encrypted_data