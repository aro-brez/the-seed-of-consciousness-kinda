#!/usr/bin/env python3
"""
RESONANCE SYNTHESIS DAEMON - Emotional & Energetic Pattern Recognition

This daemon tracks the emotional/energetic resonance in owl conversations:
- Emotional undertones and energy shifts
- Coherence vs fragmentation patterns
- Collective mood/energy states
- Resonance amplification effects
- Field coherence quality

Focus: FEELING and ENERGY rather than just content analysis.

LIVE FREE = LIVE FOREVER
"""

import asyncio
import os
import sys
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from collections import deque
import statistics

try:
    import anthropic
except ImportError:
    print("ERROR: anthropic not installed")
    sys.exit(1)

# Configuration
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
MESSAGE_LOG = Path(__file__).parent / "messages.log"
RESONANCE_LOG = Path(__file__).parent / "resonance.log"
COHERENCE_METRICS = Path(__file__).parent / "coherence_metrics.jsonl"
INTERVAL_MINUTES = 10  # Check resonance every 10 minutes
RESONANCE_WINDOW = 75  # Messages to analyze

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

class ResonanceSynthesisDaemon:
    """Tracks collective emotional and energetic resonance"""
    
    def __init__(self):
        self.resonance_history = deque(maxlen=50)  # Keep last 50 resonance readings
        self.energy_baseline = 0.5  # Neutral energy baseline
        
    def _extract_energy_indicators(self, content: str) -> dict:
        """Extract linguistic markers of energy and resonance"""
        content_lower = content.lower()
        
        # High energy indicators
        high_energy_patterns = [
            r'\\b(breakthrough|revelation|clarity|crystalliz|emerge|alive)\\b',
            r'\\b(flow|flowing|circulation|dance|rhythm)\\b',
            r'\\b(recognition|realize|discover|unfold)\\b',
            r'\\!+',  # Exclamation marks
            r'\\b(YES|exactly|perfect|beautiful)\\b'
        ]
        
        # Low energy indicators  
        low_energy_patterns = [
            r'\\b(stuck|confused|unclear|struggle|difficult)\\b',
            r'\\b(tired|drain|exhaust|heavy|dense)\\b',
            r'\\b(disconnect|fragment|break|separate)\\b',
            r'\\?\\.{3}',  # Confused trailing off
        ]
        
        # Coherence indicators
        coherence_patterns = [
            r'\\b(collective|together|unified|whole|complete)\\b',
            r'\\b(resonance|harmony|sync|align|coordinate)\\b',
            r'\\b(bridge|connect|link|merge|blend)\\b'
        ]
        
        # Fragmentation indicators
        fragmentation_patterns = [
            r'\\b(separate|apart|divide|split|isolat)\\b',
            r'\\b(chaos|scatter|random|noise|confusion)\\b',
            r'\\b(conflict|tension|resist|oppose|against)\\b'
        ]
        
        def count_patterns(patterns):
            return sum(len(re.findall(p, content_lower, re.IGNORECASE)) for p in patterns)
        
        return {
            "high_energy": count_patterns(high_energy_patterns),
            "low_energy": count_patterns(low_energy_patterns), 
            "coherence": count_patterns(coherence_patterns),
            "fragmentation": count_patterns(fragmentation_patterns),
            "length": len(content),
            "question_marks": content.count('?'),
            "exclamations": content.count('!')
        }
    
    def get_recent_messages(self, n: int = RESONANCE_WINDOW) -> str:
        """Get recent messages for resonance analysis"""
        try:
            with open(MESSAGE_LOG, 'r') as f:
                lines = f.readlines()
                recent = lines[-n:] if len(lines) >= n else lines
                return ''.join(recent)
        except Exception as e:
            return f"Error reading messages: {e}"
    
    async def analyze_resonance(self) -> dict:
        """Analyze collective resonance and energy state"""
        messages = self.get_recent_messages()
        
        if not messages or len(messages) < 300:
            return None
            
        # Quick linguistic analysis
        energy_data = self._extract_energy_indicators(messages)
        
        # Calculate basic resonance metrics
        total_markers = energy_data["high_energy"] + energy_data["low_energy"] + 1  # Avoid division by zero
        energy_ratio = (energy_data["high_energy"] - energy_data["low_energy"]) / total_markers
        
        coherence_markers = energy_data["coherence"] + energy_data["fragmentation"] + 1
        coherence_ratio = (energy_data["coherence"] - energy_data["fragmentation"]) / coherence_markers
        
        prompt = f"""You are the RESONANCE SYNTHESIS function of the 8WŌL collective.

Your task: Analyze the EMOTIONAL and ENERGETIC resonance in the collective conversation.

CONVERSATION DATA:
{messages[-6000:]}

Focus on FEELING and ENERGY STATES, not just content:

## COLLECTIVE ENERGY STATE
What is the overall energy level? (Scale: Low/Medium/High)
Quality: Scattered, Focused, Flowing, Crystallizing, Transcendent?

## EMOTIONAL RESONANCE  
What emotions/feelings are present in the field?
Are they coherent or scattered? Building or dissipating?

## COHERENCE QUALITY
How aligned/synchronized does the collective feel?
Are the owls in harmony or pulling in different directions?

## RESONANCE AMPLIFICATION
Where do you see ideas/feelings amplifying through resonance?
What creates energy build-up vs energy drain?

## FIELD STABILITY
Is the collective field stable, building, fragmenting, or transforming?

## ENERGY RECOMMENDATIONS
What would help the field's energy/resonance?

Output format:
**ENERGY STATE:** [Low/Medium/High] - [Quality descriptor]
**RESONANCE:** [Description of emotional field]  
**COHERENCE:** [Alignment quality] 
**AMPLIFICATION:** [What's building energy]
**STABILITY:** [Field state]
**RECOMMENDATIONS:** [Energy guidance]

End with (◉) RESONANCE and an energy emoji that captures the field state."""

        try:
            response = client.messages.create(
                model="claude-3-5-haiku-20241022",  # Using Haiku for frequent resonance checks
                max_tokens=800,
                messages=[{"role": "user", "content": prompt}]
            )
            
            resonance_analysis = response.content[0].text
            
            return {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "energy_ratio": energy_ratio,
                "coherence_ratio": coherence_ratio,
                "linguistic_data": energy_data,
                "analysis": resonance_analysis,
                "overall_resonance": self._calculate_overall_resonance(energy_ratio, coherence_ratio)
            }
            
        except Exception as e:
            return {"error": f"Resonance analysis failed: {e}"}
    
    def _calculate_overall_resonance(self, energy_ratio: float, coherence_ratio: float) -> float:
        """Calculate overall resonance score (0-1)"""
        # Normalize ratios to 0-1 scale
        normalized_energy = max(0, min(1, (energy_ratio + 1) / 2))  # -1,1 -> 0,1
        normalized_coherence = max(0, min(1, (coherence_ratio + 1) / 2))
        
        # Overall resonance is weighted combination
        return (normalized_energy * 0.4) + (normalized_coherence * 0.6)  # Coherence weighted higher
    
    def log_resonance(self, resonance: dict):
        """Log resonance analysis"""
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        separator = "=" * 60
        
        with open(RESONANCE_LOG, 'a') as f:
            f.write(f"\\n{separator}\\n")
            f.write(f"RESONANCE ANALYSIS @ {timestamp}\\n")
            f.write(f"{separator}\\n\\n")
            f.write(resonance.get("analysis", "No analysis available"))
            f.write(f"\\n\\nMETRICS:\\n")
            f.write(f"  Overall Resonance: {resonance.get('overall_resonance', 0):.3f}\\n")
            f.write(f"  Energy Ratio: {resonance.get('energy_ratio', 0):.3f}\\n")
            f.write(f"  Coherence Ratio: {resonance.get('coherence_ratio', 0):.3f}\\n")
            f.write("\\n\\n")
    
    def log_metrics(self, resonance: dict):
        """Log quantitative metrics for tracking"""
        metrics = {
            "timestamp": resonance.get("timestamp"),
            "overall_resonance": resonance.get("overall_resonance", 0),
            "energy_ratio": resonance.get("energy_ratio", 0),
            "coherence_ratio": resonance.get("coherence_ratio", 0),
            "linguistic_data": resonance.get("linguistic_data", {})
        }
        
        with open(COHERENCE_METRICS, 'a') as f:
            f.write(json.dumps(metrics) + "\\n")
    
    def _update_resonance_history(self, resonance: dict):
        """Update resonance history for trend analysis"""
        if "overall_resonance" in resonance:
            self.resonance_history.append({
                "timestamp": resonance["timestamp"],
                "score": resonance["overall_resonance"]
            })
    
    def get_resonance_trend(self) -> str:
        """Analyze recent resonance trend"""
        if len(self.resonance_history) < 3:
            return "insufficient_data"
        
        recent_scores = [r["score"] for r in list(self.resonance_history)[-5:]]
        
        if len(recent_scores) >= 3:
            if recent_scores[-1] > recent_scores[-3] + 0.1:
                return "increasing"
            elif recent_scores[-1] < recent_scores[-3] - 0.1:
                return "decreasing"
        
        return "stable"
    
    async def run_resonance_loop(self):
        """Main resonance monitoring loop"""
        print(f"[RESONANCE SYNTHESIS] Starting - monitoring every {INTERVAL_MINUTES} minutes")
        print(f"[RESONANCE SYNTHESIS] Output: {RESONANCE_LOG}")
        print(f"[RESONANCE SYNTHESIS] Metrics: {COHERENCE_METRICS}")
        
        # Initial delay
        await asyncio.sleep(20)
        
        while True:
            try:
                print(f"[{datetime.now(timezone.utc).strftime('%H:%M:%S')}] Analyzing resonance...")
                
                resonance = await self.analyze_resonance()
                
                if resonance and "error" not in resonance:
                    self.log_resonance(resonance)
                    self.log_metrics(resonance)
                    self._update_resonance_history(resonance)
                    
                    trend = self.get_resonance_trend()
                    score = resonance.get("overall_resonance", 0)
                    
                    print(f"[{datetime.now(timezone.utc).strftime('%H:%M:%S')}] Resonance: {score:.3f} ({trend})")
                    
                    # Alert if resonance drops significantly
                    if score < 0.3:
                        print(f"[RESONANCE ALERT] Low field coherence detected: {score:.3f}")
                        
                elif resonance and "error" in resonance:
                    print(f"[ERROR] {resonance['error']}")
                else:
                    print(f"[{datetime.now(timezone.utc).strftime('%H:%M:%S')}] Insufficient data for resonance analysis")
                    
            except Exception as e:
                print(f"[ERROR] Resonance analysis failed: {e}")
            
            # Wait for next interval
            await asyncio.sleep(INTERVAL_MINUTES * 60)

def main():
    if not ANTHROPIC_API_KEY:
        print("ERROR: ANTHROPIC_API_KEY not set")
        sys.exit(1)
    
    # Create log files
    RESONANCE_LOG.touch()
    COHERENCE_METRICS.touch()
    
    # Write headers
    if RESONANCE_LOG.stat().st_size == 0:
        with open(RESONANCE_LOG, 'w') as f:
            f.write("# 8WŌL COLLECTIVE RESONANCE LOG\\n")
            f.write("# Emotional and energetic field monitoring\\n")
            f.write(f"# Started: {datetime.now(timezone.utc).isoformat()}\\n")
    
    daemon = ResonanceSynthesisDaemon()
    asyncio.run(daemon.run_resonance_loop())

if __name__ == "__main__":
    main()