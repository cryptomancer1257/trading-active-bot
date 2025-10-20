"""
Feature Flags API Endpoints
Manage feature flags for controlling feature visibility
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from core.database import get_db
from core import models, schemas
from core.security import get_current_user
from core.models import UserRole

router = APIRouter()


def require_admin(current_user: models.User = Depends(get_current_user)):
    """Dependency to require admin role"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user


@router.get("/", response_model=schemas.FeatureFlagsListResponse)
def get_all_feature_flags(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_admin)
):
    """
    Get all feature flags (Admin only)
    """
    flags = db.query(models.FeatureFlag).order_by(models.FeatureFlag.flag_key).all()
    return {
        "flags": flags,
        "total": len(flags)
    }


@router.get("/public", response_model=List[schemas.FeatureFlagResponse])
def get_public_feature_flags(db: Session = Depends(get_db)):
    """
    Get all enabled feature flags (Public endpoint)
    No authentication required - used by frontend to check feature availability
    """
    flags = db.query(models.FeatureFlag).filter(
        models.FeatureFlag.is_enabled == True
    ).all()
    return flags


@router.get("/check/{flag_key}", response_model=dict)
def check_feature_flag(
    flag_key: str,
    db: Session = Depends(get_db)
):
    """
    Check if a specific feature flag is enabled (Public endpoint)
    Returns: {"flag_key": "...", "is_enabled": true/false}
    """
    flag = db.query(models.FeatureFlag).filter(
        models.FeatureFlag.flag_key == flag_key
    ).first()
    
    if not flag:
        # If flag doesn't exist, assume disabled
        return {"flag_key": flag_key, "is_enabled": False}
    
    return {"flag_key": flag.flag_key, "is_enabled": flag.is_enabled}


@router.get("/{flag_id}", response_model=schemas.FeatureFlagResponse)
def get_feature_flag(
    flag_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_admin)
):
    """
    Get a specific feature flag by ID (Admin only)
    """
    flag = db.query(models.FeatureFlag).filter(models.FeatureFlag.id == flag_id).first()
    if not flag:
        raise HTTPException(status_code=404, detail="Feature flag not found")
    return flag


@router.post("/", response_model=schemas.FeatureFlagResponse, status_code=status.HTTP_201_CREATED)
def create_feature_flag(
    flag: schemas.FeatureFlagCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_admin)
):
    """
    Create a new feature flag (Admin only)
    """
    # Check if flag_key already exists
    existing = db.query(models.FeatureFlag).filter(
        models.FeatureFlag.flag_key == flag.flag_key
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Feature flag with key '{flag.flag_key}' already exists"
        )
    
    db_flag = models.FeatureFlag(**flag.dict())
    db.add(db_flag)
    db.commit()
    db.refresh(db_flag)
    return db_flag


@router.put("/{flag_id}", response_model=schemas.FeatureFlagResponse)
def update_feature_flag(
    flag_id: int,
    flag_update: schemas.FeatureFlagUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_admin)
):
    """
    Update a feature flag (Admin only)
    """
    db_flag = db.query(models.FeatureFlag).filter(models.FeatureFlag.id == flag_id).first()
    if not db_flag:
        raise HTTPException(status_code=404, detail="Feature flag not found")
    
    # Update fields if provided
    update_data = flag_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_flag, field, value)
    
    db.commit()
    db.refresh(db_flag)
    return db_flag


@router.patch("/{flag_id}/toggle", response_model=schemas.FeatureFlagResponse)
def toggle_feature_flag(
    flag_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_admin)
):
    """
    Toggle a feature flag on/off (Admin only)
    """
    db_flag = db.query(models.FeatureFlag).filter(models.FeatureFlag.id == flag_id).first()
    if not db_flag:
        raise HTTPException(status_code=404, detail="Feature flag not found")
    
    db_flag.is_enabled = not db_flag.is_enabled
    db.commit()
    db.refresh(db_flag)
    return db_flag


@router.delete("/{flag_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_feature_flag(
    flag_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_admin)
):
    """
    Delete a feature flag (Admin only)
    """
    db_flag = db.query(models.FeatureFlag).filter(models.FeatureFlag.id == flag_id).first()
    if not db_flag:
        raise HTTPException(status_code=404, detail="Feature flag not found")
    
    db.delete(db_flag)
    db.commit()
    return None
