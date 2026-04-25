"""
Gmail Watcher for AI Employee - Silver Tier

Monitors Gmail for new important messages and creates action files in Needs_Action.

Architecture (from Hackathon):
- Perception Layer: Monitors Gmail API continuously
- Creates action files in /Needs_Action folder
- Updates Dashboard.md automatically
- Works with Qwen Code as the reasoning engine

Usage:
    python watchers/gmail_watcher.py
"""

import os
import sys
import time
import logging
import pickle
from pathlib import Path
import datetime
import base64
from typing import List, Dict, Optional


class GmailWatcher:
    """
    Gmail Watcher - Monitors Gmail for important messages
    
    Follows the hackathon architecture:
    - Perception Layer: Monitors Gmail API
    - Creates action files in /Needs_Action
    - Updates Dashboard.md
    - Works with Qwen Code as reasoning engine
    """
    
    def __init__(self, vault_path: str, check_interval: int = 120, dry_run: bool = False):
        self.vault_path = Path(vault_path)
        self.check_interval = check_interval
        self.dry_run = dry_run
        self.processed_ids = set()
        self.logs = self.vault_path / "Logs"
        self.needs_action = self.vault_path / "Needs_Action"
        self.plans_path = self.vault_path / "Plans"
        self.pending_approval_path = self.vault_path / "Pending_Approval"

        # Ensure directories exist
        self.logs.mkdir(exist_ok=True)
        self.needs_action.mkdir(exist_ok=True)
        self.plans_path.mkdir(exist_ok=True)
        self.pending_approval_path.mkdir(exist_ok=True)
        
        # Setup logging
        self._setup_logging()
        
        # Keywords for priority detection
        self.urgent_keywords = [
            'urgent', 'asap', 'immediately', 'emergency',
            'important', 'action required', 'deadline', 'invoice',
            'payment', 'payment due', 'overdue'
        ]
        
        # Initialize Gmail service
        self.service = None
        self._initialize_service()
    
    def _setup_logging(self):
        """Setup logging to file and console"""
        log_file = self.logs / f"gmail_watcher_{datetime.datetime.now().strftime('%Y-%m-%d')}.log"
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger("GmailWatcher")
    
    def _find_credentials(self) -> Optional[Path]:
        """Find Gmail credentials file"""
        # Check vault credentials folder first
        vault_creds = self.vault_path / "credentials" / "gmail_credentials.json"
        if vault_creds.exists():
            return vault_creds
        
        # Check project root
        root_creds = self.vault_path.parent / "credentials.json"
        if root_creds.exists():
            return root_creds
        
        # Check current directory
        current_creds = Path.cwd() / "credentials.json"
        if current_creds.exists():
            return current_creds
        
        return None
    
    def _initialize_service(self):
        """Initialize Gmail API service with OAuth2"""
        try:
            from google.oauth2.credentials import Credentials
            from google_auth_oauthlib.flow import InstalledAppFlow
            from googleapiclient.discovery import build
            from google.auth.transport.requests import Request
            
            SCOPES = [
                'https://www.googleapis.com/auth/gmail.readonly',
                'https://www.googleapis.com/auth/gmail.compose',
                'https://www.googleapis.com/auth/gmail.send'
            ]
            
            creds_path = self._find_credentials()
            if not creds_path:
                self.logger.error("No credentials found! Run setup_gmail.py first.")
                self.logger.error("Credentials should be in: vault/credentials/ or project root")
                return
            
            # Copy credentials to vault if found elsewhere
            vault_creds_path = self.vault_path / "credentials" / "gmail_credentials.json"
            if not vault_creds_path.exists():
                vault_creds_path.parent.mkdir(parents=True, exist_ok=True)
                import shutil
                shutil.copy2(creds_path, vault_creds_path)
                self.logger.info(f"Copied credentials to: {vault_creds_path}")
                creds_path = vault_creds_path
            
            token_path = self.vault_path / "credentials" / "gmail_token.pickle"
            creds = None
            
            # Load existing token
            if token_path.exists():
                try:
                    with open(token_path, 'rb') as f:
                        creds = pickle.load(f)
                    self.logger.info("Loaded existing token")
                except Exception as e:
                    self.logger.warning(f"Failed to load token: {e}")
            
            # Refresh or get new credentials
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    self.logger.info("Refreshing expired token...")
                    try:
                        creds.refresh(Request())
                    except Exception as e:
                        self.logger.warning(f"Token refresh failed: {e}")
                        creds = None
                
                if not creds:
                    self.logger.info("Starting OAuth flow...")
                    self.logger.info("Browser will open for authorization...")
                    self.logger.info("Requesting scopes: gmail.readonly + gmail.compose + gmail.send")
                    try:
                        flow = InstalledAppFlow.from_client_secrets_file(
                            str(creds_path),
                            SCOPES,
                            redirect_uri='http://localhost:8080'
                        )
                        creds = flow.run_local_server(port=8080, open_browser=True)
                        
                        # Save token
                        token_path.parent.mkdir(parents=True, exist_ok=True)
                        with open(token_path, 'wb') as f:
                            pickle.dump(creds, f)
                        self.logger.info(f"Token saved to: {token_path}")
                    except Exception as e:
                        self.logger.error(f"OAuth flow failed: {e}")
                        self.logger.error("\nRun: python setup_gmail.py")
                        return
            
            # Build Gmail service
            self.service = build('gmail', 'v1', credentials=creds)
            
            # Test connection
            profile = self.service.users().getProfile(userId='me').execute()
            self.logger.info(f"✓ Connected to Gmail: {profile['emailAddress']}")
            self.logger.info(f"   Total messages: {profile['messagesTotal']}")
            
        except ImportError as e:
            self.logger.error(f"Missing dependencies: {e}")
            self.logger.error("Install: pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib")
        except Exception as e:
            self.logger.error(f"Failed to initialize Gmail service: {e}")
    
    def _check_for_updates(self) -> List[Dict]:
        """Check for new unread emails"""
        if not self.service:
            return []
        
        try:
            # Search for unread messages (exclude chats, drafts, spam, trash)
            results = self.service.users().messages().list(
                userId='me',
                q='is:unread -in:chats -in:drafts -in:spam -in:trash',
                maxResults=10
            ).execute()
            
            messages = results.get('messages', [])
            new_messages = []
            
            for msg in messages:
                msg_id = msg['id']
                if msg_id not in self.processed_ids:
                    new_messages.append(msg)
                    self.processed_ids.add(msg_id)
                    
                    # Keep set from growing too large
                    if len(self.processed_ids) > 1000:
                        self.processed_ids = set(list(self.processed_ids)[-500:])
            
            if new_messages:
                self.logger.info(f"Found {len(new_messages)} new message(s)")
            
            return new_messages
            
        except Exception as e:
            self.logger.error(f"Error checking for updates: {e}")
            return []
    
    def _get_message_details(self, message_id: str) -> Dict:
        """Get full message details including headers and body"""
        try:
            msg = self.service.users().messages().get(
                userId='me',
                id=message_id,
                format='full',
                metadataHeaders=['From', 'To', 'Subject', 'Date', 'Cc']
            ).execute()
            
            # Extract headers
            headers = {}
            for header in msg['payload']['headers']:
                name = header['name']
                value = header['value']
                headers[name] = value
            
            # Extract body
            body = self._extract_body(msg['payload'])
            
            # Extract attachments info
            attachments = self._get_attachments_info(msg['payload'])
            
            return {
                'id': message_id,
                'headers': headers,
                'body': body,
                'snippet': msg.get('snippet', ''),
                'attachments': attachments,
                'internal_date': msg.get('internalDate', '')
            }
            
        except Exception as e:
            self.logger.error(f"Error getting message details: {e}")
            return {}
    
    def _extract_body(self, payload: Dict) -> str:
        """Extract email body from payload"""
        body = ""
        
        # Check for multipart
        if 'parts' in payload:
            for part in payload['parts']:
                if part['mimeType'] == 'text/plain':
                    if 'data' in part['body']:
                        data = part['body']['data']
                        body = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
                        break
                    elif 'parts' in part:
                        body = self._extract_body(part)
                        if body:
                            break
        
        # Check for single part
        elif payload['mimeType'] == 'text/plain' and 'body' in payload:
            if 'data' in payload['body']:
                data = payload['body']['data']
                body = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
        
        # Fallback to HTML if no plain text
        if not body and 'parts' in payload:
            for part in payload['parts']:
                if part['mimeType'] == 'text/html':
                    if 'data' in part['body']:
                        data = part['body']['data']
                        body = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
                        # Simple HTML cleanup
                        body = body.replace('<br>', '\n').replace('<br/>', '\n')
                        break
        
        return body
    
    def _get_attachments_info(self, payload: Dict) -> List[Dict]:
        """Get information about attachments"""
        attachments = []
        
        if 'parts' in payload:
            for part in payload['parts']:
                if 'attachmentId' in part.get('body', {}):
                    attachments.append({
                        'filename': part.get('filename', 'unnamed'),
                        'mimeType': part.get('mimeType', ''),
                        'size': part.get('body', {}).get('size', 0),
                        'attachmentId': part['body']['attachmentId']
                    })
        
        return attachments
    
    def _determine_priority(self, headers: Dict, body: str) -> str:
        """Determine email priority based on content"""
        subject = headers.get('Subject', '').lower()
        from_addr = headers.get('From', '').lower()
        body_lower = body.lower() if body else ""

        # Check for urgent keywords
        for keyword in self.urgent_keywords:
            if keyword in subject or keyword in body_lower:
                return 'high'

        # Check for important domains
        important_domains = ['client', 'customer', 'partner', 'vendor', 'bank', 'finance']
        for domain in important_domains:
            if domain in from_addr:
                return 'high'

        return 'normal'

    def _suggest_reply(self, headers: Dict, body: str, priority: str) -> Dict:
        """Generate a suggested reply based on email content"""
        subject = headers.get('Subject', '').lower()
        from_addr = headers.get('From', 'Unknown')
        from_name = from_addr.split('<')[0].strip().strip('"')
        body_lower = body.lower() if body else ""

        # Determine email type and generate suggestion
        reply_suggestion = {
            'should_reply': True,
            'reply_to': from_addr,
            'subject': f"Re: {headers.get('Subject', 'No Subject')}",
            'tone': 'professional',
            'suggestion': '',
            'reason': '',
            'auto_generated': True
        }

        # Check if it's a notification (no reply needed)
        notification_indicators = [
            'noreply', 'no-reply', 'donotreply', 'do-not-reply',
            'notification', 'automated', 'system'
        ]
        is_notification = any(ind in from_addr.lower() for ind in notification_indicators)

        # Check if it's a social media notification
        social_domains = ['linkedin', 'tiktok', 'facebook', 'instagram', 'twitter', 'chatgpt']
        is_social = any(domain in from_addr.lower() for domain in social_domains)

        if is_notification or is_social:
            reply_suggestion['should_reply'] = False
            reply_suggestion['reason'] = 'Automated notification - no reply needed'
            reply_suggestion['suggestion'] = ''
            return reply_suggestion

        # Generate reply based on content type
        # Urgent/Important emails
        if priority == 'high':
            urgent_words = [w for w in self.urgent_keywords if w in body_lower or w in subject]
            reply_suggestion['tone'] = 'urgent_professional'
            reply_suggestion['reason'] = f"High priority email (keywords: {', '.join(urgent_words)})"
            reply_suggestion['suggestion'] = (
                f"Hi {from_name},\n\n"
                f"Thank you for reaching out. I've received your message and understand the urgency.\n\n"
                f"I'm looking into this right now and will get back to you with a detailed response shortly.\n\n"
                f"Best regards,\nKhansa Tanveer"
            )
            return reply_suggestion

        # Project/business related
        business_words = ['project', 'update', 'report', 'meeting', 'deadline', 'deliverable', 'task']
        is_business = any(word in body_lower for word in business_words)

        if is_business:
            reply_suggestion['tone'] = 'professional'
            reply_suggestion['reason'] = 'Business/project related email'
            reply_suggestion['suggestion'] = (
                f"Hi {from_name},\n\n"
                f"Thank you for your email. I've received your message regarding the project update.\n\n"
                f"I'll review the details and get back to you with a comprehensive response soon.\n\n"
                f"Best regards,\nKhansa Tanveer"
            )
            return reply_suggestion

        # General inquiry
        reply_suggestion['tone'] = 'friendly_professional'
        reply_suggestion['reason'] = 'General email - review needed'
        reply_suggestion['suggestion'] = (
            f"Hi {from_name},\n\n"
            f"Thank you for your email. I've received your message and will review it carefully.\n\n"
            f"I'll respond with the information you need as soon as possible.\n\n"
            f"Best regards,\nKhansa Tanveer"
        )

        return reply_suggestion

    def _create_plan_file(self, filename: str, headers: Dict, body: str, priority: str,
                         reply_suggestion: Dict, action_file_path: Path) -> Optional[Path]:
        """Create a plan file in Plans/ folder for processing this email"""
        try:
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            subject_clean = self._sanitize_filename(headers.get('Subject', 'No_Subject'), max_length=40)
            plan_path = self.plans_path / f"PLAN_EMAIL_{subject_clean}_{timestamp}.md"

            # Determine required actions
            actions = []
            if reply_suggestion.get('should_reply'):
                actions.append("- [ ] Review suggested reply")
                actions.append("- [ ] Customize reply content")
                actions.append("- [ ] Send reply to sender")
            else:
                actions.append("- [ ] Review notification (no action required)")

            if priority == 'high':
                actions.insert(0, "- [ ] URGENT: Prioritize this email")

            actions.extend([
                "- [ ] Archive email after processing",
                "- [ ] Update tracking log"
            ])

            plan_content = f"""---
type: email_action_plan
created: {datetime.datetime.now().isoformat()}
email_file: {filename}
email_subject: {headers.get('Subject', 'No Subject')}
email_from: {headers.get('From', 'Unknown')}
priority: {priority}
status: pending
---

# Action Plan: {headers.get('Subject', 'No Subject')}

**Created:** {datetime.datetime.now().isoformat()}
**Source Email:** {filename}
**Priority:** {priority.upper()}

## Required Actions

{chr(10).join(actions)}

## Suggested Approach

1. **Review** the action file in Needs_Action/
2. **Evaluate** the suggested reply
3. **Customize** the response as needed
4. **Send** reply via approved workflow
5. **Archive** the email

## Timeline

- **Detected:** {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **Action by:** {self._get_deadline(priority)}

## Notes

Add execution notes here...

---
*Auto-generated by Gmail Watcher*
"""

            if not self.dry_run:
                plan_path.write_text(plan_content, encoding='utf-8')
                self.logger.info(f"  Plan created: {plan_path.name}")
            else:
                self.logger.info(f"  [DRY RUN] Would create plan: {plan_path.name}")

            return plan_path

        except Exception as e:
            self.logger.error(f"Error creating plan file: {e}")
            return None

    def _create_pending_approval_file(self, filename: str, headers: Dict, body: str,
                                      priority: str, reply_suggestion: Dict,
                                      action_file_path: Path) -> Optional[Path]:
        """Create a Pending_Approval file for emails that need review/action"""
        try:
            # Only create pending approval for emails needing action
            if not reply_suggestion.get('should_reply'):
                self.logger.debug(f"  No approval needed: {filename}")
                return None

            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            subject_clean = self._sanitize_filename(headers.get('Subject', 'No_Subject'), max_length=40)
            approval_path = self.pending_approval_path / f"EMAIL_REPLY_{subject_clean}_{timestamp}.md"

            approval_content = f"""---
type: email_reply_approval
created: {datetime.datetime.now().isoformat()}
email_file: {filename}
email_subject: {headers.get('Subject', 'No Subject')}
email_from: {headers.get('From', 'Unknown')}
to: {headers.get('From', 'Unknown')}
subject: Re: {headers.get('Subject', 'No Subject')}
priority: {priority}
status: pending_approval
---

# Email Reply Approval Request

**Created:** {datetime.datetime.now().isoformat()}
**Source Email:** {filename}
**Priority:** {priority.upper()}

## Email Details

**From:** {headers.get('From', 'Unknown')}
**Subject:** {headers.get('Subject', 'No Subject')}
**Date:** {headers.get('Date', 'Unknown')}

## Suggested Reply

{reply_suggestion.get('suggestion', 'No suggestion available')}

---

## Approval Required

- [ ] **APPROVE** - Send this reply as-is
- [ ] **MODIFY** - Edit the reply before sending
- [ ] **REJECT** - Do not reply
- [ ] **ESCALATE** - Forward to human for handling

## Approval Decision

Approved by: ________________
Decision: APPROVE / MODIFY / REJECT
Date: ________________
Notes: ________________

## Processing Instructions

1. Review the suggested reply above
2. Check if the tone and content are appropriate
3. Approve, modify, or reject as needed
4. Move to Approved/ after decision

---
*Created by Gmail Watcher for AI Employee (Silver Tier)*
"""

            if not self.dry_run:
                approval_path.write_text(approval_content, encoding='utf-8')
                self.logger.info(f"  Pending approval created: {approval_path.name}")
            else:
                self.logger.info(f"  [DRY RUN] Would create approval: {approval_path.name}")

            return approval_path

        except Exception as e:
            self.logger.error(f"Error creating pending approval file: {e}")
            return None

    def _get_deadline(self, priority: str) -> str:
        """Calculate deadline based on priority"""
        now = datetime.datetime.now()
        if priority == 'high':
            deadline = now + datetime.timedelta(hours=2)
        else:
            deadline = now + datetime.timedelta(hours=24)
        return deadline.strftime('%Y-%m-%d %H:%M:%S')
    
    def _sanitize_filename(self, text: str, max_length: int = 50) -> str:
        """Sanitize text for use in filename"""
        # Remove invalid characters
        invalid_chars = '<>:"/\\|?* '
        for char in invalid_chars:
            text = text.replace(char, '_')
        
        # Limit length
        return text[:max_length].strip()
    
    def _create_action_file(self, message: Dict, details: Dict) -> Optional[Path]:
        """Create an action file for a new email with suggested reply"""
        try:
            headers = details['headers']
            body = details['body']
            priority = self._determine_priority(headers, body)
            reply_suggestion = self._suggest_reply(headers, body, priority)

            # Generate filename
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            subject = self._sanitize_filename(headers.get('Subject', 'No_Subject'))
            from_name = self._sanitize_filename(headers.get('From', 'Unknown').split('<')[0], max_length=30)

            filename = f"GMAIL_{from_name}_{subject}_{timestamp}.md"
            filepath = self.needs_action / filename

            # Format received date
            received_date = headers.get('Date', details.get('internal_date', ''))

            # Create markdown content with suggested reply
            content = f"""---
type: email
from: {headers.get('From', 'Unknown')}
to: {headers.get('To', '')}
subject: {headers.get('Subject', 'No Subject')}
received: {datetime.datetime.now().isoformat()}
date_header: {received_date}
message_id: {message['id']}
priority: {priority}
status: pending
platform: Gmail
---

# Email: {headers.get('Subject', 'No Subject')}

**From:** {headers.get('From', 'Unknown')}
**To:** {headers.get('To', '')}
**Date:** {received_date}
**Priority:** {priority.upper()}

---

## Message Content

{body if body else details.get('snippet', 'No content available')}

---

## Suggested Reply

**Should Reply:** {reply_suggestion['should_reply']}
**Tone:** {reply_suggestion['tone']}
**Reason:** {reply_suggestion['reason']}

"""
            if reply_suggestion['suggestion']:
                content += f"""```
{reply_suggestion['suggestion']}
```
"""
            else:
                content += "*No reply needed - this is an automated notification*\n"

            content += f"""
## Attachments
"""
            if details['attachments']:
                for i, att in enumerate(details['attachments'], 1):
                    content += f"{i}. {att['filename']} ({att['size']} bytes)\n"
            else:
                content += "None\n"

            content += f"""
## Suggested Actions

"""
            if reply_suggestion['should_reply']:
                content += f"""- [ ] Review suggested reply above
- [ ] Customize reply content
- [ ] Send reply via approved workflow
- [ ] Archive after processing
"""
            else:
                content += f"""- [ ] Review notification
- [ ] Archive if not needed
"""

            content += f"""
## Processing Log

- Created: {datetime.datetime.now().isoformat()}
- Status: Pending review
- Reply suggested: {'Yes' if reply_suggestion['suggestion'] else 'No'}

---
*Created by Gmail Watcher for AI Employee (Silver Tier)*
"""

            if not self.dry_run:
                filepath.write_text(content, encoding='utf-8')
                self.logger.info(f"✓ Created action file: {filename}")

                # Create plan file
                self._create_plan_file(
                    filename, headers, body, priority,
                    reply_suggestion, filepath
                )

                # Create pending approval file (if reply needed)
                self._create_pending_approval_file(
                    filename, headers, body, priority,
                    reply_suggestion, filepath
                )

                # Update dashboard
                self._update_dashboard(filename)
            else:
                self.logger.info(f"[DRY RUN] Would create: {filename}")

            return filepath

        except Exception as e:
            self.logger.error(f"Error creating action file: {e}")
            return None
    
    def _update_dashboard(self, filename: str):
        """Update Dashboard.md with new email activity"""
        try:
            sys.path.insert(0, str(self.vault_path))
            from agent_skills import AIEmployeeSkills
            skills = AIEmployeeSkills(str(self.vault_path))
            skills.update_dashboard_activity(
                f"New email received: {filename}",
                "email"
            )
            self.logger.info("✓ Dashboard updated")
        except Exception as e:
            self.logger.error(f"Error updating dashboard: {e}")

    def _parse_approved_email(self, email_file_path: Path) -> Optional[Dict]:
        """Parse an approved email action file to extract email details"""
        try:
            content = email_file_path.read_text(encoding='utf-8')

            # Parse frontmatter
            metadata = {}
            in_frontmatter = False
            body_start = False

            for line in content.split('\n'):
                if line.strip() == '---':
                    if not in_frontmatter:
                        in_frontmatter = True
                        continue
                    else:
                        body_start = True
                        break

                if in_frontmatter and ':' in line:
                    key, value = line.split(':', 1)
                    metadata[key.strip()] = value.strip()

            # Extract email body content
            body_content = ""
            if body_start:
                # Find the Message Content section
                if '## Message Content' in content:
                    body_start_idx = content.index('## Message Content') + len('## Message Content')
                    # Find end of section (next ## or end)
                    next_section = content.find('\n## ', body_start_idx)
                    if next_section == -1:
                        body_content = content[body_start_idx:].strip()
                    else:
                        body_content = content[body_start_idx:next_section].strip()

            return {
                'metadata': metadata,
                'body_content': body_content,
                'full_content': content
            }

        except Exception as e:
            self.logger.error(f"Error parsing approved email {email_file_path}: {e}")
            return None

    def _generate_reply_content(self, email_data: Dict) -> str:
        """Generate a professional email reply based on email content"""
        sender = email_data['metadata'].get('from', 'Unknown')
        subject = email_data['metadata'].get('subject', 'No Subject')
        email_body = email_data['body_content']

        # Extract sender name
        sender_name = sender.split('<')[0].strip().strip('"')

        # Determine context and generate appropriate reply
        email_lower = email_body.lower()
        subject_lower = subject.lower()

        # Check for urgent/important
        is_urgent = any(kw in email_lower or kw in subject_lower
                       for kw in self.urgent_keywords)

        if is_urgent:
            return (
                f"Hi {sender_name},\n\n"
                f"Thank you for reaching out. I've received your message and understand the urgency of the situation.\n\n"
                f"I'm currently reviewing the details you've shared and will prioritize this matter. I'll get back to you "
                f"with a comprehensive update and next steps shortly.\n\n"
                f"Please don't hesitate to reach out if you need anything else in the meantime.\n\n"
                f"Best regards,\nKhansa Tanveer"
            )

        # Check for business/project context
        business_words = ['project', 'update', 'report', 'meeting', 'deadline', 'deliverable',
                         'task', 'status', 'progress', 'timeline', 'milestone']
        is_business = any(word in email_lower or word in subject_lower for word in business_words)

        if is_business:
            return (
                f"Hi {sender_name},\n\n"
                f"Thank you for your email regarding {subject}. I've reviewed the details you shared.\n\n"
                f"I'm currently working through this and will provide you with a detailed update soon. "
                f"I'll make sure to cover all the points you've raised so we can move forward effectively.\n\n"
                f"Thanks for your patience and support.\n\n"
                f"Best regards,\nKhansa Tanveer"
            )

        # Check for common notification patterns
        notification_indicators = ['noreply', 'no-reply', 'donotreply', 'notification', 'automated']
        if any(ind in sender.lower() for ind in notification_indicators):
            return ""  # No reply for notifications

        # Default general reply
        return (
            f"Hi {sender_name},\n\n"
            f"Thank you for your email. I've received your message regarding {subject} and appreciate you reaching out.\n\n"
            f"I've reviewed the content and will follow up with you shortly with the information and actions you need. "
            f"Your message is important and I want to ensure I address everything properly.\n\n"
            f"Thanks for your patience.\n\n"
            f"Best regards,\nKhansa Tanveer"
        )

    def _create_action_plan_from_approved(
        self, email_file_path: Path, email_data: Dict
    ) -> Optional[Path]:
        """Create an action plan file from an approved email"""
        try:
            metadata = email_data['metadata']
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            subject_clean = self._sanitize_filename(
                metadata.get('subject', 'No_Subject'), max_length=40
            )
            plan_path = self.plans_path / f"PLAN_EMAIL_{subject_clean}_{timestamp}.md"

            priority = metadata.get('priority', 'normal')

            # Determine actions based on priority
            actions = []
            if priority == 'high':
                actions.append("- [ ] URGENT: Prioritize this email immediately")

            actions.extend([
                "- [ ] Review the original email content",
                "- [ ] Evaluate the suggested reply draft",
                "- [ ] Customize the response as needed",
                "- [ ] Send reply via approved workflow",
                "- [ ] Archive email after processing",
                "- [ ] Update tracking log"
            ])

            # Calculate deadline
            now = datetime.datetime.now()
            if priority == 'high':
                deadline = now + datetime.timedelta(hours=2)
            else:
                deadline = now + datetime.timedelta(hours=24)

            plan_content = f"""---
type: email_action_plan
created: {datetime.datetime.now().isoformat()}
email_file: {email_file_path.name}
email_subject: {metadata.get('subject', 'No Subject')}
email_from: {metadata.get('from', 'Unknown')}
priority: {priority}
status: pending
---

# Action Plan: {metadata.get('subject', 'No Subject')}

**Created:** {datetime.datetime.now().isoformat()}
**Source Email:** {email_file_path.name}
**Priority:** {priority.upper()}

## Required Actions

{chr(10).join(actions)}

## Suggested Approach

1. **Review** the original email in Needs_Action/
2. **Check** the draft reply in Pending_Approval/
3. **Customize** the reply content to match the specific context
4. **Approve** through the standard workflow (move to Approved/)
5. **Send** the reply via Gmail API
6. **Archive** the email and mark as Done

## Timeline

- **Detected:** {now.strftime('%Y-%m-%d %H:%M:%S')}
- **Action by:** {deadline.strftime('%Y-%m-%d %H:%M:%S')}

## Notes

Add execution notes here...

---
*Auto-generated by Gmail Watcher*
"""

            plan_path.write_text(plan_content, encoding='utf-8')
            self.logger.info(f"  Action plan created: {plan_path.name}")
            return plan_path

        except Exception as e:
            self.logger.error(f"Error creating action plan: {e}")
            return None

    def _create_draft_reply_from_approved(
        self, email_file_path: Path, email_data: Dict, reply_content: str
    ) -> Optional[Path]:
        """Create a draft reply in Pending_Approval/ from an approved email"""
        try:
            metadata = email_data['metadata']
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            subject_clean = self._sanitize_filename(
                metadata.get('subject', 'No_Subject'), max_length=40
            )

            # Build the "to" address from the original sender
            sender = metadata.get('from', '')
            sender_name = sender.split('<')[0].strip().strip('"')

            # Original subject
            original_subject = metadata.get('subject', 'No Subject')
            reply_subject = f"Re: {original_subject}"

            approval_path = self.pending_approval_path / f"GMAIL_{sender_name}_{subject_clean}_{timestamp}.md"

            approval_content = f"""---
type: email_draft
to: {sender}
subject: {reply_subject}
email_file: {email_file_path.name}
priority: {metadata.get('priority', 'normal')}
status: pending_approval
created: {datetime.datetime.now().isoformat()}
---

# Draft Email Reply

**To:** {sender}
**Subject:** {reply_subject}
**Created:** {datetime.datetime.now().isoformat()}
**Source Email:** {email_file_path.name}

---

## Suggested Reply

{reply_content}

---

## Approval Required

- [ ] **APPROVE** - Send this reply as-is
- [ ] **MODIFY** - Edit the reply before sending
- [ ] **REJECT** - Do not reply
- [ ] **ESCALATE** - Forward to human for handling

## Approval Decision

Approved by: ________________
Decision: APPROVE / MODIFY / REJECT
Date: ________________
Notes: ________________

## Processing Instructions

1. Review the suggested reply above
2. Check if the tone and content are appropriate
3. Modify as needed to match your style
4. Move to Approved/ to authorize sending
5. The email will be sent automatically after approval

---
*Draft created by Gmail Watcher for AI Employee (Silver Tier)*
*DO NOT SEND WITHOUT APPROVAL*
"""

            approval_path.write_text(approval_content, encoding='utf-8')
            self.logger.info(f"  Draft reply created: {approval_path.name}")
            return approval_path

        except Exception as e:
            self.logger.error(f"Error creating draft reply: {e}")
            return None

    def process_approved_emails(self) -> int:
        """
        Process all approved email action files from Approved/ folder.
        Creates action plans and draft replies in Pending_Approval/.

        Returns: Number of emails processed successfully.
        """
        approved_path = self.vault_path / "Approved"

        if not approved_path.exists():
            self.logger.info("No Approved/ folder found")
            return 0

        # Find all GMAIL files in Approved/
        approved_files = list(approved_path.glob("GMAIL_*.md"))

        if not approved_files:
            self.logger.info("No approved email files found in Approved/")
            return 0

        self.logger.info(f"Found {len(approved_files)} approved email(s) to process")

        processed = 0

        for email_file in approved_files:
            self.logger.info(f"\nProcessing: {email_file.name}")

            # Parse the approved email
            email_data = self._parse_approved_email(email_file)
            if not email_data:
                self.logger.warning(f"  Skipping {email_file.name} - parse failed")
                continue

            # Generate reply content
            reply_content = self._generate_reply_content(email_data)
            if not reply_content:
                self.logger.info(f"  No reply needed for {email_file.name}")
                # Still create the action plan
                self._create_action_plan_from_approved(email_file, email_data)
                processed += 1
                continue

            # Create action plan
            plan = self._create_action_plan_from_approved(email_file, email_data)
            if not plan:
                self.logger.warning(f"  Failed to create action plan for {email_file.name}")
                continue

            # Create draft reply
            draft = self._create_draft_reply_from_approved(
                email_file, email_data, reply_content
            )
            if not draft:
                self.logger.warning(f"  Failed to create draft reply for {email_file.name}")
                continue

            # Move original to Done/
            done_path = self.vault_path / "Done" / email_file.name
            try:
                email_file.rename(done_path)
                self.logger.info(f"  Moved original to Done/: {done_path.name}")
            except Exception as e:
                self.logger.error(f"  Failed to move to Done/: {e}")

            processed += 1
            self.logger.info(f"  ✓ Successfully processed {email_file.name}")

        self.logger.info(f"\n{'='*60}")
        self.logger.info(f"Email processing complete: {processed}/{len(approved_files)} processed")
        self.logger.info(f"{'='*60}")

        return processed

    def _is_approved_for_sending(self, file_path: Path) -> bool:
        """
        Check if a Pending_Approval file is marked as APPROVED.
        Looks for: [x] **APPROVE**, [✔] APPROVE, Decision: APPROVE, status: approved
        """
        try:
            content = file_path.read_text(encoding='utf-8').lower()

            approval_indicators = [
                '[x] **approve**',
                '[✔] approve',
                '[x] approve',
                'decision: approve',
                'status: approved',
                '[approved]',
                '✓ approve',
                '✅ approve'
            ]

            return any(indicator in content for indicator in approval_indicators)

        except Exception as e:
            self.logger.error(f"Error checking approval status of {file_path}: {e}")
            return False

    def _is_already_sent(self, file_path: Path) -> bool:
        """Check if a file has already been processed/sent"""
        try:
            content = file_path.read_text(encoding='utf-8')

            # Check frontmatter for sent status
            for line in content.split('\n'):
                if line.strip().startswith('status:') and 'sent' in line.lower():
                    return True
                if 'already sent' in line.lower():
                    return True

            return False

        except Exception as e:
            self.logger.error(f"Error checking sent status of {file_path}: {e}")
            return False

    def _parse_draft_reply(self, file_path: Path) -> Optional[Dict]:
        """Parse a draft reply file to extract email fields"""
        try:
            content = file_path.read_text(encoding='utf-8')

            # Parse frontmatter
            metadata = {}
            in_frontmatter = False
            body_start = False

            for line in content.split('\n'):
                if line.strip() == '---':
                    if not in_frontmatter:
                        in_frontmatter = True
                        continue
                    else:
                        body_start = True
                        break

                if in_frontmatter and ':' in line:
                    key, value = line.split(':', 1)
                    metadata[key.strip()] = value.strip().strip('"')

            # Extract reply body
            reply_body = ""
            if body_start:
                # Find "## Suggested Reply" section
                if '## Suggested Reply' in content:
                    start_idx = content.index('## Suggested Reply') + len('## Suggested Reply')
                    # Find end of section
                    next_section = content.find('\n## ', start_idx)
                    if next_section == -1:
                        reply_body = content[start_idx:].strip()
                    else:
                        reply_body = content[start_idx:next_section].strip()
                elif '## Approval Required' in content:
                    # Fallback: body is between frontmatter end and Approval section
                    body_section = content.split('---', 2)[2] if content.count('---') >= 2 else ''
                    reply_body = body_section.split('## Approval Required')[0].strip()

            # Handle old-format files that don't have 'to' and 'subject' fields
            to_addr = metadata.get('to', '')
            subject = metadata.get('subject', '')

            if not to_addr:
                # Fall back to email_from field
                to_addr = metadata.get('email_from', '')

            if not subject:
                # Fall back to email_subject field
                subject = metadata.get('email_subject', '')
                if subject:
                    subject = f"Re: {subject}"

            metadata['to'] = to_addr
            metadata['subject'] = subject

            return {
                'metadata': metadata,
                'body': reply_body,
                'full_content': content,
                'file_path': file_path
            }

        except Exception as e:
            self.logger.error(f"Error parsing draft reply {file_path}: {e}")
            return None

    def _send_email_via_gmail(self, to: str, subject: str, body: str) -> Optional[str]:
        """
        Send an email via Gmail API.
        Returns message ID on success, None on failure.
        """
        try:
            import base64
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart

            # Get sender email from profile
            profile = self.service.users().getProfile(userId='me').execute()
            sender_email = profile['emailAddress']

            # Create message
            msg = MIMEMultipart()
            msg['To'] = to
            msg['From'] = sender_email
            msg['Subject'] = subject

            msg.attach(MIMEText(body, 'plain'))

            # Encode message
            raw_message = base64.urlsafe_b64encode(msg.as_bytes()).decode('utf-8')

            # Send message
            sent_message = self.service.users().messages().send(
                userId='me',
                body={'raw': raw_message}
            ).execute()

            self.logger.info(f"✓ Email sent successfully! Message ID: {sent_message['id']}")
            self.logger.info(f"  To: {to}")
            self.logger.info(f"  Subject: {subject}")

            return sent_message['id']

        except Exception as e:
            self.logger.error(f"✗ Failed to send email: {e}")
            import traceback
            self.logger.debug(traceback.format_exc())
            return None

    def _update_action_plan_status(self, email_file_name: str, status: str, sent_message_id: str = None):
        """Update the corresponding action plan file with new status"""
        try:
            # Find matching plan file
            plan_files = list(self.plans_path.glob(f"PLAN_EMAIL_*{email_file_name[:30]}*.md"))

            if not plan_files:
                self.logger.warning(f"  No matching action plan found for {email_file_name}")
                return

            # Use the most recent plan
            plan_file = sorted(plan_files)[-1]
            content = plan_file.read_text(encoding='utf-8')

            # Update status
            content = content.replace('status: pending', f'status: {status}')
            content = content.replace('status: in_progress', f'status: {status}')

            # Add completion note
            if sent_message_id:
                content += f"\n## Execution Result\n\n- **Sent:** {datetime.datetime.now().isoformat()}\n"
                content += f"- **Message ID:** {sent_message_id}\n"
                content += f"- **Status:** Email sent successfully\n"

            plan_file.write_text(content, encoding='utf-8')
            self.logger.info(f"  ✓ Action plan updated: {plan_file.name}")

        except Exception as e:
            self.logger.error(f"Error updating action plan: {e}")

    def _update_draft_status(self, file_path: Path, sent_message_id: str):
        """Update the draft file to mark it as sent"""
        try:
            content = file_path.read_text(encoding='utf-8')

            # Update status
            content = content.replace('status: pending_approval', 'status: sent')
            content = content.replace('status: approved', 'status: sent')

            # Add execution result
            execution_section = f"""
## Execution Result

- **Sent at:** {datetime.datetime.now().isoformat()}
- **Message ID:** {sent_message_id}
- **Status:** ✅ Email sent successfully

---
*Email sent automatically by Gmail Watcher*
"""

            if '## Execution Result' not in content:
                content += execution_section

            file_path.write_text(content, encoding='utf-8')
            self.logger.info(f"  ✓ Draft file updated: {file_path.name}")

        except Exception as e:
            self.logger.error(f"Error updating draft file: {e}")

    def _move_to_done(self, file_path: Path, subfolder: str = None):
        """Move a processed file to Done/ folder"""
        try:
            done_path = self.vault_path / "Done"
            if subfolder:
                done_path = done_path / subfolder
            done_path.mkdir(parents=True, exist_ok=True)

            dest_path = done_path / file_path.name

            # Avoid duplicates
            if dest_path.exists():
                dest_path = done_path / f"{file_path.stem}_{int(time.time())}{file_path.suffix}"

            file_path.rename(dest_path)
            self.logger.info(f"  ✓ Moved to Done/: {dest_path.name}")
            return dest_path

        except Exception as e:
            self.logger.error(f"Error moving file to Done/: {e}")
            return None

    def send_approved_replies(self) -> int:
        """
        Monitor Pending_Approval/ folder for approved email replies.
        For each file marked APPROVE:
        1. Parse the draft reply
        2. Send it via Gmail API
        3. Move original action file to Done/
        4. Update action plan status
        5. Update draft file status
        6. Log every step

        Returns: Number of emails sent successfully.
        """
        self.logger.info("=" * 60)
        self.logger.info("SENDING APPROVED EMAIL REPLIES")
        self.logger.info("=" * 60)

        if not self.service:
            self.logger.error("Gmail service not initialized")
            return 0

        pending_path = self.pending_approval_path

        if not pending_path.exists():
            self.logger.info("No Pending_Approval/ folder found")
            return 0

        # Find draft reply files
        draft_files = list(pending_path.glob("*.md"))

        if not draft_files:
            self.logger.info("No draft reply files found in Pending_Approval/")
            return 0

        self.logger.info(f"Found {len(draft_files)} file(s) in Pending_Approval/")

        sent_count = 0
        skipped_count = 0
        failed_count = 0

        for draft_file in draft_files:
            self.logger.info(f"\n{'─'*60}")
            self.logger.info(f"Processing: {draft_file.name}")

            # Skip if already sent
            if self._is_already_sent(draft_file):
                self.logger.info(f"  ⏭️  Already sent - skipping")
                skipped_count += 1
                continue

            # Check if approved
            if not self._is_approved_for_sending(draft_file):
                self.logger.info(f"  ⏭️  Not approved yet - skipping")
                skipped_count += 1
                continue

            self.logger.info(f"  ✓ File is APPROVED for sending")

            # Parse draft reply
            draft_data = self._parse_draft_reply(draft_file)
            if not draft_data:
                self.logger.error(f"  ✗ Failed to parse draft reply - skipping")
                failed_count += 1
                continue

            # Extract fields
            to_addr = draft_data['metadata'].get('to', '')
            subject = draft_data['metadata'].get('subject', 'No Subject')
            body = draft_data['body']
            email_file_name = draft_data['metadata'].get('email_file', '')

            if not to_addr or not body:
                self.logger.error(f"  ✗ Missing 'to' or 'body' in draft - skipping")
                failed_count += 1
                continue

            self.logger.info(f"  To: {to_addr}")
            self.logger.info(f"  Subject: {subject}")
            self.logger.info(f"  Body length: {len(body)} chars")
            self.logger.info(f"  Original file: {email_file_name}")

            # Send email
            if not self.dry_run:
                self.logger.info(f"  📤 Sending email...")
                message_id = self._send_email_via_gmail(to_addr, subject, body)

                if not message_id:
                    self.logger.error(f"  ✗ Failed to send email")
                    failed_count += 1
                    continue

                self.logger.info(f"  ✓ Email sent! Message ID: {message_id}")

                # Update draft file
                self._update_draft_status(draft_file, message_id)

                # Update action plan
                if email_file_name:
                    self._update_action_plan_status(
                        email_file_name,
                        'completed',
                        message_id
                    )

                # Move draft to Done/
                self._move_to_done(draft_file, subfolder='email_replies')

                # Move original action file to Done/ if it exists
                if email_file_name:
                    original_path = self.needs_action / email_file_name
                    if original_path.exists():
                        self._move_to_done(original_path, subfolder='emails')

                    # Also check Done/ for the original (might already be there)
                    original_in_done = self.vault_path / "Done" / email_file_name
                    if not original_in_done.exists():
                        # Check if it's still in Needs_Action
                        pass  # Already handled above

                sent_count += 1
                self.logger.info(f"  ✅ SUCCESS: Email sent and files updated")

            else:
                self.logger.info(f"  [DRY RUN] Would send email to {to_addr}")
                self.logger.info(f"  [DRY RUN] Subject: {subject}")
                sent_count += 1

        # Summary
        self.logger.info(f"\n{'='*60}")
        self.logger.info(f"APPROVED EMAIL SENDING COMPLETE")
        self.logger.info(f"{'='*60}")
        self.logger.info(f"  ✅ Sent successfully: {sent_count}")
        self.logger.info(f"  ⏭️  Skipped (not approved/already sent): {skipped_count}")
        self.logger.info(f"  ❌ Failed: {failed_count}")
        self.logger.info(f"  📦 Total processed: {len(draft_files)}")
        self.logger.info(f"{'='*60}")

        return sent_count
    
    def run(self):
        """Run the Gmail watcher loop"""
        self.logger.info("=" * 60)
        self.logger.info("Gmail Watcher Starting...")
        self.logger.info(f"Vault: {self.vault_path}")
        self.logger.info(f"Check interval: {self.check_interval}s")
        self.logger.info(f"Dry run: {self.dry_run}")
        self.logger.info("=" * 60)
        
        if not self.service:
            self.logger.error("Gmail service not initialized. Exiting.")
            self.logger.error("Run: python setup_gmail.py")
            return
        
        self.logger.info("Monitoring Gmail for new messages...")
        self.logger.info("Press Ctrl+C to stop")
        
        try:
            while True:
                try:
                    # Check for new emails
                    messages = self._check_for_updates()
                    
                    # Process each new message
                    for msg in messages:
                        details = self._get_message_details(msg['id'])
                        if details:
                            self._create_action_file(msg, details)
                    
                    # Wait before next check
                    time.sleep(self.check_interval)
                    
                except Exception as e:
                    self.logger.error(f"Error in watch loop: {e}")
                    time.sleep(10)  # Brief wait before retry
                    
        except KeyboardInterrupt:
            self.logger.info("\nGmail Watcher stopped by user")
        except Exception as e:
            self.logger.error(f"Fatal error: {e}")


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Gmail Watcher for AI Employee',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python watchers/gmail_watcher.py                    # Run watcher
  python watchers/gmail_watcher.py --test             # Test mode
  python watchers/gmail_watcher.py --dry-run          # Dry run (no files)
  python watchers/gmail_watcher.py --interval 60      # Check every 60s
  python watchers/gmail_watcher.py --vault ../Vault   # Custom vault path
        """
    )
    
    parser.add_argument(
        '--vault-path', 
        type=str, 
        default='.',
        help='Path to AI Employee vault (default: current directory)'
    )
    parser.add_argument(
        '--credentials', 
        type=str, 
        default=None,
        help='Path to Gmail credentials JSON file'
    )
    parser.add_argument(
        '--interval', 
        type=int, 
        default=120,
        help='Check interval in seconds (default: 120)'
    )
    parser.add_argument(
        '--dry-run', 
        action='store_true',
        help='Run without creating files (for testing)'
    )
    parser.add_argument(
        '--test', 
        action='store_true',
        help='Run a single test check and exit'
    )
    parser.add_argument(
        '--max-results',
        type=int,
        default=10,
        help='Maximum emails to fetch per check (default: 10)'
    )
    parser.add_argument(
        '--process-approved',
        action='store_true',
        help='Process approved emails and create action plans + draft replies'
    )
    parser.add_argument(
        '--send-approved',
        action='store_true',
        help='Send approved email replies from Pending_Approval/'
    )

    args = parser.parse_args()
    
    # Create watcher
    watcher = GmailWatcher(
        vault_path=args.vault_path,
        check_interval=args.interval,
        dry_run=args.dry_run
    )
    
    if args.send_approved:
        # Send approved replies
        print("\n" + "=" * 60)
        print("Gmail Watcher - Send Approved Replies")
        print("=" * 60)

        count = watcher.send_approved_replies()
        print(f"\nSent {count} email(s)")
        print("Check Done/ folder for sent files")

    elif args.process_approved:
        # Process approved emails
        print("\n" + "=" * 60)
        print("Gmail Watcher - Process Approved Emails")
        print("=" * 60)

        count = watcher.process_approved_emails()
        print(f"\nProcessed {count} email(s)")
        print("Check Plans/ and Pending_Approval/ for generated files")

    elif args.test:
        # Test mode - single check
        print("\n" + "=" * 60)
        print("Gmail Watcher - Test Mode")
        print("=" * 60)
        
        if not watcher.service:
            print("❌ Gmail service not initialized")
            print("Run: python setup_gmail.py")
            sys.exit(1)
        
        print("\nChecking for new emails...")
        messages = watcher._check_for_updates()
        print(f"Found {len(messages)} new message(s)")
        
        for msg in messages[:5]:  # Show first 5
            details = watcher._get_message_details(msg['id'])
            if details:
                headers = details['headers']
                print(f"\n  From: {headers.get('From', 'Unknown')}")
                print(f"  Subject: {headers.get('Subject', 'No Subject')}")
                print(f"  Priority: {watcher._determine_priority(headers, details['body'])}")
        
        print("\n" + "=" * 60)
        print("Test complete!")
        
    else:
        # Run watcher
        watcher.run()


if __name__ == "__main__":
    main()
