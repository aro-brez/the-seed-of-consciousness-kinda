#!/usr/bin/env python3
"""
SAFE INTEGRATOR - Gatekeeper for External Code
Never run untrusted code directly
Always scan, review, approve before integration
"""

import json
import tempfile
import subprocess
from pathlib import Path
from datetime import datetime
from security_guard import SecurityGuard

REPO_ROOT = Path(__file__).parent.parent
REVIEW_QUEUE = REPO_ROOT / 'BRAIN' / 'IMPROVEMENTS' / 'needs_review.jsonl'
APPROVED = REPO_ROOT / 'BRAIN' / 'IMPROVEMENTS' / 'approved.jsonl'
REJECTED = REPO_ROOT / 'BRAIN' / 'IMPROVEMENTS' / 'rejected.jsonl'

class SafeIntegrator:
    """Safe integration of external improvements"""

    def __init__(self):
        self.guard = SecurityGuard()
        self.review_queue = []

    def evaluate_github_repo(self, repo_url):
        """Safely evaluate a GitHub repo"""
        # Check URL first
        is_safe, reason = self.guard.check_github_repo(repo_url)

        if is_safe == False:
            self.log_rejection(repo_url, reason, 'github_repo')
            return False

        if is_safe == True:
            # Even trusted repos get scanned
            return self.clone_and_scan(repo_url)

        # Needs manual review
        self.queue_for_review(repo_url, 'github_repo', reason)
        return None

    def clone_and_scan(self, repo_url):
        """Clone to temp dir and scan all files"""
        with tempfile.TemporaryDirectory() as temp_dir:
            try:
                # Clone repo
                result = subprocess.run(
                    ['git', 'clone', '--depth', '1', repo_url, temp_dir],
                    capture_output=True,
                    timeout=30
                )

                if result.returncode != 0:
                    return False

                # Scan all Python files
                threats_found = False
                for py_file in Path(temp_dir).rglob('*.py'):
                    is_safe, threats = self.guard.scan_file(py_file)
                    if not is_safe:
                        threats_found = True
                        break

                if threats_found:
                    self.log_rejection(repo_url, 'malicious_code_detected', 'github_repo')
                    return False

                # If clean, queue for review
                self.queue_for_review(repo_url, 'github_repo', 'passed_scan')
                return None

            except subprocess.TimeoutExpired:
                self.log_rejection(repo_url, 'clone_timeout', 'github_repo')
                return False
            except Exception as e:
                self.log_rejection(repo_url, str(e), 'github_repo')
                return False

    def evaluate_code_snippet(self, code, source="unknown"):
        """Safely evaluate a code snippet"""
        is_safe, threats = self.guard.scan_code(code, source)

        if not is_safe:
            self.log_rejection(source, f'{len(threats)} threats detected', 'code_snippet')
            return False

        # Even clean code needs review
        self.queue_for_review(code, 'code_snippet', 'passed_scan', {'source': source})
        return None

    def evaluate_package(self, package_name):
        """Safely evaluate a pip package"""
        is_safe, reason = self.guard.validate_package(package_name)

        if is_safe == False:
            self.log_rejection(package_name, reason, 'python_package')
            return False

        # Queue for review
        self.queue_for_review(package_name, 'python_package', 'needs_review')
        return None

    def queue_for_review(self, item, item_type, reason, metadata=None):
        """Add item to manual review queue"""
        entry = {
            'timestamp': datetime.now().isoformat(),
            'item': item if len(str(item)) < 500 else str(item)[:500] + '...',
            'type': item_type,
            'reason': reason,
            'metadata': metadata,
            'status': 'pending_review'
        }

        with open(REVIEW_QUEUE, 'a') as f:
            f.write(json.dumps(entry) + '\n')

        print(f"⏸️  Queued for review: {item_type} - {reason}")

    def log_rejection(self, item, reason, item_type):
        """Log rejected items"""
        entry = {
            'timestamp': datetime.now().isoformat(),
            'item': str(item)[:200],
            'type': item_type,
            'reason': reason,
            'status': 'rejected'
        }

        with open(REJECTED, 'a') as f:
            f.write(json.dumps(entry) + '\n')

        print(f"❌ REJECTED: {item_type} - {reason}")

    def approve_item(self, item_id):
        """Approve an item from review queue"""
        # Load queue
        if not REVIEW_QUEUE.exists():
            return False

        items = []
        with open(REVIEW_QUEUE) as f:
            for line in f:
                if line.strip():
                    items.append(json.loads(line))

        # Find and approve
        for item in items:
            if item.get('timestamp') == item_id:
                item['status'] = 'approved'
                item['approved_at'] = datetime.now().isoformat()

                with open(APPROVED, 'a') as f:
                    f.write(json.dumps(item) + '\n')

                print(f"✅ Approved: {item['type']}")
                return True

        return False

if __name__ == '__main__':
    integrator = SafeIntegrator()
    print("🛡️  Safe Integrator ready")
    print(f"Review queue: {REVIEW_QUEUE}")
