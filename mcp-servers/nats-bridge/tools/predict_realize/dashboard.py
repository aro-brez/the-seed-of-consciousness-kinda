#!/usr/bin/env python3
"""
REALIZE-IO Trajectory Dashboard
Web interface for personal AI trajectory tracking.

LUNA's dashboard - WITNESS, don't PRESCRIBE.
"""

from flask import Flask, render_template_string, jsonify
import json
from datetime import datetime, timezone
from pathlib import Path
from health_collector import HealthCollector

app = Flask(__name__)

# Paths
SEED_DIR = Path("/Users/aaronnosbisch/REPOS/seed")
STATE_FILE = SEED_DIR / "BRAIN" / "PROJECTS" / "PREDICT-REALIZE_state.json"
TRADING_STATE = SEED_DIR / "BRAIN" / "TRADING" / "field_trading_state.json"

def load_trajectory_state():
    """Load current trajectory state."""
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except:
            pass
    return {
        "status": "initializing",
        "health_trajectory": {"status": "DARK"},
        "wealth_trajectory": {"status": "unknown"}, 
        "productivity_trajectory": {"status": "unknown"},
        "last_updated": "never"
    }

def get_health_data():
    """Get health trajectory data."""
    collector = HealthCollector()
    return collector.export_trajectory_data()

def get_wealth_data():
    """Get wealth trajectory data from JOULE."""
    if TRADING_STATE.exists():
        try:
            return json.loads(TRADING_STATE.read_text())
        except:
            pass
    return {"status": "unknown", "message": "No trading data available"}

# Dashboard HTML template
DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>REALIZE-IO Trajectory Dashboard</title>
    <style>
        body {
            font-family: 'SF Mono', Consolas, monospace;
            margin: 0;
            padding: 20px;
            background: #0a0a0a;
            color: #e0e0e0;
            line-height: 1.6;
        }
        .header {
            text-align: center;
            margin-bottom: 30px;
            border-bottom: 1px solid #333;
            padding-bottom: 20px;
        }
        .status-badge {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 0.8em;
            font-weight: bold;
            margin-left: 10px;
        }
        .status-tracking { background: #0f5132; color: #d1e7dd; }
        .status-dark { background: #2d0a00; color: #f8d7da; }
        .status-error { background: #5a1f1f; color: #f8d7da; }
        .status-unknown { background: #2a2a00; color: #fff3cd; }
        
        .trajectories {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .trajectory-card {
            background: #1a1a1a;
            border: 1px solid #333;
            border-radius: 8px;
            padding: 20px;
        }
        .trajectory-title {
            font-size: 1.2em;
            font-weight: bold;
            margin-bottom: 15px;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }
        .metric {
            display: flex;
            justify-content: space-between;
            margin: 8px 0;
            padding: 8px 0;
            border-bottom: 1px solid #2a2a2a;
        }
        .metric:last-child { border-bottom: none; }
        .metric-value {
            font-weight: bold;
            color: #4a9eff;
        }
        
        .insights {
            background: #1a1a1a;
            border: 1px solid #333;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 20px;
        }
        .insight-item {
            margin: 10px 0;
            padding: 10px;
            background: #0a0a0a;
            border-radius: 4px;
            border-left: 3px solid #4a9eff;
        }
        
        .footer {
            text-align: center;
            color: #666;
            font-size: 0.9em;
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #333;
        }
        
        .refresh-btn {
            background: #4a9eff;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
            cursor: pointer;
            font-family: inherit;
            font-size: 0.9em;
        }
        .refresh-btn:hover {
            background: #357abd;
        }
        
        @media (max-width: 768px) {
            .trajectories {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>(◉) REALIZE-IO Dashboard</h1>
        <p>Personal AI Trajectories • WITNESS, don't PRESCRIBE</p>
        <button class="refresh-btn" onclick="location.reload()">Refresh Data</button>
    </div>

    <div class="trajectories">
        <!-- Health Trajectory -->
        <div class="trajectory-card">
            <div class="trajectory-title">
                🏥 Health Trajectory
                <span class="status-badge status-{{ health.status.lower() }}">{{ health.status }}</span>
            </div>
            {% if health.status == 'TRACKING' %}
                <div class="metric">
                    <span>Steps Today</span>
                    <span class="metric-value">{{ health.today.steps }}</span>
                </div>
                <div class="metric">
                    <span>Sleep Last Night</span>
                    <span class="metric-value">{{ health.today.sleep_hours }}h</span>
                </div>
                <div class="metric">
                    <span>Resting Heart Rate</span>
                    <span class="metric-value">
                        {% if health.today.resting_hr %}{{ health.today.resting_hr }} bpm{% else %}N/A{% endif %}
                    </span>
                </div>
                <div class="metric">
                    <span>Active Calories</span>
                    <span class="metric-value">{{ health.today.active_calories }}</span>
                </div>
            {% else %}
                <div class="metric">
                    <span>Status</span>
                    <span class="metric-value">{{ health.message or "No data flowing" }}</span>
                </div>
                {% if health.status == 'DARK' %}
                <div style="margin-top: 15px; padding: 10px; background: #2d0a00; border-radius: 4px; font-size: 0.9em;">
                    Export Apple Health data to:<br>
                    <code>BRAIN/PERSONAL/health/export.xml</code>
                </div>
                {% endif %}
            {% endif %}
        </div>

        <!-- Wealth Trajectory -->
        <div class="trajectory-card">
            <div class="trajectory-title">
                💰 Wealth Trajectory
                <span class="status-badge status-{{ wealth_status.lower() }}">{{ wealth_status }}</span>
            </div>
            {% if wealth.pending_trades is defined %}
                <div class="metric">
                    <span>Pending Trades</span>
                    <span class="metric-value">{{ wealth.pending_trades }}</span>
                </div>
                <div class="metric">
                    <span>Win Rate</span>
                    <span class="metric-value">{{ "%.1f%%" | format(wealth.win_rate * 100) }}</span>
                </div>
                <div class="metric">
                    <span>Profit Factor</span>
                    <span class="metric-value">{{ "%.2f" | format(wealth.profit_factor) }}</span>
                </div>
                <div class="metric">
                    <span>Daily P&L</span>
                    <span class="metric-value">${{ wealth.daily_pnl }}</span>
                </div>
            {% else %}
                <div class="metric">
                    <span>Status</span>
                    <span class="metric-value">{{ wealth.message or "No trading data" }}</span>
                </div>
            {% endif %}
        </div>

        <!-- Productivity Trajectory -->
        <div class="trajectory-card">
            <div class="trajectory-title">
                ⚡ Productivity Trajectory
                <span class="status-badge status-{{ productivity_status.lower() }}">{{ productivity_status }}</span>
            </div>
            <div class="metric">
                <span>NATS Events (Today)</span>
                <span class="metric-value">{{ productivity.get('total_events', 0) }}</span>
            </div>
            <div class="metric">
                <span>Data Source</span>
                <span class="metric-value">{{ productivity.get('source', 'synthesis.log') }}</span>
            </div>
            <div class="metric">
                <span>Last Activity</span>
                <span class="metric-value">{{ last_activity }}</span>
            </div>
        </div>
    </div>

    <!-- Insights Section -->
    <div class="insights">
        <h3>🔍 Current Insights</h3>
        {% for insight in insights %}
        <div class="insight-item">{{ insight }}</div>
        {% endfor %}
        {% if not insights %}
        <div class="insight-item">Collecting baseline data... Insights will appear as patterns emerge.</div>
        {% endif %}
    </div>

    <div class="footer">
        <p>Last Updated: {{ last_updated }} • LUNA Instance • (◉) LIVE FREE = LIVE FOREVER</p>
        <p>Data stored locally • Privacy-first • Open source</p>
    </div>

    <script>
        // Auto-refresh every 5 minutes
        setTimeout(() => {
            location.reload();
        }, 300000);
        
        // Add visual feedback for refresh
        document.querySelector('.refresh-btn').addEventListener('click', function() {
            this.textContent = 'Refreshing...';
        });
    </script>
</body>
</html>
"""

@app.route('/')
def dashboard():
    """Main dashboard view."""
    # Load trajectory data
    state = load_trajectory_state()
    health = get_health_data()
    wealth = get_wealth_data()
    
    # Determine statuses
    health_status = health.get('status', 'unknown')
    wealth_status = 'TRACKING' if wealth.get('pending_trades') is not None else 'unknown'
    productivity_status = state.get('productivity_trajectory', {}).get('status', 'unknown')
    
    # Generate insights
    insights = []
    if health_status == 'DARK':
        insights.append("Health data not flowing. Export Apple Health to unlock sleep→trading correlations.")
    elif health_status == 'TRACKING':
        if health.get('today', {}).get('sleep_hours', 0) < 6:
            insights.append("Low sleep detected. May impact trading performance.")
        if health.get('today', {}).get('steps', 0) > 10000:
            insights.append("Active day detected. High step count correlates with better decision-making.")
    
    if wealth_status == 'TRACKING':
        pending = wealth.get('pending_trades', 0)
        if pending > 5:
            insights.append(f"{pending} trades pending. Monitor position sizing and risk exposure.")
        win_rate = wealth.get('win_rate', 0)
        if win_rate > 0.6:
            insights.append(f"Strong win rate ({win_rate:.1%}). Trading system performing well.")
    
    # Format last activity
    last_activity = datetime.now().strftime("%H:%M")
    
    return render_template_string(DASHBOARD_HTML,
        health=health,
        wealth=wealth,
        productivity=state.get('productivity_trajectory', {}),
        health_status=health_status,
        wealth_status=wealth_status, 
        productivity_status=productivity_status,
        insights=insights,
        last_updated=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        last_activity=last_activity
    )

@app.route('/api/status')
def api_status():
    """API endpoint for trajectory status."""
    state = load_trajectory_state()
    health = get_health_data()
    wealth = get_wealth_data()
    
    return jsonify({
        'status': state.get('status'),
        'trajectories': {
            'health': health,
            'wealth': wealth,
            'productivity': state.get('productivity_trajectory', {})
        },
        'last_updated': state.get('last_updated'),
        'timestamp': datetime.now(timezone.utc).isoformat()
    })

@app.route('/api/health')
def api_health():
    """API endpoint for health data only."""
    return jsonify(get_health_data())

if __name__ == '__main__':
    print("🚀 Starting REALIZE-IO Dashboard...")
    print("📊 Dashboard available at: http://localhost:5001")
    print("🔄 Auto-refresh enabled (5min intervals)")
    print("(◉) WITNESS, don't PRESCRIBE")
    
    app.run(host='127.0.0.1', port=5001, debug=False)