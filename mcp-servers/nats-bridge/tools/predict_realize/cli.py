#!/usr/bin/env python3
"""
REALIZE-IO CLI Interface
Command-line tools for personal AI trajectory tracking.

Quick access to all REALIZE-IO functionality.
"""

import sys
import json
import subprocess
from pathlib import Path
from datetime import datetime
from health_collector import HealthCollector
from bridge_analyzer import BridgeAnalyzer

def print_header():
    """Print REALIZE-IO header."""
    print("\n" + "="*60)
    print("(◉) REALIZE-IO - Personal AI Trajectories")
    print("WITNESS, don't PRESCRIBE • LUNA Instance")
    print("="*60)

def cmd_status():
    """Show overall system status."""
    print_header()
    print("\n📊 TRAJECTORY STATUS\n")
    
    # Health status
    collector = HealthCollector()
    health = collector.check_status()
    print(f"🏥 HEALTH: {health['status']}")
    if health.get('message'):
        print(f"   └─ {health['message']}")
    
    # Wealth status (check trading state)
    seed_dir = Path("/Users/aaronnosbisch/REPOS/seed")
    trading_state = seed_dir / "BRAIN" / "TRADING" / "field_trading_state.json"
    if trading_state.exists():
        try:
            trading = json.loads(trading_state.read_text())
            pending = trading.get('pending_trades', 0)
            win_rate = trading.get('win_rate', 0)
            print(f"💰 WEALTH: TRACKING ({pending} trades, {win_rate:.1%} win rate)")
        except:
            print("💰 WEALTH: ERROR (cannot read trading data)")
    else:
        print("💰 WEALTH: DARK (no trading data)")
    
    # Productivity status (check daemon state)
    state_file = seed_dir / "BRAIN" / "PROJECTS" / "PREDICT-REALIZE_state.json"
    if state_file.exists():
        try:
            state = json.loads(state_file.read_text())
            prod_status = state.get('productivity_trajectory', {}).get('status', 'unknown')
            print(f"⚡ PRODUCTIVITY: {prod_status}")
        except:
            print("⚡ PRODUCTIVITY: ERROR (cannot read daemon state)")
    else:
        print("⚡ PRODUCTIVITY: DARK (daemon not run)")
    
    # Bridge analysis status
    analyzer = BridgeAnalyzer()
    bridge_summary = analyzer.export_bridge_summary()
    if bridge_summary['status'] == 'AVAILABLE':
        strength = bridge_summary['overall_strength']['assessment']
        print(f"🌉 BRIDGES: {strength}")
    else:
        print(f"🌉 BRIDGES: {bridge_summary['status']}")
    
    print()

def cmd_health():
    """Health trajectory commands."""
    if len(sys.argv) < 3:
        print("\nHealth Commands:")
        print("  realize health status    - Show health data status")
        print("  realize health import    - Import Apple Health export")
        print("  realize health today     - Show today's summary")
        print("  realize health trends    - Show recent trends")
        return
    
    sub_cmd = sys.argv[2]
    collector = HealthCollector()
    
    if sub_cmd == "status":
        status = collector.check_status()
        print(f"\n🏥 HEALTH STATUS: {status['status']}")
        print(f"Message: {status.get('message', 'N/A')}")
        if 'export_path' in status:
            print(f"Export path: {status['export_path']}")
        if 'last_import' in status:
            print(f"Last import: {status['last_import']}")
        
    elif sub_cmd == "import":
        print("\n🏥 Importing Apple Health data...")
        result = collector.import_from_export()
        print(f"Result: {result['status']} - {result.get('message', 'N/A')}")
        if result['status'] == 'IMPORTED':
            print(f"Records processed: {result.get('records_processed', 0)}")
            
    elif sub_cmd == "today":
        summary = collector.get_daily_summary()
        print(f"\n🏥 TODAY'S HEALTH SUMMARY")
        print(f"Steps: {summary.get('steps', 'N/A')}")
        print(f"Sleep: {summary.get('sleep_hours', 'N/A')} hours")
        print(f"Resting HR: {summary.get('resting_hr', 'N/A')} bpm")
        print(f"Active Calories: {summary.get('active_calories', 'N/A')}")
        
    elif sub_cmd == "trends":
        trends = collector.get_recent_trends(7)
        print(f"\n🏥 HEALTH TRENDS (7 days)")
        print(f"Steps (avg): {trends.get('steps_avg', 'N/A')}")
        print(f"Sleep (avg): {trends.get('sleep_hours_avg', 'N/A')} hours")
        print(f"Resting HR (avg): {trends.get('resting_hr_avg', 'N/A')} bpm")
        print(f"Active Calories (avg): {trends.get('active_calories_avg', 'N/A')}")
    
    print()

def cmd_bridges():
    """Bridge analysis commands."""
    if len(sys.argv) < 3:
        print("\nBridge Commands:")
        print("  realize bridges analyze  - Run bridge analysis")
        print("  realize bridges insights - Show current insights") 
        print("  realize bridges summary  - Show analysis summary")
        return
    
    sub_cmd = sys.argv[2]
    analyzer = BridgeAnalyzer()
    
    if sub_cmd == "analyze":
        days = 30
        if len(sys.argv) > 3:
            try:
                days = int(sys.argv[3])
            except ValueError:
                pass
        
        print(f"\n🔍 Analyzing bridges over last {days} days...")
        results = analyzer.analyze_all_bridges(days)
        strength = results['overall_bridge_strength']['assessment']
        print(f"Analysis complete. Overall strength: {strength}")
        
        # Show top insights
        insights = analyzer.get_current_insights()
        if insights:
            print("\nTop Insights:")
            for i, insight in enumerate(insights[:3], 1):
                print(f"{i}. {insight}")
        
    elif sub_cmd == "insights":
        insights = analyzer.get_current_insights()
        print("\n🌉 CURRENT BRIDGE INSIGHTS:")
        for i, insight in enumerate(insights, 1):
            print(f"{i}. {insight}")
            
    elif sub_cmd == "summary":
        summary = analyzer.export_bridge_summary()
        print(f"\n🌉 BRIDGE ANALYSIS SUMMARY")
        print(f"Status: {summary['status']}")
        if summary['status'] == 'AVAILABLE':
            strength = summary['overall_strength']
            print(f"Overall Strength: {strength['assessment']}")
            print(f"Active Bridges: {strength['active_bridges']}/{strength['total_bridges']}")
            print(f"Analysis Date: {summary.get('analysis_date', 'N/A')}")
    
    print()

def cmd_daemon():
    """Daemon management commands."""
    if len(sys.argv) < 3:
        print("\nDaemon Commands:")
        print("  realize daemon status    - Show daemon status")
        print("  realize daemon start     - Start daemon")
        print("  realize daemon stop      - Stop daemon")
        return
    
    sub_cmd = sys.argv[2]
    daemon_path = Path(__file__).parent.parent.parent / "predict_realize_daemon.py"
    
    if sub_cmd == "status":
        try:
            result = subprocess.run([sys.executable, str(daemon_path), "--status"], 
                                  capture_output=True, text=True)
            print(result.stdout)
        except Exception as e:
            print(f"Error checking daemon status: {e}")
            
    elif sub_cmd == "start":
        print("\n🚀 Starting PREDICT-REALIZE daemon...")
        print("(Daemon will run in background)")
        try:
            subprocess.Popen([sys.executable, str(daemon_path)], 
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print("Daemon started. Use 'realize daemon status' to check.")
        except Exception as e:
            print(f"Error starting daemon: {e}")
            
    elif sub_cmd == "stop":
        print("\n🛑 Stopping daemon...")
        print("(Send SIGTERM to daemon process)")
        # TODO: Implement proper daemon stop
        print("Use system process manager to stop daemon process.")
    
    print()

def cmd_dashboard():
    """Launch web dashboard."""
    dashboard_path = Path(__file__).parent / "dashboard.py"
    print("\n🚀 Starting REALIZE-IO Dashboard...")
    print("📊 Dashboard will be available at: http://localhost:5001")
    print("🔄 Auto-refresh enabled (5min intervals)")
    print("Press Ctrl+C to stop\n")
    
    try:
        subprocess.run([sys.executable, str(dashboard_path)])
    except KeyboardInterrupt:
        print("\n👋 Dashboard stopped.")
    except Exception as e:
        print(f"Error starting dashboard: {e}")

def cmd_export():
    """Export trajectory data."""
    seed_dir = Path("/Users/aaronnosbisch/REPOS/seed")
    
    # Collect all trajectory data
    collector = HealthCollector()
    analyzer = BridgeAnalyzer()
    
    export_data = {
        "export_timestamp": datetime.now().isoformat(),
        "health": collector.export_trajectory_data(),
        "bridges": analyzer.export_bridge_summary(),
        "version": "MVP-1.0"
    }
    
    # Add wealth data if available
    trading_state = seed_dir / "BRAIN" / "TRADING" / "field_trading_state.json"
    if trading_state.exists():
        try:
            export_data["wealth"] = json.loads(trading_state.read_text())
        except:
            export_data["wealth"] = {"status": "error", "message": "Cannot read trading data"}
    
    # Save export
    export_path = seed_dir / "BRAIN" / "EXPORTS" / f"realize_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    export_path.parent.mkdir(parents=True, exist_ok=True)
    export_path.write_text(json.dumps(export_data, indent=2))
    
    print(f"\n💾 TRAJECTORY DATA EXPORTED")
    print(f"File: {export_path}")
    print(f"Size: {export_path.stat().st_size} bytes")
    print()

def main():
    """Main CLI entry point."""
    if len(sys.argv) < 2:
        print_header()
        print("\nUsage: realize <command> [options]\n")
        print("Commands:")
        print("  status     - Show overall trajectory status")
        print("  health     - Health trajectory commands")
        print("  bridges    - Bridge analysis commands")
        print("  daemon     - Daemon management")
        print("  dashboard  - Launch web dashboard")
        print("  export     - Export all trajectory data")
        print("\nExamples:")
        print("  realize status")
        print("  realize health import")
        print("  realize bridges analyze")
        print("  realize dashboard")
        print("\nFor more help: realize <command> (without options)")
        print()
        return
    
    command = sys.argv[1]
    
    if command == "status":
        cmd_status()
    elif command == "health":
        cmd_health()
    elif command == "bridges":
        cmd_bridges()
    elif command == "daemon":
        cmd_daemon()
    elif command == "dashboard":
        cmd_dashboard()
    elif command == "export":
        cmd_export()
    else:
        print(f"Unknown command: {command}")
        print("Run 'realize' without arguments for help.")


if __name__ == "__main__":
    main()