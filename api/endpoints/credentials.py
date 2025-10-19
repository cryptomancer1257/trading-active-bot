"""
Exchange Credentials API endpoints
Manages API keys and secrets for developers to connect to exchanges
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from core import crud, models, schemas, security
from core.database import get_db

router = APIRouter()

@router.get("/credentials", response_model=List[schemas.DeveloperExchangeCredentialsPublic])
def list_credentials_alt(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_active_user)
):
    """Get all credentials for current user - alternative endpoint"""
    return list_credentials(skip, limit, db, current_user)

@router.post("/credentials", response_model=schemas.DeveloperExchangeCredentialsPublic)
def create_credentials_alt(
    credentials: schemas.DeveloperExchangeCredentialsCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_active_user)
):
    """Create new exchange credentials - alternative endpoint"""
    return create_credentials(credentials, db, current_user)

@router.post("/", response_model=schemas.DeveloperExchangeCredentialsPublic)
def create_credentials(
    credentials: schemas.DeveloperExchangeCredentialsCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_active_user)
):
    """Create new exchange credentials"""
    
    # Only developers and admins can create credentials
    if current_user.role not in [models.UserRole.DEVELOPER, models.UserRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only developers and admins can manage exchange credentials"
        )
    
    try:
        db_credentials = crud.create_developer_exchange_credentials(
            db=db, 
            credentials=credentials, 
            user_id=current_user.id
        )
        return db_credentials
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create credentials: {str(e)}"
        )

@router.get("/", response_model=List[schemas.DeveloperExchangeCredentialsPublic])
def list_credentials(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_active_user)
):
    """Get all credentials for current user"""
    
    if current_user.role not in [models.UserRole.DEVELOPER, models.UserRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only developers and admins can manage exchange credentials"
        )
    
    credentials = crud.get_user_developer_credentials(
        db=db, 
        user_id=current_user.id, 
        skip=skip, 
        limit=limit
    )
    return credentials

@router.get("/{credentials_id}", response_model=schemas.DeveloperExchangeCredentialsInDB)
def get_credentials(
    credentials_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_active_user)
):
    """Get specific credentials with decrypted secrets (for owner only)"""
    
    if current_user.role not in [models.UserRole.DEVELOPER, models.UserRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only developers and admins can manage exchange credentials"
        )
    
    credentials = crud.get_developer_credentials_by_id(
        db=db, 
        credentials_id=credentials_id, 
        user_id=current_user.id
    )
    
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Credentials not found"
        )
    
    # Decrypt sensitive data for the owner
    decrypted_credentials = schemas.DeveloperExchangeCredentialsInDB(
        id=credentials.id,
        user_id=credentials.user_id,
        exchange_type=credentials.exchange_type,
        credential_type=credentials.credential_type,
        network_type=credentials.network_type,
        name=credentials.name,
        api_key=security.decrypt_sensitive_data(credentials.api_key),
        api_secret=security.decrypt_sensitive_data(credentials.api_secret),
        passphrase=security.decrypt_sensitive_data(credentials.passphrase) if credentials.passphrase else None,
        is_default=credentials.is_default,
        is_active=credentials.is_active,
        last_used_at=credentials.last_used_at,
        created_at=credentials.created_at,
        updated_at=credentials.updated_at
    )
    
    return decrypted_credentials

@router.get("/default/{exchange_type}/{credential_type}/{network_type}", response_model=Optional[schemas.DeveloperExchangeCredentialsInDB])
def get_default_credentials(
    exchange_type: models.ExchangeType,
    credential_type: models.CredentialType,
    network_type: models.NetworkType,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_active_user)
):
    """Get default credentials for specific exchange/type/network combination"""
    
    # Allow both DEVELOPER and ADMIN roles
    if current_user.role not in [models.UserRole.DEVELOPER, models.UserRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only developers and admins can manage exchange credentials"
        )
    
    credentials = crud.get_default_developer_credentials(
        db=db,
        user_id=current_user.id,
        exchange_type=exchange_type,
        credential_type=credential_type,
        network_type=network_type
    )
    
    if not credentials:
        return None
    
    # Decrypt sensitive data for the owner
    decrypted_credentials = schemas.DeveloperExchangeCredentialsInDB(
        id=credentials.id,
        user_id=credentials.user_id,
        exchange_type=credentials.exchange_type,
        credential_type=credentials.credential_type,
        network_type=credentials.network_type,
        name=credentials.name,
        api_key=security.decrypt_sensitive_data(credentials.api_key),
        api_secret=security.decrypt_sensitive_data(credentials.api_secret),
        passphrase=security.decrypt_sensitive_data(credentials.passphrase) if credentials.passphrase else None,
        is_default=credentials.is_default,
        is_active=credentials.is_active,
        last_used_at=credentials.last_used_at,
        created_at=credentials.created_at,
        updated_at=credentials.updated_at
    )
    
    return decrypted_credentials

@router.put("/{credentials_id}", response_model=schemas.DeveloperExchangeCredentialsPublic)
def update_credentials(
    credentials_id: int,
    credentials_update: schemas.DeveloperExchangeCredentialsUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_active_user)
):
    """Update exchange credentials"""
    
    if current_user.role not in [models.UserRole.DEVELOPER, models.UserRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only developers and admins can manage exchange credentials"
        )
    
    updated_credentials = crud.update_developer_exchange_credentials(
        db=db,
        credentials_id=credentials_id,
        user_id=current_user.id,
        credentials_update=credentials_update
    )
    
    if not updated_credentials:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Credentials not found"
        )
    
    return updated_credentials

@router.delete("/{credentials_id}")
def delete_credentials(
    credentials_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_active_user)
):
    """Delete exchange credentials"""
    import logging
    logger = logging.getLogger(__name__)
    
    logger.info(f"DELETE request for credential {credentials_id} by user {current_user.id} ({current_user.email})")
    
    if current_user.role not in [models.UserRole.DEVELOPER, models.UserRole.ADMIN]:
        logger.warning(f"User {current_user.id} is not a developer/admin, role={current_user.role}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only developers and admins can manage exchange credentials"
        )
    
    deleted_credentials = crud.delete_developer_exchange_credentials(
        db=db,
        credentials_id=credentials_id,
        user_id=current_user.id
    )
    
    if not deleted_credentials:
        logger.warning(f"Credential {credentials_id} not found for user {current_user.id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Credentials {credentials_id} not found or you don't have permission to delete it"
        )
    
    logger.info(f"Successfully soft-deleted credential {credentials_id}")
    return {"message": "Credentials deleted successfully"}

@router.post("/{credentials_id}/mark-used")
def mark_credentials_used(
    credentials_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_active_user)
):
    """Mark credentials as recently used (updates last_used_at)"""
    
    if current_user.role not in [models.UserRole.DEVELOPER, models.UserRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only developers and admins can manage exchange credentials"
        )
    
    # Verify ownership
    credentials = crud.get_developer_credentials_by_id(
        db=db, 
        credentials_id=credentials_id, 
        user_id=current_user.id
    )
    
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Credentials not found"
        )
    
    crud.update_developer_credentials_last_used(db=db, credentials_id=credentials_id)
    
    return {"message": "Credentials marked as used"}
