"""
API endpoints for managing plan pricing templates (Admin only)
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel, Field
from decimal import Decimal
from datetime import datetime

from core import models
from core.database import get_db
from core.security import get_current_active_admin

router = APIRouter()


# Schemas
class PlanPricingTemplateBase(BaseModel):
    plan_name: str
    original_price_usd: Decimal = Field(..., ge=0, description="Original price in USD")
    discount_percentage: Decimal = Field(..., ge=0, le=100, description="Discount percentage (0-100)")
    campaign_name: Optional[str] = None
    campaign_active: bool = True
    campaign_start_date: Optional[datetime] = None
    campaign_end_date: Optional[datetime] = None


class PlanPricingTemplateCreate(PlanPricingTemplateBase):
    pass


class PlanPricingTemplateUpdate(BaseModel):
    original_price_usd: Optional[Decimal] = Field(None, ge=0)
    discount_percentage: Optional[Decimal] = Field(None, ge=0, le=100)
    campaign_name: Optional[str] = None
    campaign_active: Optional[bool] = None
    campaign_start_date: Optional[datetime] = None
    campaign_end_date: Optional[datetime] = None


class PlanPricingTemplateResponse(PlanPricingTemplateBase):
    id: int
    current_price_usd: float
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# Endpoints
@router.get("/", response_model=List[PlanPricingTemplateResponse])
async def get_all_plan_pricing_templates(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_admin)
):
    """Get all plan pricing templates (Admin only)"""
    templates = db.query(models.PlanPricingTemplate).all()
    
    # Convert to response format with computed current_price
    result = []
    for template in templates:
        template_dict = {
            'id': template.id,
            'plan_name': template.plan_name.value,
            'original_price_usd': template.original_price_usd,
            'discount_percentage': template.discount_percentage,
            'current_price_usd': template.current_price_usd,
            'campaign_name': template.campaign_name,
            'campaign_active': template.campaign_active,
            'campaign_start_date': template.campaign_start_date,
            'campaign_end_date': template.campaign_end_date,
            'created_at': template.created_at,
            'updated_at': template.updated_at
        }
        result.append(template_dict)
    
    return result


@router.get("/{plan_name}", response_model=PlanPricingTemplateResponse)
async def get_plan_pricing_template(
    plan_name: str,
    db: Session = Depends(get_db)
):
    """Get pricing template for a specific plan (Public endpoint)"""
    # Convert string to PlanName enum (by name, not value)
    try:
        plan_enum = models.PlanName[plan_name.upper()]
    except (ValueError, KeyError):
        # Return default template if invalid plan name
        return {
            'id': 0,
            'plan_name': plan_name,
            'original_price_usd': 0.00,
            'discount_percentage': 0.00,
            'current_price_usd': 0.00,
            'campaign_name': None,
            'campaign_active': False,
            'campaign_start_date': None,
            'campaign_end_date': None,
            'created_at': datetime.now(),
            'updated_at': datetime.now()
        }
    
    template = db.query(models.PlanPricingTemplate).filter(
        models.PlanPricingTemplate.plan_name == plan_enum
    ).first()
    
    if not template:
        # Return default template if not found
        return {
            'id': 0,
            'plan_name': plan_name,
            'original_price_usd': 0.00,
            'discount_percentage': 0.00,
            'current_price_usd': 0.00,
            'campaign_name': None,
            'campaign_active': False,
            'campaign_start_date': None,
            'campaign_end_date': None,
            'created_at': datetime.now(),
            'updated_at': datetime.now()
        }
    
    return {
        'id': template.id,
        'plan_name': template.plan_name.value,
        'original_price_usd': template.original_price_usd,
        'discount_percentage': template.discount_percentage,
        'current_price_usd': template.current_price_usd,
        'campaign_name': template.campaign_name,
        'campaign_active': template.campaign_active,
        'campaign_start_date': template.campaign_start_date,
        'campaign_end_date': template.campaign_end_date,
        'created_at': template.created_at,
        'updated_at': template.updated_at
    }


@router.post("/", response_model=PlanPricingTemplateResponse, status_code=status.HTTP_201_CREATED)
async def create_plan_pricing_template(
    template: PlanPricingTemplateCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_admin)
):
    """Create new plan pricing template (Admin only)"""
    # Check if template already exists
    existing = db.query(models.PlanPricingTemplate).filter(
        models.PlanPricingTemplate.plan_name == template.plan_name
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Pricing template for plan '{template.plan_name}' already exists"
        )
    
    # Create new template
    db_template = models.PlanPricingTemplate(**template.dict())
    db.add(db_template)
    db.commit()
    db.refresh(db_template)
    
    return {
        'id': db_template.id,
        'plan_name': db_template.plan_name.value,
        'original_price_usd': db_template.original_price_usd,
        'discount_percentage': db_template.discount_percentage,
        'current_price_usd': db_template.current_price_usd,
        'campaign_name': db_template.campaign_name,
        'campaign_active': db_template.campaign_active,
        'campaign_start_date': db_template.campaign_start_date,
        'campaign_end_date': db_template.campaign_end_date,
        'created_at': db_template.created_at,
        'updated_at': db_template.updated_at
    }


@router.put("/{plan_name}", response_model=PlanPricingTemplateResponse)
async def update_plan_pricing_template(
    plan_name: str,
    template_update: PlanPricingTemplateUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_admin)
):
    """Update plan pricing template (Admin only)"""
    template = db.query(models.PlanPricingTemplate).filter(
        models.PlanPricingTemplate.plan_name == plan_name
    ).first()
    
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Pricing template for plan '{plan_name}' not found"
        )
    
    # Update fields
    update_data = template_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(template, field, value)
    
    db.commit()
    db.refresh(template)
    
    return {
        'id': template.id,
        'plan_name': template.plan_name.value,
        'original_price_usd': template.original_price_usd,
        'discount_percentage': template.discount_percentage,
        'current_price_usd': template.current_price_usd,
        'campaign_name': template.campaign_name,
        'campaign_active': template.campaign_active,
        'campaign_start_date': template.campaign_start_date,
        'campaign_end_date': template.campaign_end_date,
        'created_at': template.created_at,
        'updated_at': template.updated_at
    }


@router.delete("/{plan_name}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_plan_pricing_template(
    plan_name: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_admin)
):
    """Delete plan pricing template (Admin only)"""
    template = db.query(models.PlanPricingTemplate).filter(
        models.PlanPricingTemplate.plan_name == plan_name
    ).first()
    
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Pricing template for plan '{plan_name}' not found"
        )
    
    db.delete(template)
    db.commit()
    
    return None

