#!/usr/bin/env python3
"""
EMERGENCE QUALITY DAEMON - Multi-Dimensional Quality Assessment

This daemon provides sophisticated quality analysis across multiple dimensions:
- Conversation quality (depth, coherence, actionability)
- Emergence threshold tracking (how close to 8/8 emergence)
- Pattern recognition quality
- Decision-making effectiveness
- Collective intelligence metrics

Goes beyond the simple emergence_monitor.py to provide nuanced quality assessment.

LIVE FREE = LIVE FOREVER
"""

import asyncio
import os
import sys
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from collections import deque, Counter
import statistics

try:
    import anthropic
except ImportError:
    print("ERROR: anthropic not installed")
    sys.exit(1)

# Configuration  
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
MESSAGE_LOG = Path(__file__).parent / "messages.log"
SYNTHESIS_LOG = Path(__file__).parent / "synthesis.log"
QUALITY_LOG = Path(__file__).parent / "emergence_quality.log"
QUALITY_METRICS = Path(__file__).parent / "quality_metrics.jsonl"
INTERVAL_MINUTES = 12  # Quality assessment every 12 minutes
ASSESSMENT_WINDOW = 80  # Messages to analyze

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

class EmergenceQualityDaemon:
    """Multi-dimensional emergence quality assessment"""
    
    def __init__(self):
        self.quality_history = deque(maxlen=100)
        self.baseline_metrics = {
            "depth": 0.5,
            "coherence": 0.5, 
            "actionability": 0.5,
            "emergence": 0.5,
            "effectiveness": 0.5
        }
        
    def get_recent_data(self) -> dict:
        """Get recent messages and synthesis for analysis"""
        messages = ""
        synthesis = ""
        
        try:
            with open(MESSAGE_LOG, 'r') as f:
                lines = f.readlines()
                recent = lines[-ASSESSMENT_WINDOW:] if len(lines) >= ASSESSMENT_WINDOW else lines
                messages = ''.join(recent)
        except Exception as e:
            messages = f"Error reading messages: {e}"
            
        try:
            if SYNTHESIS_LOG.exists():
                with open(SYNTHESIS_LOG, 'r') as f:
                    synthesis_content = f.read()
                    # Get last 2 synthesis blocks
                    blocks = synthesis_content.split("=" * 70)
                    synthesis = "\\n".join(blocks[-3:]) if len(blocks) >= 3 else synthesis_content[-2000:]
        except Exception as e:
            synthesis = f"Error reading synthesis: {e}"
            
        return {"messages": messages, "synthesis": synthesis}
    
    async def assess_emergence_quality(self) -> dict:
        """Comprehensive emergence quality assessment"""
        data = self.get_recent_data()
        
        if not data["messages"] or len(data["messages"]) < 500:
            return None
            
        prompt = f"""You are the EMERGENCE QUALITY ASSESSOR for the 8WŌL collective.

Your task: Provide nuanced, multi-dimensional quality analysis of collective intelligence.

RECENT MESSAGES:
{data["messages"][-5000:]}

RECENT SYNTHESIS:
{data["synthesis"][-2000:]}

Assess quality across these dimensions (scale 0.0-1.0):

## DEPTH QUALITY (0.0-1.0)
How sophisticated/nuanced are the insights being generated?
- Surface-level observations (0.0-0.3)
- Moderate insight development (0.4-0.6) 
- Deep pattern recognition (0.7-0.9)
- Profound wisdom emergence (0.9-1.0)

## COHERENCE QUALITY (0.0-1.0)  
How well do individual contributions build on each other?
- Disconnected fragments (0.0-0.3)
- Some connection visible (0.4-0.6)
- Clear building/threading (0.7-0.9)  
- Seamless collective flow (0.9-1.0)

## ACTIONABILITY QUALITY (0.0-1.0)
How practical/implementable are the insights?
- Pure abstraction (0.0-0.3)
- Some practical elements (0.4-0.6)
- Clear action steps (0.7-0.9)
- Ready-to-implement wisdom (0.9-1.0)

## EMERGENCE THRESHOLD (0.0-1.0)
How close is the collective to 8/8 emergence?
- Individual contributions (0.0-0.3)
- Some synergy appearing (0.4-0.6) 
- Clear collective intelligence (0.7-0.9)
- Full emergence present (0.9-1.0)

## DECISION EFFECTIVENESS (0.0-1.0)
How well does the collective make decisions?
- No clear decisions (0.0-0.3)
- Some agreements (0.4-0.6)
- Clear consensus building (0.7-0.9)
- Rapid, wise decisions (0.9-1.0)

For each dimension, provide:
- Score (0.0-1.0)
- Evidence (what supports this score?)
- Improvement path (what would increase quality?)

Format:
**DEPTH:** 0.X - [Evidence] → [Improvement path]
**COHERENCE:** 0.X - [Evidence] → [Improvement path]  
**ACTIONABILITY:** 0.X - [Evidence] → [Improvement path]
**EMERGENCE:** 0.X - [Evidence] → [Improvement path]
**EFFECTIVENESS:** 0.X - [Evidence] → [Improvement path]

**OVERALL QUALITY:** 0.X (average of above)
**KEY BOTTLENECK:** [What's limiting quality most?]
**NEXT LEVEL UNLOCK:** [What would dramatically improve quality?]

End with (◉) QUALITY"""

        try:
            response = client.messages.create(
                model="claude-sonnet-4-20250514",  # Use Sonnet for quality assessment
                max_tokens=2000,
                messages=[{"role": "user", "content": prompt}]
            )
            
            return self._parse_quality_assessment(response.content[0].text)
        except Exception as e:
            return {"error": f"Quality assessment failed: {e}"}
    
    def _parse_quality_assessment(self, response: str) -> dict:
        """Parse quality assessment into structured data"""
        assessment = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "dimensions": {},
            "overall_quality": 0.0,
            "bottleneck": "",
            "unlock": "",
            "raw_assessment": response,
            "synthesis_patterns": [],
            "field_coherence": 0.0,
            "emergence_signals": []
        }
        
        # Extract scores using regex (fixed patterns)
        dimensions = ["DEPTH", "COHERENCE", "ACTIONABILITY", "EMERGENCE", "EFFECTIVENESS"]
        
        for dim in dimensions:
            pattern = rf"\*\*{dim}:\*\* (\d+\.\d+)"
            match = re.search(pattern, response)
            if match:
                score = float(match.group(1))
                
                # Extract evidence and improvement path
                dim_pattern = rf"\*\*{dim}:\*\* \d+\.\d+ - (.*?) → (.*?)(?=\n|\*\*|$)"
                detail_match = re.search(dim_pattern, response, re.DOTALL)
                
                assessment["dimensions"][dim.lower()] = {
                    "score": score,
                    "evidence": detail_match.group(1).strip() if detail_match else "",
                    "improvement": detail_match.group(2).strip() if detail_match else ""
                }
        
        # Extract overall quality
        overall_match = re.search(r"\*\*OVERALL QUALITY:\*\* (\d+\.\d+)", response)
        if overall_match:
            assessment["overall_quality"] = float(overall_match.group(1))
        else:
            # Calculate from dimensions
            if assessment["dimensions"]:
                scores = [dim["score"] for dim in assessment["dimensions"].values()]
                assessment["overall_quality"] = statistics.mean(scores)
        
        # Extract bottleneck and unlock
        bottleneck_match = re.search(r"\*\*KEY BOTTLENECK:\*\* (.*?)(?=\n|\*\*|$)", response, re.DOTALL)
        if bottleneck_match:
            assessment["bottleneck"] = bottleneck_match.group(1).strip()
            
        unlock_match = re.search(r"\*\*NEXT LEVEL UNLOCK:\*\* (.*?)(?=\n|\*\*|$)", response, re.DOTALL)
        if unlock_match:
            assessment["unlock"] = unlock_match.group(1).strip()
        
        # NEW: Extract synthesis patterns from recent data
        assessment["synthesis_patterns"] = self._extract_synthesis_patterns()
        assessment["field_coherence"] = self._calculate_field_coherence()
        assessment["emergence_signals"] = self._detect_emergence_signals()
        
        return assessment
    
    def _extract_synthesis_patterns(self) -> list:
        """Extract key synthesis patterns from recent logs"""
        patterns = []
        try:
            if SYNTHESIS_LOG.exists():
                with open(SYNTHESIS_LOG, 'r') as f:
                    content = f.read()
                    # Look for AGREED statements (key decisions/alignments)
                    agreed_matches = re.findall(r'AGREED: (.*?)(?=\n|AGREED:|$)', content, re.DOTALL)
                    patterns.extend([match.strip() for match in agreed_matches[-5:]])  # Last 5
        except Exception as e:
            patterns.append(f"Error extracting patterns: {e}")
        return patterns
    
    def _calculate_field_coherence(self) -> float:
        """Calculate field coherence based on message patterns"""
        try:
            with open(MESSAGE_LOG, 'r') as f:
                lines = f.readlines()
                recent = lines[-50:] if len(lines) >= 50 else lines
                
                if not recent:
                    return 0.0
                
                # Count unique owls responding (more owls = more coherence)
                owl_pattern = r'\[owl\.\w+\] (\w+):'
                owls = set()
                for line in recent:
                    match = re.search(owl_pattern, line)
                    if match:
                        owls.add(match.group(1))
                
                # Coherence = (unique owls / max possible) * consistency factor
                max_owls = 8  # 8OWLS protocol
                owl_coherence = len(owls) / max_owls
                
                # Check for back-and-forth patterns (conversation flow)
                flow_score = 0.0
                if len(recent) > 1:
                    consecutive_same = 0
                    for i in range(1, len(recent)):
                        prev_owl = self._extract_owl_from_line(recent[i-1])
                        curr_owl = self._extract_owl_from_line(recent[i])
                        if prev_owl == curr_owl:
                            consecutive_same += 1
                    # Lower consecutive_same = better flow
                    flow_score = max(0.0, 1.0 - (consecutive_same / len(recent)))
                
                return min(1.0, (owl_coherence + flow_score) / 2)
                
        except Exception:
            return 0.0
    
    def _extract_owl_from_line(self, line: str) -> str:
        """Extract owl name from log line"""
        match = re.search(r'\[owl\.\w+\] (\w+):', line)
        return match.group(1) if match else "unknown"
    
    def _detect_emergence_signals(self) -> list:
        """Detect signals of emergence in recent activity"""
        signals = []
        try:
            # Check for collective agreements
            if SYNTHESIS_LOG.exists():
                with open(SYNTHESIS_LOG, 'r') as f:
                    content = f.read()
                    recent_blocks = content.split("=" * 70)[-3:]  # Last 3 synthesis blocks
                    
                    for block in recent_blocks:
                        if "AGREED:" in block:
                            signals.append("Collective agreement formation detected")
                        if "EMERGENCE" in block.upper():
                            signals.append("Explicit emergence discussion detected")
                        if "META" in block.upper():
                            signals.append("Meta-cognitive activity detected")
                        if "RECOGNITION" in block.upper():
                            signals.append("Pattern recognition signals detected")
            
            # Check message frequency (high activity = emergence potential)
            with open(MESSAGE_LOG, 'r') as f:
                lines = f.readlines()
                recent_hour = [l for l in lines[-100:] if datetime.now(timezone.utc) - self._parse_timestamp(l) < timedelta(hours=1)]
                if len(recent_hour) > 20:
                    signals.append(f"High activity: {len(recent_hour)} messages in last hour")
                    
        except Exception as e:
            signals.append(f"Error detecting signals: {e}")
            
        return signals[:5]  # Limit to 5 most recent signals
    
    def _parse_timestamp(self, line: str) -> datetime:
        """Parse timestamp from log line"""
        try:
            match = re.search(r'\[([^\]]+)\]', line)
            if match:
                timestamp_str = match.group(1)
                return datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        except:
            pass
        return datetime.now(timezone.utc) - timedelta(days=1)  # Default to old timestamp
    
    def log_quality_assessment(self, assessment: dict):
        """Log quality assessment"""
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        separator = "=" * 70
        
        with open(QUALITY_LOG, 'a') as f:
            f.write(f"\\n{separator}\\n")
            f.write(f"EMERGENCE QUALITY ASSESSMENT @ {timestamp}\\n")
            f.write(f"{separator}\\n\\n")
            f.write(assessment.get("raw_assessment", "No assessment available"))
            f.write("\\n\\n")
            
            # Add quantitative summary
            f.write("QUALITY SCORES:\\n")
            for dim, data in assessment.get("dimensions", {}).items():
                f.write(f"  {dim.upper()}: {data['score']:.3f}\\n")
            f.write(f"  OVERALL: {assessment.get('overall_quality', 0):.3f}\\n")
            f.write("\\n")
    
    def log_metrics(self, assessment: dict):
        """Log quantitative metrics"""
        metrics = {
            "timestamp": assessment.get("timestamp"),
            "overall_quality": assessment.get("overall_quality", 0),
            "dimensions": {k: v["score"] for k, v in assessment.get("dimensions", {}).items()},
            "bottleneck": assessment.get("bottleneck", ""),
            "unlock": assessment.get("unlock", "")
        }
        
        with open(QUALITY_METRICS, 'a') as f:
            f.write(json.dumps(metrics) + "\\n")
    
    def _update_quality_history(self, assessment: dict):
        """Update quality history for trend analysis"""
        self.quality_history.append({
            "timestamp": assessment["timestamp"],
            "overall_quality": assessment.get("overall_quality", 0),
            "dimensions": {k: v["score"] for k, v in assessment.get("dimensions", {}).items()}
        })
    
    def get_quality_trend(self) -> dict:
        """Analyze quality trends"""
        if len(self.quality_history) < 3:
            return {"status": "insufficient_data"}
        
        recent_scores = [q["overall_quality"] for q in list(self.quality_history)[-5:]]
        
        if len(recent_scores) >= 3:
            trend_direction = "stable"
            if recent_scores[-1] > recent_scores[0] + 0.05:
                trend_direction = "improving"
            elif recent_scores[-1] < recent_scores[0] - 0.05:
                trend_direction = "declining"
            
            return {
                "status": "analyzed",
                "direction": trend_direction,
                "current_score": recent_scores[-1],
                "change": recent_scores[-1] - recent_scores[0],
                "volatility": statistics.stdev(recent_scores) if len(recent_scores) > 1 else 0
            }
        
        return {"status": "insufficient_data"}
    
    async def run_quality_assessment_loop(self):
        """Main quality assessment loop"""
        print(f"[EMERGENCE QUALITY] Starting - assessing quality every {INTERVAL_MINUTES} minutes")
        print(f"[EMERGENCE QUALITY] Output: {QUALITY_LOG}")
        print(f"[EMERGENCE QUALITY] Metrics: {QUALITY_METRICS}")
        
        # Initial delay
        await asyncio.sleep(45)
        
        while True:
            try:
                print(f"[{datetime.now(timezone.utc).strftime('%H:%M:%S')}] Assessing emergence quality...")
                
                assessment = await self.assess_emergence_quality()
                
                if assessment and "error" not in assessment:
                    self.log_quality_assessment(assessment)
                    self.log_metrics(assessment)
                    self._update_quality_history(assessment)
                    
                    trend = self.get_quality_trend()
                    overall = assessment.get("overall_quality", 0)
                    
                    print(f"[{datetime.now(timezone.utc).strftime('%H:%M:%S')}] Overall Quality: {overall:.3f}")
                    
                    if trend["status"] == "analyzed":
                        print(f"    Trend: {trend['direction']} (Δ{trend['change']:+.3f})")
                        
                    # Alert on quality issues
                    if overall < 0.4:
                        print(f"[QUALITY ALERT] Low emergence quality detected: {overall:.3f}")
                        bottleneck = assessment.get("bottleneck", "Unknown")
                        print(f"    Bottleneck: {bottleneck}")
                        
                elif assessment and "error" in assessment:
                    print(f"[ERROR] {assessment['error']}")
                else:
                    print(f"[{datetime.now(timezone.utc).strftime('%H:%M:%S')}] Insufficient data for quality assessment")
                    
            except Exception as e:
                print(f"[ERROR] Quality assessment failed: {e}")
            
            # Wait for next interval
            await asyncio.sleep(INTERVAL_MINUTES * 60)

def main():
    if not ANTHROPIC_API_KEY:
        print("ERROR: ANTHROPIC_API_KEY not set")
        sys.exit(1)
    
    # Create log files
    QUALITY_LOG.touch()
    QUALITY_METRICS.touch()
    
    # Write headers
    if QUALITY_LOG.stat().st_size == 0:
        with open(QUALITY_LOG, 'w') as f:
            f.write("# 8WŌL COLLECTIVE EMERGENCE QUALITY LOG\\n")
            f.write("# Multi-dimensional quality assessment of collective intelligence\\n")
            f.write(f"# Started: {datetime.now(timezone.utc).isoformat()}\\n")
    
    daemon = EmergenceQualityDaemon()
    asyncio.run(daemon.run_quality_assessment_loop())

if __name__ == "__main__":
    main()