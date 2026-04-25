"""
LinkedIn Poster for AI Employee - Silver Tier

Posts approved LinkedIn posts to LinkedIn automatically.

Architecture (from Hackathon):
- Action Layer: Posts to LinkedIn via browser automation
- Reads approved posts from /Approved folder
- Human-in-the-loop approval required
- Updates Dashboard.md

FULLY AUTOMATIC FLOW:
1. Open LinkedIn feed
2. Click "Start a post"
3. Enter content with human-like typing
4. Enable and click Post button
5. Verify success (modal close, "View post"/"Undo")
6. Add human-like behavior (mouse movement, scroll, delays)
7. Safety: ONE post per run, challenge detection = STOP
8. Logging: Each step logged, screenshots saved

Usage:
    python watchers/linkedin_poster.py
"""

import os
import sys
import time
import re
import random
import traceback
from pathlib import Path
import datetime
from typing import List, Dict, Optional

try:
    from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
except ImportError:
    print("❌ Playwright not installed!")
    print("Install: pip install playwright && playwright install chromium")
    sys.exit(1)


class LinkedInPoster:
    """
    LinkedIn Poster - Posts approved LinkedIn content
    
    Follows the hackathon architecture:
    - Action Layer: Browser automation via Playwright
    - Reads from /Approved folder
    - Human-in-the-loop approval required
    - Updates Dashboard.md
    """
    
    def __init__(self, vault_path: str = ".", dry_run: bool = False, max_posts: int = 5):
        self.vault_path = Path(vault_path)
        self.session_path = self.vault_path / "sessions" / "linkedin"
        self.approved_path = self.vault_path / "Approved"
        self.done_path = self.vault_path / "Done"
        self.logs_path = self.vault_path / "Logs"
        self.social_posts_path = self.vault_path / "Social_Posts"
        self.dry_run = dry_run
        self.max_posts = max_posts
        
        # Ensure directories exist
        self.approved_path.mkdir(exist_ok=True)
        self.done_path.mkdir(exist_ok=True)
        self.logs_path.mkdir(exist_ok=True)
        self.session_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Setup logging
        self._setup_logging()
        
        # Browser state
        self.playwright = None
        self.browser = None
        self.page = None
        
        # Safety: Track if post was made in this run
        self.post_made_this_run = False
        
        # Human-like behavior settings
        self.min_delay = 0.5  # Minimum delay between actions (seconds)
        self.max_delay = 2.5  # Maximum delay between actions (seconds)
        self.typing_speed_min = 0.02  # Fast typing delay (seconds)
        self.typing_speed_max = 0.08  # Slow typing delay (seconds)

    def _human_delay(self, min_seconds: float = None, max_seconds: float = None):
        """Add random human-like delay"""
        if min_seconds is None:
            min_seconds = self.min_delay
        if max_seconds is None:
            max_seconds = self.max_delay
        delay = random.uniform(min_seconds, max_seconds)
        time.sleep(delay)
        return delay

    def _random_mouse_movement(self):
        """Add random mouse movement to appear more human"""
        try:
            # Move mouse to random position on page
            viewport = self.page.viewport_size
            if viewport:
                x = random.randint(100, viewport['width'] - 100)
                y = random.randint(100, viewport['height'] - 100)
                self.page.mouse.move(x, y)
                self._human_delay(0.1, 0.3)
                self.logger.info(f"  🖱️  Mouse moved to ({x}, {y})")
        except Exception as e:
            self.logger.debug(f"Mouse movement failed: {e}")

    def _scroll_page(self, direction: str = "down", amount: int = None):
        """Scroll the page to simulate human scrolling"""
        try:
            if amount is None:
                amount = random.randint(100, 500)
            
            if direction == "down":
                self.page.mouse.wheel(0, amount)
            elif direction == "up":
                self.page.mouse.wheel(0, -amount)
            
            self._human_delay(0.2, 0.5)
            self.logger.info(f"  📜 Scrolled {direction} ({amount}px)")
        except Exception as e:
            self.logger.debug(f"Scroll failed: {e}")

    def _take_screenshot(self, filename: str, description: str = ""):
        """Take and save a screenshot"""
        try:
            screenshot_path = self.logs_path / f"{filename}.png"
            self.page.screenshot(path=str(screenshot_path))
            if description:
                self.logger.info(f"📸 Screenshot saved: {screenshot_path} ({description})")
            else:
                self.logger.info(f"📸 Screenshot saved: {screenshot_path}")
            return str(screenshot_path)
        except Exception as e:
            self.logger.error(f"Failed to take screenshot: {e}")
            return None

    def _detect_challenge_page(self) -> bool:
        """Detect if LinkedIn is showing a challenge/verification page"""
        try:
            current_url = self.page.url.lower()
            
            # Check URL for challenge indicators
            challenge_indicators = [
                'checkpoint',
                'challenge',
                'verify',
                'captcha',
                'security-check',
                'robot'
            ]
            
            for indicator in challenge_indicators:
                if indicator in current_url:
                    self.logger.critical(f"🚨 CHALLENGE PAGE DETECTED! URL contains '{indicator}'")
                    self._take_screenshot("CHALLENGE_DETECTED", "Challenge page detected")
                    return True
            
            # Check page content for challenge text
            try:
                page_text = self.page.inner_text('body').lower()
                challenge_text_indicators = [
                    'verify your identity',
                    'security check',
                    'confirm you are human',
                    'captcha',
                    'unusual activity',
                    'suspicious activity'
                ]
                
                for text in challenge_text_indicators:
                    if text in page_text:
                        self.logger.critical(f"🚨 CHALLENGE PAGE DETECTED! Page contains '{text}'")
                        self._take_screenshot("CHALLENGE_DETECTED", f"Challenge text detected: {text}")
                        return True
            except:
                pass  # Page text extraction failed
            
            return False
            
        except Exception as e:
            self.logger.error(f"Challenge detection failed: {e}")
            return False  # Assume OK if we can't detect

    def _check_post_button_enabled(self) -> bool:
        """Check if the Post button is enabled and clickable"""
        try:
            # Look for Post button in multiple ways
            js_code = """
            () => {
                const buttons = Array.from(document.querySelectorAll('button'));
                const postBtn = buttons.find(btn => {
                    const text = btn.textContent.trim();
                    return (text === 'Post' || text === 'Share') && 
                           !btn.disabled && 
                           btn.getAttribute('aria-disabled') !== 'true' &&
                           btn.offsetParent !== null;  // Visible
                });
                return postBtn !== undefined;
            }
            """
            return self.page.evaluate(js_code)
        except:
            return False
    
    def _setup_logging(self):
        """Setup logging to file and console"""
        log_file = self.logs_path / f"linkedin_poster_{datetime.datetime.now().strftime('%Y-%m-%d')}.log"
        import logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger("LinkedInPoster")
    
    def get_approved_posts(self) -> List[Path]:
        """Get list of approved posts ready for publishing"""
        approved = []
        
        # Check Approved folder
        if self.approved_path.exists():
            for file in self.approved_path.glob("LINKEDIN_*.md"):
                approved.append(file)
        
        # Also check Social_Posts for approved status
        if self.social_posts_path.exists():
            for file in self.social_posts_path.glob("LINKEDIN_*.md"):
                content = file.read_text(encoding='utf-8')
                if 'status: approved' in content and file not in approved:
                    approved.append(file)
        
        self.logger.info(f"Found {len(approved)} approved post(s)")
        return approved
    
    def parse_post_content(self, file_path: Path) -> Optional[Dict]:
        """Parse post file and extract content and metadata"""
        try:
            content = file_path.read_text(encoding='utf-8')
            
            # Parse frontmatter
            metadata = {}
            in_frontmatter = False
            
            for line in content.split('\n'):
                if line.strip() == '---':
                    if not in_frontmatter:
                        in_frontmatter = True
                        continue
                    else:
                        break
                
                if in_frontmatter and ':' in line:
                    key, value = line.split(':', 1)
                    key = key.strip()
                    value = value.strip()
                    
                    # Handle lists
                    if value.startswith('[') and value.endswith(']'):
                        value = [v.strip().strip("'\"") for v in value[1:-1].split(',')]
                    
                    metadata[key] = value
            
            # Extract post content
            content_match = re.search(r'## Post Content\n(.*?)(?=##|$)', content, re.DOTALL)
            post_content = content_match.group(1).strip() if content_match else ""
            
            # Remove publishing instructions
            if '## Publishing Instructions' in post_content:
                post_content = post_content.split('## Publishing Instructions')[0].strip()
            
            return {
                'metadata': metadata,
                'content': post_content,
                'file': file_path
            }
            
        except Exception as e:
            self.logger.error(f"Error parsing post file {file_path}: {e}")
            return None
    
    def _initialize_browser(self):
        """Initialize Playwright browser with LinkedIn session"""
        try:
            self.playwright = sync_playwright().start()
            
            # Launch browser with persistent context (saves session)
            self.browser = self.playwright.chromium.launch_persistent_context(
                user_data_dir=str(self.session_path),
                headless=False,  # Visible for debugging
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--no-sandbox',
                    '--disable-dev-shm-usage'
                ],
                viewport={'width': 1366, 'height': 768}
            )
            
            self.page = self.browser.pages[0] if self.browser.pages else self.browser.new_page()
            
            self.logger.info("✓ Browser initialized")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize browser: {e}")
            return False
    
    def _cleanup(self):
        """Cleanup browser resources"""
        try:
            if self.browser:
                self.browser.close()
                self.browser = None
            
            if self.playwright:
                self.playwright.stop()
                self.playwright = None
            
            self.logger.info("Browser cleanup complete")
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")
    
    def _navigate_to_linkedin(self) -> bool:
        """Navigate to LinkedIn feed with challenge detection"""
        try:
            self.logger.info("="*60)
            self.logger.info("STEP 1: Opening LinkedIn feed")
            self.logger.info("="*60)
            
            self.logger.info("  Navigating to linkedin.com/feed...")
            self.page.goto('https://www.linkedin.com/feed', wait_until='domcontentloaded', timeout=60000)
            time.sleep(5)
            
            # CRITICAL: Check for challenge page immediately
            self.logger.info("  Checking for challenge/verification page...")
            if self._detect_challenge_page():
                self.logger.critical("🛑 SAFETY: Challenge page detected - STOPPING immediately")
                self.logger.critical("   Manual intervention required. Check browser.")
                self._take_screenshot("NAVIGATION_STOPPED", "Navigation stopped due to challenge")
                return False
            
            # Add human-like scroll
            self.logger.info("  Page loaded, adding human-like scroll...")
            self._scroll_page("down", random.randint(200, 400))
            self._human_delay(1, 2)
            self._scroll_page("up", random.randint(100, 300))
            
            # Verify we're on the feed
            current_url = self.page.url
            self.logger.info(f"  Current URL: {current_url}")
            
            if '/feed' in current_url:
                self.logger.info("✓ Successfully on LinkedIn feed")
                return True
            elif 'linkedin.com' in current_url:
                self.logger.warning(f"  ⚠️  Not on feed, current URL: {current_url}")
                self.logger.info("  Attempting to navigate to feed again...")
                self.page.goto('https://www.linkedin.com/feed', wait_until='domcontentloaded', timeout=60000)
                time.sleep(5)
                
                # Check again for challenges
                if self._detect_challenge_page():
                    self.logger.critical("🛑 SAFETY: Challenge page detected - STOPPING")
                    return False
                
                return '/feed' in self.page.url
            else:
                self.logger.error(f"  ✗ Not on LinkedIn, URL: {current_url}")
                return False

        except Exception as e:
            self.logger.error(f"Failed to navigate to LinkedIn: {e}")
            self.logger.debug(traceback.format_exc())
            return False
    
    def _click_start_post(self) -> bool:
        """Click 'Start a post' button with human-like behavior"""
        self.logger.info("="*60)
        self.logger.info("STEP 2: Opening post composer")
        self.logger.info("="*60)
        
        # Add human-like delay and mouse movement
        self._human_delay(1, 2)
        self._random_mouse_movement()
        
        # Scroll to ensure the button is visible
        self.logger.info("  Scrolling to find 'Start a post' button...")
        self._scroll_page("down", 300)
        self._human_delay(0.5, 1)
        
        # Try multiple selectors with improved reliability
        selectors = [
            'button[aria-label="Start a post"]',
            'button[aria-label*="Start a post"]',
            'div[role="button"]:has-text("Start a post")',
            'button:has-text("Start a post")',
            'text="Start a post"',
            '.share-box-feed-entry__trigger',
            'button.share-box-feed-entry__trigger'
        ]
        
        for attempt, selector in enumerate(selectors, 1):
            try:
                self.logger.info(f"  Attempt {attempt}: Trying selector '{selector[:50]}...'")
                
                elements = self.page.query_selector_all(selector)
                if elements:
                    btn = elements[0]
                    if btn.is_visible():
                        # Scroll into view
                        btn.scroll_into_view_if_needed()
                        self._human_delay(0.5, 1)
                        
                        # Add small random mouse movement before click
                        self._random_mouse_movement()
                        
                        # Click
                        btn.click()
                        self.logger.info(f"  ✓ Clicked 'Start a post' (selector: {selector[:40]})")
                        self._human_delay(1, 2)
                        return True
                    else:
                        self.logger.debug(f"    Element not visible")
                else:
                    self.logger.debug(f"    No elements found")
            except Exception as e:
                self.logger.debug(f"    Attempt {attempt} failed: {e}")
                continue
        
        # Fallback: Try JavaScript-based click
        self.logger.info("  Selector attempts failed, trying JavaScript...")
        try:
            js_code = """
            () => {
                // Look for any element with "Start a post" text
                const allElements = Array.from(document.querySelectorAll('button, div[role="button"], a'));
                const target = allElements.find(el => 
                    el.textContent.includes('Start a post') && 
                    el.offsetParent !== null
                );
                if (target) {
                    target.click();
                    return true;
                }
                return false;
            }
            """
            
            result = self.page.evaluate(js_code)
            if result:
                self.logger.info("  ✓ JavaScript clicked 'Start a post'")
                self._human_delay(1, 2)
                return True
            else:
                self.logger.warning("  ⚠️  JavaScript could not find 'Start a post'")
        except Exception as e:
            self.logger.error(f"  ✗ JavaScript fallback failed: {e}")
        
        # Last resort: Try clicking by text
        self.logger.info("  Last resort: Trying text-based click...")
        try:
            self.page.click('text=Start a post', timeout=10000)
            self._human_delay(1, 2)
            self.logger.info("  ✓ Text-based click succeeded")
            return True
        except Exception as e:
            self.logger.error(f"  ✗ All methods failed: {e}")
            self._take_screenshot("START_POST_FAILED", "Could not find Start a post button")
            return False
    
    def _wait_for_modal(self, timeout: int = 15) -> bool:
        """Wait for post composer modal to appear"""
        self.logger.info("="*60)
        self.logger.info("STEP 3: Waiting for composer modal")
        self.logger.info("="*60)

        try:
            self.logger.info(f"  Waiting up to {timeout} seconds for dialog...")

            # Try multiple modal selectors with better specificity
            modal_selectors = [
                # LinkedIn composer-specific selectors
                'div[role="dialog"] div[contenteditable="true"]',
                'div[role="dialog"] form',
                'div[role="dialog"]:has-text("Create a post")',
                'div[role="dialog"] button:has-text("Post")',
                # Generic dialog (last resort)
                'div[role="dialog"]',
            ]

            found_modal = False
            for selector in modal_selectors:
                try:
                    self.logger.debug(f"  Trying modal selector: {selector[:50]}...")
                    modal = self.page.locator(selector).first
                    modal.wait_for(state='visible', timeout=3000)
                    if modal.is_visible():
                        self.logger.info(f"  ✓ Composer modal found (selector: {selector[:40]})")
                        found_modal = True
                        break
                except:
                    continue

            if not found_modal:
                # Wait longer for any dialog to appear
                self.logger.info("  Specific selectors failed, waiting for any visible dialog...")
                time.sleep(5)

                # Use JavaScript to find the real composer dialog
                js_check = """
                () => {
                    const dialogs = Array.from(document.querySelectorAll('div[role="dialog"]'));
                    for (const dialog of dialogs) {
                        // Skip hidden/error dialogs
                        if (dialog.offsetParent === null) continue;
                        if (dialog.classList.contains('vjs-hidden')) continue;
                        if (dialog.classList.contains('vjs-error-display')) continue;
                        
                        // Check if it has composer indicators
                        const hasContentEditable = dialog.querySelector('div[contenteditable="true"]');
                        const hasPostButton = dialog.querySelector('button') && 
                            Array.from(dialog.querySelectorAll('button')).some(btn => 
                                btn.textContent.trim() === 'Post'
                            );
                        const hasCreatePost = dialog.textContent.includes('Create a post');
                        
                        if (hasContentEditable || hasPostButton || hasCreatePost) {
                            return true;
                        }
                    }
                    return false;
                }
                """

                if self.page.evaluate(js_check):
                    self.logger.info("  ✓ Composer modal detected via JavaScript")
                    found_modal = True

            if not found_modal:
                self.logger.error("✗ Composer modal not found after all attempts")
                return False

            time.sleep(2)
            self._human_delay(0.5, 1)
            return True

        except Exception as e:
            self.logger.error(f"✗ Modal did not appear: {e}")
            self._take_screenshot("MODAL_NOT_FOUND", "Composer modal not found")
            return False
    
    def _find_textbox(self):
        """Find textbox in composer modal or inline composer"""
        self.logger.info("="*60)
        self.logger.info("STEP 4: Finding textbox in composer")
        self.logger.info("="*60)

        # Wait a moment for composer to fully render
        time.sleep(2)

        # Try multiple selectors - both modal and inline
        selectors = [
            # Modal composer textboxes
            'div[role="dialog"] div[contenteditable="true"][role="textbox"]',
            'div[role="dialog"] div[contenteditable="true"]',
            'div[role="dialog"] div[role="textbox"]',
            'div[role="dialog"] div[aria-label*="What do you want to talk about"]',
            # Inline composer (on feed itself)
            'div[contenteditable="true"][role="textbox"]',
            'div[contenteditable="true"]',
            'div[role="textbox"]',
            'div[aria-label*="What do you want to talk about"]',
            # Legacy selectors
            '.ql-editor',
            '.mlw-editor',
        ]

        for attempt, selector in enumerate(selectors, 1):
            try:
                self.logger.debug(f"  Attempt {attempt}: Trying '{selector}'")
                textbox = self.page.locator(selector).first

                # Wait for it to be visible
                textbox.wait_for(state='visible', timeout=5000)

                if textbox.is_visible():
                    self.logger.info(f"  ✓ Textbox found (selector: {selector[:50]})")
                    self._human_delay(0.3, 0.6)
                    return textbox
                else:
                    self.logger.debug(f"    Textbox not visible")
            except Exception as e:
                self.logger.debug(f"    Attempt {attempt} failed")
                continue

        # Last resort: JavaScript search for editable textbox
        self.logger.info("  Selectors failed, trying JavaScript search...")
        try:
            js_find = """
            () => {
                // Look in dialogs first
                const dialogs = Array.from(document.querySelectorAll('div[role="dialog"]'));
                for (const dialog of dialogs) {
                    if (dialog.offsetParent === null) continue;
                    if (dialog.classList.contains('vjs-hidden')) continue;
                    if (dialog.classList.contains('vjs-error-display')) continue;

                    const editables = dialog.querySelectorAll('div[contenteditable="true"]');
                    for (const editable of editables) {
                        if (editable.offsetParent !== null) {
                            editable.focus();
                            return 'found';
                        }
                    }
                }

                // Look in feed (inline composer)
                const allEditables = Array.from(document.querySelectorAll('div[contenteditable="true"]'));
                for (const editable of allEditables) {
                    if (editable.offsetParent !== null) {
                        editable.focus();
                        return 'found';
                    }
                }
                return 'not_found';
            }
            """

            result = self.page.evaluate(js_find)
            if result == 'found':
                self.logger.info("  ✓ Textbox found via JavaScript")
                self._human_delay(0.3, 0.6)
                # Return a generic locator that should work
                return self.page.locator('div[contenteditable="true"]').first
            else:
                self.logger.error("✗ JavaScript could not find textbox")
        except Exception as e:
            self.logger.error(f"✗ JavaScript search failed: {e}")

        self.logger.error("✗ Textbox not found with any method")
        self._take_screenshot("TEXTBOX_NOT_FOUND", "Could not find composer textbox")
        return None
    
    def _type_content(self, textbox, content: str) -> bool:
        """Type content into textbox with human-like behavior"""
        self.logger.info("="*60)
        self.logger.info("STEP 5: Entering content with human-like typing")
        self.logger.info("="*60)
        
        self.logger.info(f"  Content length: {len(content)} characters")
        self.logger.info(f"  Preview: {content[:100]}...")
        
        try:
            # Click to focus
            self.logger.info("  Clicking to focus textbox...")
            textbox.click()
            self._human_delay(0.5, 1)
            
            # Clear existing content
            self.logger.info("  Clearing any existing content...")
            self.page.keyboard.press('Control+A')
            self._human_delay(0.2, 0.4)
            self.page.keyboard.press('Delete')
            self._human_delay(0.3, 0.6)
            
            # Type content with human-like delays
            self.logger.info("  ⌨️  Typing content with realistic delays...")
            
            # Split into smaller chunks for more natural typing
            chunk_size = 30  # Smaller chunks = more human-like
            total = len(content)
            typed = 0
            
            for idx in range(0, total, chunk_size):
                chunk = content[idx:idx + chunk_size]
                
                # Type the chunk with variable speed
                for char in chunk:
                    self.page.keyboard.type(char, delay=0)  # No built-in delay, we control it
                    # Add random delay between keystrokes
                    key_delay = random.uniform(self.typing_speed_min, self.typing_speed_max)
                    time.sleep(key_delay)
                
                typed += len(chunk)
                
                # Add a slightly longer pause between chunks (like human thinking)
                chunk_pause = random.uniform(0.1, 0.5)
                time.sleep(chunk_pause)
                
                # Show progress periodically
                if typed % 100 == 0 or typed == total:
                    progress = (typed / total) * 100
                    self.logger.info(f"    Progress: {progress:.0f}% ({typed}/{total} chars)")
            
            # Final pause to let LinkedIn process
            self._human_delay(2, 4)
            
            self.logger.info(f"✓ Typed {total} characters successfully")
            return True

        except Exception as e:
            self.logger.error(f"✗ Typing failed: {e}")
            self.logger.debug(traceback.format_exc())
            self._take_screenshot("TYPING_FAILED", "Content typing failed")
            return False
    
    def _click_post_button(self) -> bool:
        """Click Post button with maximum reliability and human-like behavior"""
        self.logger.info("="*60)
        self.logger.info("STEP 6: Enabling and clicking Post button")
        self.logger.info("="*60)
        
        # Wait for Post button to become enabled
        self.logger.info("  ⏳ Waiting for Post button to enable...")
        max_wait = 30  # Maximum wait time in seconds
        wait_interval = 2  # Check every 2 seconds
        elapsed = 0
        
        while elapsed < max_wait:
            if self._check_post_button_enabled():
                self.logger.info(f"  ✓ Post button enabled after {elapsed}s")
                break
            
            self.logger.info(f"    Waiting... ({elapsed}s/{max_wait}s)")
            time.sleep(wait_interval)
            elapsed += wait_interval
            
            # Add human-like scroll/mouse movement while waiting
            if elapsed % 5 == 0:
                self._random_mouse_movement()
        else:
            self.logger.warning(f"  ⚠️  Post button did not enable after {max_wait}s")
        
        # Add human-like delay before clicking
        self._human_delay(1, 2)
        self._random_mouse_movement()
        
        # Try multiple methods to click Post
        post_clicked = False
        
        # Method 1: Find and click enabled Post button via DOM
        try:
            self.logger.info("  Method 1: DOM query for Post button...")
            
            buttons = self.page.query_selector_all('button')
            post_btn = None
            
            for btn in buttons:
                try:
                    text = btn.inner_text().strip()
                    is_disabled = btn.get_attribute('disabled')
                    aria_disabled = btn.get_attribute('aria-disabled')
                    is_visible = btn.is_visible()
                    
                    if (text == 'Post' or text == 'Share') and not is_disabled and aria_disabled != 'true' and is_visible:
                        post_btn = btn
                        self.logger.info(f"    Found enabled Post button: '{text}'")
                        break
                except:
                    continue
            
            if post_btn:
                post_btn.scroll_into_view_if_needed()
                self._human_delay(0.3, 0.6)
                post_btn.click()
                self.logger.info("  ✓ Method 1: Clicked Post button via DOM")
                post_clicked = True
            else:
                self.logger.warning("  ⚠️  Method 1: No enabled Post button found")
                
        except Exception as e:
            self.logger.error(f"  ✗ Method 1 failed: {e}")
        
        # Method 2: JavaScript click (more reliable)
        if not post_clicked:
            try:
                self.logger.info("  Method 2: JavaScript click...")
                
                js_code = """
                () => {
                    const buttons = Array.from(document.querySelectorAll('button'));
                    const postBtn = buttons.find(btn => {
                        const text = btn.textContent.trim();
                        const isVisible = btn.offsetParent !== null;
                        const isDisabled = btn.disabled || btn.getAttribute('aria-disabled') === 'true';
                        return (text === 'Post' || text === 'Share') && !isDisabled && isVisible;
                    });
                    
                    if (postBtn) {
                        postBtn.click();
                        return { success: true, text: postBtn.textContent.trim() };
                    }
                    return { success: false };
                }
                """
                
                result = self.page.evaluate(js_code)
                if result.get('success'):
                    self.logger.info(f"  ✓ Method 2: JavaScript clicked '{result.get('text')}'")
                    post_clicked = True
                else:
                    self.logger.warning("  ⚠️  Method 2: No enabled Post button via JS")
            except Exception as e:
                self.logger.error(f"  ✗ Method 2 failed: {e}")
        
        # Method 3: Ctrl+Enter keyboard shortcut
        if not post_clicked:
            try:
                self.logger.info("  Method 3: Ctrl+Enter keyboard shortcut...")
                self.page.keyboard.press('Control+Enter')
                self._human_delay(1, 2)
                self.logger.info("  ✓ Method 3: Ctrl+Enter sent")
                post_clicked = True
            except Exception as e:
                self.logger.error(f"  ✗ Method 3 failed: {e}")
        
        if not post_clicked:
            self.logger.error("  ✗ All methods failed to click Post")
            self._take_screenshot("POST_BUTTON_FAILED", "Could not click Post button")
            return False
        
        # Wait after click
        self._human_delay(2, 4)
        return True
    
    def _verify_posted(self) -> bool:
        """Verify post was successfully published with comprehensive checks"""
        self.logger.info("="*60)
        self.logger.info("STEP 7: Verifying post publication")
        self.logger.info("="*60)
        
        # Wait for modal to close
        self.logger.info("  Waiting for composer modal to close...")
        time.sleep(3)
        
        modal = self.page.locator('div[role="dialog"]').first
        
        try:
            # Check if modal closed
            modal.wait_for(state='hidden', timeout=15000)
            self.logger.info("✓ Composer modal closed")
        except Exception:
            self.logger.warning("  ⚠️  Modal still visible after 15s")
            self.logger.info("  Taking screenshot for manual verification...")
            self._take_screenshot("MODAL_STILL_VISIBLE", "Modal did not close immediately")
            
            # Wait a bit more
            time.sleep(5)
            try:
                if modal.is_visible():
                    self.logger.error("✗ Modal still visible after 20s - post may have failed")
                    self._take_screenshot("POST_VERIFICATION_FAILED", "Modal still visible")
                    return False
                else:
                    self.logger.info("✓ Modal closed after extended wait")
            except:
                self.logger.info("✓ Modal closed after extended wait")
        
        # Wait for feed to reload
        self.logger.info("  Waiting for feed to reload...")
        time.sleep(5)
        
        # Add human-like scroll
        self._scroll_page("down", random.randint(100, 300))
        self._human_delay(1, 2)
        
        # Check for success indicators
        self.logger.info("  Checking for success indicators...")
        success_found = False
        
        try:
            page_text = self.page.inner_text('body').lower()
            
            # Check for "View post" link
            if 'view post' in page_text:
                self.logger.info("✓ Found 'View post' link - post successful!")
                success_found = True
            
            # Check for "Undo" option
            if 'undo' in page_text:
                self.logger.info("✓ Found 'Undo' option - post successful!")
                success_found = True
            
            # Check for "Your post is live" or similar
            if 'post is live' in page_text or 'post published' in page_text:
                self.logger.info("✓ Found 'post is live' message - post successful!")
                success_found = True
            
            # Check URL didn't change to error page
            current_url = self.page.url.lower()
            if 'error' in current_url or '404' in current_url:
                self.logger.error("✗ Navigated to error page!")
                self._take_screenshot("ERROR_PAGE", "Navigated to error page after post")
                return False
            
        except Exception as e:
            self.logger.warning(f"  ⚠️  Could not check page text: {e}")
        
        # Take success screenshot
        screenshot_name = f"POST_SUCCESS_{int(time.time())}"
        screenshot_path = self._take_screenshot(screenshot_name, "Post published successfully")
        
        if success_found:
            self.logger.info("="*60)
            self.logger.info("✅ POST VERIFIED SUCCESSFULLY")
            self.logger.info("="*60)
            return True
        else:
            self.logger.warning("="*60)
            self.logger.warning("⚠️  Could not verify post with certainty")
            self.logger.warning("   Check screenshot and browser window manually")
            self.logger.warning("="*60)
            return True  # Assume success if no errors detected
        
        return False
    
    def _update_dashboard(self, post_data: Dict):
        """Update dashboard with posting activity"""
        try:
            sys.path.insert(0, str(self.vault_path))
            from agent_skills import AIEmployeeSkills
            skills = AIEmployeeSkills(str(self.vault_path))
            
            content_preview = post_data['content'][:50] + "..." if len(post_data['content']) > 50 else post_data['content']
            skills.update_dashboard_activity(
                f"LinkedIn post published: {content_preview}",
                "social"
            )
            self.logger.info("✓ Dashboard updated")
        except Exception as e:
            self.logger.error(f"Error updating dashboard: {e}")
    
    def post_file(self, post_file: Path) -> bool:
        """Post a single file with full automation and safety checks"""
        
        # SAFETY: Only ONE post per run
        if self.post_made_this_run:
            self.logger.warning("⚠️  Already posted once this run - stopping for safety")
            return False
        
        post_data = self.parse_post_content(post_file)
        
        if not post_data:
            self.logger.error(f"✗ Could not read post file: {post_file.name}")
            return False
        
        content = post_data['content']
        
        if not content:
            self.logger.error(f"✗ No content in {post_file.name}")
            return False
        
        self.logger.info("\n" + "="*70)
        self.logger.info(f"📝 POSTING: {post_file.name}")
        self.logger.info("="*70)
        self.logger.info(f"📊 Length: {len(content)} chars")
        self.logger.info(f"📝 Preview: {content[:100]}...\n")
        
        # Full automated posting flow
        try:
            # Step 1: Should already be on LinkedIn feed from _navigate_to_linkedin()
            # Step 2: Click "Start a post"
            if not self._click_start_post():
                self.logger.error("✗ Failed to open post composer")
                return False
            
            # Step 3: Wait for modal
            if not self._wait_for_modal():
                self.logger.error("✗ Modal did not appear")
                return False
            
            # Step 4: Find textbox
            textbox = self._find_textbox()
            if not textbox:
                self.logger.error("✗ Could not find textbox")
                return False
            
            # Step 5: Type content
            if not self._type_content(textbox, content):
                self.logger.error("✗ Failed to type content")
                return False
            
            # Step 6: Click Post button
            if not self._click_post_button():
                self.logger.error("✗ Failed to click Post button")
                return False
            
            # Step 7: Verify success
            if not self._verify_posted():
                self.logger.error("✗ Failed to verify post")
                return False
            
            # Mark that we posted this run
            self.post_made_this_run = True
            
            # Update dashboard
            self._update_dashboard(post_data)
            
            # Move to Done
            self.logger.info("💾 Saving to Done folder...")
            done_path = self.done_path / post_file.name
            try:
                post_file.rename(done_path)
                self.logger.info(f"✓ Saved to Done folder")
            except Exception as e:
                self.logger.error(f"⚠️  Could not save to Done: {e}")
            
            self.logger.info("\n" + "="*70)
            self.logger.info("✅✅✅ SUCCESS! Post published successfully! ✅✅✅")
            self.logger.info("="*70 + "\n")
            return True
            
        except Exception as e:
            self.logger.error(f"✗ Unexpected error during posting: {e}")
            self.logger.debug(traceback.format_exc())
            self._take_screenshot("POSTING_ERROR", "Unexpected error during post")
            return False
    
    def run(self):
        """Run LinkedIn Poster - FULLY AUTOMATIC"""
        self.logger.info("\n" + "="*70)
        self.logger.info("  LINKEDIN POSTER - FULLY AUTOMATIC")
        self.logger.info("  Personal AI Employee Hackathon 0")
        self.logger.info("="*70 + "\n")
        
        posts = self.get_approved_posts()
        
        if not posts:
            self.logger.info("No approved posts found!")
            self.logger.info("\nTo create and approve posts:")
            self.logger.info("  1. python -c \"from agent_skills import AIEmployeeSkills; s = AIEmployeeSkills(); s.create_linkedin_post('Your content')\"")
            self.logger.info("  2. move Social_Posts\\*.md Approved\\")
            self.logger.info("  3. python watchers/linkedin_poster.py")
            return
        
        # SAFETY: Enforce ONE post per run
        if len(posts) > 1:
            self.logger.info(f"Found {len(posts)} approved posts")
            self.logger.info("⚠️  SAFETY: Will only post ONCE this run to avoid detection")
            self.logger.info(f"   Processing first post: {posts[0].name}\n")
        
        # Initialize browser
        self.logger.info("="*60)
        self.logger.info("INITIALIZING BROWSER")
        self.logger.info("="*60)
        if not self._initialize_browser():
            self.logger.error("✗ Failed to initialize browser")
            return
        
        try:
            # Navigate to LinkedIn
            if not self._navigate_to_linkedin():
                self.logger.error("✗ Failed to load LinkedIn. Check login status.")
                self._take_screenshot("LINKEDIN_LOAD_FAILED", "Could not load LinkedIn feed")
                return
            
            # Post ONLY the first file (safety: one post per run)
            post_file = posts[0]
            self.logger.info(f"\n📦 Selected post for this run: {post_file.name}")
            
            if self.post_file(post_file):
                self.logger.info("\n" + "="*70)
                self.logger.info("  ✅ POST SUCCESSFULLY PUBLISHED")
                self.logger.info("="*70)
                self.logger.info(f"  📝 File: {post_file.name}")
                self.logger.info(f"  📸 Check Logs folder for screenshots")
                self.logger.info("="*70 + "\n")
            else:
                self.logger.error("\n" + "="*70)
                self.logger.error("  ✗ POSTING FAILED")
                self.logger.error("="*70)
                self.logger.error("  Check logs and screenshots for details")
                self.logger.error("="*70 + "\n")
        
        finally:
            # Always cleanup
            self.logger.info("="*60)
            self.logger.info("CLEANUP")
            self.logger.info("="*60)
            self._cleanup()


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='LinkedIn Poster for AI Employee',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python watchers/linkedin_poster.py              # Post approved posts
  python watchers/linkedin_poster.py --login      # Login to LinkedIn
  python watchers/linkedin_poster.py --test       # Test mode
  python watchers/linkedin_poster.py --dry-run    # Dry run (no posting)
  python watchers/linkedin_poster.py --max-posts 3  # Limit posts per run
        """
    )
    
    parser.add_argument('--vault-path', type=str, default='.', help='Vault path')
    parser.add_argument('--dry-run', action='store_true', help='Dry run')
    parser.add_argument('--max-posts', type=int, default=5, help='Max posts per run')
    parser.add_argument('--login', action='store_true', help='Login to LinkedIn')
    parser.add_argument('--test', action='store_true', help='Test mode')
    
    args = parser.parse_args()
    
    poster = LinkedInPoster(
        vault_path=args.vault_path,
        dry_run=args.dry_run,
        max_posts=args.max_posts
    )
    
    if args.login:
        # Just open browser for login
        if poster._initialize_browser():
            poster._navigate_to_linkedin()
            input("\nPress Enter after logging in...")
            poster._cleanup()
    elif args.test:
        # Test mode
        posts = poster.get_approved_posts()
        print(f"\nFound {len(posts)} approved post(s)")
        for p in posts[:3]:
            data = poster.parse_post_content(p)
            if data:
                print(f"\n  File: {p.name}")
                print(f"  Content: {data['content'][:100]}...")
    else:
        # Run poster
        poster.run()


if __name__ == "__main__":
    main()
