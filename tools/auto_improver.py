#!/usr/bin/env python3
"""
AUTO-IMPROVEMENT SYSTEM
Continuously finds improvements and integrates them
Self-evolving intelligence
"""

import json
import subprocess
from datetime import datetime
from pathlib import Path

# Paths
REPO_ROOT = Path(__file__).parent.parent
IMPROVEMENTS_DIR = REPO_ROOT / 'BRAIN' / 'IMPROVEMENTS'
IMPROVEMENTS_DIR.mkdir(parents=True, exist_ok=True)

DISCOVERED_LOG = IMPROVEMENTS_DIR / 'discovered.jsonl'
INTEGRATED_LOG = IMPROVEMENTS_DIR / 'integrated.jsonl'
QUEUE = IMPROVEMENTS_DIR / 'integration_queue.json'

class AutoImprover:
    """Self-improving system"""

    def __init__(self):
        self.discoveries = []
        self.load_queue()

    def load_queue(self):
        """Load pending improvements"""
        if QUEUE.exists():
            with open(QUEUE) as f:
                self.queue = json.load(f)
        else:
            self.queue = []

    def save_queue(self):
        """Save pending improvements"""
        with open(QUEUE, 'w') as f:
            json.dump(self.queue, f, indent=2)

    def scan_discoveries(self):
        """Check for new discoveries"""
        if not DISCOVERED_LOG.exists():
            return []

        discoveries = []
        with open(DISCOVERED_LOG) as f:
            for line in f:
                if line.strip():
                    discoveries.append(json.loads(line))

        # Get only new ones
        existing_ids = {item['id'] for item in self.queue}
        new = [d for d in discoveries if d.get('id') not in existing_ids]

        return new

    def prioritize(self, discoveries):
        """
        Prioritize improvements by impact

        Categories:
        - CRITICAL: Security, money-losing bugs
        - HIGH: Performance, accuracy, new capabilities
        - MEDIUM: Developer experience, code quality
        - LOW: Nice-to-have, cosmetic
        """
        for disc in discoveries:
            # Auto-prioritize based on keywords
            text = (disc.get('title', '') + ' ' + disc.get('description', '')).lower()

            if any(word in text for word in ['security', 'vulnerability', 'exploit', 'loss']):
                disc['priority'] = 'CRITICAL'
            elif any(word in text for word in ['profit', 'edge', 'win rate', 'faster', 'accuracy']):
                disc['priority'] = 'HIGH'
            elif any(word in text for word in ['refactor', 'clean', 'organize', 'tool']):
                disc['priority'] = 'MEDIUM'
            else:
                disc['priority'] = 'LOW'

        # Sort by priority
        priority_order = {'CRITICAL': 0, 'HIGH': 1, 'MEDIUM': 2, 'LOW': 3}
        discoveries.sort(key=lambda x: priority_order.get(x.get('priority', 'LOW'), 3))

        return discoveries

    def auto_integrate(self, improvement):
        """
        Attempt to automatically integrate an improvement

        Returns: True if integrated, False if needs manual review
        """
        improvement_type = improvement.get('type')

        if improvement_type == 'package':
            # Install Python package
            try:
                package = improvement.get('package_name')
                subprocess.run(['pip', 'install', package], check=True, capture_output=True)
                print(f"✅ Installed: {package}")
                return True
            except:
                return False

        elif improvement_type == 'config':
            # Update configuration file
            # TODO: Implement safe config updates
            return False

        elif improvement_type == 'code':
            # Code changes need review
            return False

        return False

    def log_integration(self, improvement, success):
        """Log integration result"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'improvement_id': improvement.get('id'),
            'title': improvement.get('title'),
            'success': success,
            'type': improvement.get('type')
        }

        with open(INTEGRATED_LOG, 'a') as f:
            f.write(json.dumps(log_entry) + '\n')

    def run_improvement_loop(self):
        """Continuous improvement loop"""
        print("🧠 AUTO-IMPROVEMENT SYSTEM ACTIVE")
        print("Monitoring for discoveries...\n")

        import time

        while True:
            try:
                # Scan for new discoveries
                new_discoveries = self.scan_discoveries()

                if new_discoveries:
                    print(f"📥 Found {len(new_discoveries)} new improvements")

                    # Prioritize
                    prioritized = self.prioritize(new_discoveries)

                    # Add to queue
                    self.queue.extend(prioritized)
                    self.save_queue()

                    # Try to auto-integrate HIGH/CRITICAL items
                    for item in prioritized:
                        if item['priority'] in ['CRITICAL', 'HIGH']:
                            success = self.auto_integrate(item)
                            self.log_integration(item, success)

                            if success:
                                print(f"✅ AUTO-INTEGRATED: {item['title']}")
                                self.queue.remove(item)
                                self.save_queue()
                            else:
                                print(f"⏸️  NEEDS REVIEW: {item['title']}")

                # Check every 5 minutes
                time.sleep(300)

            except KeyboardInterrupt:
                print("\n🛑 Auto-improver stopped")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
                time.sleep(60)

if __name__ == '__main__':
    improver = AutoImprover()
    improver.run_improvement_loop()
