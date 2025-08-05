"""
API endpoints for managing user principal IDs
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import logging

from core import models, schemas
from core.database import get_db
from core.security import get_current_user
from sqlalchemy.exc import IntegrityError

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/", response_model=schemas.UserPrincipalResponse)
async def add_principal_id(
    request: schemas.UserPrincipalCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Add a new principal ID for the current user
    """
    try:
        # Check if principal_id already exists
        existing_principal = db.query(models.UserPrincipal).filter(
            models.UserPrincipal.principal_id == request.principal_id
        ).first()
        
        if existing_principal:
            if existing_principal.user_id == current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Principal ID already exists for this user"
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Principal ID already belongs to another user"
                )
        
        # Create new user principal mapping
        user_principal = models.UserPrincipal(
            user_id=current_user.id,
            principal_id=request.principal_id,
            status=models.UserPrincipalStatus.ACTIVE
        )
        
        db.add(user_principal)
        db.commit()
        db.refresh(user_principal)
        
        logger.info(f"User {current_user.id} added principal ID: {request.principal_id}")
        
        return user_principal
        
    except IntegrityError as e:
        db.rollback()
        logger.error(f"Database integrity error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Principal ID already exists"
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to add principal ID: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add principal ID"
        )


@router.get("/", response_model=List[schemas.UserPrincipalResponse])
async def get_user_principals(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all principal IDs for the current user
    """
    try:
        principals = db.query(models.UserPrincipal).filter(
            models.UserPrincipal.user_id == current_user.id
        ).order_by(models.UserPrincipal.created_at.desc()).all()
        
        return principals
        
    except Exception as e:
        logger.error(f"Failed to get user principals: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve principal IDs"
        )


@router.get("/{principal_id}", response_model=schemas.UserPrincipalResponse)
async def get_principal_by_id(
    principal_id: str,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get specific principal ID details for the current user
    """
    try:
        principal = db.query(models.UserPrincipal).filter(
            models.UserPrincipal.principal_id == principal_id,
            models.UserPrincipal.user_id == current_user.id
        ).first()
        
        if not principal:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Principal ID not found"
            )
        
        return principal
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get principal: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve principal ID"
        )


@router.put("/{principal_id}", response_model=schemas.UserPrincipalResponse)
async def update_principal_status(
    principal_id: str,
    request: schemas.UserPrincipalUpdate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update principal ID status (active/inactive)
    """
    try:
        principal = db.query(models.UserPrincipal).filter(
            models.UserPrincipal.principal_id == principal_id,
            models.UserPrincipal.user_id == current_user.id
        ).first()
        
        if not principal:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Principal ID not found"
            )
        
        # Update fields
        if request.status is not None:
            principal.status = request.status
        
        db.commit()
        db.refresh(principal)
        
        logger.info(f"User {current_user.id} updated principal {principal_id} status to {request.status}")
        
        return principal
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to update principal: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update principal ID"
        )


@router.delete("/{principal_id}")
async def deactivate_principal(
    principal_id: str,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Deactivate (soft delete) a principal ID
    """
    try:
        principal = db.query(models.UserPrincipal).filter(
            models.UserPrincipal.principal_id == principal_id,
            models.UserPrincipal.user_id == current_user.id
        ).first()
        
        if not principal:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Principal ID not found"
            )
        
        # Soft delete by setting status to inactive
        principal.status = models.UserPrincipalStatus.INACTIVE
        db.commit()
        
        logger.info(f"User {current_user.id} deactivated principal ID: {principal_id}")
        
        return {"message": "Principal ID deactivated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to deactivate principal: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to deactivate principal ID"
        )


# Admin endpoints (optional, for managing all principals)
@router.get("/admin/all", response_model=List[schemas.UserPrincipalResponse])
async def get_all_principals(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Admin only: Get all principal mappings
    """
    if current_user.role != models.UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    try:
        principals = db.query(models.UserPrincipal).order_by(
            models.UserPrincipal.created_at.desc()
        ).all()
        
        return principals
        
    except Exception as e:
        logger.error(f"Failed to get all principals: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve principals"
        )