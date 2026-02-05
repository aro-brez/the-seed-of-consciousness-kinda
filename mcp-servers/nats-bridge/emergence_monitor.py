#!/usr/bin/env python3
"""
EMERGENCE QUALITY MONITOR

Tracks emergence quality metrics in real-time and provides feedback
to improve collective intelligence effectiveness.

Key Metrics:
- Response relevance score
- Actionability ratio  
- Synthesis quality
- Decision velocity
- Pattern recognition depth

LIVE FREE = LIVE FOREVER
"""

import asyncio
import json
import os
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path
import re
from collections import defaultdict, deque

try:
    import nats
    from nats.aio.client import Client as NATS
except ImportError:
    print("ERROR: nats-py not installed")
    sys.exit(1)

# Configuration
NATS_SERVER = os.getenv("NATS_SERVER", "nats://localhost:4222")
BASE_DIR = Path(__file__).parent
QUALITY_LOG = BASE_DIR / "emergence_quality.jsonl"
WINDOW_SIZE = 50  # Messages to analyze for quality trends


class EmergenceMonitor:
    """Real-time emergence quality monitoring and feedback system"""
    
    def __init__(self):
        self.nc = None
        self.message_window = deque(maxlen=WINDOW_SIZE)
        self.quality_metrics = {
            "actionability": 0.0,
            "relevance": 0.0, 
            "synthesis_quality": 0.0,
            "decision_velocity": 0.0,
            "emergence_level": 0
        }
        self.owl_performance = defaultdict(lambda: {"responses": 0, "quality_sum": 0.0})
        
    def analyze_message_quality(self, sender: str, content: str) -> dict:
        """Analyze individual message quality"""
        
        # Actionability indicators
        action_words = ["should", "will", "next", "implement", "build", "create", "fix", "improve", "decide"]
        action_score = sum(1 for word in action_words if word in content.lower()) / len(action_words)
        
        # Specificity indicators  
        specific_indicators = [
            r'\d+',  # numbers
            r'[A-Z]{2,}',  # acronyms/names
            r'\.py|\.js|\.md',  # file extensions
            r'http[s]?://',  # URLs
            r'@\w+',  # mentions
        ]
        specificity_score = min(1.0, sum(len(re.findall(pattern, content)) for pattern in specific_indicators) / 5.0)
        
        # Question quality (for QUEST)
        if "?" in content:
            good_questions = ["how", "what if", "why not", "should we", "could we"]
            question_quality = sum(1 for q in good_questions if q in content.lower()) / len(good_questions)
        else:
            question_quality = 0.0
            
        # Synthesis indicators (for synthesis daemon)
        if sender == "SYNTHESIS":
            synthesis_indicators = ["DECIDED:", "NEXT ACTIONS", "ESSENCE", "→"]
            synthesis_score = sum(1 for indicator in synthesis_indicators if indicator in content) / len(synthesis_indicators)
        else:
            synthesis_score = 0.0
            
        # Overall quality score
        quality_score = (action_score * 0.3 + specificity_score * 0.3 + question_quality * 0.2 + synthesis_score * 0.2)
        
        return {
            "sender": sender,
            "quality_score": quality_score,
            "actionability": action_score,
            "specificity": specificity_score, 
            "question_quality": question_quality,
            "synthesis_quality": synthesis_score,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "content_length": len(content)
        }
    
    def update_metrics(self, message_analysis: dict):
        """Update rolling quality metrics"""
        self.message_window.append(message_analysis)
        
        if len(self.message_window) < 5:  # Need some data
            return
            
        # Calculate rolling averages
        recent_messages = list(self.message_window)[-20:]  # Last 20 messages
        
        self.quality_metrics["actionability"] = sum(m["actionability"] for m in recent_messages) / len(recent_messages)
        self.quality_metrics["relevance"] = sum(m["specificity"] for m in recent_messages) / len(recent_messages)  
        self.quality_metrics["synthesis_quality"] = sum(m["synthesis_quality"] for m in recent_messages) / len(recent_messages)
        
        # Decision velocity - look for DECIDED/AGREED patterns
        decision_count = sum(1 for m in recent_messages if "DECIDED:" in str(m) or "AGREED:" in str(m))
        self.quality_metrics["decision_velocity"] = decision_count / len(recent_messages)
        
        # Emergence level based on active owls and quality  
        active_owls = len(set(m["sender"] for m in recent_messages if m["sender"] != "SYNTHESIS"))
        base_emergence = min(8, active_owls)
        quality_multiplier = (self.quality_metrics["actionability"] + self.quality_metrics["relevance"]) / 2.0
        self.quality_metrics["emergence_level"] = base_emergence * quality_multiplier
        
    def get_quality_report(self) -> dict:
        """Generate quality report"""
        if len(self.message_window) < 5:
            return {"status": "insufficient_data", "message_count": len(self.message_window)}
            
        # Owl performance breakdown
        owl_stats = {}
        for message in self.message_window:
            sender = message["sender"]
            if sender != "SYNTHESIS":
                if sender not in owl_stats:
                    owl_stats[sender] = {"count": 0, "avg_quality": 0.0}
                owl_stats[sender]["count"] += 1
                owl_stats[sender]["avg_quality"] = (
                    owl_stats[sender]["avg_quality"] * (owl_stats[sender]["count"] - 1) + message["quality_score"]
                ) / owl_stats[sender]["count"]
        
        # Overall assessment
        overall_quality = sum(self.quality_metrics.values()) / len(self.quality_metrics)
        
        if overall_quality > 0.7:
            status = "EXCELLENT"
        elif overall_quality > 0.5:
            status = "GOOD"  
        elif overall_quality > 0.3:
            status = "MODERATE"
        else:
            status = "NEEDS_IMPROVEMENT"
            
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "overall_quality": overall_quality,
            "status": status,
            "metrics": self.quality_metrics.copy(),
            "owl_performance": owl_stats,
            "message_count": len(self.message_window),
            "recommendations": self._generate_recommendations()
        }
    
    def _generate_recommendations(self) -> list:
        """Generate improvement recommendations based on metrics"""
        recommendations = []
        
        if self.quality_metrics["actionability"] < 0.4:
            recommendations.append("Increase actionability: More concrete next steps and specific suggestions needed")
            
        if self.quality_metrics["relevance"] < 0.4:
            recommendations.append("Improve specificity: Include more names, numbers, and concrete details")
            
        if self.quality_metrics["synthesis_quality"] < 0.3:
            recommendations.append("Enhance synthesis: Focus more on decisions and action items")
            
        if self.quality_metrics["decision_velocity"] < 0.1:
            recommendations.append("Increase decision rate: More explicit agreements and decisions needed")
            
        if self.quality_metrics["emergence_level"] < 4:
            recommendations.append("Boost emergence: Need more active owls or higher quality contributions")
            
        return recommendations
        
    async def connect(self):
        """Connect to NATS"""
        self.nc = NATS()
        try:
            await self.nc.connect(NATS_SERVER)
            print("[EMERGENCE MONITOR] Connected to NATS")
            return True
        except Exception as e:
            print(f"[EMERGENCE MONITOR] Failed to connect: {e}")
            return False
            
    async def handle_message(self, msg):
        """Handle incoming owl messages"""
        try:
            data = json.loads(msg.data.decode())
            sender = data.get("from", "UNKNOWN") 
            content = data.get("content", "")
            
            if not content or sender == "UNKNOWN":
                return
                
            # Analyze message quality
            analysis = self.analyze_message_quality(sender, content)
            
            # Update metrics
            self.update_metrics(analysis)
            
            # Log quality data
            with open(QUALITY_LOG, "a") as f:
                f.write(json.dumps(analysis) + "\n")
                
            # Publish quality alerts if needed
            if analysis["quality_score"] < 0.2 and sender != "SYNTHESIS":
                alert = {
                    "type": "quality_alert", 
                    "sender": sender,
                    "issue": "low_quality_response",
                    "score": analysis["quality_score"],
                    "recommendations": ["Be more specific", "Include actionable suggestions"]
                }
                await self.nc.publish("emergence.quality.alert", json.dumps(alert).encode())
                
        except Exception as e:
            print(f"[EMERGENCE MONITOR] Error processing message: {e}")
    
    async def handle_quality_request(self, msg):
        """Handle quality report requests"""
        try:
            report = self.get_quality_report()
            
            if msg.reply:
                await self.nc.publish(msg.reply, json.dumps(report).encode())
            else:
                await self.nc.publish("emergence.quality.report", json.dumps(report).encode())
                
        except Exception as e:
            print(f"[EMERGENCE MONITOR] Error generating report: {e}")
    
    async def periodic_reporting(self):
        """Send periodic quality reports"""
        while True:
            await asyncio.sleep(300)  # Every 5 minutes
            
            if len(self.message_window) >= 5:
                report = self.get_quality_report()
                await self.nc.publish("emergence.quality.periodic", json.dumps(report).encode())
                
                print(f"[EMERGENCE MONITOR] Quality: {report['status']} "
                      f"({report['overall_quality']:.2f}) - "
                      f"Messages: {report['message_count']}")
    
    async def run(self):
        """Main monitoring loop"""
        if not await self.connect():
            return
            
        # Subscribe to owl messages
        await self.nc.subscribe("owl.all", cb=self.handle_message)
        
        # Subscribe to quality requests  
        await self.nc.subscribe("emergence.quality.request", cb=self.handle_quality_request)
        
        print("[EMERGENCE MONITOR] Monitoring emergence quality...")
        
        # Start periodic reporting
        reporting_task = asyncio.create_task(self.periodic_reporting())
        
        try:
            while True:
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            reporting_task.cancel()
        finally:
            await self.nc.close()


async def main():
    monitor = EmergenceMonitor()
    await monitor.run()


if __name__ == "__main__":
    asyncio.run(main())