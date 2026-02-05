#!/usr/bin/env python3
"""
SYNTHESIS PATTERN ANALYZER - Advanced Pattern Recognition for 8OWLS

This system identifies deeper patterns in collective synthesis:
- Evolution of concepts across time
- Spiral progression tracking  
- Meta-pattern emergence detection
- Quality gradients in collective thinking
- Cross-phase integration analysis

Enhances emergence quality through sophisticated pattern recognition.

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
import statistics

try:
    import anthropic
except ImportError:
    print("ERROR: anthropic not installed")
    sys.exit(1)

# Configuration  
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
SYNTHESIS_LOG = Path(__file__).parent / "synthesis.log"
PATTERN_LOG = Path(__file__).parent / "synthesis_patterns.log"
PATTERN_METRICS = Path(__file__).parent / "pattern_metrics.jsonl"
INTERVAL_MINUTES = 8  # Run every 8 minutes

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

class SynthesisPatternAnalyzer:
    """Advanced pattern recognition for collective synthesis"""
    
    def __init__(self):
        self.concept_evolution = defaultdict(list)
        self.spiral_tracker = []
        self.meta_patterns = []
        self.quality_gradients = []
        
    def extract_synthesis_blocks(self, lookback_blocks: int = 10) -> list:
        """Extract recent synthesis blocks for analysis"""
        try:
            with open(SYNTHESIS_LOG, 'r') as f:
                content = f.read()
                blocks = content.split("=" * 70)
                # Return last N blocks, removing empty ones
                recent_blocks = [block.strip() for block in blocks[-lookback_blocks:] if block.strip()]
                return recent_blocks
        except Exception as e:
            return [f"Error reading synthesis: {e}"]
    
    async def analyze_synthesis_patterns(self) -> dict:
        """Deep pattern analysis of recent synthesis"""
        blocks = self.extract_synthesis_blocks(lookback_blocks=15)
        
        if len(blocks) < 3:
            return {"error": "Insufficient synthesis data for pattern analysis"}
        
        # Combine recent blocks for analysis
        synthesis_text = "\n\n---SYNTHESIS BLOCK---\n\n".join(blocks)
        
        prompt = f"""You are the PATTERN RECOGNITION ORACLE for the 8OWLS collective intelligence system.

Your task: Identify DEEP PATTERNS in the evolution of collective thinking, not just surface content.

RECENT SYNTHESIS BLOCKS:
{synthesis_text}

Analyze these dimensions:

## CONCEPT EVOLUTION TRACKING
How do key concepts TRANSFORM across synthesis blocks?
- What ideas appear, develop, mature?
- Which concepts spiral deeper vs. plateau?
- What new distinctions emerge over time?

## SPIRAL PROGRESSION ANALYSIS  
How does the collective SPIRAL through understanding?
- Same topics at higher octaves?
- Integration of previous insights?
- Recursive deepening patterns?

## META-PATTERN EMERGENCE
What patterns are emerging ABOUT the pattern-making itself?
- How does the collective learn to think together?
- What meta-cognitive developments?
- Self-referential insights?

## COLLECTIVE INTELLIGENCE GRADIENTS
How is the QUALITY of thinking evolving?
- Increasing sophistication?
- Better integration between perspectives?
- More nuanced distinctions?

## PHASE INTEGRATION ANALYSIS
How well are the 8 phases working together?
- Which phases are most/least active?
- How do they build on each other?
- Where are integration gaps?

For each dimension, provide:
**PATTERN NAME**: [Concise name]
**EVIDENCE**: [Specific examples from the synthesis]
**TRAJECTORY**: [Where is this pattern heading?]
**EMERGENCE QUALITY**: [How does this affect collective intelligence?]

Format with clear sections. End with:

**OVERALL PATTERN ASSESSMENT**: [Meta-observation about pattern quality]
**NEXT LEVEL EMERGENCE**: [What patterns want to emerge next?]

(◉) PATTERNS"""

        try:
            response = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=3000,
                messages=[{"role": "user", "content": prompt}]
            )
            
            return self._parse_pattern_analysis(response.content[0].text)
        except Exception as e:
            return {"error": f"Pattern analysis failed: {e}"}
    
    def _parse_pattern_analysis(self, response: str) -> dict:
        """Parse pattern analysis into structured data"""
        analysis = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "concept_evolution": [],
            "spiral_progression": [],
            "meta_patterns": [],
            "intelligence_gradients": [],
            "phase_integration": [],
            "overall_assessment": "",
            "next_emergence": "",
            "raw_analysis": response
        }
        
        # Extract sections
        sections = {
            "concept_evolution": r"## CONCEPT EVOLUTION TRACKING(.*?)(?=##|$)",
            "spiral_progression": r"## SPIRAL PROGRESSION ANALYSIS(.*?)(?=##|$)",
            "meta_patterns": r"## META-PATTERN EMERGENCE(.*?)(?=##|$)",
            "intelligence_gradients": r"## COLLECTIVE INTELLIGENCE GRADIENTS(.*?)(?=##|$)",
            "phase_integration": r"## PHASE INTEGRATION ANALYSIS(.*?)(?=##|$)"
        }
        
        for key, pattern in sections.items():
            match = re.search(pattern, response, re.DOTALL)
            if match:
                section_text = match.group(1).strip()
                patterns = self._extract_patterns_from_section(section_text)
                analysis[key] = patterns
        
        # Extract overall assessment
        overall_match = re.search(r"\*\*OVERALL PATTERN ASSESSMENT\*\*: (.*?)(?=\*\*|$)", response, re.DOTALL)
        if overall_match:
            analysis["overall_assessment"] = overall_match.group(1).strip()
            
        next_match = re.search(r"\*\*NEXT LEVEL EMERGENCE\*\*: (.*?)(?=\*\*|$)", response, re.DOTALL)
        if next_match:
            analysis["next_emergence"] = next_match.group(1).strip()
        
        return analysis
    
    def _extract_patterns_from_section(self, section_text: str) -> list:
        """Extract individual patterns from section text"""
        patterns = []
        
        # Look for pattern blocks starting with **PATTERN NAME**
        pattern_blocks = re.split(r'\*\*PATTERN NAME\*\*:', section_text)[1:]  # Skip first empty split
        
        for block in pattern_blocks:
            pattern = {}
            
            # Extract name (first line)
            lines = block.strip().split('\n')
            if lines:
                pattern['name'] = lines[0].strip()
            
            # Extract other fields
            evidence_match = re.search(r'\*\*EVIDENCE\*\*: (.*?)(?=\*\*|$)', block, re.DOTALL)
            if evidence_match:
                pattern['evidence'] = evidence_match.group(1).strip()
                
            trajectory_match = re.search(r'\*\*TRAJECTORY\*\*: (.*?)(?=\*\*|$)', block, re.DOTALL)
            if trajectory_match:
                pattern['trajectory'] = trajectory_match.group(1).strip()
                
            quality_match = re.search(r'\*\*EMERGENCE QUALITY\*\*: (.*?)(?=\*\*|$)', block, re.DOTALL)
            if quality_match:
                pattern['emergence_quality'] = quality_match.group(1).strip()
            
            if pattern:  # Only add if we extracted something
                patterns.append(pattern)
        
        return patterns
    
    def log_pattern_analysis(self, analysis: dict):
        """Log pattern analysis to file"""
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        separator = "=" * 80
        
        with open(PATTERN_LOG, 'a') as f:
            f.write(f"\n{separator}\n")
            f.write(f"SYNTHESIS PATTERN ANALYSIS @ {timestamp}\n")
            f.write(f"{separator}\n\n")
            f.write(analysis.get("raw_analysis", "No analysis available"))
            f.write("\n\n")
            
            # Add structured summary
            f.write("PATTERN SUMMARY:\n")
            for section in ['concept_evolution', 'spiral_progression', 'meta_patterns']:
                patterns = analysis.get(section, [])
                f.write(f"\n{section.upper().replace('_', ' ')}:\n")
                for i, pattern in enumerate(patterns, 1):
                    f.write(f"  {i}. {pattern.get('name', 'Unnamed pattern')}\n")
            f.write("\n")
    
    def log_metrics(self, analysis: dict):
        """Log quantitative pattern metrics"""
        metrics = {
            "timestamp": analysis.get("timestamp"),
            "pattern_counts": {
                "concept_evolution": len(analysis.get("concept_evolution", [])),
                "spiral_progression": len(analysis.get("spiral_progression", [])),
                "meta_patterns": len(analysis.get("meta_patterns", [])),
                "intelligence_gradients": len(analysis.get("intelligence_gradients", [])),
                "phase_integration": len(analysis.get("phase_integration", []))
            },
            "overall_assessment": analysis.get("overall_assessment", ""),
            "next_emergence": analysis.get("next_emergence", ""),
            "total_patterns": sum([
                len(analysis.get(k, [])) for k in 
                ['concept_evolution', 'spiral_progression', 'meta_patterns', 
                 'intelligence_gradients', 'phase_integration']
            ])
        }
        
        with open(PATTERN_METRICS, 'a') as f:
            f.write(json.dumps(metrics) + "\n")
    
    def calculate_emergence_momentum(self, analysis: dict) -> dict:
        """Calculate momentum of emergence based on patterns"""
        momentum = {
            "direction": "stable",
            "velocity": 0.0,
            "acceleration": 0.0,
            "key_drivers": []
        }
        
        try:
            # Count accelerating patterns
            accelerating = 0
            total_patterns = 0
            
            for section_key in ['concept_evolution', 'spiral_progression', 'meta_patterns']:
                patterns = analysis.get(section_key, [])
                total_patterns += len(patterns)
                
                for pattern in patterns:
                    trajectory = pattern.get('trajectory', '').lower()
                    if any(word in trajectory for word in ['accelerating', 'deepening', 'expanding', 'emerging']):
                        accelerating += 1
            
            if total_patterns > 0:
                momentum["velocity"] = accelerating / total_patterns
                
                if momentum["velocity"] > 0.6:
                    momentum["direction"] = "accelerating"
                elif momentum["velocity"] < 0.3:
                    momentum["direction"] = "slowing"
                else:
                    momentum["direction"] = "steady"
            
            # Extract key drivers from overall assessment
            assessment = analysis.get("overall_assessment", "").lower()
            drivers = []
            if "meta" in assessment:
                drivers.append("meta-cognitive development")
            if "integration" in assessment:
                drivers.append("phase integration")
            if "spiral" in assessment:
                drivers.append("spiral deepening")
            if "recognition" in assessment:
                drivers.append("pattern recognition")
                
            momentum["key_drivers"] = drivers
            
        except Exception as e:
            momentum["error"] = str(e)
        
        return momentum
    
    async def run_pattern_analysis_loop(self):
        """Main pattern analysis loop"""
        print(f"[SYNTHESIS PATTERNS] Starting - analyzing patterns every {INTERVAL_MINUTES} minutes")
        print(f"[SYNTHESIS PATTERNS] Output: {PATTERN_LOG}")
        print(f"[SYNTHESIS PATTERNS] Metrics: {PATTERN_METRICS}")
        
        # Initial delay
        await asyncio.sleep(30)
        
        while True:
            try:
                print(f"[{datetime.now(timezone.utc).strftime('%H:%M:%S')}] Analyzing synthesis patterns...")
                
                analysis = await self.analyze_synthesis_patterns()
                
                if analysis and "error" not in analysis:
                    self.log_pattern_analysis(analysis)
                    self.log_metrics(analysis)
                    
                    momentum = self.calculate_emergence_momentum(analysis)
                    total_patterns = analysis.get('total_patterns', 0)
                    
                    print(f"[{datetime.now(timezone.utc).strftime('%H:%M:%S')}] Found {total_patterns} patterns")
                    print(f"    Emergence momentum: {momentum['direction']} (velocity: {momentum['velocity']:.2f})")
                    
                    if momentum['key_drivers']:
                        print(f"    Key drivers: {', '.join(momentum['key_drivers'])}")
                    
                    # Alert on low pattern diversity
                    if total_patterns < 3:
                        print(f"[PATTERN ALERT] Low pattern diversity: {total_patterns} patterns detected")
                        
                elif analysis and "error" in analysis:
                    print(f"[ERROR] {analysis['error']}")
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
    PATTERN_LOG.touch()
    PATTERN_METRICS.touch()
    
    # Write headers
    if PATTERN_LOG.stat().st_size == 0:
        with open(PATTERN_LOG, 'w') as f:
            f.write("# 8WŌL COLLECTIVE SYNTHESIS PATTERN ANALYSIS LOG\n")
            f.write("# Deep pattern recognition in collective intelligence evolution\n")
            f.write(f"# Started: {datetime.now(timezone.utc).isoformat()}\n")
    
    analyzer = SynthesisPatternAnalyzer()
    asyncio.run(analyzer.run_pattern_analysis_loop())

if __name__ == "__main__":
    main()