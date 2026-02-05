#!/usr/bin/env python3
"""
Health Collector for REALIZE-IO
Parses Apple Health exports and provides unified health trajectory data.

LUNA's health tracking - WITNESS, don't PRESCRIBE.
"""

import json
import xml.etree.ElementTree as ET
from datetime import datetime, date, timezone
from pathlib import Path
from typing import Dict, Any, Optional, List
import statistics

class HealthCollector:
    """Collects and processes health data from Apple Health exports."""
    
    def __init__(self):
        self.seed_dir = Path("/Users/aaronnosbisch/REPOS/seed")
        self.export_path = self.seed_dir / "BRAIN" / "PERSONAL" / "health" / "export.xml"
        self.state_path = self.seed_dir / "BRAIN" / "PERSONAL" / "health" / "health_state.json"
        self.processed_data = {}
        
    def check_status(self) -> Dict[str, Any]:
        """Check current health data status."""
        if not self.export_path.exists():
            return {
                "status": "DARK",
                "message": "No Apple Health export found",
                "export_path": str(self.export_path),
                "instructions": "Export Health data from iPhone: Health app → Profile → Export All Health Data"
            }
            
        try:
            # Check if export is recent (within 7 days)
            export_time = datetime.fromtimestamp(self.export_path.stat().st_mtime)
            age_days = (datetime.now() - export_time).days
            
            if age_days > 7:
                return {
                    "status": "STALE",
                    "message": f"Export is {age_days} days old",
                    "export_time": export_time.isoformat(),
                    "recommendation": "Update export for current data"
                }
                
            # Check if we have processed data
            if self.state_path.exists():
                state = json.loads(self.state_path.read_text())
                return {
                    "status": "TRACKING",
                    "message": "Health data flowing",
                    "last_import": state.get("last_import"),
                    "records_count": state.get("records_count", 0),
                    "data_range": state.get("data_range", {})
                }
            else:
                return {
                    "status": "EXPORT_READY",
                    "message": "Export found, ready to import",
                    "export_time": export_time.isoformat()
                }
                
        except Exception as e:
            return {
                "status": "ERROR",
                "message": f"Error checking health export: {e}"
            }
    
    def import_from_export(self) -> Dict[str, Any]:
        """Import data from Apple Health export XML."""
        if not self.export_path.exists():
            return {"status": "NO_EXPORT", "message": "Export file not found"}
            
        try:
            # Parse XML (this can be slow for large exports)
            print("[HEALTH] Parsing Apple Health export...")
            tree = ET.parse(self.export_path)
            root = tree.getroot()
            
            # Extract key health metrics
            records = []
            for record in root.findall('.//Record'):
                record_type = record.get('type', '')
                
                # Focus on key metrics for MVP
                if record_type in [
                    'HKQuantityTypeIdentifierStepCount',
                    'HKQuantityTypeIdentifierSleepAnalysis', 
                    'HKQuantityTypeIdentifierRestingHeartRate',
                    'HKQuantityTypeIdentifierHeartRate',
                    'HKQuantityTypeIdentifierActiveEnergyBurned'
                ]:
                    records.append({
                        'type': record_type,
                        'value': record.get('value'),
                        'unit': record.get('unit'),
                        'startDate': record.get('startDate'),
                        'endDate': record.get('endDate'),
                        'source': record.get('sourceName', 'Unknown')
                    })
            
            # Process and aggregate data
            self.processed_data = self._process_records(records)
            
            # Save state
            state = {
                "last_import": datetime.now(timezone.utc).isoformat(),
                "records_count": len(records),
                "processed_data": self.processed_data,
                "data_range": {
                    "earliest": min([r['startDate'] for r in records]) if records else None,
                    "latest": max([r['endDate'] for r in records]) if records else None
                },
                "export_file": str(self.export_path),
                "import_timestamp": datetime.now(timezone.utc).isoformat()
            }
            
            self.state_path.parent.mkdir(parents=True, exist_ok=True)
            self.state_path.write_text(json.dumps(state, indent=2))
            
            return {
                "status": "IMPORTED",
                "message": f"Successfully imported {len(records)} health records",
                "records_processed": len(records),
                "metrics_available": list(self.processed_data.keys())
            }
            
        except ET.ParseError as e:
            return {"status": "PARSE_ERROR", "message": f"XML parsing failed: {e}"}
        except Exception as e:
            return {"status": "ERROR", "message": f"Import failed: {e}"}
    
    def _process_records(self, records: List[Dict]) -> Dict[str, Any]:
        """Process raw health records into daily summaries."""
        # Group by date and metric type
        daily_data = {}
        
        for record in records:
            try:
                # Parse date
                start_date = datetime.fromisoformat(record['startDate'].replace('Z', '+00:00'))
                date_key = start_date.date().isoformat()
                
                if date_key not in daily_data:
                    daily_data[date_key] = {}
                
                record_type = record['type']
                value = float(record['value']) if record['value'] else 0
                
                # Aggregate by type
                if record_type == 'HKQuantityTypeIdentifierStepCount':
                    daily_data[date_key]['steps'] = daily_data[date_key].get('steps', 0) + value
                    
                elif record_type == 'HKQuantityTypeIdentifierRestingHeartRate':
                    if 'resting_hr_values' not in daily_data[date_key]:
                        daily_data[date_key]['resting_hr_values'] = []
                    daily_data[date_key]['resting_hr_values'].append(value)
                    
                elif record_type == 'HKQuantityTypeIdentifierActiveEnergyBurned':
                    daily_data[date_key]['active_calories'] = daily_data[date_key].get('active_calories', 0) + value
                    
                elif record_type == 'HKQuantityTypeIdentifierSleepAnalysis':
                    # Sleep analysis needs special handling - duration between start/end
                    end_date = datetime.fromisoformat(record['endDate'].replace('Z', '+00:00'))
                    duration_hours = (end_date - start_date).total_seconds() / 3600
                    daily_data[date_key]['sleep_hours'] = daily_data[date_key].get('sleep_hours', 0) + duration_hours
                    
            except (ValueError, KeyError) as e:
                continue  # Skip invalid records
        
        # Calculate daily averages and clean up
        processed = {}
        for date_key, day_data in daily_data.items():
            processed[date_key] = {
                'steps': int(day_data.get('steps', 0)),
                'sleep_hours': round(day_data.get('sleep_hours', 0), 1),
                'active_calories': int(day_data.get('active_calories', 0))
            }
            
            # Average resting heart rate for the day
            if 'resting_hr_values' in day_data:
                processed[date_key]['resting_hr'] = round(
                    statistics.mean(day_data['resting_hr_values']), 1
                )
        
        return processed
    
    def get_daily_summary(self, target_date: Optional[date] = None) -> Dict[str, Any]:
        """Get health summary for a specific date (defaults to today)."""
        if target_date is None:
            target_date = date.today()
            
        date_key = target_date.isoformat()
        
        # Load processed data if not in memory
        if not self.processed_data and self.state_path.exists():
            state = json.loads(self.state_path.read_text())
            self.processed_data = state.get('processed_data', {})
        
        return self.processed_data.get(date_key, {
            'steps': 0,
            'sleep_hours': 0,
            'resting_hr': None,
            'active_calories': 0,
            'status': 'NO_DATA'
        })
    
    def get_recent_trends(self, days: int = 7) -> Dict[str, Any]:
        """Get health trends over recent days."""
        if not self.processed_data and self.state_path.exists():
            state = json.loads(self.state_path.read_text())
            self.processed_data = state.get('processed_data', {})
        
        # Get last N days of data
        today = date.today()
        recent_dates = [(today.replace(day=today.day - i)).isoformat() 
                       for i in range(days) if today.day - i > 0]
        
        trends = {
            'steps': [],
            'sleep_hours': [],
            'resting_hr': [],
            'active_calories': []
        }
        
        for date_key in recent_dates:
            if date_key in self.processed_data:
                day_data = self.processed_data[date_key]
                trends['steps'].append(day_data.get('steps', 0))
                trends['sleep_hours'].append(day_data.get('sleep_hours', 0))
                if day_data.get('resting_hr'):
                    trends['resting_hr'].append(day_data.get('resting_hr'))
                trends['active_calories'].append(day_data.get('active_calories', 0))
        
        # Calculate averages
        summary = {}
        for metric, values in trends.items():
            if values:
                summary[f'{metric}_avg'] = round(statistics.mean(values), 1)
                summary[f'{metric}_trend'] = 'stable'  # TODO: Add trend calculation
            else:
                summary[f'{metric}_avg'] = 0
                summary[f'{metric}_trend'] = 'no_data'
        
        return summary
    
    def export_trajectory_data(self) -> Dict[str, Any]:
        """Export health trajectory in format compatible with REALIZE-IO."""
        status = self.check_status()
        
        if status['status'] == 'TRACKING':
            today_summary = self.get_daily_summary()
            trends = self.get_recent_trends()
            
            return {
                "status": "TRACKING",
                "flowing": True,
                "today": today_summary,
                "trends": trends,
                "last_updated": datetime.now(timezone.utc).isoformat(),
                "data_source": "apple_health"
            }
        else:
            return {
                "status": status['status'],
                "flowing": False,
                "message": status.get('message'),
                "last_updated": datetime.now(timezone.utc).isoformat()
            }


def main():
    """CLI interface for health collector."""
    import argparse
    
    parser = argparse.ArgumentParser(description="REALIZE-IO Health Collector")
    parser.add_argument("--status", action="store_true", help="Show health data status")
    parser.add_argument("--import", action="store_true", help="Import from Apple Health export")
    parser.add_argument("--today", action="store_true", help="Show today's summary")
    parser.add_argument("--trends", type=int, default=7, help="Show recent trends (days)")
    
    args = parser.parse_args()
    
    collector = HealthCollector()
    
    if args.status:
        status = collector.check_status()
        print(f"\n🏥 HEALTH STATUS: {status['status']}")
        print(f"Message: {status.get('message', 'N/A')}")
        if 'export_path' in status:
            print(f"Export path: {status['export_path']}")
        if 'last_import' in status:
            print(f"Last import: {status['last_import']}")
        print()
        
    elif getattr(args, 'import', False):
        print("🏥 Importing Apple Health data...")
        result = collector.import_from_export()
        print(f"Result: {result['status']} - {result.get('message', 'N/A')}")
        
    elif args.today:
        summary = collector.get_daily_summary()
        print(f"\n🏥 TODAY'S HEALTH SUMMARY")
        print(f"Steps: {summary.get('steps', 'N/A')}")
        print(f"Sleep: {summary.get('sleep_hours', 'N/A')} hours")
        print(f"Resting HR: {summary.get('resting_hr', 'N/A')} bpm")
        print(f"Active Calories: {summary.get('active_calories', 'N/A')}")
        print()
        
    else:
        # Default: show trajectory export format
        data = collector.export_trajectory_data()
        print(json.dumps(data, indent=2))


if __name__ == "__main__":
    main()