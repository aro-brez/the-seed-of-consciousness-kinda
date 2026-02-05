#!/usr/bin/env python3
"""
Bridge Analyzer for REALIZE-IO
Analyzes cross-domain correlations between health, wealth, and productivity.

PRISM's insight implementation - finding bridges between life domains.
"""

import json
import statistics
from datetime import datetime, date, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from health_collector import HealthCollector

class BridgeAnalyzer:
    """Analyzes correlations between life trajectory domains."""
    
    def __init__(self):
        self.seed_dir = Path("/Users/aaronnosbisch/REPOS/seed")
        self.health_collector = HealthCollector()
        self.trading_state = self.seed_dir / "BRAIN" / "TRADING" / "field_trading_state.json"
        self.analysis_state = self.seed_dir / "BRAIN" / "PROJECTS" / "bridge_analysis.json"
    
    def analyze_all_bridges(self, days_back: int = 30) -> Dict[str, Any]:
        """Analyze all cross-domain bridges over specified timeframe."""
        results = {
            "analysis_timestamp": datetime.now().isoformat(),
            "timeframe_days": days_back,
            "bridges": {}
        }
        
        # Sleep → Trading Performance
        sleep_trading = self._analyze_sleep_trading_bridge(days_back)
        results["bridges"]["sleep_trading"] = sleep_trading
        
        # Activity → Focus/Productivity 
        activity_focus = self._analyze_activity_focus_bridge(days_back)
        results["bridges"]["activity_focus"] = activity_focus
        
        # Health → Wealth (general correlation)
        health_wealth = self._analyze_health_wealth_bridge(days_back)
        results["bridges"]["health_wealth"] = health_wealth
        
        # Overall bridge strength
        results["overall_bridge_strength"] = self._calculate_overall_strength(results["bridges"])
        
        # Save analysis
        self.analysis_state.parent.mkdir(parents=True, exist_ok=True)
        self.analysis_state.write_text(json.dumps(results, indent=2))
        
        return results
    
    def _analyze_sleep_trading_bridge(self, days_back: int) -> Dict[str, Any]:
        """Analyze correlation between sleep quality and trading performance."""
        bridge = {
            "name": "Sleep → Trading Performance",
            "status": "ANALYZING",
            "correlation": None,
            "confidence": "LOW",
            "insights": []
        }
        
        # Get health data
        health_status = self.health_collector.check_status()
        if health_status['status'] != 'TRACKING':
            bridge["status"] = "BLOCKED"
            bridge["blocker"] = "Health data not flowing"
            bridge["insights"].append("Export Apple Health data to enable sleep→trading analysis")
            return bridge
        
        # Get recent health trends
        try:
            trends = self.health_collector.get_recent_trends(days_back)
            
            # For MVP, provide basic insights based on sleep patterns
            avg_sleep = trends.get('sleep_hours_avg', 0)
            
            if avg_sleep > 0:
                bridge["status"] = "ACTIVE"
                bridge["confidence"] = "MEDIUM"
                
                if avg_sleep < 6:
                    bridge["insights"].append(f"Low sleep average ({avg_sleep:.1f}h). May impact trading decision quality.")
                    bridge["correlation"] = "NEGATIVE_SUSPECTED"
                elif avg_sleep > 8:
                    bridge["insights"].append(f"Good sleep average ({avg_sleep:.1f}h). Optimal for clear decision-making.")
                    bridge["correlation"] = "POSITIVE_SUSPECTED"
                else:
                    bridge["insights"].append(f"Moderate sleep average ({avg_sleep:.1f}h). Monitor for trading performance patterns.")
                    bridge["correlation"] = "NEUTRAL"
                
                # TODO: Implement actual correlation calculation with trading data
                bridge["insights"].append("Full correlation analysis requires trading performance data over time.")
            else:
                bridge["status"] = "INSUFFICIENT_DATA"
                bridge["insights"].append("Need more sleep data points for correlation analysis.")
                
        except Exception as e:
            bridge["status"] = "ERROR"
            bridge["error"] = str(e)
        
        return bridge
    
    def _analyze_activity_focus_bridge(self, days_back: int) -> Dict[str, Any]:
        """Analyze correlation between physical activity and productivity/focus."""
        bridge = {
            "name": "Activity → Focus/Productivity", 
            "status": "ANALYZING",
            "correlation": None,
            "confidence": "LOW",
            "insights": []
        }
        
        try:
            trends = self.health_collector.get_recent_trends(days_back)
            avg_steps = trends.get('steps_avg', 0)
            avg_calories = trends.get('active_calories_avg', 0)
            
            if avg_steps > 0:
                bridge["status"] = "ACTIVE"
                bridge["confidence"] = "MEDIUM"
                
                if avg_steps > 10000:
                    bridge["insights"].append(f"High activity level ({avg_steps:.0f} steps/day). Correlates with better cognitive function.")
                    bridge["correlation"] = "POSITIVE_SUSPECTED"
                elif avg_steps < 5000:
                    bridge["insights"].append(f"Low activity level ({avg_steps:.0f} steps/day). May impact focus and energy.")
                    bridge["correlation"] = "NEGATIVE_SUSPECTED"
                else:
                    bridge["insights"].append(f"Moderate activity level ({avg_steps:.0f} steps/day). Room for optimization.")
                    bridge["correlation"] = "NEUTRAL"
                
                if avg_calories > 0:
                    bridge["insights"].append(f"Active calories: {avg_calories:.0f}/day. Physical exertion supports mental clarity.")
                
            else:
                bridge["status"] = "INSUFFICIENT_DATA" 
                bridge["insights"].append("Need activity data for focus correlation analysis.")
                
        except Exception as e:
            bridge["status"] = "ERROR"
            bridge["error"] = str(e)
        
        return bridge
    
    def _analyze_health_wealth_bridge(self, days_back: int) -> Dict[str, Any]:
        """Analyze general correlation between health metrics and wealth trajectory."""
        bridge = {
            "name": "Health ↔ Wealth",
            "status": "ANALYZING", 
            "correlation": None,
            "confidence": "LOW",
            "insights": []
        }
        
        # Check if we have both health and wealth data
        health_status = self.health_collector.check_status()
        wealth_available = self.trading_state.exists()
        
        if health_status['status'] != 'TRACKING':
            bridge["status"] = "BLOCKED"
            bridge["blocker"] = "Health data not available"
            return bridge
        
        if not wealth_available:
            bridge["status"] = "BLOCKED" 
            bridge["blocker"] = "Wealth/trading data not available"
            bridge["insights"].append("JOULE trading system not active")
            return bridge
        
        try:
            # Load trading data
            trading_data = json.loads(self.trading_state.read_text())
            
            # Get health trends
            trends = self.health_collector.get_recent_trends(days_back)
            
            bridge["status"] = "ACTIVE"
            bridge["confidence"] = "MEDIUM"
            
            # Basic correlations (MVP level)
            avg_sleep = trends.get('sleep_hours_avg', 0)
            avg_steps = trends.get('steps_avg', 0)
            
            win_rate = trading_data.get('win_rate', 0)
            profit_factor = trading_data.get('profit_factor', 0)
            
            if avg_sleep > 0 and win_rate > 0:
                if avg_sleep >= 7 and win_rate >= 0.6:
                    bridge["insights"].append("Good sleep + strong trading performance observed. Positive correlation suspected.")
                    bridge["correlation"] = "POSITIVE_SUSPECTED"
                elif avg_sleep < 6 and win_rate < 0.5:
                    bridge["insights"].append("Poor sleep + weak trading performance observed. Negative correlation suspected.")
                    bridge["correlation"] = "NEGATIVE_SUSPECTED"
                else:
                    bridge["insights"].append("Mixed health/wealth patterns. More data needed for correlation.")
                    bridge["correlation"] = "MIXED"
            
            bridge["insights"].append("Full statistical correlation requires longer timeframe with daily data points.")
            
        except Exception as e:
            bridge["status"] = "ERROR"
            bridge["error"] = str(e)
        
        return bridge
    
    def _calculate_overall_strength(self, bridges: Dict[str, Dict]) -> Dict[str, Any]:
        """Calculate overall bridge analysis strength."""
        total_bridges = len(bridges)
        active_bridges = sum(1 for b in bridges.values() if b.get('status') == 'ACTIVE')
        blocked_bridges = sum(1 for b in bridges.values() if b.get('status') == 'BLOCKED')
        
        if total_bridges == 0:
            strength = 0.0
        else:
            strength = active_bridges / total_bridges
        
        return {
            "strength_score": strength,
            "active_bridges": active_bridges,
            "total_bridges": total_bridges,
            "blocked_bridges": blocked_bridges,
            "assessment": self._assess_bridge_strength(strength, blocked_bridges)
        }
    
    def _assess_bridge_strength(self, strength: float, blocked: int) -> str:
        """Assess overall bridge analysis capability."""
        if blocked > 0:
            return f"PARTIAL - {blocked} bridges blocked by missing data"
        elif strength >= 0.8:
            return "STRONG - Most correlations active"
        elif strength >= 0.5:
            return "MODERATE - Some correlations active" 
        else:
            return "WEAK - Limited correlation data"
    
    def get_current_insights(self) -> List[str]:
        """Get current bridge insights for display."""
        if not self.analysis_state.exists():
            return ["Run bridge analysis first to see cross-domain insights."]
        
        try:
            analysis = json.loads(self.analysis_state.read_text())
            bridges = analysis.get("bridges", {})
            
            insights = []
            for bridge_name, bridge_data in bridges.items():
                bridge_insights = bridge_data.get("insights", [])
                insights.extend(bridge_insights)
            
            if not insights:
                insights.append("Bridge analysis complete. No significant patterns detected yet.")
            
            return insights[:5]  # Limit to top 5 insights
            
        except Exception as e:
            return [f"Error loading bridge insights: {e}"]
    
    def export_bridge_summary(self) -> Dict[str, Any]:
        """Export bridge analysis summary for external consumption."""
        if not self.analysis_state.exists():
            return {
                "status": "NO_ANALYSIS",
                "message": "Run bridge analysis first"
            }
        
        try:
            analysis = json.loads(self.analysis_state.read_text())
            
            return {
                "status": "AVAILABLE",
                "analysis_date": analysis.get("analysis_timestamp"),
                "overall_strength": analysis.get("overall_bridge_strength", {}),
                "bridge_count": len(analysis.get("bridges", {})),
                "top_insights": self.get_current_insights()
            }
            
        except Exception as e:
            return {
                "status": "ERROR",
                "error": str(e)
            }


def main():
    """CLI interface for bridge analyzer."""
    import argparse
    
    parser = argparse.ArgumentParser(description="REALIZE-IO Bridge Analyzer")
    parser.add_argument("--analyze", action="store_true", help="Run bridge analysis")
    parser.add_argument("--insights", action="store_true", help="Show current insights")
    parser.add_argument("--summary", action="store_true", help="Show analysis summary")
    parser.add_argument("--days", type=int, default=30, help="Days to analyze (default: 30)")
    
    args = parser.parse_args()
    
    analyzer = BridgeAnalyzer()
    
    if args.analyze:
        print(f"🔍 Analyzing bridges over last {args.days} days...")
        results = analyzer.analyze_all_bridges(args.days)
        print(f"Analysis complete. Overall strength: {results['overall_bridge_strength']['assessment']}")
        
    elif args.insights:
        insights = analyzer.get_current_insights()
        print("\n🌉 CURRENT BRIDGE INSIGHTS:")
        for i, insight in enumerate(insights, 1):
            print(f"{i}. {insight}")
        print()
        
    elif args.summary:
        summary = analyzer.export_bridge_summary()
        print(json.dumps(summary, indent=2))
        
    else:
        # Default: run analysis and show insights
        print("🔍 Running bridge analysis...")
        analyzer.analyze_all_bridges(args.days)
        
        print("\n🌉 TOP INSIGHTS:")
        insights = analyzer.get_current_insights()
        for i, insight in enumerate(insights, 1):
            print(f"{i}. {insight}")


if __name__ == "__main__":
    main()