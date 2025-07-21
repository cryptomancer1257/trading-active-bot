#!/usr/bin/env python3
"""
Cleanup script for remaining unnecessary files
"""

import os
import shutil
import sys
from pathlib import Path

def cleanup_remaining_files():
    """Clean up remaining unnecessary files"""
    print("🧹 Bot Marketplace - Final Cleanup")
    print("=" * 50)
    
    # Get current directory
    current_dir = Path(__file__).parent
    print(f"Cleaning directory: {current_dir}")
    
    # Files to delete
    files_to_delete = [
        # Test files
        "test.py",
        
        # State files (temporary)
        "alternating_bot_state_BTC_USDT.json",
        
        # Celery files (regenerated automatically)
        "celerybeat-schedule.dat",
        "celerybeat-schedule.dir",
        "celerybeat-schedule.bak",
        
        # Redundant email service (replaced by modular templates)
        "email_service.py",
    ]
    
    # Folders to delete
    folders_to_delete = [
        "__pycache__",
    ]
    
    deleted_files = []
    deleted_folders = []
    errors = []
    
    # Delete files
    print("\n📁 Deleting files:")
    for file_name in files_to_delete:
        file_path = current_dir / file_name
        if file_path.exists():
            try:
                file_size = file_path.stat().st_size
                file_path.unlink()
                deleted_files.append((file_name, file_size))
                print(f"   ✅ Deleted: {file_name} ({file_size / 1024:.1f} KB)")
            except Exception as e:
                errors.append(f"Failed to delete {file_name}: {e}")
                print(f"   ❌ Error deleting {file_name}: {e}")
        else:
            print(f"   ⚠️  Not found: {file_name}")
    
    # Delete folders
    print("\n📂 Deleting folders:")
    for folder_name in folders_to_delete:
        folder_path = current_dir / folder_name
        if folder_path.exists():
            try:
                # Calculate folder size
                folder_size = sum(f.stat().st_size for f in folder_path.rglob('*') if f.is_file())
                shutil.rmtree(folder_path)
                deleted_folders.append((folder_name, folder_size))
                print(f"   ✅ Deleted: {folder_name}/ ({folder_size / 1024:.1f} KB)")
            except Exception as e:
                errors.append(f"Failed to delete {folder_name}: {e}")
                print(f"   ❌ Error deleting {folder_name}: {e}")
        else:
            print(f"   ⚠️  Not found: {folder_name}/")
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Cleanup Summary:")
    print(f"   Files deleted: {len(deleted_files)}")
    print(f"   Folders deleted: {len(deleted_folders)}")
    print(f"   Errors: {len(errors)}")
    
    if deleted_files:
        print(f"\n🗑️  Deleted files:")
        total_file_size = 0
        for file_name, file_size in deleted_files:
            total_file_size += file_size
            print(f"   • {file_name} ({file_size / 1024:.1f} KB)")
    
    if deleted_folders:
        print(f"\n🗑️  Deleted folders:")
        total_folder_size = 0
        for folder_name, folder_size in deleted_folders:
            total_folder_size += folder_size
            print(f"   • {folder_name}/ ({folder_size / 1024:.1f} KB)")
    
    if errors:
        print(f"\n❌ Errors:")
        for error in errors:
            print(f"   • {error}")
    
    total_saved = total_file_size + total_folder_size
    print(f"\n💾 Total space saved: {total_saved / 1024:.1f} KB")
    
    # Remaining important files
    print(f"\n✅ Important files preserved:")
    important_files = [
        "main.py",
        "tasks.py",
        "models.py",
        "schemas.py",
        "crud.py",
        "database.py",
        "security.py",
        "celery_app.py",
        "bot_base_classes.py",
        "email_templates.py",
        "sendgrid_email_service.py",
        "gmail_smtp_service.py",
        "binance_integration.py",
        "exchange_factory.py",
        "s3_manager.py",
        "bot_manager.py",
        "requirements.txt",
        "docker-compose.yml",
        "Dockerfile",
        "docker.env",
        "seed_data.py",
        "run_beat.py",
        "run_celery.py",
        ".gitignore",
        "README.md",
    ]
    
    missing_files = []
    for file_name in important_files:
        file_path = current_dir / file_name
        if file_path.exists():
            print(f"   ✅ {file_name}")
        else:
            missing_files.append(file_name)
            print(f"   ⚠️  Missing: {file_name}")
    
    if missing_files:
        print(f"\n⚠️  Missing important files:")
        for file_name in missing_files:
            print(f"   • {file_name}")
    
    print(f"\n🎉 Final cleanup completed!")
    print(f"   The system is now optimized and clean.")

def dry_run():
    """Show what would be deleted without actually deleting"""
    print("🧹 Bot Marketplace - Final Cleanup (DRY RUN)")
    print("=" * 50)
    
    current_dir = Path(__file__).parent
    print(f"Would clean directory: {current_dir}")
    
    files_to_delete = [
        "test.py",
        "alternating_bot_state_BTC_USDT.json",
        "celerybeat-schedule.dat",
        "celerybeat-schedule.dir",
        "celerybeat-schedule.bak",
        "email_service.py",
    ]
    
    folders_to_delete = [
        "__pycache__",
    ]
    
    total_size = 0
    
    print("\n📁 Files that would be deleted:")
    for file_name in files_to_delete:
        file_path = current_dir / file_name
        if file_path.exists():
            size = file_path.stat().st_size
            total_size += size
            print(f"   📄 {file_name} ({size / 1024:.1f} KB)")
        else:
            print(f"   ⚠️  {file_name} (not found)")
    
    print("\n📂 Folders that would be deleted:")
    for folder_name in folders_to_delete:
        folder_path = current_dir / folder_name
        if folder_path.exists():
            folder_size = sum(f.stat().st_size for f in folder_path.rglob('*') if f.is_file())
            total_size += folder_size
            print(f"   📁 {folder_name}/ ({folder_size / 1024:.1f} KB)")
        else:
            print(f"   ⚠️  {folder_name}/ (not found)")
    
    print(f"\n💾 Total space that would be saved: {total_size / 1024:.1f} KB")
    print(f"\n🔍 This is a dry run. Run without --dry-run to actually delete files.")

if __name__ == "__main__":
    if "--dry-run" in sys.argv:
        dry_run()
    else:
        # Ask for confirmation
        print("⚠️  This will delete remaining unnecessary files:")
        print("   • test.py - Test script")
        print("   • alternating_bot_state_BTC_USDT.json - Temporary state")
        print("   • celerybeat-schedule.* - Celery cache files")
        print("   • email_service.py - Redundant email service")
        print("   • __pycache__/ - Python cache")
        print("\n   Make sure you want to proceed!")
        confirm = input("\nContinue with final cleanup? (y/N): ")
        
        if confirm.lower() in ['y', 'yes']:
            cleanup_remaining_files()
        else:
            print("❌ Cleanup cancelled.")
            print("   Run with --dry-run to see what would be deleted.") 