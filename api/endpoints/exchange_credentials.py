"""
Exchange Credentials Management API
Secure management of user's exchange API keys with encryption
"""

import logging
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from core.database import get_db
from core import models, schemas, security
from core.api_key_manager import api_key_manager

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/credentials", response_model=Dict[str, Any])
async def create_exchange_credentials(
    exchange: str,
    api_key: str,
    api_secret: str,
    api_passphrase: str = None,
    is_testnet: bool = True,
    current_user: models.User = Depends(security.get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Create or update exchange credentials for current user
    
    Args:
        exchange: Exchange name (BINANCE, COINBASE, KRAKEN)
        api_key: Exchange API key (will be encrypted)
        api_secret: Exchange API secret (will be encrypted)
        api_passphrase: Exchange API passphrase (optional, will be encrypted)
        is_testnet: Whether these are testnet credentials
    """
    try:
        # Validate exchange
        if exchange.upper() not in ["BINANCE", "COINBASE", "KRAKEN"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unsupported exchange. Supported: BINANCE, COINBASE, KRAKEN"
            )
        
        # Store encrypted credentials
        success = api_key_manager.store_user_exchange_credentials(
            db=db,
            user_id=current_user.id,
            exchange=exchange.upper(),
            api_key=api_key,
            api_secret=api_secret,
            api_passphrase=api_passphrase,
            is_testnet=is_testnet
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to store exchange credentials"
            )
        
        # Validate credentials after storing
        is_valid = api_key_manager.validate_exchange_credentials(
            db=db,
            user_id=current_user.id,
            exchange=exchange.upper(),
            is_testnet=is_testnet
        )
        
        return {
            "status": "success",
            "message": f"Exchange credentials stored and validated",
            "exchange": exchange.upper(),
            "is_testnet": is_testnet,
            "validation_status": "valid" if is_valid else "invalid"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create exchange credentials: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.get("/credentials", response_model=List[Dict[str, Any]])
async def get_user_exchange_credentials(
    current_user: models.User = Depends(security.get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all exchange credentials for current user (without revealing keys)"""
    try:
        credentials = api_key_manager.get_all_user_exchanges(db, current_user.id)
        return credentials
        
    except Exception as e:
        logger.error(f"Failed to get exchange credentials: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.get("/credentials/{exchange}", response_model=Dict[str, Any])
async def get_specific_exchange_credentials(
    exchange: str,
    is_testnet: bool = True,
    current_user: models.User = Depends(security.get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get specific exchange credentials (metadata only, no actual keys)"""
    try:
        credentials = api_key_manager.get_user_exchange_credentials(
            db=db,
            user_id=current_user.id,
            exchange=exchange.upper(),
            is_testnet=is_testnet
        )
        
        if not credentials:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No {exchange} credentials found"
            )
        
        # Return metadata only (never expose actual keys)
        return {
            "exchange": credentials["exchange"],
            "is_testnet": credentials["is_testnet"],
            "validation_status": credentials["validation_status"],
            "last_validated": credentials["last_validated"],
            "has_api_key": bool(credentials["api_key"]),
            "has_api_secret": bool(credentials["api_secret"]),
            "has_api_passphrase": bool(credentials["api_passphrase"])
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get specific exchange credentials: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.post("/credentials/{exchange}/validate", response_model=Dict[str, Any])
async def validate_exchange_credentials(
    exchange: str,
    is_testnet: bool = True,
    current_user: models.User = Depends(security.get_current_active_user),
    db: Session = Depends(get_db)
):
    """Validate exchange credentials by testing API connection"""
    try:
        is_valid = api_key_manager.validate_exchange_credentials(
            db=db,
            user_id=current_user.id,
            exchange=exchange.upper(),
            is_testnet=is_testnet
        )
        
        return {
            "exchange": exchange.upper(),
            "is_testnet": is_testnet,
            "validation_status": "valid" if is_valid else "invalid",
            "message": "Credentials are valid" if is_valid else "Credentials are invalid or connectivity failed"
        }
        
    except Exception as e:
        logger.error(f"Failed to validate exchange credentials: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to validate credentials"
        )

@router.delete("/credentials/{exchange}", response_model=Dict[str, Any])
async def delete_exchange_credentials(
    exchange: str,
    is_testnet: bool = True,
    current_user: models.User = Depends(security.get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete exchange credentials"""
    try:
        # Find credentials
        credentials_list = db.query(models.ExchangeCredentials).filter(
            models.ExchangeCredentials.user_id == current_user.id,
            models.ExchangeCredentials.exchange == models.ExchangeType(exchange.upper()),
            models.ExchangeCredentials.is_testnet == is_testnet
        ).all()
        
        if not credentials_list:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No {exchange} credentials found"
            )
        
        # Delete credentials
        for cred in credentials_list:
            db.delete(cred)
        
        db.commit()
        
        return {
            "status": "success",
            "message": f"{exchange} credentials deleted successfully",
            "exchange": exchange.upper(),
            "is_testnet": is_testnet
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete exchange credentials: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete credentials"
        )

# Admin endpoints for managing user credentials
@router.get("/admin/users/{user_id}/credentials", response_model=List[Dict[str, Any]])
async def admin_get_user_credentials(
    user_id: int,
    current_user: models.User = Depends(security.get_current_active_admin),
    db: Session = Depends(get_db)
):
    """Admin: Get all exchange credentials for specific user"""
    try:
        credentials = api_key_manager.get_all_user_exchanges(db, user_id)
        return credentials
        
    except Exception as e:
        logger.error(f"Admin failed to get user credentials: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

# Marketplace endpoint for getting credentials by principal ID
@router.get("/marketplace/credentials/{principal_id}", response_model=Dict[str, Any])
async def get_credentials_by_principal_id(
    principal_id: str,
    exchange: str = "BINANCE",
    is_testnet: bool = True,
    api_key: str = Depends(security.api_key_header),
    db: Session = Depends(get_db)
):
    """
    Marketplace: Get exchange credentials by ICP Principal ID
    Requires valid marketplace API key
    """
    try:
        # Verify marketplace API key
        if api_key != security.MARKETPLACE_API_KEY:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid marketplace API key"
            )
        
        credentials = api_key_manager.get_user_credentials_by_principal_id(
            db=db,
            user_principal_id=principal_id,
            exchange=exchange.upper(),
            is_testnet=is_testnet
        )
        
        if not credentials:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No {exchange} credentials found for principal ID: {principal_id}"
            )
        
        # Return actual credentials for marketplace (bot usage)
        # Note: This is secure because it requires marketplace API key
        return {
            "api_key": credentials["api_key"],
            "api_secret": credentials["api_secret"],
            "api_passphrase": credentials["api_passphrase"],
            "exchange": credentials["exchange"],
            "is_testnet": credentials["is_testnet"],
            "validation_status": credentials["validation_status"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Marketplace failed to get credentials: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

