from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import logging

from core.database import get_db
from core import models, schemas
from core.security import get_current_user
from core.models import FeatureFlagType

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin/feature-flags", tags=["Admin - Feature Flags"])

# Pydantic schemas for Feature Flags
from pydantic import BaseModel

class FeatureFlagBase(BaseModel):
    feature_type: FeatureFlagType
    is_enabled: bool
    disabled_from: Optional[datetime] = None
    disabled_until: Optional[datetime] = None
    reason: Optional[str] = None

class FeatureFlagCreate(FeatureFlagBase):
    pass

class FeatureFlagUpdate(BaseModel):
    is_enabled: Optional[bool] = None
    disabled_from: Optional[datetime] = None
    disabled_until: Optional[datetime] = None
    reason: Optional[str] = None

class FeatureFlagResponse(FeatureFlagBase):
    id: int
    created_by: Optional[int]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

def require_admin(current_user: models.User = Depends(get_current_user)):
    """Require admin role for feature flag management"""
    if current_user.role != models.UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user

@router.get("/", response_model=List[FeatureFlagResponse])
async def get_all_feature_flags(
    db: Session = Depends(get_db),
    admin_user: models.User = Depends(require_admin)
):
    """Get all feature flags (Admin only)"""
    try:
        flags = db.query(models.FeatureFlag).all()
        return flags
    except Exception as e:
        logger.error(f"Error fetching feature flags: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch feature flags"
        )

@router.get("/{feature_type}", response_model=FeatureFlagResponse)
async def get_feature_flag(
    feature_type: FeatureFlagType,
    db: Session = Depends(get_db),
    admin_user: models.User = Depends(require_admin)
):
    """Get specific feature flag (Admin only)"""
    try:
        flag = db.query(models.FeatureFlag).filter(
            models.FeatureFlag.feature_type == feature_type
        ).first()
        
        if not flag:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Feature flag {feature_type} not found"
            )
        
        return flag
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching feature flag {feature_type}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch feature flag"
        )

@router.put("/{feature_type}", response_model=FeatureFlagResponse)
async def update_feature_flag(
    feature_type: FeatureFlagType,
    update_data: FeatureFlagUpdate,
    db: Session = Depends(get_db),
    admin_user: models.User = Depends(require_admin)
):
    """Update feature flag (Admin only)"""
    try:
        flag = db.query(models.FeatureFlag).filter(
            models.FeatureFlag.feature_type == feature_type
        ).first()
        
        if not flag:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Feature flag {feature_type} not found"
            )
        
        # Update fields
        update_dict = update_data.dict(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(flag, field, value)
        
        flag.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(flag)
        
        logger.info(f"Feature flag {feature_type} updated by admin {admin_user.id}: {update_dict}")
        return flag
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating feature flag {feature_type}: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update feature flag"
        )

@router.post("/disable-plan-package", response_model=FeatureFlagResponse)
async def disable_plan_package(
    disabled_from: datetime,
    disabled_until: datetime,
    reason: str,
    db: Session = Depends(get_db),
    admin_user: models.User = Depends(require_admin)
):
    """Disable plan package for specific date range (Admin only)"""
    try:
        if disabled_from >= disabled_until:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="disabled_from must be before disabled_until"
            )
        
        flag = db.query(models.FeatureFlag).filter(
            models.FeatureFlag.feature_type == FeatureFlagType.PLAN_PACKAGE
        ).first()
        
        if not flag:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Plan package feature flag not found"
            )
        
        # Update flag to disable for date range
        flag.is_enabled = False
        flag.disabled_from = disabled_from
        flag.disabled_until = disabled_until
        flag.reason = reason
        flag.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(flag)
        
        logger.info(f"Plan package disabled from {disabled_from} to {disabled_until} by admin {admin_user.id}: {reason}")
        return flag
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error disabling plan package: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to disable plan package"
        )

@router.post("/enable-plan-package", response_model=FeatureFlagResponse)
async def enable_plan_package(
    db: Session = Depends(get_db),
    admin_user: models.User = Depends(require_admin)
):
    """Re-enable plan package (Admin only)"""
    try:
        flag = db.query(models.FeatureFlag).filter(
            models.FeatureFlag.feature_type == FeatureFlagType.PLAN_PACKAGE
        ).first()
        
        if not flag:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Plan package feature flag not found"
            )
        
        # Re-enable flag
        flag.is_enabled = True
        flag.disabled_from = None
        flag.disabled_until = None
        flag.reason = "Re-enabled by admin"
        flag.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(flag)
        
        logger.info(f"Plan package re-enabled by admin {admin_user.id}")
        return flag
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error enabling plan package: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to enable plan package"
        )

# Public endpoint to check if plan package is enabled
@router.get("/public/plan-package-status")
async def get_plan_package_status(db: Session = Depends(get_db)):
    """Check if plan package is currently enabled (Public endpoint)"""
    try:
        flag = db.query(models.FeatureFlag).filter(
            models.FeatureFlag.feature_type == FeatureFlagType.PLAN_PACKAGE
        ).first()
        
        if not flag:
            # Default to enabled if flag doesn't exist
            return {"is_enabled": True, "reason": "Default enabled"}
        
        current_time = datetime.utcnow()
        
        # Check if currently in disabled period
        if (flag.disabled_from and flag.disabled_until and 
            flag.disabled_from <= current_time <= flag.disabled_until):
            return {
                "is_enabled": False,
                "reason": flag.reason,
                "disabled_until": flag.disabled_until
            }
        
        return {
            "is_enabled": flag.is_enabled,
            "reason": flag.reason if not flag.is_enabled else "Enabled"
        }
        
    except Exception as e:
        logger.error(f"Error checking plan package status: {e}")
        # Default to enabled on error
        return {"is_enabled": True, "reason": "Default enabled (error occurred)"}
