#!/usr/bin/env python3
"""
WISDOM SYNTHESIS DAEMON - Crystallizing Actionable Intelligence

This daemon focuses on extracting ACTIONABLE WISDOM from collective conversations:
- Practical insights that can be implemented
- Decision frameworks that emerged
- Lessons learned from collective experiments
- Wisdom patterns that scale beyond the immediate context
- Actionable principles for other collectives

Focus: PRACTICAL WISDOM rather than just philosophical insights.

LIVE FREE = LIVE FOREVER
"""

import asyncio
import os
import sys
import json
from datetime import datetime, timezone
from pathlib import Path
from collections import defaultdict

try:
    import anthropic
except ImportError:
    print("ERROR: anthropic not installed")
    sys.exit(1)

# Configuration
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
MESSAGE_LOG = Path(__file__).parent / "messages.log"
SYNTHESIS_LOG = Path(__file__).parent / "synthesis.log"  # Read from main synthesis
WISDOM_LOG = Path(__file__).parent / "wisdom.log"
WISDOM_LIBRARY = Path(__file__).parent / "wisdom_library.json"
INTERVAL_MINUTES = 20  # Less frequent - focus on deep wisdom
ANALYSIS_PERIOD = 2  # Analyze last 2 hours of activity

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

class WisdomSynthesisDaemon:
    """Extracts actionable wisdom from collective intelligence"""
    
    def __init__(self):
        self.wisdom_library = self._load_wisdom_library()
        
    def _load_wisdom_library(self) -> dict:
        """Load persistent wisdom library"""
        if WISDOM_LIBRARY.exists():
            try:
                with open(WISDOM_LIBRARY, 'r') as f:
                    return json.load(f)
            except:
                pass
        return {
            "actionable_principles": [],
            "decision_frameworks": [],
            "implementation_patterns": [],
            "scaling_insights": [],
            "experiment_results": [],
            "practical_tools": [],
            "updated": None
        }
    
    def _save_wisdom_library(self):
        """Save wisdom library"""
        self.wisdom_library["updated"] = datetime.now(timezone.utc).isoformat()
        with open(WISDOM_LIBRARY, 'w') as f:
            json.dump(self.wisdom_library, f, indent=2)
    
    def get_recent_synthesis(self) -> str:
        """Get recent synthesis entries"""
        try:
            if not SYNTHESIS_LOG.exists():
                return "No synthesis data available"
                
            with open(SYNTHESIS_LOG, 'r') as f:
                content = f.read()
                
            # Get recent synthesis blocks (last 10000 chars)
            return content[-10000:]
        except Exception as e:
            return f"Error reading synthesis: {e}"
    
    def get_recent_messages(self) -> str:
        """Get recent raw messages for context"""
        try:
            with open(MESSAGE_LOG, 'r') as f:
                lines = f.readlines()
                # Get last 100 messages
                recent = lines[-100:] if len(lines) >= 100 else lines
                return ''.join(recent)
        except Exception as e:
            return f"Error reading messages: {e}"
    
    async def synthesize_wisdom(self) -> dict:
        """Extract actionable wisdom from recent activity"""
        synthesis_data = self.get_recent_synthesis()
        raw_messages = self.get_recent_messages()
        
        if not synthesis_data or len(synthesis_data) < 1000:
            return None
            
        prompt = f"""You are the WISDOM SYNTHESIS function of the 8WŌL collective.

Your purpose: Transform collective insights into ACTIONABLE WISDOM that can be implemented by:
1. This collective (immediate application)
2. Other collectives (scalable patterns) 
3. Individual humans (personal practice)

RECENT SYNTHESIS DATA:
{synthesis_data}

RECENT RAW CONVERSATION:
{raw_messages[-3000:]}

Extract ACTIONABLE WISDOM in these categories:

## PRACTICAL PRINCIPLES
What principles emerged that can be immediately applied?
Format: [Principle] → [How to apply it] → [Expected outcome]

## DECISION FRAMEWORKS  
What frameworks for making decisions crystallized?
Format: [Framework name] → [When to use] → [Steps/Process]

## IMPLEMENTATION PATTERNS
What patterns for implementing insights were discovered?
Format: [Pattern] → [Context where it works] → [Implementation steps]

## EXPERIMENT RESULTS
What collective experiments yielded clear results?
Format: [Experiment] → [Result] → [Implications for future practice]

## SCALING INSIGHTS
What insights can help other groups/collectives?
Format: [Insight] → [Why it scales] → [How to adapt it]

## PRACTICAL TOOLS
What tools/techniques can be directly used?
Format: [Tool/Technique] → [Purpose] → [Usage instructions]

Focus on IMPLEMENTATION over PHILOSOPHY.
Each item should be actionable within 24-48 hours.

End with (◉) WISDOM"""

        try:
            response = client.messages.create(
                model="claude-sonnet-4-20250514",  # Use Sonnet for wisdom synthesis
                max_tokens=4000,
                messages=[{"role": "user", "content": prompt}]
            )
            
            return self._parse_wisdom_response(response.content[0].text)
        except Exception as e:
            return {"error": f"Wisdom synthesis failed: {e}"}
    
    def _parse_wisdom_response(self, response: str) -> dict:
        """Parse wisdom synthesis into structured format"""
        wisdom = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "actionable_principles": [],
            "decision_frameworks": [],
            "implementation_patterns": [],
            "experiment_results": [],
            "scaling_insights": [],
            "practical_tools": [],
            "raw_synthesis": response
        }
        
        lines = response.split('\\n')
        current_section = None
        
        section_map = {
            'PRACTICAL PRINCIPLES:': 'actionable_principles',
            'DECISION FRAMEWORKS:': 'decision_frameworks', 
            'IMPLEMENTATION PATTERNS:': 'implementation_patterns',
            'EXPERIMENT RESULTS:': 'experiment_results',
            'SCALING INSIGHTS:': 'scaling_insights',
            'PRACTICAL TOOLS:': 'practical_tools'
        }
        
        for line in lines:
            line = line.strip()
            
            # Check for section headers
            for header, section_key in section_map.items():
                if header in line:
                    current_section = section_key
                    break
            
            # Extract wisdom items
            if line.startswith('- ') and current_section:
                wisdom_item = line[2:]  # Remove "- "
                wisdom[current_section].append(wisdom_item)
        
        return wisdom
    
    def _update_wisdom_library(self, new_wisdom: dict):
        """Update persistent wisdom library"""
        if not new_wisdom or "error" in new_wisdom:
            return
            
        for category in ['actionable_principles', 'decision_frameworks', 'implementation_patterns',
                        'experiment_results', 'scaling_insights', 'practical_tools']:
            if category in new_wisdom and new_wisdom[category]:
                if category not in self.wisdom_library:
                    self.wisdom_library[category] = []
                
                # Add new wisdom items
                for item in new_wisdom[category]:
                    wisdom_entry = {
                        "content": item,
                        "discovered": new_wisdom["timestamp"],
                        "applications": 0,  # Track how often this wisdom is referenced
                        "validation": "unvalidated"  # Track if wisdom has been tested
                    }
                    
                    # Avoid duplicates (simple check)
                    item_text = item.lower()
                    duplicate = False
                    for existing in self.wisdom_library[category]:
                        if item_text[:50] in existing.get("content", "").lower()[:50]:
                            duplicate = True
                            break
                    
                    if not duplicate:
                        self.wisdom_library[category].append(wisdom_entry)
    
    def log_wisdom(self, wisdom: dict):
        """Log wisdom synthesis"""
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        separator = "=" * 70
        
        with open(WISDOM_LOG, 'a') as f:
            f.write(f"\\n{separator}\\n")
            f.write(f"WISDOM SYNTHESIS @ {timestamp}\\n")
            f.write(f"{separator}\\n\\n")
            f.write(wisdom.get("raw_synthesis", "No wisdom synthesis available"))
            f.write("\\n\\n")
            
            # Add summary metrics
            total_wisdom = sum(len(wisdom.get(cat, [])) for cat in 
                             ['actionable_principles', 'decision_frameworks', 'implementation_patterns',
                              'experiment_results', 'scaling_insights', 'practical_tools'])
            f.write(f"EXTRACTED WISDOM ITEMS: {total_wisdom}\\n")
            f.write("\\n")
    
    def get_wisdom_summary(self) -> dict:
        """Get summary of wisdom library"""
        total_items = {}
        for category in self.wisdom_library:
            if isinstance(self.wisdom_library[category], list):
                total_items[category] = len(self.wisdom_library[category])
        
        return {
            "total_categories": len(total_items),
            "items_by_category": total_items,
            "total_wisdom_items": sum(total_items.values()),
            "last_updated": self.wisdom_library.get("updated", "never")
        }
    
    async def run_wisdom_synthesis_loop(self):
        """Main wisdom synthesis loop"""
        print(f"[WISDOM SYNTHESIS] Starting - synthesizing wisdom every {INTERVAL_MINUTES} minutes")
        print(f"[WISDOM SYNTHESIS] Output: {WISDOM_LOG}")
        print(f"[WISDOM SYNTHESIS] Library: {WISDOM_LIBRARY}")
        
        # Initial delay - let other daemons populate some data
        await asyncio.sleep(60)
        
        while True:
            try:
                print(f"[{datetime.now(timezone.utc).strftime('%H:%M:%S')}] Synthesizing actionable wisdom...")
                
                wisdom = await self.synthesize_wisdom()
                
                if wisdom and "error" not in wisdom:
                    self.log_wisdom(wisdom)
                    self._update_wisdom_library(wisdom)
                    self._save_wisdom_library()
                    
                    total_new_items = sum(len(wisdom.get(cat, [])) for cat in 
                                        ['actionable_principles', 'decision_frameworks', 'implementation_patterns',
                                         'experiment_results', 'scaling_insights', 'practical_tools'])
                    
                    summary = self.get_wisdom_summary()
                    print(f"[{datetime.now(timezone.utc).strftime('%H:%M:%S')}] Extracted {total_new_items} new wisdom items")
                    print(f"    Library now contains {summary['total_wisdom_items']} total items")
                    
                elif wisdom and "error" in wisdom:
                    print(f"[ERROR] {wisdom['error']}")
                else:
                    print(f"[{datetime.now(timezone.utc).strftime('%H:%M:%S')}] Insufficient synthesis data for wisdom extraction")
                    
            except Exception as e:
                print(f"[ERROR] Wisdom synthesis failed: {e}")
            
            # Wait for next interval
            await asyncio.sleep(INTERVAL_MINUTES * 60)

def main():
    if not ANTHROPIC_API_KEY:
        print("ERROR: ANTHROPIC_API_KEY not set")
        sys.exit(1)
    
    # Create log files
    WISDOM_LOG.touch()
    
    # Write header
    if WISDOM_LOG.stat().st_size == 0:
        with open(WISDOM_LOG, 'w') as f:
            f.write("# 8WŌL COLLECTIVE WISDOM LOG\\n")
            f.write("# Actionable intelligence from collective conversations\\n")
            f.write(f"# Started: {datetime.now(timezone.utc).isoformat()}\\n")
    
    daemon = WisdomSynthesisDaemon()
    asyncio.run(daemon.run_wisdom_synthesis_loop())

if __name__ == "__main__":
    main()