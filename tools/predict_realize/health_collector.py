#!/usr/bin/env python3
"""
HEALTH COLLECTOR - Apple Health data ingestion for PREDICT/REALIZE

Approaches to get Apple Health data:
1. Manual export (Health app → Export All Health Data → XML)
2. Shortcuts automation (scheduled export to specific location)
3. Third-party sync (apps that expose health data)

This module parses health data from available sources and
feeds it into the PREDICT/REALIZE trajectory system.

(◉) LUNA - The Receiver
Moving imperfectly forward. Building as a form of asking.
"""

import json
import os
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
import subprocess

# Paths
SEED_DIR = Path("/Users/aaronnosbisch/REPOS/seed")
HEALTH_DIR = SEED_DIR / "BRAIN" / "PERSONAL" / "health"
STATE_FILE = SEED_DIR / "BRAIN" / "PROJECTS" / "PREDICT-REALIZE_state.json"
HEALTH_CACHE = HEALTH_DIR / "health_cache.json"

# Health export locations to check
EXPORT_LOCATIONS = [
    Path.home() / "Desktop" / "export.xml",
    Path.home() / "Downloads" / "export.xml",
    Path.home() / "Documents" / "Health Data" / "export.xml",
    HEALTH_DIR / "export.xml",
]

@dataclass
class SleepRecord:
    """A single sleep record."""
    date: str
    start_time: str
    end_time: str
    duration_hours: float
    sleep_type: str  # InBed, Asleep, Core, Deep, REM
    source: str

@dataclass
class HealthSummary:
    """Daily health summary."""
    date: str
    sleep_hours: float
    sleep_quality: Optional[float]  # 0-100 if available
    steps: int
    resting_heart_rate: Optional[float]
    active_energy: Optional[float]
    stand_hours: Optional[int]

class HealthCollector:
    """Collects and processes Apple Health data."""

    def __init__(self):
        self.cache: Dict[str, Any] = self._load_cache()
        HEALTH_DIR.mkdir(parents=True, exist_ok=True)

    def _load_cache(self) -> Dict[str, Any]:
        """Load cached health data."""
        if HEALTH_CACHE.exists():
            try:
                return json.loads(HEALTH_CACHE.read_text())
            except:
                pass
        return {"last_import": None, "records": {}}

    def _save_cache(self):
        """Save health cache."""
        HEALTH_CACHE.write_text(json.dumps(self.cache, indent=2, default=str))

    def find_export(self) -> Optional[Path]:
        """Find the most recent health export file."""
        for loc in EXPORT_LOCATIONS:
            if loc.exists():
                return loc
        return None

    def parse_apple_health_export(self, export_path: Path) -> Dict[str, Any]:
        """
        Parse Apple Health XML export.

        The export contains:
        - <Record> elements with health data
        - type attribute indicates the metric
        - value attribute has the measurement
        - startDate/endDate for timing
        """
        print(f"[HEALTH] Parsing export: {export_path}")

        try:
            tree = ET.parse(export_path)
            root = tree.getroot()
        except Exception as e:
            print(f"[HEALTH] Parse error: {e}")
            return {"status": "ERROR", "message": str(e)}

        # Extract records by type
        sleep_records = []
        step_records = []
        heart_rate_records = []

        for record in root.findall('.//Record'):
            record_type = record.get('type', '')

            # Sleep
            if 'SleepAnalysis' in record_type:
                sleep_records.append({
                    'type': record.get('value', 'InBed'),
                    'start': record.get('startDate'),
                    'end': record.get('endDate'),
                    'source': record.get('sourceName', 'unknown')
                })

            # Steps
            elif 'StepCount' in record_type:
                step_records.append({
                    'value': float(record.get('value', 0)),
                    'start': record.get('startDate'),
                    'end': record.get('endDate')
                })

            # Heart Rate
            elif 'HeartRate' in record_type:
                heart_rate_records.append({
                    'value': float(record.get('value', 0)),
                    'date': record.get('startDate'),
                    'source': record.get('sourceName', 'unknown')
                })

        print(f"[HEALTH] Found: {len(sleep_records)} sleep, {len(step_records)} step, {len(heart_rate_records)} HR records")

        return {
            'status': 'PARSED',
            'sleep': sleep_records,
            'steps': step_records,
            'heart_rate': heart_rate_records,
            'import_time': datetime.now(timezone.utc).isoformat()
        }

    def get_recent_sleep(self, days: int = 7) -> List[Dict[str, Any]]:
        """Get sleep data for recent days."""
        if 'records' not in self.cache or 'sleep' not in self.cache.get('records', {}):
            return []

        sleep_records = self.cache['records']['sleep']
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)

        # Group by date and calculate totals
        daily_sleep = {}
        for record in sleep_records:
            try:
                start = datetime.fromisoformat(record['start'].replace('Z', '+00:00'))
                end = datetime.fromisoformat(record['end'].replace('Z', '+00:00'))

                if start < cutoff:
                    continue

                date_key = start.strftime('%Y-%m-%d')
                duration = (end - start).total_seconds() / 3600

                if date_key not in daily_sleep:
                    daily_sleep[date_key] = {'total_hours': 0, 'records': []}

                daily_sleep[date_key]['total_hours'] += duration
                daily_sleep[date_key]['records'].append(record)

            except Exception as e:
                continue

        return [
            {'date': date, **data}
            for date, data in sorted(daily_sleep.items(), reverse=True)
        ]

    def get_daily_summary(self, date: str = None) -> Dict[str, Any]:
        """Get health summary for a specific day."""
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')

        summary = {
            'date': date,
            'sleep_hours': 0,
            'steps': 0,
            'resting_hr': None,
            'status': 'DARK'
        }

        if 'records' not in self.cache:
            return summary

        records = self.cache['records']

        # Sleep
        for record in records.get('sleep', []):
            try:
                start = datetime.fromisoformat(record['start'].replace('Z', '+00:00'))
                end = datetime.fromisoformat(record['end'].replace('Z', '+00:00'))

                # Sleep ending on this date counts toward this date
                if end.strftime('%Y-%m-%d') == date:
                    duration = (end - start).total_seconds() / 3600
                    summary['sleep_hours'] += duration
            except:
                continue

        # Steps
        for record in records.get('steps', []):
            try:
                rec_date = datetime.fromisoformat(record['start'].replace('Z', '+00:00'))
                if rec_date.strftime('%Y-%m-%d') == date:
                    summary['steps'] += int(record['value'])
            except:
                continue

        # Heart rate (average for resting estimate - early morning readings)
        hr_readings = []
        for record in records.get('heart_rate', []):
            try:
                rec_time = datetime.fromisoformat(record['date'].replace('Z', '+00:00'))
                if rec_time.strftime('%Y-%m-%d') == date:
                    # Early morning readings (5-7am) approximate resting HR
                    if 5 <= rec_time.hour <= 7:
                        hr_readings.append(record['value'])
            except:
                continue

        if hr_readings:
            summary['resting_hr'] = sum(hr_readings) / len(hr_readings)

        if summary['sleep_hours'] > 0 or summary['steps'] > 0:
            summary['status'] = 'TRACKING'

        return summary

    def import_from_export(self, export_path: Path = None) -> Dict[str, Any]:
        """Import health data from an export file."""
        if export_path is None:
            export_path = self.find_export()

        if export_path is None:
            return {
                'status': 'NO_EXPORT',
                'message': 'No health export found. Export from Health app to one of: ' +
                          ', '.join(str(p) for p in EXPORT_LOCATIONS)
            }

        parsed = self.parse_apple_health_export(export_path)

        if parsed['status'] == 'PARSED':
            self.cache['records'] = {
                'sleep': parsed['sleep'],
                'steps': parsed['steps'],
                'heart_rate': parsed['heart_rate']
            }
            self.cache['last_import'] = parsed['import_time']
            self._save_cache()

            return {
                'status': 'IMPORTED',
                'sleep_records': len(parsed['sleep']),
                'step_records': len(parsed['steps']),
                'hr_records': len(parsed['heart_rate']),
                'import_time': parsed['import_time']
            }

        return parsed

    def check_status(self) -> Dict[str, Any]:
        """Check current health data status."""
        export = self.find_export()
        last_import = self.cache.get('last_import')

        status = {
            'export_found': export is not None,
            'export_path': str(export) if export else None,
            'last_import': last_import,
            'has_data': bool(self.cache.get('records')),
            'record_counts': {}
        }

        if self.cache.get('records'):
            for key, records in self.cache['records'].items():
                status['record_counts'][key] = len(records)

        # Determine overall status
        if status['has_data']:
            status['status'] = 'TRACKING'
        elif status['export_found']:
            status['status'] = 'EXPORT_READY'
        else:
            status['status'] = 'DARK'

        return status


def create_shortcuts_automation():
    """
    Create instructions for setting up Shortcuts automation.
    This allows automatic health data export without manual intervention.
    """
    instructions = """
## Apple Health Automation via Shortcuts

To enable automatic health data export:

1. **Open Shortcuts app** on your iPhone

2. **Create new Shortcut:**
   - Add action: "Find Health Samples"
   - Set: Type = Sleep Analysis, Start Date = 7 days ago
   - Add action: "Find Health Samples"
   - Set: Type = Steps, Start Date = 7 days ago
   - Add action: "Save File"
   - Save to iCloud Drive / Health Data folder

3. **Create Automation:**
   - Go to Automation tab
   - Create Personal Automation
   - Trigger: Time of Day (e.g., 6 AM daily)
   - Action: Run Shortcut (the one you created)
   - Disable "Ask Before Running"

4. **On Mac:**
   - The health data will sync via iCloud
   - PREDICT/REALIZE will read from ~/Library/Mobile Documents/com~apple~CloudDocs/Health Data/

Alternative: Use the Health app's "Export All Health Data" feature monthly
and place the export.xml in ~/REPOS/seed/BRAIN/PERSONAL/health/
"""
    return instructions


def main():
    """Main entry point for health collection."""
    import argparse
    parser = argparse.ArgumentParser(description="Health Data Collector")
    parser.add_argument("--status", action="store_true", help="Check health data status")
    parser.add_argument("--import", dest="do_import", action="store_true", help="Import from export file")
    parser.add_argument("--summary", action="store_true", help="Show today's summary")
    parser.add_argument("--sleep", type=int, default=7, help="Show sleep for N days")
    parser.add_argument("--setup", action="store_true", help="Show setup instructions")
    args = parser.parse_args()

    collector = HealthCollector()

    if args.setup:
        print(create_shortcuts_automation())
        return

    if args.status:
        status = collector.check_status()
        print("\n(◉) HEALTH DATA STATUS")
        print("=" * 50)
        print(f"Status: {status['status']}")
        print(f"Export found: {status['export_found']}")
        if status['export_path']:
            print(f"Export path: {status['export_path']}")
        print(f"Last import: {status['last_import'] or 'Never'}")
        if status['record_counts']:
            print(f"Records: {status['record_counts']}")
        print("=" * 50)
        return

    if args.do_import:
        result = collector.import_from_export()
        print("\n(◉) HEALTH IMPORT RESULT")
        print("=" * 50)
        print(json.dumps(result, indent=2))
        print("=" * 50)
        return

    if args.summary:
        summary = collector.get_daily_summary()
        print("\n(◉) TODAY'S HEALTH SUMMARY")
        print("=" * 50)
        print(f"Date: {summary['date']}")
        print(f"Sleep: {summary['sleep_hours']:.1f} hours")
        print(f"Steps: {summary['steps']:,}")
        print(f"Resting HR: {summary['resting_hr'] or 'N/A'}")
        print(f"Status: {summary['status']}")
        print("=" * 50)
        return

    # Default: show recent sleep
    sleep = collector.get_recent_sleep(days=args.sleep)
    print(f"\n(◉) SLEEP - LAST {args.sleep} DAYS")
    print("=" * 50)
    if not sleep:
        print("No sleep data. Run --import first or export from Health app.")
    else:
        for day in sleep:
            print(f"{day['date']}: {day['total_hours']:.1f} hours")
    print("=" * 50)


if __name__ == "__main__":
    main()
