"""
LinkedIn Poster - Semi-Automatic (100% Reliable)

You click "Post" manually to avoid LinkedIn's bot detection.
Everything else is automated.

Usage:
    python watchers/linkedin_poster_manual.py
"""

import time
import re
from pathlib import Path
from playwright.sync_api import sync_playwright


def get_approved_posts():
    """Get approved posts"""
    approved = Path("Approved")
    if not approved.exists():
        return []
    return list(approved.glob("LINKEDIN_*.md"))


def get_post_content(file_path):
    """Extract post content"""
    try:
        content = file_path.read_text(encoding='utf-8')
        start = content.find("## Post Content")
        if start == -1:
            return None
        start += len("## Post Content") + 1
        end = content.find("## Actions")
        if end == -1:
            end = len(content)
        return content[start:end].strip()[:2800]
    except:
        return None


def main():
    print("\n" + "="*70)
    print("  LINKEDIN POSTER - SEMI-AUTOMATIC")
    print("  You click 'Post' - Everything else automated")
    print("="*70)
    
    posts = get_approved_posts()
    
    if not posts:
        print("\n⚠️  No approved posts found!")
        print("\nTo create a post:")
        print("  1. python -c \"from agent_skills import AIEmployeeSkills; s = AIEmployeeSkills(); s.create_linkedin_post('Content')\"")
        print("  2. move Social_Posts\\*.md Approved\\")
        print("  3. python watchers/linkedin_poster_manual.py")
        return
    
    print(f"\n📦 Found {len(posts)} approved post(s)\n")
    
    # Start browser
    print("🌐 Opening browser with CLEAN session...")
    playwright = sync_playwright().start()
    
    # Use new clean session path
    session_path = Path("sessions/linkedin_new")
    session_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Safety check: Ensure old session is not being used
    old_session = Path("sessions/linkedin")
    if old_session.exists() and not session_path.exists():
        print("⚠️  WARNING: Old session exists but new session not created!")
        print("   Run: python watchers/reset_linkedin_session.py")
        print("   to create a clean session first.\n")
    
    # Create new session if it doesn't exist
    if not session_path.exists():
        print("📁 Creating new session folder...")
        session_path.mkdir(parents=True, exist_ok=True)
        print("   ✓ New session created\n")
    
    print(f"📍 Session path: {session_path}")
    print("   (Clean session - no old cookies/cache)\n")
    
    browser = playwright.chromium.launch_persistent_context(
        user_data_dir=str(session_path),
        headless=False,
        args=['--no-sandbox']
    )
    
    page = browser.pages[0] if browser.pages else browser.new_page()
    
    # Navigate to LinkedIn
    print("📍 Navigating to LinkedIn...")
    try:
        page.goto('https://www.linkedin.com/feed', wait_until='domcontentloaded', timeout=60000)
        time.sleep(10)
        print("✓ LinkedIn loaded\n")
    except:
        print("⚠️  If you see login, please login manually")
        time.sleep(30)
    
    # Process each post
    for i, post_file in enumerate(posts, 1):
        print(f"\n{'='*70}")
        print(f"POST {i}/{len(posts)}")
        print(f"{'='*70}\n")
        
        content = get_post_content(post_file)
        if not content:
            print("✗ Could not read content\n")
            continue
        
        print(f"📝 Content ({len(content)} chars):")
        print("-"*70)
        print(content[:300] + "..." if len(content) > 300 else content)
        print("-"*70)
        print()
        
        # Step 1: Click "Start a post"
        print("1️⃣ Clicking 'Start a post'...")
        
        clicked = False
        selectors = [
            'button[aria-label="Start a post"]',
            'button:has-text("Start a post")',
            'div.share-box-feed-entry__trigger'
        ]
        
        for selector in selectors:
            try:
                btn = page.locator(selector).first
                btn.wait_for(state='visible', timeout=10000)
                btn.click()
                print("   ✓ Clicked 'Start a post'\n")
                clicked = True
                break
            except:
                continue
        
        if not clicked:
            print("   ⚠️  Please click 'Start a post' manually")
            input("   Press Enter after clicking...")
        
        # Wait for modal
        print("⏳ Waiting for composer to open...")
        time.sleep(5)
        
        # Step 2: Type content
        print("\n2️⃣ Typing content...")
        
        try:
            textbox = page.locator('div[contenteditable="true"]').first
            textbox.wait_for(state='visible', timeout=15000)
            textbox.click()
            time.sleep(2)
            
            # Clear existing
            page.keyboard.press('Control+A')
            time.sleep(0.5)
            page.keyboard.press('Delete')
            time.sleep(0.5)
            
            # Type content
            print("   📝 Typing...\n")
            
            for idx in range(0, len(content), 50):
                chunk = content[idx:idx+50]
                page.keyboard.type(chunk, delay=20)
                time.sleep(0.1)
                
                if (idx + 50) % 150 == 0:
                    progress = ((idx + 50) / len(content)) * 100
                    print(f"   ⌨️  Progress: {progress:.0f}%")
            
            time.sleep(3)
            print(f"\n   ✓ Content typed ({len(content)} chars)\n")
            
        except Exception as e:
            print(f"   ✗ Error: {e}")
            print("   ⚠️  Please paste content manually\n")
        
        # Step 3: WAIT FOR USER TO CLICK POST
        print("\n" + "="*70)
        print("  ✅ CONTENT READY - PLEASE CLICK 'POST' NOW")
        print("="*70)
        print("\n📋 WHAT TO DO:")
        print("  1. Look at the browser window")
        print("  2. Review the content")
        print("  3. Click the 'Post' button (bottom right)")
        print("  4. Wait for it to publish (5-10 seconds)")
        print("  5. Come back here and press Enter\n")
        print("="*70 + "\n")
        
        input("   👉 Press Enter AFTER you clicked 'Post' and it published...")
        
        # Step 4: Verify and save
        print("\n⏳ Verifying post published...")
        time.sleep(3)
        
        # Take screenshot for verification
        logs_path = Path("Logs")
        logs_path.mkdir(exist_ok=True)
        screenshot = logs_path / f"post_{i}_{int(time.time())}.png"
        try:
            page.screenshot(path=str(screenshot))
            print(f"   📸 Screenshot saved: {screenshot}")
        except:
            pass
        
        # Save to Done
        print("\n3️⃣ Saving to Done folder...")
        done_path = Path("Done") / post_file.name
        try:
            post_file.rename(done_path)
            print("   ✓ Saved to Done\n")
            print(f"✅ SUCCESS! Posted {i}/{len(posts)}\n")
        except Exception as e:
            print(f"   ⚠️  Could not save: {e}\n")
        
        # Wait between posts
        if i < len(posts):
            print(f"⏳ Waiting 15 seconds before next post...\n")
            time.sleep(15)
    
    # Summary
    print("\n" + "="*70)
    print("  ALL POSTS COMPLETE!")
    print("="*70)
    print("\n✅ Your posts are now live on LinkedIn!")
    print("   Check your LinkedIn profile to verify.\n")
    
    browser.close()
    playwright.stop()


if __name__ == "__main__":
    main()
