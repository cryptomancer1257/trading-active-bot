# Script to fix security validation in marketplace endpoints

# Read current file
with open('api/endpoints/marketplace.py', 'r') as f:
    content = f.read()

# Fix PAUSE endpoint
old_pause_auth = '''        # Authenticate using bot API key
        bot_registration = crud.get_bot_registration_by_api_key(db, request.api_key)
        if not bot_registration:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid bot API key - authentication failed"
            )
        
        # Get subscription by ID and principal ID
        subscription = crud.get_subscription_by_id_and_principal(
            db, request.subscription_id, request.principal_id
        )
        if not subscription:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Subscription not found or access denied"
            )'''

new_pause_auth = '''        # Validate subscription access with enhanced security
        subscription, bot_registration = crud.validate_marketplace_subscription_access(
            db, request.subscription_id, request.principal_id, request.api_key
        )'''

content = content.replace(old_pause_auth, new_pause_auth)

# Fix CANCEL endpoint (similar pattern)
old_cancel_auth = old_pause_auth  # Same pattern
content = content.replace(old_cancel_auth, new_pause_auth, 1)  # Only replace next occurrence

# Fix RESUME endpoint (similar pattern) 
content = content.replace(old_cancel_auth, new_pause_auth, 1)  # Only replace next occurrence

# Write updated file
with open('api/endpoints/marketplace.py', 'w') as f:
    f.write(content)

print("✅ Security fix applied to marketplace.py")
