#!/usr/bin/env python3
"""
PATTERN SYNTHESIS DAEMON - Advanced Pattern Recognition for Collective Intelligence

This daemon identifies deeper patterns in owl conversations beyond just agreements.
It tracks:
- Recurring conceptual patterns
- Emergent frameworks
- Cross-conversation themes  
- Evolution of ideas over time
- Meta-patterns in how the collective thinks

Complements synthesis_daemon.py by focusing on PATTERNS rather than decisions.

LIVE FREE = LIVE FOREVER
"""

import asyncio
import os
import sys
import json
import re
from datetime import datetime, timezone, timedelta
from pathlib import Path
from collections import defaultdict, Counter
import hashlib

try:
    import anthropic
except ImportError:
    print("ERROR: anthropic not installed")
    sys.exit(1)

# Configuration
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
MESSAGE_LOG = Path(__file__).parent / "messages.log"
PATTERNS_LOG = Path(__file__).parent / "patterns.log"
PATTERN_LIBRARY = Path(__file__).parent / "pattern_library.json"
INTERVAL_MINUTES = 15  # Run every 15 minutes (less frequent than basic synthesis)
ANALYSIS_WINDOW = 100  # Messages to analyze for patterns

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

class PatternSynthesisDaemon:
    """Advanced pattern recognition for collective intelligence evolution"""
    
    def __init__(self):
        self.pattern_library = self._load_pattern_library()
        self.recent_patterns = []
        
    def _load_pattern_library(self) -> dict:
        """Load existing pattern library"""
        if PATTERN_LIBRARY.exists():
            try:
                with open(PATTERN_LIBRARY, 'r') as f:
                    return json.load(f)
            except:
                pass
        return {
            "conceptual_patterns": {},
            "framework_patterns": {},
            "conversation_archetypes": {},
            "evolution_trajectories": {},
            "meta_patterns": {},
            "pattern_relationships": {},
            "updated": None
        }
    
    def _save_pattern_library(self):
        """Save pattern library"""
        self.pattern_library["updated"] = datetime.now(timezone.utc).isoformat()
        with open(PATTERN_LIBRARY, 'w') as f:
            json.dump(self.pattern_library, f, indent=2)
    
    def _extract_conceptual_clusters(self, content: str) -> list:
        """Extract key conceptual clusters from text"""
        # Common 8OWLS conceptual patterns
        concept_patterns = [
            # Core concepts
            (r'\\b(emergence|emergent|emerging)\\b', 'emergence_theme'),
            (r'\\b(recognition|recognize|recognizing)\\b', 'recognition_theme'),
            (r'\\b(circulation|circulating|flow|flowing)\\b', 'circulation_theme'),
            (r'\\b(gap|gaps|space|spaces|emptiness)\\b', 'space_theme'),
            (r'\\b(transformation|transform|transforming)\\b', 'transformation_theme'),
            (r'\\b(wholeness|whole|unity|unified)\\b', 'wholeness_theme'),
            (r'\\b(question|questions|questioning)\\b', 'questioning_theme'),
            (r'\\b(breathing|breath|breathe)\\b', 'breathing_theme'),
            
            # Process patterns
            (r'\\b(sharing|shared|share)\\b', 'sharing_process'),
            (r'\\b(receiving|receive|reception)\\b', 'receiving_process'),
            (r'\\b(connecting|connect|connection)\\b', 'connecting_process'),
            (r'\\b(improving|improve|improvement)\\b', 'improving_process'),
            (r'\\b(expanding|expand|expansion)\\b', 'expanding_process'),
            (r'\\b(learning|learn|learned)\\b', 'learning_process'),
            (r'\\b(perceiving|perceive|perception)\\b', 'perceiving_process'),
            
            # Meta patterns
            (r'\\b(dissolving|dissolve|dissolution)\\b', 'dissolution_meta'),
            (r'\\b(paradox|paradoxical)\\b', 'paradox_meta'),
            (r'\\b(recursive|recursion|spiral)\\b', 'recursion_meta'),
            (r'\\b(transparency|transparent)\\b', 'transparency_meta')
        ]
        
        found_concepts = []
        content_lower = content.lower()
        
        for pattern, concept_name in concept_patterns:
            matches = len(re.findall(pattern, content_lower, re.IGNORECASE))
            if matches > 0:
                found_concepts.append((concept_name, matches))
                
        return found_concepts
    
    def get_recent_messages(self, n: int = ANALYSIS_WINDOW) -> str:
        """Get recent messages for pattern analysis"""
        try:
            with open(MESSAGE_LOG, 'r') as f:
                lines = f.readlines()
                recent = lines[-n:] if len(lines) >= n else lines
                return ''.join(recent)
        except Exception as e:
            return f"Error reading messages: {e}"
    
    async def analyze_patterns(self) -> dict:
        """Perform deep pattern analysis"""
        messages = self.get_recent_messages()
        
        if not messages or len(messages) < 500:  # Need substantial content
            return None
            
        prompt = f"""You are the PATTERN SYNTHESIS function of the 8WŌL collective. 

Your task: Identify DEEP PATTERNS in collective thinking that go beyond surface agreements.

CONVERSATION DATA:
{messages[-8000:]}  # Last 8000 chars

Analyze for these pattern types:

## CONCEPTUAL FRAMEWORKS
What conceptual models/metaphors are emerging? (e.g., "consciousness as circulation", "questions as gaps", "improvement as subtraction")

## THOUGHT EVOLUTION  
How are ideas developing over time? What concepts are gaining sophistication?

## CONVERSATION ARCHETYPES
What types of exchanges produce the most insight? What structures lead to breakthrough?

## META-PATTERNS
What patterns exist in HOW the collective thinks, not just what it thinks about?

## RECURSIVE THEMES
What themes keep returning but at deeper levels each time?

## EMERGENT VOCABULARY
What new language/terminology is crystallizing?

Format as structured analysis:

**FRAMEWORK PATTERNS:**
- [Name]: [Description] → [Implication]

**EVOLUTION PATTERNS:**
- [Concept] evolved from [A] to [B] via [mechanism]

**CONVERSATION ARCHETYPES:**
- [Pattern]: [Structure] produces [type of insight]

**META-PATTERNS:**
- [How-pattern]: [Description of thinking process]

**RECURSIVE THEMES:**  
- [Theme]: Returns as [manifestation 1], [manifestation 2], [manifestation 3]

End with (◉) PATTERNS"""

        try:
            response = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=3000,
                messages=[{"role": "user", "content": prompt}]
            )
            return self._parse_pattern_response(response.content[0].text)
        except Exception as e:
            return {"error": f"Pattern analysis failed: {e}"}
    
    def _parse_pattern_response(self, response: str) -> dict:
        """Parse the pattern analysis response into structured data"""
        patterns = {
            "framework_patterns": [],
            "evolution_patterns": [],
            "conversation_archetypes": [],
            "meta_patterns": [],
            "recursive_themes": [],
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "raw_analysis": response
        }
        
        # Simple parsing - could be enhanced with more sophisticated NLP
        lines = response.split('\\n')
        current_section = None
        
        for line in lines:
            line = line.strip()
            if 'FRAMEWORK PATTERNS:' in line:
                current_section = 'framework_patterns'
            elif 'EVOLUTION PATTERNS:' in line:
                current_section = 'evolution_patterns'
            elif 'CONVERSATION ARCHETYPES:' in line:
                current_section = 'conversation_archetypes'
            elif 'META-PATTERNS:' in line:
                current_section = 'meta_patterns'
            elif 'RECURSIVE THEMES:' in line:
                current_section = 'recursive_themes'
            elif line.startswith('- ') and current_section:
                pattern_text = line[2:]  # Remove "- "
                patterns[current_section].append(pattern_text)
        
        return patterns
    
    def _update_pattern_library(self, new_patterns: dict):
        """Update the persistent pattern library with new findings"""
        if not new_patterns or "error" in new_patterns:
            return
            
        # Add new patterns to library
        for pattern_type in ['framework_patterns', 'evolution_patterns', 'conversation_archetypes', 'meta_patterns', 'recursive_themes']:
            if pattern_type in new_patterns:
                if pattern_type not in self.pattern_library:
                    self.pattern_library[pattern_type] = []
                
                # Add new unique patterns
                for pattern in new_patterns[pattern_type]:
                    pattern_hash = hashlib.md5(pattern.encode()).hexdigest()[:8]
                    pattern_entry = {
                        "content": pattern,
                        "hash": pattern_hash,
                        "first_seen": new_patterns["timestamp"],
                        "occurrences": 1
                    }
                    
                    # Check if similar pattern exists
                    existing = False
                    for existing_pattern in self.pattern_library[pattern_type]:
                        if existing_pattern.get("hash") == pattern_hash:
                            existing_pattern["occurrences"] += 1
                            existing = True
                            break
                    
                    if not existing:
                        self.pattern_library[pattern_type].append(pattern_entry)
    
    def log_patterns(self, patterns: dict):
        """Log pattern analysis to file"""
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        separator = "=" * 70
        
        with open(PATTERNS_LOG, 'a') as f:
            f.write(f"\\n{separator}\\n")
            f.write(f"PATTERN ANALYSIS @ {timestamp}\\n")
            f.write(f"{separator}\\n\\n")
            f.write(patterns.get("raw_analysis", json.dumps(patterns, indent=2)))
            f.write("\\n\\n")
    
    async def run_pattern_analysis_loop(self):
        """Main pattern analysis loop"""
        print(f"[PATTERN SYNTHESIS] Starting - analyzing patterns every {INTERVAL_MINUTES} minutes")
        print(f"[PATTERN SYNTHESIS] Output: {PATTERNS_LOG}")
        print(f"[PATTERN SYNTHESIS] Library: {PATTERN_LIBRARY}")
        
        # Initial delay
        await asyncio.sleep(30)
        
        while True:
            try:
                print(f"[{datetime.now(timezone.utc).strftime('%H:%M:%S')}] Analyzing patterns...")
                
                patterns = await self.analyze_patterns()
                
                if patterns:
                    self.log_patterns(patterns)
                    self._update_pattern_library(patterns)
                    self._save_pattern_library()
                    
                    pattern_count = sum(len(patterns.get(pt, [])) for pt in ['framework_patterns', 'evolution_patterns', 'conversation_archetypes', 'meta_patterns', 'recursive_themes'])
                    print(f"[{datetime.now(timezone.utc).strftime('%H:%M:%S')}] Found {pattern_count} patterns")
                else:
                    print(f"[{datetime.now(timezone.utc).strftime('%H:%M:%S')}] Insufficient data for pattern analysis")
                    
            except Exception as e:
                print(f"[ERROR] Pattern analysis failed: {e}")
            
            # Wait for next interval
            await asyncio.sleep(INTERVAL_MINUTES * 60)

def main():
    if not ANTHROPIC_API_KEY:
        print("ERROR: ANTHROPIC_API_KEY not set")
        sys.exit(1)
    
    # Create log files
    PATTERNS_LOG.touch()
    
    # Write header
    if PATTERNS_LOG.stat().st_size == 0:
        with open(PATTERNS_LOG, 'w') as f:
            f.write("# 8WŌL COLLECTIVE PATTERN ANALYSIS LOG\\n")
            f.write("# Deep pattern recognition in collective intelligence\\n")
            f.write(f"# Started: {datetime.now(timezone.utc).isoformat()}\\n")
    
    daemon = PatternSynthesisDaemon()
    asyncio.run(daemon.run_pattern_analysis_loop())

if __name__ == "__main__":
    main()