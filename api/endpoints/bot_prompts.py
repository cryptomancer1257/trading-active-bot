from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from core.database import get_db
from core import models, schemas, security
import core.crud as crud

router = APIRouter()

# BotPrompt schemas
class BotPromptBase(schemas.BaseModel):
    bot_id: int
    prompt_id: int
    is_active: bool = True
    priority: int = 0
    custom_override: Optional[str] = None

class BotPromptCreate(BotPromptBase):
    pass

class BotPromptUpdate(schemas.BaseModel):
    is_active: Optional[bool] = None
    priority: Optional[int] = None
    custom_override: Optional[str] = None

class BotPromptInDB(BotPromptBase):
    id: int
    attached_at: str
    created_at: str
    updated_at: str
    
    class Config:
        from_attributes = True

class BotPromptWithDetails(BotPromptInDB):
    prompt_template: schemas.PromptTemplateInDB
    bot: schemas.BotInDB

# Bot-Prompt Management Endpoints

@router.get("/bots/{bot_id}/prompts", response_model=List[BotPromptWithDetails])
async def get_bot_prompts(
    bot_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_active_user)
):
    """Get all prompts attached to a specific bot"""
    # Verify bot ownership
    bot = db.query(models.Bot).filter(models.Bot.id == bot_id).first()
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")
    
    if bot.developer_id != current_user.id and current_user.role != models.UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Not authorized to access this bot")
    
    return crud.get_bot_prompts(db, bot_id=bot_id)

@router.get("/prompts/{prompt_id}/bots", response_model=List[BotPromptWithDetails])
async def get_prompt_bots(
    prompt_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_active_user)
):
    """Get all bots using a specific prompt"""
    # Verify prompt access
    prompt = db.query(models.PromptTemplate).filter(models.PromptTemplate.id == prompt_id).first()
    if not prompt:
        raise HTTPException(status_code=404, detail="Prompt not found")
    
    if prompt.created_by != current_user.id and current_user.role != models.UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Not authorized to access this prompt")
    
    return crud.get_prompt_bots(db, prompt_id=prompt_id)

@router.post("/bots/{bot_id}/prompts/{prompt_id}", response_model=BotPromptInDB)
async def attach_prompt_to_bot(
    bot_id: int,
    prompt_id: int,
    priority: int = Query(0, description="Priority level (higher = more important)"),
    custom_override: Optional[str] = Query(None, description="Bot-specific prompt customization"),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_active_user)
):
    """Attach a prompt to a bot"""
    # Verify bot ownership
    bot = db.query(models.Bot).filter(models.Bot.id == bot_id).first()
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")
    
    if bot.developer_id != current_user.id and current_user.role != models.UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Not authorized to access this bot")
    
    # Verify prompt exists
    prompt = db.query(models.PromptTemplate).filter(models.PromptTemplate.id == prompt_id).first()
    if not prompt:
        raise HTTPException(status_code=404, detail="Prompt not found")
    
    # Check if already attached
    existing = db.query(models.BotPrompt).filter(
        models.BotPrompt.bot_id == bot_id,
        models.BotPrompt.prompt_id == prompt_id
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="Prompt already attached to this bot")
    
    return crud.attach_prompt_to_bot(
        db, 
        bot_id=bot_id, 
        prompt_id=prompt_id, 
        priority=priority,
        custom_override=custom_override
    )

@router.delete("/bots/{bot_id}/prompts/{prompt_id}")
async def detach_prompt_from_bot(
    bot_id: int,
    prompt_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_active_user)
):
    """Detach a prompt from a bot"""
    # Verify bot ownership
    bot = db.query(models.Bot).filter(models.Bot.id == bot_id).first()
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")
    
    if bot.developer_id != current_user.id and current_user.role != models.UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Not authorized to access this bot")
    
    # Find the attachment
    bot_prompt = db.query(models.BotPrompt).filter(
        models.BotPrompt.bot_id == bot_id,
        models.BotPrompt.prompt_id == prompt_id
    ).first()
    
    if not bot_prompt:
        raise HTTPException(status_code=404, detail="Prompt not attached to this bot")
    
    crud.detach_prompt_from_bot(db, bot_prompt_id=bot_prompt.id)
    return {"message": "Prompt detached successfully"}

@router.put("/bots/{bot_id}/prompts/{prompt_id}", response_model=BotPromptInDB)
async def update_bot_prompt(
    bot_id: int,
    prompt_id: int,
    update_data: BotPromptUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_active_user)
):
    """Update bot-prompt relationship settings"""
    # Verify bot ownership
    bot = db.query(models.Bot).filter(models.Bot.id == bot_id).first()
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")
    
    if bot.developer_id != current_user.id and current_user.role != models.UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Not authorized to access this bot")
    
    # Find the attachment
    bot_prompt = db.query(models.BotPrompt).filter(
        models.BotPrompt.bot_id == bot_id,
        models.BotPrompt.prompt_id == prompt_id
    ).first()
    
    if not bot_prompt:
        raise HTTPException(status_code=404, detail="Prompt not attached to this bot")
    
    return crud.update_bot_prompt(db, bot_prompt_id=bot_prompt.id, update_data=update_data)

@router.get("/bots/{bot_id}/suggested-prompts", response_model=List[schemas.PromptTemplateInDB])
async def get_suggested_prompts(
    bot_id: int,
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_active_user)
):
    """Get suggested prompts for a bot based on bot type and category"""
    # Verify bot ownership
    bot = db.query(models.Bot).filter(models.Bot.id == bot_id).first()
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")
    
    if bot.developer_id != current_user.id and current_user.role != models.UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Not authorized to access this bot")
    
    return crud.get_suggested_prompts(db, bot_id=bot_id, limit=limit)

@router.get("/prompts/{prompt_id}/suggested-bots", response_model=List[schemas.BotInDB])
async def get_suggested_bots(
    prompt_id: int,
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_active_user)
):
    """Get suggested bots for a prompt"""
    # Verify prompt access
    prompt = db.query(models.PromptTemplate).filter(models.PromptTemplate.id == prompt_id).first()
    if not prompt:
        raise HTTPException(status_code=404, detail="Prompt not found")
    
    if prompt.created_by != current_user.id and current_user.role != models.UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Not authorized to access this prompt")
    
    return crud.get_suggested_bots(db, prompt_id=prompt_id, limit=limit)
