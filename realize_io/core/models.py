"""Data models for REALIZE-IO trajectories"""

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Union
from enum import Enum
import json
import uuid


class DataDomain(Enum):
    """Main data domains for personal trajectories"""
    HEALTH = "health"
    WEALTH = "wealth" 
    SOCIAL = "social"
    PERFORMANCE = "performance"


class DataQuality(Enum):
    """Data quality indicators"""
    HIGH = "high"      # Verified, accurate data
    MEDIUM = "medium"  # Estimated or derived data
    LOW = "low"        # Interpolated or guessed data
    UNKNOWN = "unknown"


@dataclass
class DataPoint:
    """Base data point for all trajectory data"""
    timestamp: datetime
    domain: DataDomain
    source: str
    value: Union[float, int, str, Dict[str, Any]]
    quality: DataQuality = DataQuality.MEDIUM
    metadata: Dict[str, Any] = field(default_factory=dict)
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    
    def __post_init__(self):
        # Ensure timezone awareness
        if self.timestamp.tzinfo is None:
            self.timestamp = self.timestamp.replace(tzinfo=timezone.utc)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        result = asdict(self)
        result['timestamp'] = self.timestamp.isoformat()
        result['domain'] = self.domain.value
        result['quality'] = self.quality.value
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DataPoint':
        """Create from dictionary"""
        data = data.copy()
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        data['domain'] = DataDomain(data['domain'])
        data['quality'] = DataQuality(data['quality'])
        return cls(**data)


@dataclass
class HealthData(DataPoint):
    """Health-specific data point"""
    domain: DataDomain = field(default=DataDomain.HEALTH, init=False)
    
    # Common health metrics
    steps: Optional[int] = None
    sleep_hours: Optional[float] = None
    heart_rate: Optional[int] = None
    weight: Optional[float] = None
    calories: Optional[int] = None
    exercise_minutes: Optional[int] = None
    mood_score: Optional[float] = None  # 1-10 scale
    
    def __post_init__(self):
        super().__post_init__()
        # Pack specific fields into value if not already set
        if isinstance(self.value, (int, float, str)):
            # Keep existing value
            pass
        else:
            self.value = {
                k: v for k, v in {
                    'steps': self.steps,
                    'sleep_hours': self.sleep_hours, 
                    'heart_rate': self.heart_rate,
                    'weight': self.weight,
                    'calories': self.calories,
                    'exercise_minutes': self.exercise_minutes,
                    'mood_score': self.mood_score
                }.items() if v is not None
            }


@dataclass
class WealthData(DataPoint):
    """Wealth-specific data point"""
    domain: DataDomain = field(default=DataDomain.WEALTH, init=False)
    
    # Financial metrics
    net_worth: Optional[float] = None
    income: Optional[float] = None
    expenses: Optional[float] = None
    savings_rate: Optional[float] = None
    investment_returns: Optional[float] = None
    debt_total: Optional[float] = None
    
    def __post_init__(self):
        super().__post_init__()
        if isinstance(self.value, (int, float, str)):
            pass
        else:
            self.value = {
                k: v for k, v in {
                    'net_worth': self.net_worth,
                    'income': self.income,
                    'expenses': self.expenses,
                    'savings_rate': self.savings_rate,
                    'investment_returns': self.investment_returns,
                    'debt_total': self.debt_total
                }.items() if v is not None
            }


@dataclass
class SocialData(DataPoint):
    """Social-specific data point"""
    domain: DataDomain = field(default=DataDomain.SOCIAL, init=False)
    
    # Social metrics
    interactions_count: Optional[int] = None
    relationship_quality: Optional[float] = None  # 1-10 scale
    social_time_hours: Optional[float] = None
    network_size: Optional[int] = None
    support_level: Optional[float] = None  # 1-10 scale
    
    def __post_init__(self):
        super().__post_init__()
        if isinstance(self.value, (int, float, str)):
            pass
        else:
            self.value = {
                k: v for k, v in {
                    'interactions_count': self.interactions_count,
                    'relationship_quality': self.relationship_quality,
                    'social_time_hours': self.social_time_hours,
                    'network_size': self.network_size,
                    'support_level': self.support_level
                }.items() if v is not None
            }


@dataclass
class PerformanceData(DataPoint):
    """Performance-specific data point"""
    domain: DataDomain = field(default=DataDomain.PERFORMANCE, init=False)
    
    # Performance metrics
    productivity_score: Optional[float] = None  # 1-10 scale
    focus_hours: Optional[float] = None
    tasks_completed: Optional[int] = None
    learning_time: Optional[float] = None
    skill_level: Optional[float] = None  # 1-10 scale
    challenge_level: Optional[float] = None  # 1-10 scale
    
    def __post_init__(self):
        super().__post_init__()
        if isinstance(self.value, (int, float, str)):
            pass
        else:
            self.value = {
                k: v for k, v in {
                    'productivity_score': self.productivity_score,
                    'focus_hours': self.focus_hours,
                    'tasks_completed': self.tasks_completed,
                    'learning_time': self.learning_time,
                    'skill_level': self.skill_level,
                    'challenge_level': self.challenge_level
                }.items() if v is not None
            }


@dataclass
class TrajectoryPrediction:
    """Prediction for future trajectory"""
    domain: DataDomain
    prediction_horizon: int  # days into future
    predicted_value: float
    confidence_interval: tuple  # (lower, upper)
    confidence_score: float  # 0-1
    contributing_factors: List[str]
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    algorithm_version: str = "1.0"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        result = asdict(self)
        result['domain'] = self.domain.value
        result['created_at'] = self.created_at.isoformat()
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TrajectoryPrediction':
        """Create from dictionary"""
        data = data.copy()
        data['domain'] = DataDomain(data['domain'])
        data['created_at'] = datetime.fromisoformat(data['created_at'])
        return cls(**data)


@dataclass
class PersonalState:
    """Complete personal state snapshot"""
    timestamp: datetime
    health_score: Optional[float] = None
    wealth_score: Optional[float] = None
    social_score: Optional[float] = None
    performance_score: Optional[float] = None
    overall_trajectory: Optional[float] = None
    predictions: List[TrajectoryPrediction] = field(default_factory=list)
    insights: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        result = asdict(self)
        result['timestamp'] = self.timestamp.isoformat()
        result['predictions'] = [p.to_dict() for p in self.predictions]
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PersonalState':
        """Create from dictionary"""
        data = data.copy()
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        data['predictions'] = [TrajectoryPrediction.from_dict(p) for p in data.get('predictions', [])]
        return cls(**data)


def create_data_point(domain: DataDomain, source: str, value: Any, **kwargs) -> DataPoint:
    """Factory function to create appropriate data point type"""
    base_kwargs = {
        'timestamp': kwargs.get('timestamp', datetime.now(timezone.utc)),
        'source': source,
        'value': value,
        'quality': kwargs.get('quality', DataQuality.MEDIUM),
        'metadata': kwargs.get('metadata', {})
    }
    
    if domain == DataDomain.HEALTH:
        return HealthData(**base_kwargs, **kwargs)
    elif domain == DataDomain.WEALTH:
        return WealthData(**base_kwargs, **kwargs)
    elif domain == DataDomain.SOCIAL:
        return SocialData(**base_kwargs, **kwargs)
    elif domain == DataDomain.PERFORMANCE:
        return PerformanceData(**base_kwargs, **kwargs)
    else:
        return DataPoint(domain=domain, **base_kwargs)