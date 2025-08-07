# Fix to remove principal ID validation (marketplace users != bot owners)

with open('core/crud.py', 'r') as f:
    content = f.read()

# Remove the principal ID validation section
old_validation = '''    # Step 4: Verify principal_id matches bot registration (ADDITIONAL SECURITY)
    if hasattr(bot_registration, 'user_principal_id') and bot_registration.user_principal_id:
        if bot_registration.user_principal_id != principal_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Principal ID does not match bot registration. Access denied."
            )'''

new_validation = '''    # Note: Skip principal ID validation because in marketplace:
    # - Bot owner (bot_registration.user_principal_id) creates the bot
    # - Subscription user (principal_id) rents the bot
    # These are different users, which is expected in marketplace model'''

content = content.replace(old_validation, new_validation)

with open('core/crud.py', 'w') as f:
    f.write(content)

print("✅ Principal ID validation removed - marketplace users can rent bots from different owners")
