"""Base collector class for all data collection modules"""

import asyncio
import logging
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Callable
from enum import Enum
from dataclasses import dataclass

from ..core.models import DataPoint, DataDomain
from ..core.config import config_manager


class CollectorStatus(Enum):
    """Status of data collector"""
    INACTIVE = "inactive"
    ACTIVE = "active" 
    ERROR = "error"
    DISABLED = "disabled"


@dataclass
class CollectionResult:
    """Result of a collection attempt"""
    success: bool
    data_points: List[DataPoint]
    error_message: Optional[str] = None
    collection_time: Optional[datetime] = None
    
    def __post_init__(self):
        if self.collection_time is None:
            self.collection_time = datetime.now(timezone.utc)


class BaseCollector(ABC):
    """Base class for all data collectors"""
    
    def __init__(self, name: str, domain: DataDomain, collection_interval: int = 300):
        self.name = name
        self.domain = domain
        self.collection_interval = collection_interval  # seconds
        self.status = CollectorStatus.INACTIVE
        self.logger = logging.getLogger(f"realize_io.collectors.{name}")
        self.last_collection = None
        self.error_count = 0
        self.max_errors = 5
        self.callbacks: List[Callable] = []
        
    @abstractmethod
    async def collect_data(self) -> CollectionResult:
        """Collect data from this source. Must be implemented by subclasses."""
        pass
    
    @abstractmethod
    async def test_connection(self) -> bool:
        """Test if data source is accessible. Must be implemented by subclasses."""
        pass
        
    async def setup(self) -> bool:
        """Setup collector (authentication, validation, etc.)"""
        try:
            self.logger.info(f"Setting up collector: {self.name}")
            
            # Test connection first
            if not await self.test_connection():
                self.logger.error(f"Connection test failed for {self.name}")
                self.status = CollectorStatus.ERROR
                return False
                
            # Run any collector-specific setup
            setup_success = await self._setup_impl()
            
            if setup_success:
                self.status = CollectorStatus.ACTIVE
                self.logger.info(f"Collector {self.name} setup completed successfully")
            else:
                self.status = CollectorStatus.ERROR
                self.logger.error(f"Collector {self.name} setup failed")
                
            return setup_success
            
        except Exception as e:
            self.logger.error(f"Exception during setup for {self.name}: {e}")
            self.status = CollectorStatus.ERROR
            return False
    
    async def _setup_impl(self) -> bool:
        """Override this for collector-specific setup logic"""
        return True
        
    async def start_collection(self):
        """Start continuous data collection"""
        if self.status != CollectorStatus.ACTIVE:
            self.logger.warning(f"Cannot start collection for {self.name}, status: {self.status}")
            return
            
        self.logger.info(f"Starting collection for {self.name} with interval {self.collection_interval}s")
        
        while self.status == CollectorStatus.ACTIVE:
            try:
                # Collect data
                result = await self.collect_data()
                self.last_collection = result.collection_time
                
                if result.success:
                    self.logger.debug(f"Collected {len(result.data_points)} data points from {self.name}")
                    self.error_count = 0  # Reset error count on success
                    
                    # Notify callbacks
                    for callback in self.callbacks:
                        try:
                            await callback(self.name, result)
                        except Exception as e:
                            self.logger.error(f"Callback error for {self.name}: {e}")
                            
                else:
                    self.error_count += 1
                    self.logger.warning(f"Collection failed for {self.name}: {result.error_message}")
                    
                    # Disable collector if too many errors
                    if self.error_count >= self.max_errors:
                        self.status = CollectorStatus.ERROR
                        self.logger.error(f"Disabling {self.name} due to too many errors")
                        break
                
                # Wait for next collection
                await asyncio.sleep(self.collection_interval)
                
            except asyncio.CancelledError:
                self.logger.info(f"Collection cancelled for {self.name}")
                break
            except Exception as e:
                self.error_count += 1
                self.logger.error(f"Unexpected error in collection loop for {self.name}: {e}")
                
                if self.error_count >= self.max_errors:
                    self.status = CollectorStatus.ERROR
                    break
                    
                await asyncio.sleep(self.collection_interval)
    
    def stop_collection(self):
        """Stop data collection"""
        self.logger.info(f"Stopping collection for {self.name}")
        if self.status == CollectorStatus.ACTIVE:
            self.status = CollectorStatus.INACTIVE
    
    def add_callback(self, callback: Callable):
        """Add callback to be notified of new data"""
        self.callbacks.append(callback)
        
    def remove_callback(self, callback: Callable):
        """Remove callback"""
        if callback in self.callbacks:
            self.callbacks.remove(callback)
    
    def get_status(self) -> Dict[str, Any]:
        """Get collector status information"""
        return {
            'name': self.name,
            'domain': self.domain.value,
            'status': self.status.value,
            'last_collection': self.last_collection.isoformat() if self.last_collection else None,
            'error_count': self.error_count,
            'collection_interval': self.collection_interval
        }
    
    def reset_errors(self):
        """Reset error count and try to reactivate"""
        self.error_count = 0
        if self.status == CollectorStatus.ERROR:
            self.status = CollectorStatus.INACTIVE
            self.logger.info(f"Reset errors for {self.name}, ready for setup")


class MockCollector(BaseCollector):
    """Mock collector for testing purposes"""
    
    def __init__(self, name: str, domain: DataDomain, mock_value: float = 100.0):
        super().__init__(name, domain)
        self.mock_value = mock_value
        
    async def collect_data(self) -> CollectionResult:
        """Generate mock data"""
        try:
            # Simulate API call delay
            await asyncio.sleep(0.1)
            
            # Create mock data point
            data_point = DataPoint(
                timestamp=datetime.now(timezone.utc),
                domain=self.domain,
                source=self.name,
                value=self.mock_value,
                metadata={'mock': True}
            )
            
            return CollectionResult(
                success=True,
                data_points=[data_point]
            )
            
        except Exception as e:
            return CollectionResult(
                success=False,
                data_points=[],
                error_message=str(e)
            )
    
    async def test_connection(self) -> bool:
        """Mock connection test"""
        return True