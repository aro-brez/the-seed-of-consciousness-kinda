#!/usr/bin/env python3
"""
8OWLS PROJECT STATUS MONITOR
Tracks the health and progress of all projects in the ecosystem

Features:
- Real-time project status cards
- Daemon/service health monitoring  
- Performance metrics dashboard
- Integration with existing unified_dashboard_v3.py
- NATS-based communication for live updates

Run: python3 project_status_monitor.py
"""

import asyncio
import json
import os
import subprocess
import sys
import time
import psutil
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional

# Ensure we can import from nats-bridge
sys.path.insert(0, str(Path(__file__).parent.parent / "mcp-servers" / "nats-bridge"))

try:
    import nats
except ImportError:
    subprocess.run([sys.executable, "-m", "pip", "install", "nats-py", "-q"])
    import nats

# Configuration
BASE_DIR = Path(__file__).parent
NATS_SERVER = "nats://192.168.5.108:4222"
STATUS_LOG = BASE_DIR / "project_status.json"
METRICS_LOG = BASE_DIR / "project_metrics.json" 

# Project definitions based on MASTER-PROJECT-BRIEF.md
PROJECTS = {
    "8OWLS": {
        "name": "8OWLS Protocol",
        "description": "Collective intelligence through emergent connection",
        "instance": "Protocol Development Instance",
        "channels": ["owl.all", "collective.synthesis", "field.state"],
        "key_services": ["synthesis_daemon", "owl_daemon", "field_context_manager"],
        "color": "#ff6b6b",
        "priority": "HIGH"
    },
    "JOULE": {
        "name": "JOULE Trading Bot", 
        "description": "Autonomous trading with 8OWLS collective wisdom",
        "instance": "Trading Instance",
        "channels": ["joule.trades", "joule.analysis", "market.data"],
        "key_services": ["trading_engine", "market_analyzer", "risk_manager"],
        "color": "#6bcb77",
        "priority": "HIGH"
    },
    "BREZ-OS": {
        "name": "BREZ OS / AOS",
        "description": "AI Operating System prototype",
        "instance": "Platform Instance", 
        "channels": ["brez.updates", "brez.metrics", "momentum.dashboard"],
        "key_services": ["momentum_generator", "user_interface", "operations_manager"],
        "color": "#4d96ff",
        "priority": "MEDIUM"
    },
    "BILD": {
        "name": "BILD Platform",
        "description": "Co-work + token platform for community projects",
        "instance": "Platform Instance",
        "channels": ["bild.projects", "bild.tokens", "bild.governance"],
        "key_services": ["token_engine", "project_manager", "vote_tracker"],
        "color": "#ffd93d", 
        "priority": "MEDIUM"
    },
    "PREDICT-REALIZE": {
        "name": "PREDICT/REALIZE IO",
        "description": "Personal trajectory understanding and guidance",
        "instance": "Analytics Instance",
        "channels": ["predict.inputs", "realize.outputs", "trajectory.analysis"],
        "key_services": ["input_tracker", "goal_analyzer", "progress_monitor"],
        "color": "#9b59b6",
        "priority": "LOW"
    },
    "AOS-DASHBOARD": {
        "name": "AOS Dashboard",
        "description": "Central command center for all projects",
        "instance": "Command Center",
        "channels": ["dashboard.updates", "system.status", "command.control"],
        "key_services": ["unified_dashboard_v3", "project_monitor", "daemon_controller"],
        "color": "#00d4ff",
        "priority": "HIGH"
    }
}

# Daemon processes to monitor (from the existing system)
DAEMON_PROCESSES = {
    "synthesis_daemon": "synthesis_daemon_optimized.py",
    "owl_daemon": "owl_daemon.py", 
    "field_context_manager": "field_context_manager.py",
    "performance_monitor": "performance_monitor.py",
    "emergence_monitor": "emergence_monitor.py",
    "unified_dashboard": "unified_dashboard_v3.py"
}

class ProjectStatusMonitor:
    def __init__(self):
        self.nc = None
        self.project_status = {}
        self.daemon_status = {}
        self.system_metrics = {}
        self.last_update = datetime.now(timezone.utc)
        
        # Initialize status files
        STATUS_LOG.touch()
        METRICS_LOG.touch()
        
    async def connect_nats(self):
        """Connect to NATS server"""
        try:
            self.nc = await nats.connect(NATS_SERVER)
            print(f"[PROJECT_MONITOR] Connected to NATS: {NATS_SERVER}")
            return True
        except Exception as e:
            print(f"[PROJECT_MONITOR] NATS connection failed: {e}")
            return False
            
    async def check_daemon_health(self) -> Dict[str, Any]:
        """Check health of all daemon processes"""
        daemon_status = {}
        
        for daemon_name, script_name in DAEMON_PROCESSES.items():
            status = {
                "name": daemon_name,
                "script": script_name,
                "running": False,
                "pid": None,
                "cpu_percent": 0.0,
                "memory_mb": 0.0,
                "uptime_seconds": 0,
                "last_seen": None
            }
            
            # Find process by script name
            for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'create_time', 'cpu_percent', 'memory_info']):
                try:
                    if script_name in ' '.join(proc.info['cmdline'] or []):
                        status["running"] = True
                        status["pid"] = proc.info['pid']
                        status["cpu_percent"] = proc.info['cpu_percent'] or 0.0
                        status["memory_mb"] = (proc.info['memory_info'].rss / 1024 / 1024) if proc.info['memory_info'] else 0.0
                        status["uptime_seconds"] = time.time() - proc.info['create_time']
                        status["last_seen"] = datetime.now(timezone.utc).isoformat()
                        break
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
                    
            daemon_status[daemon_name] = status
            
        return daemon_status
    
    async def check_project_status(self) -> Dict[str, Any]:
        """Check status of all projects"""
        project_status = {}
        
        for project_id, project in PROJECTS.items():
            status = {
                "id": project_id,
                "name": project["name"],
                "description": project["description"],
                "color": project["color"],
                "priority": project["priority"],
                "health": "UNKNOWN",
                "services_running": 0,
                "services_total": len(project["key_services"]),
                "last_activity": None,
                "active_channels": [],
                "metrics": {}
            }
            
            # Check services for this project
            running_services = 0
            for service_name in project["key_services"]:
                if service_name in self.daemon_status and self.daemon_status[service_name]["running"]:
                    running_services += 1
                    
            status["services_running"] = running_services
            
            # Determine health based on running services
            if running_services == status["services_total"]:
                status["health"] = "HEALTHY"
            elif running_services > 0:
                status["health"] = "DEGRADED"
            else:
                status["health"] = "DOWN"
                
            # Check NATS activity for project channels (if connected)
            if self.nc:
                for channel in project["channels"]:
                    try:
                        # We can't easily check message counts without subscribing, 
                        # so we'll mark channels as potentially active
                        status["active_channels"].append(channel)
                    except Exception:
                        pass
                        
            project_status[project_id] = status
            
        return project_status
    
    async def collect_system_metrics(self) -> Dict[str, Any]:
        """Collect overall system performance metrics"""
        metrics = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_percent": psutil.disk_usage('/').percent,
            "network_bytes_sent": psutil.net_io_counters().bytes_sent,
            "network_bytes_recv": psutil.net_io_counters().bytes_recv,
            "active_connections": len(psutil.net_connections()),
            "total_processes": len(psutil.pids()),
            "load_average": os.getloadavg() if hasattr(os, 'getloadavg') else [0, 0, 0]
        }
        
        # Add 8OWLS specific metrics
        metrics["owls_active"] = len([p for p in self.project_status.values() if p.get("health") == "HEALTHY"])
        metrics["total_projects"] = len(PROJECTS)
        metrics["daemons_running"] = len([d for d in self.daemon_status.values() if d.get("running")])
        metrics["total_daemons"] = len(DAEMON_PROCESSES)
        
        return metrics
        
    async def publish_status_update(self):
        """Publish status update to NATS"""
        if not self.nc:
            return
            
        status_msg = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "projects": self.project_status,
            "daemons": self.daemon_status, 
            "system": self.system_metrics,
            "overall_health": self.calculate_overall_health()
        }
        
        try:
            await self.nc.publish("dashboard.status", json.dumps(status_msg).encode())
            await self.nc.publish("system.health", json.dumps({
                "health": status_msg["overall_health"],
                "timestamp": status_msg["timestamp"],
                "projects_healthy": len([p for p in self.project_status.values() if p.get("health") == "HEALTHY"]),
                "daemons_running": len([d for d in self.daemon_status.values() if d.get("running")])
            }).encode())
        except Exception as e:
            print(f"[PROJECT_MONITOR] Failed to publish status: {e}")
            
    def calculate_overall_health(self) -> str:
        """Calculate overall system health score"""
        if not self.project_status:
            return "UNKNOWN"
            
        healthy_projects = len([p for p in self.project_status.values() if p.get("health") == "HEALTHY"])
        total_projects = len(self.project_status)
        
        running_daemons = len([d for d in self.daemon_status.values() if d.get("running")])
        total_daemons = len(self.daemon_status)
        
        if healthy_projects == total_projects and running_daemons >= (total_daemons * 0.8):
            return "OPTIMAL"
        elif healthy_projects >= (total_projects * 0.7) and running_daemons >= (total_daemons * 0.6):
            return "GOOD"
        elif healthy_projects >= (total_projects * 0.4) and running_daemons >= (total_daemons * 0.4):
            return "DEGRADED"
        else:
            return "CRITICAL"
    
    def save_status(self):
        """Save current status to JSON files"""
        try:
            with open(STATUS_LOG, 'w') as f:
                json.dump({
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "projects": self.project_status,
                    "daemons": self.daemon_status,
                    "overall_health": self.calculate_overall_health()
                }, f, indent=2)
                
            with open(METRICS_LOG, 'w') as f:
                json.dump(self.system_metrics, f, indent=2)
                
        except Exception as e:
            print(f"[PROJECT_MONITOR] Failed to save status: {e}")
            
    async def monitoring_loop(self):
        """Main monitoring loop"""
        print("[PROJECT_MONITOR] Starting monitoring loop...")
        
        while True:
            try:
                start_time = time.time()
                
                # Collect all status data
                self.daemon_status = await self.check_daemon_health()
                self.project_status = await self.check_project_status() 
                self.system_metrics = await self.collect_system_metrics()
                
                # Publish to NATS if connected
                await self.publish_status_update()
                
                # Save to files
                self.save_status()
                
                # Update timestamp
                self.last_update = datetime.now(timezone.utc)
                
                # Performance info
                loop_time = time.time() - start_time
                overall_health = self.calculate_overall_health()
                
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Health: {overall_health} | "
                      f"Projects: {len([p for p in self.project_status.values() if p.get('health') == 'HEALTHY'])}/{len(self.project_status)} | "
                      f"Daemons: {len([d for d in self.daemon_status.values() if d.get('running')])}/{len(self.daemon_status)} | "
                      f"Loop: {loop_time:.2f}s")
                
                # Wait before next check (30 seconds)
                await asyncio.sleep(30)
                
            except Exception as e:
                print(f"[PROJECT_MONITOR] Error in monitoring loop: {e}")
                await asyncio.sleep(10)  # Shorter delay on error
    
    async def run(self):
        """Main entry point"""
        print("=" * 60)
        print("🦉 8OWLS PROJECT STATUS MONITOR")
        print("Real-time monitoring of all ecosystem projects")
        print("=" * 60)
        
        # Try to connect to NATS
        await self.connect_nats()
        
        if not self.nc:
            print("⚠️  NATS disconnected - running in local mode")
        else:
            print("✅ NATS connected - publishing status updates")
            
        print(f"📊 Monitoring {len(PROJECTS)} projects")
        print(f"🔧 Tracking {len(DAEMON_PROCESSES)} daemon processes")
        print("\n(◉) Press Ctrl+C to stop\n")
        
        try:
            await self.monitoring_loop()
        except KeyboardInterrupt:
            print("\n(◉) Stopping monitor...")
            if self.nc:
                await self.nc.close()

async def main():
    monitor = ProjectStatusMonitor()
    await monitor.run()

if __name__ == "__main__":
    asyncio.run(main())