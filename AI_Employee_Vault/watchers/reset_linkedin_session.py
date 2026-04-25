"""
LinkedIn Session Reset Tool

Completely removes old LinkedIn session and creates a fresh one.

This will:
1. Delete old session (sessions/linkedin/)
2. Create new clean session (sessions/linkedin_new/)
3. Update all scripts to use new session
4. Ensure complete isolation

Usage:
    python watchers/reset_linkedin_session.py
"""

import shutil
import sys
from pathlib import Path
import time


def get_session_paths():
    """Get session directory paths"""
    vault_path = Path(__file__).parent.parent
    old_session = vault_path / "sessions" / "linkedin"
    new_session = vault_path / "sessions" / "linkedin_new"
    return vault_path, old_session, new_session


def delete_folder_safely(folder_path: Path, description: str) -> bool:
    """Delete a folder with retry logic"""
    if not folder_path.exists():
        print(f"   ℹ️  {description} does not exist (already clean)")
        return True
    
    print(f"   🗑️  Deleting {description}...")
    print(f"      Path: {folder_path}")
    
    max_retries = 3
    for attempt in range(1, max_retries + 1):
        try:
            shutil.rmtree(folder_path, ignore_errors=False)
            
            # Verify deletion
            if not folder_path.exists():
                print(f"   ✓ {description} deleted successfully")
                return True
            else:
                print(f"   ⚠️  Attempt {attempt}: Folder still exists, retrying...")
                time.sleep(1)
                
        except Exception as e:
            print(f"   ⚠️  Attempt {attempt}: {e}")
            time.sleep(1)
    
    # Force delete if still exists
    if folder_path.exists():
        print(f"   ⚠️  Force deleting {description}...")
        try:
            shutil.rmtree(folder_path, ignore_errors=True)
            if not folder_path.exists():
                print(f"   ✓ {description} force deleted")
                return True
            else:
                print(f"   ❌ Could not delete {description}")
                return False
        except:
            return False
    
    return True


def create_clean_session(session_path: Path):
    """Create a new clean session directory"""
    print(f"\n   📁 Creating new session folder...")
    print(f"      Path: {session_path}")
    
    try:
        session_path.mkdir(parents=True, exist_ok=True)
        
        # Verify creation
        if session_path.exists():
            print(f"   ✓ New session folder created")
            return True
        else:
            print(f"   ❌ Could not create session folder")
            return False
            
    except Exception as e:
        print(f"   ❌ Error creating folder: {e}")
        return False


def update_scripts_to_use_new_session():
    """Update all scripts to use the new session path"""
    print(f"\n   📝 Updating scripts to use new session...")
    
    vault_path = Path(__file__).parent.parent
    scripts_to_update = [
        vault_path / "watchers" / "linkedin_poster.py",
        vault_path / "watchers" / "linkedin_poster_manual.py",
        vault_path / "watchers" / "linkedin_watcher.py",
    ]
    
    updated_count = 0
    
    for script_path in scripts_to_update:
        if not script_path.exists():
            print(f"   ℹ️  Script not found (skipping): {script_path.name}")
            continue
        
        try:
            content = script_path.read_text(encoding='utf-8')
            
            # Replace old session path with new one
            if 'sessions/linkedin' in content and 'sessions/linkedin_new' not in content:
                # Update the session path
                content = content.replace(
                    'session_path = self.vault_path / "sessions" / "linkedin"',
                    'session_path = self.vault_path / "sessions" / "linkedin_new"'
                )
                content = content.replace(
                    'session_path = Path("sessions/linkedin")',
                    'session_path = Path("sessions/linkedin_new")'
                )
                content = content.replace(
                    'self.session_path = self.vault_path / "sessions" / "linkedin"',
                    'self.session_path = self.vault_path / "sessions" / "linkedin_new"'
                )
                
                script_path.write_text(content, encoding='utf-8')
                print(f"   ✓ Updated: {script_path.name}")
                updated_count += 1
            else:
                print(f"   ℹ️  Already using new session: {script_path.name}")
                
        except Exception as e:
            print(f"   ⚠️  Could not update {script_path.name}: {e}")
    
    print(f"\n   📊 Scripts updated: {updated_count}")
    return updated_count


def main():
    print("\n" + "="*70)
    print("  LINKEDIN SESSION RESET TOOL")
    print("  Complete Session Reset for Fresh Start")
    print("="*70)
    
    vault_path, old_session, new_session = get_session_paths()
    
    print(f"\n📍 Vault: {vault_path}")
    print(f"🗑️  Old session: {old_session}")
    print(f"📁 New session: {new_session}")
    
    # Confirm with user
    print("\n" + "="*70)
    print("  ⚠️  WARNING: This will DELETE all LinkedIn session data!")
    print("="*70)
    print("\nThis will:")
    print("  • Delete ALL cookies, cache, and session data")
    print("  • Remove saved login state")
    print("  • Create a completely fresh session")
    print("  • Update all scripts to use the new session")
    print("\nYou will need to:")
    print("  • Login to LinkedIn again after reset")
    print("  • Complete any verification/CAPTCHA")
    print("\n" + "="*70)
    
    confirm = input("\n❓ Are you sure you want to continue? (yes/no): ").strip().lower()
    
    if confirm != 'yes':
        print("\n❌ Reset cancelled")
        return
    
    print("\n" + "="*70)
    print("  STARTING SESSION RESET")
    print("="*70)
    
    # Step 1: Delete old session
    print("\n1️⃣ DELETING OLD SESSION")
    print("-"*70)
    
    if not delete_folder_safely(old_session, "Old session"):
        print("\n❌ Failed to delete old session!")
        print("   Please close any programs using the session folder and try again")
        return
    
    # Step 2: Create new clean session
    print("\n2️⃣ CREATING NEW SESSION")
    print("-"*70)
    
    if not create_clean_session(new_session):
        print("\n❌ Failed to create new session!")
        return
    
    # Step 3: Update scripts
    print("\n3️⃣ UPDATING SCRIPTS")
    print("-"*70)
    
    updated_count = update_scripts_to_use_new_session()
    
    # Summary
    print("\n" + "="*70)
    print("  SESSION RESET COMPLETE!")
    print("="*70)
    print("\n✅ What was done:")
    print(f"  ✓ Deleted old session: {old_session}")
    print(f"  ✓ Created new session: {new_session}")
    print(f"  ✓ Updated {updated_count} scripts")
    
    print("\n📋 Next steps:")
    print("  1. Run the LinkedIn poster to login with new account:")
    print("     python watchers/linkedin_poster_manual.py")
    print("\n  2. Login to your NEW LinkedIn account")
    print("  3. Complete any verification")
    print("  4. The new session will be saved automatically")
    
    print("\n⚠️  Important:")
    print("  • The old session is completely gone")
    print("  • The new session is completely clean")
    print("  • No data is shared between them")
    print("  • You must login again")
    
    print("\n" + "="*70 + "\n")


if __name__ == "__main__":
    main()
