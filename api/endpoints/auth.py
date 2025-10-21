import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# file: api/endpoints/auth.py

from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import Annotated, List, Optional
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
import os
from datetime import datetime, timedelta
import secrets

from core import crud, schemas, security
from core.database import get_db
from services.email_service import email_service

router = APIRouter()

@router.post("/register", response_model=schemas.UserInDB)
def register_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    """Register a new user"""
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create user with email_verified = False
    new_user = crud.create_user(db=db, user=user)
    
    # Generate verification token
    verification_token = secrets.token_urlsafe(32)
    new_user.verification_token = verification_token
    new_user.verification_token_expires = datetime.utcnow() + timedelta(hours=24)
    new_user.email_verified = False
    db.commit()
    db.refresh(new_user)
    
    # Send verification email
    # Use developer_name if available, otherwise use email as username
    username = new_user.developer_name if new_user.developer_name else new_user.email.split('@')[0]
    email_service.send_verification_email(
        to_email=new_user.email,
        username=username,
        verification_token=verification_token
    )
    
    return new_user

@router.post("/token", response_model=schemas.Token)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Session = Depends(get_db)
):
    """Login and get access token"""
    user = crud.get_user_by_email(db, email=form_data.username)
    if not user or not security.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if email is verified
    if not user.email_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email not verified. Please check your inbox and verify your email address.",
        )
    
    access_token = security.create_access_token(
        data={"sub": str(user.id), "role": user.role.value}
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/google", response_model=schemas.Token)
async def google_auth(
    credential: str = Body(..., embed=True),
    db: Session = Depends(get_db)
):
    """
    Authenticate with Google OAuth 2.0
    
    Args:
        credential: Google OAuth credential (JWT token from Google Sign-In)
        db: Database session
    
    Returns:
        Access token and token type
        
    Raises:
        HTTPException: If token is invalid or user creation fails
    """
    try:
        # Verify the Google token
        # Get Google Client ID from environment variable
        google_client_id = os.getenv("GOOGLE_CLIENT_ID")
        if not google_client_id:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Google OAuth not configured. Please set GOOGLE_CLIENT_ID environment variable."
            )
        
        # Verify the token with Google
        idinfo = id_token.verify_oauth2_token(
            credential, 
            google_requests.Request(), 
            google_client_id
        )
        
        # Extract user information from Google token
        email = idinfo.get('email')
        name = idinfo.get('name', '')
        picture = idinfo.get('picture', '')
        google_id = idinfo.get('sub')
        
        if not email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email not provided by Google"
            )
        
        # Check if user exists
        user = crud.get_user_by_email(db, email=email)
        
        if not user:
            # Create new user with Google OAuth
            # Generate a random password (user won't use it for Google login)
            random_password = secrets.token_urlsafe(32)
            
            user_create = schemas.UserCreate(
                email=email,
                password=random_password,
                role=schemas.UserRole.DEVELOPER,  # Default to DEVELOPER for Google OAuth users
                full_name=name
            )
            user = crud.create_user(db=db, user=user_create)
            
            # Mark email as verified for Google OAuth users
            user.email_verified = True
            user.verification_token = None
            user.verification_token_expires = None
            db.commit()
            db.refresh(user)
        else:
            # For existing users logging in via Google, also mark email as verified
            if not user.email_verified:
                user.email_verified = True
                user.verification_token = None
                user.verification_token_expires = None
                db.commit()
                db.refresh(user)
        
        # Generate access token for the user
        access_token = security.create_access_token(
            data={"sub": str(user.id), "role": user.role.value}
        )
        
        return {"access_token": access_token, "token_type": "bearer"}
        
    except ValueError as e:
        # Invalid token
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid Google token: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Authentication failed: {str(e)}"
        )

@router.post("/verify-email")
async def verify_email(
    token: str = Query(..., description="Email verification token"),
    db: Session = Depends(get_db)
):
    """Verify user's email address"""
    # Find user by verification token
    user = db.query(crud.models.User).filter(
        crud.models.User.verification_token == token
    ).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid verification token"
        )
    
    # Check if token is expired
    if user.verification_token_expires and user.verification_token_expires < datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Verification token has expired. Please request a new one."
        )
    
    # Mark email as verified
    user.email_verified = True
    user.verification_token = None
    user.verification_token_expires = None
    db.commit()
    
    return {
        "success": True,
        "message": "Email verified successfully. You can now log in."
    }

@router.post("/resend-verification")
async def resend_verification_email(
    email: str = Body(..., embed=True),
    db: Session = Depends(get_db)
):
    """Resend verification email"""
    user = crud.get_user_by_email(db, email=email)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if user.email_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is already verified"
        )
    
    # Generate new verification token
    verification_token = secrets.token_urlsafe(32)
    user.verification_token = verification_token
    user.verification_token_expires = datetime.utcnow() + timedelta(hours=24)
    db.commit()
    
    # Send verification email
    # Use developer_name if available, otherwise use email as username
    username = user.developer_name if user.developer_name else user.email.split('@')[0]
    email_sent = email_service.send_verification_email(
        to_email=user.email,
        username=username,
        verification_token=verification_token
    )
    
    if not email_sent:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send verification email. Please try again later."
        )
    
    return {
        "success": True,
        "message": "Verification email sent. Please check your inbox."
    }

@router.post("/forgot-password")
async def forgot_password(
    email: str = Body(..., embed=True),
    db: Session = Depends(get_db)
):
    """Request password reset email"""
    user = crud.get_user_by_email(db, email=email)
    
    # Don't reveal if user exists or not for security
    if not user:
        return {
            "success": True,
            "message": "If an account exists with this email, a password reset link will be sent."
        }
    
    # Generate reset token
    reset_token = secrets.token_urlsafe(32)
    user.reset_password_token = reset_token
    user.reset_password_token_expires = datetime.utcnow() + timedelta(hours=1)
    db.commit()
    
    # Send reset email
    username = user.developer_name if user.developer_name else user.email.split('@')[0]
    email_sent = email_service.send_password_reset_email(
        to_email=user.email,
        username=username,
        reset_token=reset_token
    )
    
    if not email_sent:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send reset email. Please try again later."
        )
    
    return {
        "success": True,
        "message": "If an account exists with this email, a password reset link will be sent."
    }

@router.post("/reset-password")
async def reset_password(
    token: str = Body(...),
    new_password: str = Body(..., min_length=8),
    db: Session = Depends(get_db)
):
    """Reset password using reset token"""
    # Find user by reset token
    user = db.query(crud.models.User).filter(
        crud.models.User.reset_password_token == token
    ).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )
    
    # Check if token is expired
    if user.reset_password_token_expires and user.reset_password_token_expires < datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reset token has expired. Please request a new one."
        )
    
    # Update password
    user.hashed_password = security.get_password_hash(new_password)
    user.reset_password_token = None
    user.reset_password_token_expires = None
    db.commit()
    
    return {
        "success": True,
        "message": "Password reset successfully. You can now log in with your new password."
    }

@router.get("/me", response_model=schemas.UserProfile)
def get_current_user_profile(
    current_user: schemas.UserInDB = Depends(security.get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get current user profile with statistics"""
    return crud.get_user_profile(db, user_id=current_user.id)

@router.put("/me", response_model=schemas.UserInDB)
def update_user_profile(
    user_update: schemas.UserUpdate,
    current_user: schemas.UserInDB = Depends(security.get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update current user profile"""
    return crud.update_user(db, user_id=current_user.id, user_update=user_update)

@router.get("/users", response_model=List[schemas.UserInDB])
def list_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: schemas.UserInDB = Depends(security.get_current_active_admin)
):
    """List all users (admin only)"""
    return crud.get_users(db, skip=skip, limit=limit)

@router.get("/users/{user_id}", response_model=schemas.UserProfile)
def get_user_profile(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: schemas.UserInDB = Depends(security.get_current_active_user)
):
    """Get user profile by ID"""
    if current_user.id != user_id and current_user.role != schemas.UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    user_profile = crud.get_user_profile(db, user_id=user_id)
    if not user_profile:
        raise HTTPException(status_code=404, detail="User not found")
    return user_profile

# --- Exchange Credentials Endpoints ---
@router.get("/me/credentials", response_model=List[schemas.ExchangeCredentialsPublic])
def get_my_exchange_credentials(
    exchange: Optional[str] = Query(None, description="Filter by exchange"),
    is_testnet: Optional[bool] = Query(None, description="Filter by testnet/mainnet"),
    current_user: schemas.UserInDB = Depends(security.get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get current user's exchange credentials"""
    credentials = crud.get_user_exchange_credentials(
        db, user_id=current_user.id, exchange=exchange, is_testnet=is_testnet
    )
    
    # Convert to public view (hide sensitive data)
    result = []
    for cred in credentials:
        result.append(schemas.ExchangeCredentialsPublic(
            id=cred.id,
            exchange=cred.exchange,
            is_testnet=cred.is_testnet,
            is_active=cred.is_active,
            validation_status=cred.validation_status,
            last_validated=cred.last_validated,
            api_key_preview=cred.api_key[:8] + "..." if len(cred.api_key) > 8 else cred.api_key
        ))
    
    return result

@router.post("/me/credentials", response_model=schemas.ExchangeCredentialsPublic, status_code=status.HTTP_201_CREATED)
def create_exchange_credentials(
    credentials: schemas.ExchangeCredentialsCreate,
    current_user: schemas.UserInDB = Depends(security.get_current_active_user),
    db: Session = Depends(get_db)
):
    """Add new exchange credentials"""
    try:
        new_credentials = crud.create_exchange_credentials(
            db, credentials=credentials, user_id=current_user.id
        )
        
        # Return public view
        return schemas.ExchangeCredentialsPublic(
            id=new_credentials.id,
            exchange=new_credentials.exchange,
            is_testnet=new_credentials.is_testnet,
            is_active=new_credentials.is_active,
            validation_status=new_credentials.validation_status,
            last_validated=new_credentials.last_validated,
            api_key_preview=new_credentials.api_key[:8] + "..." if len(new_credentials.api_key) > 8 else new_credentials.api_key
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create credentials: {str(e)}")

@router.put("/me/credentials/{credentials_id}", response_model=schemas.ExchangeCredentialsPublic)
def update_exchange_credentials(
    credentials_id: int,
    credentials_update: schemas.ExchangeCredentialsUpdate,
    current_user: schemas.UserInDB = Depends(security.get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update exchange credentials"""
    updated_credentials = crud.update_exchange_credentials(
        db, credentials_id=credentials_id, user_id=current_user.id, credentials_update=credentials_update
    )
    
    if not updated_credentials:
        raise HTTPException(status_code=404, detail="Credentials not found")
    
    # Return public view
    return schemas.ExchangeCredentialsPublic(
        id=updated_credentials.id,
        exchange=updated_credentials.exchange,
        is_testnet=updated_credentials.is_testnet,
        is_active=updated_credentials.is_active,
        validation_status=updated_credentials.validation_status,
        last_validated=updated_credentials.last_validated,
        api_key_preview=updated_credentials.api_key[:8] + "..." if len(updated_credentials.api_key) > 8 else updated_credentials.api_key
    )

@router.delete("/me/credentials/{credentials_id}")
def delete_exchange_credentials(
    credentials_id: int,
    current_user: schemas.UserInDB = Depends(security.get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete exchange credentials"""
    success = crud.delete_exchange_credentials(
        db, credentials_id=credentials_id, user_id=current_user.id
    )
    
    if not success:
        raise HTTPException(status_code=404, detail="Credentials not found")
    
    return {"message": "Credentials deleted successfully"}

@router.post("/me/credentials/{credentials_id}/validate", response_model=schemas.ExchangeCredentialsValidation)
def validate_exchange_credentials(
    credentials_id: int,
    current_user: schemas.UserInDB = Depends(security.get_current_active_user),
    db: Session = Depends(get_db)
):
    """Validate specific exchange credentials"""
    # Get credentials
    credentials = crud.get_exchange_credentials_by_id(
        db, credentials_id=credentials_id, user_id=current_user.id
    )
    
    if not credentials:
        raise HTTPException(status_code=404, detail="Credentials not found")
    
    # Validate using exchange factory
    from services.exchange_factory import validate_exchange_credentials
    
    is_valid, message = validate_exchange_credentials(
        exchange_name=credentials.exchange.value,
        api_key=credentials.api_key,
        api_secret=credentials.api_secret,
        testnet=credentials.is_testnet
    )
    
    # Update validation status in database
    crud.update_credentials_validation(db, credentials_id, is_valid, message)
    
    return schemas.ExchangeCredentialsValidation(
        valid=is_valid,
        message=message,
        exchange=credentials.exchange,
        is_testnet=credentials.is_testnet
    )