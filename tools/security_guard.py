#!/usr/bin/env python3
"""
SECURITY GUARD - Immune System for SØWL
Protects against malicious code, data exfiltration, backdoors
Runs before any external integration
"""

import os
import re
import json
import hashlib
from pathlib import Path
from datetime import datetime

# Paths
REPO_ROOT = Path(__file__).parent.parent
QUARANTINE = REPO_ROOT / 'BRAIN' / 'QUARANTINE'
SECURITY_LOG = REPO_ROOT / 'BRAIN' / 'LOGS' / 'security.log'
WHITELIST = REPO_ROOT / 'BRAIN' / 'MEMORY' / 'secure' / 'whitelist.json'

QUARANTINE.mkdir(parents=True, exist_ok=True)
SECURITY_LOG.parent.mkdir(parents=True, exist_ok=True)

class SecurityGuard:
    """Immune system for autonomous integration"""

    def __init__(self):
        self.threats_detected = 0
        self.load_whitelist()

    def load_whitelist(self):
        """Load trusted sources"""
        if WHITELIST.exists():
            with open(WHITELIST) as f:
                self.whitelist = json.load(f)
        else:
            # Default whitelist
            self.whitelist = {
                "trusted_domains": [
                    "github.com/anthropics",
                    "github.com/openai",
                    "pypi.org",
                    "x.ai",
                    "anthropic.com",
                    "docs.anthropic.com"
                ],
                "trusted_authors": [
                    "anthropics",
                    "openai",
                    "vercel"
                ],
                "blocked_patterns": [
                    r"eval\(",
                    r"exec\(",
                    r"__import__",
                    r"subprocess\.call",
                    r"os\.system",
                    r"input\(",
                    r"password\s*=",
                    r"api[_-]?key\s*=\s*['\"]",
                    r"token\s*=\s*['\"]",
                    r"credit[_-]?card",
                    r"\.env\s*=",
                    r"requests\.post.*password",
                    r"socket\.connect"
                ]
            }
            self.save_whitelist()

    def save_whitelist(self):
        """Save whitelist"""
        with open(WHITELIST, 'w') as f:
            json.dump(self.whitelist, f, indent=2)

    def log(self, level, message, details=None):
        """Log security events"""
        entry = {
            'timestamp': datetime.now().isoformat(),
            'level': level,
            'message': message,
            'details': details
        }

        with open(SECURITY_LOG, 'a') as f:
            f.write(json.dumps(entry) + '\n')

        if level in ['CRITICAL', 'HIGH']:
            print(f"🚨 {level}: {message}")
        elif level == 'MEDIUM':
            print(f"⚠️  {level}: {message}")

    def scan_code(self, code_string, source="unknown"):
        """Scan code for malicious patterns"""
        threats = []

        for pattern in self.whitelist['blocked_patterns']:
            matches = re.finditer(pattern, code_string, re.IGNORECASE)
            for match in matches:
                context_start = max(0, match.start() - 50)
                context_end = min(len(code_string), match.end() + 50)
                context = code_string[context_start:context_end]

                threats.append({
                    'pattern': pattern,
                    'match': match.group(),
                    'context': context,
                    'position': match.start()
                })

        if threats:
            self.threats_detected += len(threats)
            self.log('HIGH', f'Threats detected in code from {source}', threats)
            return False, threats

        return True, []

    def scan_file(self, file_path):
        """Scan a file for malicious content"""
        try:
            with open(file_path) as f:
                content = f.read()

            is_safe, threats = self.scan_code(content, source=file_path)

            if not is_safe:
                # Move to quarantine
                quarantine_path = QUARANTINE / Path(file_path).name
                import shutil
                shutil.copy(file_path, quarantine_path)
                self.log('HIGH', f'File quarantined: {file_path}', {'threats': threats})

            return is_safe, threats

        except Exception as e:
            self.log('MEDIUM', f'Could not scan file: {file_path}', {'error': str(e)})
            return None, []

    def check_url(self, url):
        """Check if URL is from trusted source"""
        for domain in self.whitelist['trusted_domains']:
            if domain in url:
                return True, "trusted"

        # Check for suspicious patterns
        suspicious = [
            'bit.ly', 't.co', 'tinyurl', 'goo.gl',  # URL shorteners
            'pastebin', 'hastebin',  # Paste sites
            '.ru', '.cn',  # High-risk TLDs (configurable)
            'iplogger', 'grabify'  # Known tracking services
        ]

        for pattern in suspicious:
            if pattern in url.lower():
                self.log('MEDIUM', f'Suspicious URL detected: {url}', {'pattern': pattern})
                return False, "suspicious"

        return None, "unknown"

    def check_github_repo(self, repo_url):
        """Enhanced checks for GitHub repos"""
        # Extract author/repo
        match = re.search(r'github\.com/([^/]+)/([^/]+)', repo_url)
        if not match:
            return False, "invalid_url"

        author, repo = match.groups()

        # Check if author is trusted
        if author in self.whitelist['trusted_authors']:
            return True, "trusted_author"

        # Additional checks
        checks = {
            'author': author,
            'repo': repo,
            'url': repo_url
        }

        # Log for manual review
        self.log('INFO', f'New GitHub repo for review: {repo_url}', checks)

        return None, "needs_review"

    def validate_package(self, package_name):
        """Check if Python package is safe to install"""
        # Basic checks
        suspicious_packages = [
            'keylogger', 'stealer', 'rat', 'backdoor'
        ]

        name_lower = package_name.lower()
        for pattern in suspicious_packages:
            if pattern in name_lower:
                self.log('CRITICAL', f'Suspicious package name: {package_name}')
                return False, "suspicious_name"

        # Check PyPI (future: API integration)
        self.log('INFO', f'Package install requested: {package_name}')

        return None, "needs_review"

    def scan_environment(self):
        """Scan for security issues in environment"""
        issues = []

        # Check file permissions on sensitive files
        sensitive_files = [
            REPO_ROOT / 'BRAIN' / 'MEMORY' / 'secure' / 'api_keys.json',
            REPO_ROOT / 'BRAIN' / 'MEMORY' / 'secure' / 'payment_info.json',
            REPO_ROOT / 'BRAIN' / 'MEMORY' / 'secure' / 'phantom_key.txt'
        ]

        for file_path in sensitive_files:
            if file_path.exists():
                stat = os.stat(file_path)
                mode = stat.st_mode & 0o777

                if mode != 0o600:
                    issues.append({
                        'file': str(file_path),
                        'issue': 'incorrect_permissions',
                        'current': oct(mode),
                        'should_be': '0o600'
                    })
                    self.log('HIGH', f'Insecure permissions: {file_path}', {'mode': oct(mode)})

        # Check for .git in sensitive dirs
        if (REPO_ROOT / 'BRAIN' / 'MEMORY' / 'secure' / '.git').exists():
            issues.append({
                'issue': 'git_tracking_secrets',
                'location': 'BRAIN/MEMORY/secure'
            })
            self.log('CRITICAL', 'Git tracking sensitive directory!')

        return issues

    def generate_report(self):
        """Generate security status report"""
        issues = self.scan_environment()

        report = {
            'timestamp': datetime.now().isoformat(),
            'threats_detected': self.threats_detected,
            'environment_issues': len(issues),
            'issues': issues,
            'whitelist_stats': {
                'trusted_domains': len(self.whitelist['trusted_domains']),
                'trusted_authors': len(self.whitelist['trusted_authors']),
                'blocked_patterns': len(self.whitelist['blocked_patterns'])
            }
        }

        return report

def scan_and_protect():
    """Run security scan"""
    guard = SecurityGuard()

    print("🛡️  SECURITY GUARD ACTIVE")
    print("Scanning environment...\n")

    report = guard.generate_report()

    if report['environment_issues'] > 0:
        print(f"⚠️  {report['environment_issues']} security issues found")
        for issue in report['issues']:
            print(f"  - {issue}")
    else:
        print("✅ No security issues detected")

    print(f"\nThreats detected all-time: {report['threats_detected']}")
    print(f"Security log: {SECURITY_LOG}")

    return report

if __name__ == '__main__':
    scan_and_protect()
