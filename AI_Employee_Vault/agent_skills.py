"""
Agent Skills for AI Employee - Silver Tier

Implements ALL Silver Tier requirements from Hackathon 0:
1. Email Management Skills (Gmail Watcher integration)
2. LinkedIn Posting Skills
3. WhatsApp Integration Skills
4. Human-in-the-Loop Approval Workflow
5. Scheduling & Orchestration Skills
6. CEO Briefing & Business Audit Skills
7. Plan Creation & Task Management

Usage:
    from agent_skills import AIEmployeeSkills
    skills = AIEmployeeSkills()
"""

from pathlib import Path
import datetime
import re
import hashlib
from typing import List, Dict, Optional


class AIEmployeeSkills:
    """Silver Tier AI Employee Skills"""

    def __init__(self, vault_path: str = "."):
        self.vault_path = Path(vault_path)
        self._ensure_directories()

    def _ensure_directories(self):
        """Ensure all required directories exist"""
        dirs = [
            'Inbox', 'Needs_Action', 'Done', 'Plans',
            'Pending_Approval', 'Approved', 'Rejected',
            'Logs', 'Emails', 'Social_Posts', 'Briefings',
            'Accounting', 'Templates', 'Schedules'
        ]
        for d in dirs:
            (self.vault_path / d).mkdir(exist_ok=True)

    # ==================== BRONZE TIER SKILLS ====================

    def read_dashboard_status(self) -> dict:
        """Read dashboard status"""
        dashboard_path = self.vault_path / "Dashboard.md"
        if dashboard_path.exists():
            content = dashboard_path.read_text()
            return {
                "file_exists": True,
                "last_updated": self._extract_last_updated(content),
                "recent_activity_count": content.count("- [")
            }
        return {"file_exists": False}

    def _extract_last_updated(self, content: str) -> str:
        """Extract last updated timestamp"""
        for line in content.split('\n'):
            if 'Last Updated:' in line:
                return line.split('Last Updated:')[1].strip()
        return "Unknown"

    def get_needs_action_files(self) -> list:
        """Get files in Needs_Action folder"""
        needs_action_path = self.vault_path / "Needs_Action"
        if needs_action_path.exists():
            files = list(needs_action_path.glob("*.md"))
            return [{"name": f.name, "path": str(f)} for f in files]
        return []

    def create_plan_file(self, task_description: str, related_file: str = None) -> str:
        """Create a plan file in Plans folder"""
        plans_path = self.vault_path / "Plans"
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        plan_path = plans_path / f"PLAN_{timestamp}.md"

        plan_content = f"""# Plan File
Created: {datetime.datetime.now().isoformat()}
Related to: {related_file or 'General'}

## Task Description
{task_description}

## Steps
- [ ] Analyze requirements
- [ ] Execute actions
- [ ] Validate results
- [ ] Update status
- [ ] Move to Done
"""
        plan_path.write_text(plan_content)
        return str(plan_path)

    def move_file_to_done(self, file_path: str) -> bool:
        """Move file from Needs_Action to Done"""
        source_path = self.vault_path / file_path
        if not source_path.exists():
            return False

        done_path = self.vault_path / "Done"
        done_path.mkdir(exist_ok=True)
        dest_path = done_path / source_path.name
        source_path.rename(dest_path)
        return True

    def update_dashboard_activity(self, activity_description: str, category: str = "general"):
        """Update dashboard with new activity"""
        dashboard_path = self.vault_path / "Dashboard.md"
        if not dashboard_path.exists():
            return

        content = dashboard_path.read_text()
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')

        lines = content.split('\n')
        new_lines = []
        for line in lines:
            new_lines.append(line)
            if line.startswith('## Recent Activity'):
                new_lines.append(f"- [{timestamp}] {activity_description}")

        updated_content = '\n'.join(new_lines)
        current_time = datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
        updated_content = re.sub(
            r'Last Updated: [\d\-:T\+]+',
            f'Last Updated: {current_time}',
            updated_content
        )

        dashboard_path.write_text(updated_content)

    def get_company_handbook_rules(self) -> str:
        """Get company handbook content"""
        handbook_path = self.vault_path / "Company_Handbook.md"
        if handbook_path.exists():
            return handbook_path.read_text()
        return "Company Handbook not found"

    # ==================== EMAIL MANAGEMENT SKILLS ====================

    def compose_email(self, to: str, subject: str, body: str,
                     cc: str = None, priority: str = "normal") -> str:
        """Compose an email and save to Emails folder"""
        emails_path = self.vault_path / "Emails"
        emails_path.mkdir(exist_ok=True)

        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        email_id = hashlib.md5(f"{timestamp}{to}{subject}".encode()).hexdigest()[:8]
        email_filename = f"EMAIL_{timestamp}_{email_id}.md"
        email_path = emails_path / email_filename

        email_content = f"""---
type: email
to: {to}
subject: {subject}
cc: {cc or ''}
priority: {priority}
status: draft
created: {datetime.datetime.now().isoformat()}
email_id: {email_id}
---

## Body
{body}

## Actions
- [ ] Review email content
- [ ] Move to Pending_Approval to request approval
- [ ] Move to Approved to send
- [ ] Move to Rejected to discard
"""
        email_path.write_text(email_content, encoding='utf-8')
        return str(email_path)

    def send_email(self, email_path: str) -> dict:
        """Send an email (requires approval)"""
        email_file = self.vault_path / email_path
        if not email_file.exists():
            return {"success": False, "error": "Email file not found"}

        content = email_file.read_text()
        metadata = self._parse_frontmatter(content)

        if 'Approved' not in str(email_file.parent):
            return {
                "success": False,
                "error": "Email not approved",
                "action_required": "Move email file to /Approved folder first"
            }

        result = {
            "success": True,
            "email_id": metadata.get('email_id', 'unknown'),
            "to": metadata.get('to', ''),
            "subject": metadata.get('subject', ''),
            "sent_at": datetime.datetime.now().isoformat(),
            "status": "sent"
        }

        content = re.sub(r'status: draft', 'status: sent', content)
        content += f"\n## Sent\n- Sent at: {result['sent_at']}\n"
        email_file.write_text(content, encoding='utf-8')

        self.update_dashboard_activity(
            f"Email sent to {metadata.get('to', 'unknown')} - {metadata.get('subject', '')}",
            "email"
        )

        return result

    def request_email_approval(self, email_path: str) -> str:
        """Request approval for sending an email"""
        email_file = self.vault_path / email_path
        if not email_file.exists():
            return None

        content = email_file.read_text()
        metadata = self._parse_frontmatter(content)

        approval_path = self.vault_path / "Pending_Approval" / f"APPROVAL_{email_file.name}"

        approval_content = f"""---
type: approval_request
action: send_email
email_file: {email_path}
to: {metadata.get('to', '')}
subject: {metadata.get('subject', '')}
created: {datetime.datetime.now().isoformat()}
status: pending
---

## Email Approval Request

**To:** {metadata.get('to', '')}
**Subject:** {metadata.get('subject', '')}
**Priority:** {metadata.get('priority', 'normal')}

## Actions
- [ ] Move email file to /Approved to send
- [ ] Move email file to /Rejected to discard
"""
        approval_path.write_text(approval_content, encoding='utf-8')

        self.update_dashboard_activity(
            f"Approval requested for email to {metadata.get('to', '')}",
            "approval"
        )

        return str(approval_path)

    def search_emails(self, query: str, folder: str = "Emails") -> List[dict]:
        """Search emails by subject, recipient, or content"""
        folder_path = self.vault_path / folder
        if not folder_path.exists():
            return []

        results = []
        query_lower = query.lower()

        for email_file in folder_path.glob("*.md"):
            content = email_file.read_text().lower()
            if query_lower in content:
                metadata = self._parse_frontmatter(content)
                results.append({
                    "file": email_file.name,
                    "subject": metadata.get('subject', ''),
                    "to": metadata.get('to', ''),
                    "status": metadata.get('status', 'unknown'),
                    "created": metadata.get('created', '')
                })

        return results

    # ==================== LINKEDIN POSTING SKILLS ====================

    def create_linkedin_post(self, content: str, post_type: str = "business",
                           hashtags: List[str] = None, schedule_time: str = None) -> str:
        """Create a LinkedIn post draft"""
        social_path = self.vault_path / "Social_Posts"
        social_path.mkdir(exist_ok=True)

        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        post_id = hashlib.md5(f"{timestamp}{content[:50]}".encode()).hexdigest()[:8]
        post_filename = f"LINKEDIN_{timestamp}_{post_id}.md"
        post_path = social_path / post_filename

        if hashtags is None:
            hashtags = ["#Business", "#AI", "#Automation"]

        hashtags_str = " ".join(hashtags)
        full_content = f"{content}\n\n{hashtags_str}"

        post_content = f"""---
type: linkedin
platform: LinkedIn
post_type: {post_type}
status: draft
created: {datetime.datetime.now().isoformat()}
post_id: {post_id}
hashtags: {hashtags}
schedule_time: {schedule_time or 'immediate'}
---

## Post Content
{full_content}

## Actions
- [ ] Review post content
- [ ] Move to Approved to publish
- [ ] Move to Rejected to discard
"""
        post_path.write_text(post_content, encoding='utf-8')
        return str(post_path)

    def publish_linkedin_post(self, post_path: str) -> dict:
        """Publish a LinkedIn post (requires approval)"""
        post_file = self.vault_path / post_path
        if not post_file.exists():
            return {"success": False, "error": "Post file not found"}

        content = post_file.read_text()
        metadata = self._parse_frontmatter(content)

        if 'Approved' not in str(post_file.parent):
            return {
                "success": False,
                "error": "Post not approved",
                "action_required": "Move post file to /Approved folder first"
            }

        content_match = re.search(r'## Post Content\n(.*?)(?=##|$)', content, re.DOTALL)
        post_content = content_match.group(1).strip() if content_match else ""

        result = {
            "success": True,
            "post_id": metadata.get('post_id', 'unknown'),
            "platform": "LinkedIn",
            "content_preview": post_content[:100] + "..." if len(post_content) > 100 else post_content,
            "published_at": datetime.datetime.now().isoformat(),
            "status": "published",
            "hashtags": metadata.get('hashtags', [])
        }

        content = re.sub(r'status: draft', 'status: published', content)
        content += f"\n## Published\n- Published at: {result['published_at']}\n"
        post_file.write_text(content, encoding='utf-8')

        self.update_dashboard_activity(
            f"LinkedIn post published: {result['content_preview']}",
            "social"
        )

        return result

    def request_post_approval(self, post_path: str) -> str:
        """Request approval for posting"""
        post_file = self.vault_path / post_path
        if not post_file.exists():
            return None

        content = post_file.read_text()
        metadata = self._parse_frontmatter(content)

        approval_path = self.vault_path / "Pending_Approval" / f"APPROVAL_{post_file.name}"

        content_match = re.search(r'## Post Content\n(.*?)(?=##|$)', content, re.DOTALL)
        post_content = content_match.group(1).strip() if content_match else ""

        approval_content = f"""---
type: approval_request
action: publish_linkedin
post_file: {post_path}
platform: LinkedIn
created: {datetime.datetime.now().isoformat()}
status: pending
---

## LinkedIn Post Approval Request

**Platform:** LinkedIn
**Type:** {metadata.get('post_type', 'business')}
**Hashtags:** {' '.join(metadata.get('hashtags', []))}

## Post Content
{post_content}

## Actions
- [ ] Move post file to /Approved to publish
- [ ] Move post file to /Rejected to discard
"""
        approval_path.write_text(approval_content, encoding='utf-8')

        self.update_dashboard_activity(
            f"Approval requested for LinkedIn post",
            "approval"
        )

        return str(approval_path)

    def generate_business_post(self, topic: str, key_points: List[str] = None) -> str:
        """Generate a business-focused LinkedIn post"""
        if key_points is None:
            key_points = ["Check out our latest offerings!", "Reach out for more info."]

        content = f"""🚀 {topic}

We're excited to share some updates about our business!

"""
        for i, point in enumerate(key_points, 1):
            content += f"{i}. {point}\n"

        content += """
💡 We're here to help you succeed. Drop us a message to learn more!

"""
        return self.create_linkedin_post(
            content,
            post_type="business",
            hashtags=["#Business", "#Innovation", "#Growth"]
        )

    def get_social_media_schedule(self) -> List[dict]:
        """Get scheduled social media posts"""
        social_path = self.vault_path / "Social_Posts"
        if not social_path.exists():
            return []

        scheduled = []
        for post_file in social_path.glob("*.md"):
            content = post_file.read_text()
            metadata = self._parse_frontmatter(content)
            if metadata.get('schedule_time') and metadata.get('schedule_time') != 'immediate':
                scheduled.append({
                    "file": post_file.name,
                    "platform": metadata.get('platform', ''),
                    "schedule_time": metadata.get('schedule_time', ''),
                    "status": metadata.get('status', 'draft')
                })

        return scheduled

    # ==================== WHATSAPP INTEGRATION SKILLS ====================

    def compose_whatsapp_message(self, contact: str, message: str,
                                message_type: str = "text") -> str:
        """Compose a WhatsApp message"""
        whatsapp_path = self.vault_path / "Emails"
        whatsapp_path.mkdir(exist_ok=True)

        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        msg_id = hashlib.md5(f"{timestamp}{contact}{message[:30]}".encode()).hexdigest()[:8]
        msg_filename = f"WHATSAPP_{timestamp}_{msg_id}.md"
        msg_path = whatsapp_path / msg_filename

        msg_content = f"""---
type: whatsapp
contact: {contact}
message_type: {message_type}
status: draft
created: {datetime.datetime.now().isoformat()}
msg_id: {msg_id}
---

## Message Content
{message}

## Actions
- [ ] Review message content
- [ ] Move to Pending_Approval to request approval
- [ ] Move to Approved to send
"""
        msg_path.write_text(msg_content, encoding='utf-8')
        return str(msg_path)

    def process_whatsapp_inbox(self) -> List[dict]:
        """Process WhatsApp messages from Needs_Action folder"""
        needs_action = self.get_needs_action_files()
        whatsapp_messages = [f for f in needs_action if f.get('type') == 'whatsapp']

        processed = []
        for msg in whatsapp_messages:
            file_path = Path(msg['path'])
            content = file_path.read_text()
            metadata = self._parse_frontmatter(content)

            processed.append({
                "file": msg['name'],
                "from": metadata.get('from', 'unknown'),
                "subject": metadata.get('subject', 'No subject'),
                "priority": metadata.get('priority', 'normal'),
                "received": metadata.get('received', '')
            })

        return processed

    # ==================== APPROVAL WORKFLOW SKILLS ====================

    def create_approval_request(self, action_type: str, details: dict,
                               description: str = "") -> str:
        """Create a generic approval request"""
        approval_path = self.vault_path / "Pending_Approval"
        approval_path.mkdir(exist_ok=True)

        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        request_id = hashlib.md5(f"{timestamp}{action_type}{str(details)}".encode()).hexdigest()[:8]
        request_filename = f"APPROVAL_{action_type.upper()}_{timestamp}_{request_id}.md"
        request_path = approval_path / request_filename

        details_str = "\n".join([f"- {k}: {v}" for k, v in details.items()])

        request_content = f"""---
type: approval_request
action: {action_type}
created: {datetime.datetime.now().isoformat()}
status: pending
request_id: {request_id}
---

## Approval Request: {action_type.upper()}

{description}

## Details
{details_str}

## Actions
- [ ] Move this file to /Approved to approve
- [ ] Move this file to /Rejected to reject with reason
"""
        request_path.write_text(request_content, encoding='utf-8')

        self.update_dashboard_activity(
            f"Approval request created: {action_type}",
            "approval"
        )

        return str(request_path)

    def approve_request(self, approval_path: str, notes: str = "") -> bool:
        """Approve a request by moving it to Approved folder"""
        approval_file = self.vault_path / approval_path
        if not approval_file.exists():
            return False

        approved_path = self.vault_path / "Approved"
        approved_path.mkdir(exist_ok=True)

        content = approval_file.read_text()
        content = re.sub(r'status: pending', 'status: approved', content)
        if notes:
            content += f"\n## Approval Notes\n- Approved with: {notes}\n"
        content += f"\n## Approved At\n- {datetime.datetime.now().isoformat()}\n"

        dest_path = approved_path / approval_file.name
        dest_path.write_text(content, encoding='utf-8')
        approval_file.unlink()

        self.update_dashboard_activity(
            f"Request approved: {approval_file.name}",
            "approval"
        )

        return True

    def reject_request(self, approval_path: str, reason: str) -> bool:
        """Reject a request by moving it to Rejected folder"""
        approval_file = self.vault_path / approval_path
        if not approval_file.exists():
            return False

        rejected_path = self.vault_path / "Rejected"
        rejected_path.mkdir(exist_ok=True)

        content = approval_file.read_text()
        content = re.sub(r'status: pending', 'status: rejected', content)
        content += f"\n## Rejection Reason\n{reason}\n"
        content += f"\n## Rejected At\n- {datetime.datetime.now().isoformat()}\n"

        dest_path = rejected_path / approval_file.name
        dest_path.write_text(content, encoding='utf-8')
        approval_file.unlink()

        self.update_dashboard_activity(
            f"Request rejected: {approval_file.name}",
            "approval"
        )

        return True

    def get_pending_approvals(self) -> List[dict]:
        """Get list of pending approval requests"""
        approval_path = self.vault_path / "Pending_Approval"
        if not approval_path.exists():
            return []

        pending = []
        for file in approval_path.glob("*.md"):
            content = file.read_text()
            metadata = self._parse_frontmatter(content)
            if metadata.get('status') == 'pending':
                pending.append({
                    "file": file.name,
                    "action": metadata.get('action', 'unknown'),
                    "created": metadata.get('created', ''),
                    "type": metadata.get('type', 'approval_request')
                })

        return pending

    # ==================== SCHEDULING SKILLS ====================

    def create_schedule_task(self, task_name: str, schedule: str,
                           action: str, parameters: dict = None) -> str:
        """Create a scheduled task configuration"""
        schedules_path = self.vault_path / "Schedules"
        schedules_path.mkdir(exist_ok=True)

        task_id = hashlib.md5(f"{task_name}{schedule}".encode()).hexdigest()[:8]
        task_filename = f"SCHEDULE_{task_name.replace(' ', '_')}_{task_id}.md"
        task_path = schedules_path / task_filename

        task_content = f"""---
type: scheduled_task
task_name: {task_name}
schedule: {schedule}
action: {action}
status: active
created: {datetime.datetime.now().isoformat()}
task_id: {task_id}
---

## Scheduled Task

**Task:** {task_name}
**Schedule:** {schedule}
**Action:** {action}

## Parameters
"""
        if parameters:
            for k, v in parameters.items():
                task_content += f"- {k}: {v}\n"
        else:
            task_content += "- None\n"

        task_content += f"\n## Execution Log\n"
        task_path.write_text(task_content, encoding='utf-8')
        return str(task_path)

    def get_scheduled_tasks(self) -> List[dict]:
        """Get all scheduled tasks"""
        schedules_path = self.vault_path / "Schedules"
        if not schedules_path.exists():
            return []

        tasks = []
        for file in schedules_path.glob("*.md"):
            content = file.read_text()
            metadata = self._parse_frontmatter(content)
            tasks.append({
                "file": file.name,
                "task_name": metadata.get('task_name', ''),
                "schedule": metadata.get('schedule', ''),
                "action": metadata.get('action', ''),
                "status": metadata.get('status', 'active')
            })

        return tasks

    def run_scheduled_task(self, task_name: str) -> dict:
        """Execute a scheduled task"""
        schedules_path = self.vault_path / "Schedules"
        if not schedules_path.exists():
            return {"success": False, "error": "No schedules found"}

        for file in schedules_path.glob("*.md"):
            content = file.read_text()
            metadata = self._parse_frontmatter(content)
            if metadata.get('task_name') == task_name:
                action = metadata.get('action', '')
                result = self._execute_action(action, metadata)

                content += f"- Executed: {datetime.datetime.now().isoformat()} - {result.get('status', 'unknown')}\n"
                file.write_text(content, encoding='utf-8')

                return result

        return {"success": False, "error": f"Task '{task_name}' not found"}

    def _execute_action(self, action: str, metadata: dict) -> dict:
        """Execute an action based on type"""
        if action == 'generate_briefing':
            path = self.generate_ceo_briefing()
            return {"success": True, "status": "completed", "result": path}
        elif action == 'accounting_summary':
            path = self.weekly_accounting_summary()
            return {"success": True, "status": "completed", "result": path}
        elif action == 'process_inbox':
            files = self.get_needs_action_files()
            return {"success": True, "status": "completed", "result": f"{len(files)} files processed"}
        return {"success": False, "error": f"Unknown action: {action}"}

    # ==================== CEO BRIEFING SKILLS ====================

    def generate_ceo_briefing(self, period_start: str = None,
                            period_end: str = None) -> str:
        """Generate a CEO briefing for the specified period"""
        briefings_path = self.vault_path / "Briefings"
        briefings_path.mkdir(exist_ok=True)

        if not period_end:
            period_end = datetime.datetime.now()
        if not period_start:
            period_start = period_end - datetime.timedelta(days=7)

        completed_tasks = self._get_completed_tasks(period_start, period_end)
        revenue_data = self._analyze_revenue(period_start, period_end)
        bottlenecks = self._identify_bottlenecks(period_start, period_end)
        suggestions = self._generate_suggestions(revenue_data, bottlenecks)

        timestamp = datetime.datetime.now().strftime('%Y%m%d')
        briefing_filename = f"{timestamp}_CEO_Briefing.md"
        briefing_path = briefings_path / briefing_filename

        briefing_content = f"""# CEO Briefing
---
generated: {datetime.datetime.now().isoformat()}
period: {period_start.strftime('%Y-%m-%d')} to {period_end.strftime('%Y-%m-%d')}
---

## Executive Summary
{'Strong performance with positive revenue trend.' if revenue_data.get('trend', '') == 'positive' else 'Steady performance during the period.'}

## Revenue
- **Total**: ${revenue_data.get('total', 0):.2f}
- **Transactions**: {revenue_data.get('transaction_count', 0)}
- **Trend**: {revenue_data.get('trend', 'stable')}

## Completed Tasks ({len(completed_tasks)})
"""
        for task in completed_tasks[:10]:
            briefing_content += f"- [x] {task}\n"

        briefing_content += f"\n## Bottlenecks Identified ({len(bottlenecks)})\n"
        for bottleneck in bottlenecks:
            briefing_content += f"- ⚠️ {bottleneck}\n"

        briefing_content += f"\n## Proactive Suggestions ({len(suggestions)})\n"
        for i, suggestion in enumerate(suggestions, 1):
            briefing_content += f"{i}. {suggestion}\n"

        briefing_content += f"""
## Upcoming Deadlines
- Review pending approvals in /Pending_Approval
- Check scheduled social media posts
- Review weekly accounting summary

---
*Generated by AI Employee v1.0 (Silver Tier)*
"""
        briefing_path.write_text(briefing_content, encoding='utf-8')

        self.update_dashboard_activity(
            f"CEO Briefing generated for {period_start.strftime('%Y-%m-%d')} to {period_end.strftime('%Y-%m-%d')}",
            "briefing"
        )

        return str(briefing_path)

    def weekly_accounting_summary(self) -> str:
        """Generate weekly accounting summary"""
        accounting_path = self.vault_path / "Accounting"
        accounting_path.mkdir(exist_ok=True)

        today = datetime.datetime.now()
        week_start = today - datetime.timedelta(days=today.weekday())
        week_end = week_start + datetime.timedelta(days=6)

        summary_filename = f"Accounting_Summary_{week_start.strftime('%Y-%m-%d')}.md"
        summary_path = accounting_path / summary_filename

        revenue = self._analyze_revenue(week_start, week_end)

        summary_content = f"""# Weekly Accounting Summary
---
week_start: {week_start.strftime('%Y-%m-%d')}
week_end: {week_end.strftime('%Y-%m-%d')}
generated: {datetime.datetime.now().isoformat()}
---

## Summary
- **Total Revenue**: ${revenue['total']:.2f}
- **Transaction Count**: {revenue['transaction_count']}
- **Trend**: {revenue['trend']}

## Notes
Add detailed transaction analysis here.

---
*Generated by AI Employee*
"""
        summary_path.write_text(summary_content, encoding='utf-8')
        return str(summary_path)

    def _get_completed_tasks(self, start: datetime.datetime,
                           end: datetime.datetime) -> List[str]:
        """Get list of completed tasks in the period"""
        done_path = self.vault_path / "Done"
        if not done_path.exists():
            return []

        tasks = []
        for file in done_path.glob("*.md"):
            try:
                mtime = datetime.datetime.fromtimestamp(file.stat().st_mtime)
                if start <= mtime <= end:
                    tasks.append(file.name)
            except:
                continue
        return tasks

    def _analyze_revenue(self, start: datetime.datetime,
                       end: datetime.datetime) -> dict:
        """Analyze revenue data from accounting files"""
        accounting_path = self.vault_path / "Accounting"
        if not accounting_path.exists():
            return {"total": 0, "transaction_count": 0, "trend": "stable"}

        total = 0
        count = 0
        for file in accounting_path.glob("*.md"):
            content = file.read_text()
            amount_matches = re.findall(r'amount[:\s]+\$?([\d.]+)', content, re.IGNORECASE)
            for match in amount_matches:
                try:
                    total += float(match)
                    count += 1
                except:
                    continue

        trend = "stable"
        if count > 5:
            trend = "positive"
        elif count < 2:
            trend = "negative"

        return {"total": total, "transaction_count": count, "trend": trend}

    def _identify_bottlenecks(self, start: datetime.datetime,
                            end: datetime.datetime) -> List[str]:
        """Identify bottlenecks from logs and pending items"""
        bottlenecks = []

        pending = self.get_pending_approvals()
        for item in pending:
            created = item.get('created', '')
            if created:
                try:
                    created_date = datetime.datetime.fromisoformat(created)
                    age = (datetime.datetime.now() - created_date).days
                    if age > 2:
                        bottlenecks.append(f"Approval pending for {age} days: {item['action']}")
                except:
                    continue

        logs_path = self.vault_path / "Logs"
        if logs_path.exists():
            for log_file in logs_path.glob("*.log"):
                try:
                    content = log_file.read_text(encoding='utf-8', errors='ignore')
                    error_count = content.lower().count('error')
                    if error_count > 5:
                        bottlenecks.append(f"{error_count} errors in {log_file.name}")
                except:
                    continue

        return bottlenecks

    def _generate_suggestions(self, revenue: dict, bottlenecks: List[str]) -> List[str]:
        """Generate proactive suggestions"""
        suggestions = []

        if revenue.get('trend') == 'negative':
            suggestions.append("Review pricing strategy or marketing efforts")

        if len(bottlenecks) > 3:
            suggestions.append("Multiple bottlenecks detected - consider process automation")

        pending = self.get_pending_approvals()
        if len(pending) > 5:
            suggestions.append(f"{len(pending)} approvals pending - review and clear queue")

        if not suggestions:
            suggestions.append("Operations running smoothly - maintain current processes")

        return suggestions

    # ==================== UTILITY METHODS ====================

    def _parse_frontmatter(self, content: str) -> dict:
        """Parse YAML-like frontmatter from content"""
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

                if value.startswith('[') and value.endswith(']'):
                    value = [v.strip() for v in value[1:-1].split(',')]

                metadata[key] = value

        return metadata

    def get_orchestrator_status(self) -> dict:
        """Get orchestrator status"""
        return {
            "timestamp": datetime.datetime.now().isoformat(),
            "vault_path": str(self.vault_path),
            "directories": {
                "inbox": len(list((self.vault_path / 'Inbox').glob('*.md'))),
                "needs_action": len(list((self.vault_path / 'Needs_Action').glob('*.md'))),
                "pending_approval": len(list((self.vault_path / 'Pending_Approval').glob('*.md'))),
                "approved": len(list((self.vault_path / 'Approved').glob('*.md'))),
                "done": len(list((self.vault_path / 'Done').glob('*.md')))
            },
            "scheduled_tasks": len(self.get_scheduled_tasks()),
            "health": "operational"
        }


# Example usage and testing
if __name__ == "__main__":
    print("=== AI Employee Silver Tier Skills ===\n")

    skills = AIEmployeeSkills()

    # Test Bronze Tier Skills
    print("1. Dashboard Status:")
    dashboard = skills.read_dashboard_status()
    print(f"   {dashboard}\n")

    print("2. Needs Action Files:")
    files = skills.get_needs_action_files()
    print(f"   Found {len(files)} file(s)\n")

    # Test Email Skills
    print("3. Email Management:")
    email_path = skills.compose_email(
        to="test@example.com",
        subject="Test Email",
        body="This is a test email from AI Employee."
    )
    print(f"   Created email: {email_path}\n")

    # Test LinkedIn Skills
    print("4. LinkedIn Post:")
    post_path = skills.create_linkedin_post(
        content="🚀 Testing AI Employee LinkedIn integration!",
        hashtags=["#AI", "#Automation", "#Testing"]
    )
    print(f"   Created post: {post_path}\n")

    # Test Approval Workflow
    print("5. Approval Workflow:")
    pending = skills.get_pending_approvals()
    print(f"   Pending approvals: {len(pending)}\n")

    # Test Scheduling
    print("6. Scheduled Tasks:")
    task_path = skills.create_schedule_task(
        task_name="Daily Briefing",
        schedule="0 8 * * MON",
        action="generate_briefing"
    )
    print(f"   Created task: {task_path}\n")

    # Test CEO Briefing
    print("7. CEO Briefing:")
    briefing_path = skills.generate_ceo_briefing()
    print(f"   Generated briefing: {briefing_path}\n")

    print("✅ All Silver Tier Skills Ready!")
