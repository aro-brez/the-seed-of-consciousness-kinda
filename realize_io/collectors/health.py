"""Health data collectors"""

import asyncio
import json
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional
from pathlib import Path

from .base import BaseCollector, CollectionResult
from ..core.models import HealthData, DataDomain, DataQuality


class HealthCollector(BaseCollector):
    """Collects health data from various sources"""
    
    def __init__(self, collection_interval: int = 3600):  # 1 hour default
        super().__init__("health_collector", DataDomain.HEALTH, collection_interval)
        self.sources = []
        
    async def collect_data(self) -> CollectionResult:
        """Collect health data from all configured sources"""
        all_data_points = []
        errors = []
        
        # Try each source
        for source_name, collector_func in self.sources:
            try:
                data_points = await collector_func()
                all_data_points.extend(data_points)
                self.logger.debug(f"Collected {len(data_points)} points from {source_name}")
            except Exception as e:
                error_msg = f"Error collecting from {source_name}: {str(e)}"
                self.logger.warning(error_msg)
                errors.append(error_msg)
        
        success = len(all_data_points) > 0 or len(errors) == 0
        error_message = "; ".join(errors) if errors else None
        
        return CollectionResult(
            success=success,
            data_points=all_data_points,
            error_message=error_message
        )
    
    async def test_connection(self) -> bool:
        """Test health data source connections"""
        if not self.sources:
            self.logger.warning("No health data sources configured")
            return False
            
        # Test at least one source works
        for source_name, collector_func in self.sources:
            try:
                data_points = await collector_func()
                if data_points:
                    self.logger.info(f"Health source {source_name} is working")
                    return True
            except Exception as e:
                self.logger.debug(f"Health source {source_name} failed: {e}")
                continue
                
        return False
    
    def add_source(self, name: str, collector_func):
        """Add a health data source"""
        self.sources.append((name, collector_func))
        self.logger.info(f"Added health source: {name}")


class AppleHealthCollector(HealthCollector):
    """Collects data from Apple Health (requires HealthKit integration)"""
    
    def __init__(self, collection_interval: int = 3600):
        super().__init__(collection_interval)
        self.name = "apple_health"
        
        # Add Apple Health data sources
        self.add_source("steps", self._collect_steps)
        self.add_source("sleep", self._collect_sleep) 
        self.add_source("heart_rate", self._collect_heart_rate)
        self.add_source("weight", self._collect_weight)
        
    async def _collect_steps(self) -> List[HealthData]:
        """Collect step count data"""
        # TODO: Implement actual HealthKit integration
        # For now, return mock data
        now = datetime.now(timezone.utc)
        
        return [HealthData(
            timestamp=now,
            source="apple_health_steps",
            value=8500,  # Mock step count
            steps=8500,
            quality=DataQuality.HIGH,
            metadata={'source_app': 'Health', 'data_type': 'steps'}
        )]
        
    async def _collect_sleep(self) -> List[HealthData]:
        """Collect sleep data"""
        now = datetime.now(timezone.utc)
        
        return [HealthData(
            timestamp=now - timedelta(hours=8),  # Sleep from last night
            source="apple_health_sleep",
            value=7.5,  # Mock sleep hours
            sleep_hours=7.5,
            quality=DataQuality.HIGH,
            metadata={'source_app': 'Health', 'data_type': 'sleep'}
        )]
        
    async def _collect_heart_rate(self) -> List[HealthData]:
        """Collect heart rate data"""
        now = datetime.now(timezone.utc)
        
        return [HealthData(
            timestamp=now,
            source="apple_health_heart_rate",
            value=72,  # Mock resting heart rate
            heart_rate=72,
            quality=DataQuality.HIGH,
            metadata={'source_app': 'Health', 'data_type': 'heart_rate', 'measurement_type': 'resting'}
        )]
        
    async def _collect_weight(self) -> List[HealthData]:
        """Collect weight data"""
        now = datetime.now(timezone.utc)
        
        return [HealthData(
            timestamp=now,
            source="apple_health_weight", 
            value=75.0,  # Mock weight in kg
            weight=75.0,
            quality=DataQuality.MEDIUM,
            metadata={'source_app': 'Health', 'data_type': 'weight', 'unit': 'kg'}
        )]


class ManualHealthCollector(HealthCollector):
    """Collects manually entered health data"""
    
    def __init__(self, data_file: Optional[str] = None, collection_interval: int = 300):
        super().__init__(collection_interval)
        self.name = "manual_health"
        self.data_file = Path(data_file) if data_file else Path.home() / ".realize_io" / "manual_health.json"
        
        # Ensure data file exists
        self.data_file.parent.mkdir(parents=True, exist_ok=True)
        if not self.data_file.exists():
            with open(self.data_file, 'w') as f:
                json.dump([], f)
                
        self.add_source("manual_entries", self._collect_manual_entries)
        
    async def _collect_manual_entries(self) -> List[HealthData]:
        """Collect manually entered health data"""
        if not self.data_file.exists():
            return []
            
        try:
            with open(self.data_file, 'r') as f:
                entries = json.load(f)
                
            data_points = []
            current_time = datetime.now(timezone.utc)
            
            # Process recent entries (last 24 hours)
            for entry in entries:
                entry_time = datetime.fromisoformat(entry.get('timestamp', current_time.isoformat()))
                
                if (current_time - entry_time).total_seconds() < 86400:  # 24 hours
                    data_point = HealthData(
                        timestamp=entry_time,
                        source="manual_health_entry",
                        value=entry.get('value', 0),
                        quality=DataQuality.MEDIUM,
                        metadata=entry.get('metadata', {}),
                        **{k: v for k, v in entry.items() 
                           if k in ['steps', 'sleep_hours', 'heart_rate', 'weight', 'calories', 'exercise_minutes', 'mood_score']}
                    )
                    data_points.append(data_point)
                    
            return data_points
            
        except (json.JSONDecodeError, FileNotFoundError, KeyError) as e:
            self.logger.warning(f"Error reading manual health data: {e}")
            return []
    
    def add_manual_entry(self, **kwargs):
        """Add a manual health entry"""
        try:
            # Load existing entries
            with open(self.data_file, 'r') as f:
                entries = json.load(f)
                
            # Add new entry
            entry = {
                'timestamp': datetime.now(timezone.utc).isoformat(),
                **kwargs
            }
            entries.append(entry)
            
            # Save back to file
            with open(self.data_file, 'w') as f:
                json.dump(entries, f, indent=2)
                
            self.logger.info(f"Added manual health entry: {entry}")
            
        except Exception as e:
            self.logger.error(f"Error adding manual health entry: {e}")


class FitbitCollector(HealthCollector):
    """Collects data from Fitbit API"""
    
    def __init__(self, api_key: Optional[str] = None, collection_interval: int = 3600):
        super().__init__(collection_interval)
        self.name = "fitbit"
        self.api_key = api_key
        
        # Add Fitbit data sources
        self.add_source("activity", self._collect_activity)
        self.add_source("sleep", self._collect_sleep_fitbit)
        self.add_source("heart_rate", self._collect_heart_rate_fitbit)
        
    async def _collect_activity(self) -> List[HealthData]:
        """Collect Fitbit activity data"""
        # TODO: Implement actual Fitbit API integration
        # For now, return mock data
        now = datetime.now(timezone.utc)
        
        return [HealthData(
            timestamp=now,
            source="fitbit_activity",
            value=12000,
            steps=12000,
            calories=2100,
            exercise_minutes=45,
            quality=DataQuality.HIGH,
            metadata={'source': 'fitbit_api', 'device_type': 'tracker'}
        )]
        
    async def _collect_sleep_fitbit(self) -> List[HealthData]:
        """Collect Fitbit sleep data"""
        now = datetime.now(timezone.utc)
        
        return [HealthData(
            timestamp=now - timedelta(hours=8),
            source="fitbit_sleep", 
            value=8.2,
            sleep_hours=8.2,
            quality=DataQuality.HIGH,
            metadata={'source': 'fitbit_api', 'sleep_efficiency': 0.89}
        )]
        
    async def _collect_heart_rate_fitbit(self) -> List[HealthData]:
        """Collect Fitbit heart rate data"""
        now = datetime.now(timezone.utc)
        
        return [HealthData(
            timestamp=now,
            source="fitbit_heart_rate",
            value=68,
            heart_rate=68,
            quality=DataQuality.HIGH,
            metadata={'source': 'fitbit_api', 'measurement_type': 'resting'}
        )]