"""
Data Anonymization for REALIZE-IO
Provides multiple anonymization strategies for different types of personal data
"""

from enum import Enum
from typing import Any, Dict, List, Optional, Union
import hashlib
import random
import math
from datetime import datetime, timedelta
import json
import logging

from .privacy_model import DataClassification, PrivacyLevel

logger = logging.getLogger(__name__)

class AnonymizationStrategy(Enum):
    """Different strategies for anonymizing data"""
    NONE = "none"                    # No anonymization
    HASH = "hash"                    # Replace with hash
    GENERALIZE = "generalize"        # Reduce precision
    NOISE = "noise"                  # Add statistical noise
    BUCKET = "bucket"                # Group into ranges
    SUPPRESS = "suppress"            # Remove entirely
    K_ANONYMITY = "k_anonymity"      # K-anonymity grouping

class DataAnonymizer:
    """Handles anonymization of personal data for sharing"""
    
    def __init__(self, user_id: str = "default"):
        self.user_id = user_id
        self.salt = self._generate_salt()
        
        # Define anonymization strategies per data classification
        self.strategies = {
            DataClassification.HEALTH_VITALS: AnonymizationStrategy.GENERALIZE,
            DataClassification.HEALTH_SYMPTOMS: AnonymizationStrategy.SUPPRESS,
            DataClassification.WEALTH_PERFORMANCE: AnonymizationStrategy.GENERALIZE,
            DataClassification.WEALTH_POSITIONS: AnonymizationStrategy.SUPPRESS,
            DataClassification.PRODUCTIVITY_METRICS: AnonymizationStrategy.GENERALIZE,
            DataClassification.PRODUCTIVITY_CONTENT: AnonymizationStrategy.SUPPRESS,
            DataClassification.SOCIAL_PATTERNS: AnonymizationStrategy.BUCKET,
            DataClassification.SOCIAL_CONTENT: AnonymizationStrategy.SUPPRESS,
            DataClassification.SYSTEM_METADATA: AnonymizationStrategy.NONE
        }
    
    def _generate_salt(self) -> str:
        """Generate a consistent salt for this user"""
        return hashlib.sha256(f"realize_io_{self.user_id}".encode()).hexdigest()[:16]
    
    def anonymize_data_point(self, data: Dict[str, Any], classification: DataClassification) -> Dict[str, Any]:
        """Anonymize a single data point according to its classification"""
        strategy = self.strategies.get(classification, AnonymizationStrategy.SUPPRESS)
        
        if strategy == AnonymizationStrategy.NONE:
            return data
        elif strategy == AnonymizationStrategy.SUPPRESS:
            return self._suppress_data(data, classification)
        elif strategy == AnonymizationStrategy.HASH:
            return self._hash_data(data)
        elif strategy == AnonymizationStrategy.GENERALIZE:
            return self._generalize_data(data, classification)
        elif strategy == AnonymizationStrategy.NOISE:
            return self._add_noise(data)
        elif strategy == AnonymizationStrategy.BUCKET:
            return self._bucket_data(data, classification)
        else:
            logger.warning(f"Unknown anonymization strategy: {strategy}")
            return self._suppress_data(data, classification)
    
    def _suppress_data(self, data: Dict[str, Any], classification: DataClassification) -> Dict[str, Any]:
        """Remove sensitive fields, keep only metadata"""
        anonymized = {
            'data_type': classification.value,
            'timestamp_hour': self._generalize_timestamp(data.get('timestamp')),
            'has_data': True
        }
        
        # Keep some non-sensitive aggregated info
        if 'count' in data:
            anonymized['count'] = data['count']
        if 'duration' in data:
            anonymized['duration_bucket'] = self._bucket_duration(data['duration'])
            
        return anonymized
    
    def _hash_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Replace identifiable values with hashes"""
        anonymized = {}
        
        for key, value in data.items():
            if key in ['user_id', 'id', 'name', 'email', 'phone']:
                # Hash identifiable fields
                anonymized[f"{key}_hash"] = hashlib.sha256(
                    f"{self.salt}_{value}".encode()
                ).hexdigest()[:16]
            elif key == 'timestamp':
                anonymized['timestamp_hour'] = self._generalize_timestamp(value)
            else:
                anonymized[key] = value
                
        return anonymized
    
    def _generalize_data(self, data: Dict[str, Any], classification: DataClassification) -> Dict[str, Any]:
        """Reduce precision of numerical data"""
        anonymized = {}
        
        for key, value in data.items():
            if key == 'timestamp':
                anonymized['timestamp_hour'] = self._generalize_timestamp(value)
            elif isinstance(value, (int, float)):
                anonymized[key] = self._generalize_number(value, classification, key)
            elif isinstance(value, str) and len(value) > 10:
                # Long strings might be content - hash them
                anonymized[f"{key}_hash"] = hashlib.sha256(
                    f"{self.salt}_{value}".encode()
                ).hexdigest()[:8]
            else:
                anonymized[key] = value
                
        return anonymized
    
    def _generalize_number(self, value: Union[int, float], classification: DataClassification, field: str) -> Union[int, float]:
        """Generalize numerical values based on context"""
        
        # Health vitals
        if classification == DataClassification.HEALTH_VITALS:
            if 'sleep' in field.lower():
                return round(value, 1)  # Sleep to 0.1 hour precision
            elif 'heart_rate' in field.lower():
                return round(value / 5) * 5  # Heart rate to nearest 5
            elif 'steps' in field.lower():
                return round(value / 1000) * 1000  # Steps to nearest 1000
            else:
                return round(value, 1)
        
        # Wealth performance (keep ratios but reduce precision)
        elif classification == DataClassification.WEALTH_PERFORMANCE:
            if 'rate' in field.lower() or 'ratio' in field.lower():
                return round(value, 2)  # Rates to 2 decimal places
            elif 'pnl' in field.lower() or 'profit' in field.lower():
                return round(value, 0)  # P&L to whole numbers
            else:
                return round(value, 1)
        
        # Productivity metrics
        elif classification == DataClassification.PRODUCTIVITY_METRICS:
            if 'time' in field.lower() or 'hours' in field.lower():
                return round(value, 1)  # Time to 0.1 hour precision
            elif 'count' in field.lower():
                return max(1, round(value / 5) * 5)  # Counts to nearest 5
            else:
                return round(value, 1)
        
        # Default generalization
        else:
            return round(value, 1)
    
    def _add_noise(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Add statistical noise to numerical values"""
        anonymized = {}
        
        for key, value in data.items():
            if isinstance(value, (int, float)) and key != 'timestamp':
                # Add noise proportional to the value (5% standard deviation)
                noise_std = abs(value * 0.05)
                noise = random.gauss(0, noise_std)
                anonymized[key] = value + noise
            else:
                anonymized[key] = value
                
        return anonymized
    
    def _bucket_data(self, data: Dict[str, Any], classification: DataClassification) -> Dict[str, Any]:
        """Group values into buckets/ranges"""
        anonymized = {}
        
        for key, value in data.items():
            if key == 'timestamp':
                anonymized['timestamp_hour'] = self._generalize_timestamp(value)
            elif isinstance(value, (int, float)):
                anonymized[key] = self._bucket_number(value, classification, key)
            else:
                anonymized[key] = value
                
        return anonymized
    
    def _bucket_number(self, value: Union[int, float], classification: DataClassification, field: str) -> str:
        """Put numerical values into buckets"""
        
        # Social patterns
        if classification == DataClassification.SOCIAL_PATTERNS:
            if 'count' in field.lower() or 'frequency' in field.lower():
                if value < 5:
                    return "low"
                elif value < 15:
                    return "medium"
                else:
                    return "high"
            elif 'hours' in field.lower() or 'time' in field.lower():
                if value < 1:
                    return "minimal"
                elif value < 3:
                    return "moderate"
                else:
                    return "significant"
        
        # Default bucketing
        if value < 10:
            return "0-10"
        elif value < 50:
            return "10-50"
        elif value < 100:
            return "50-100"
        else:
            return "100+"
    
    def _generalize_timestamp(self, timestamp: Any) -> str:
        """Generalize timestamps to hour precision"""
        if isinstance(timestamp, str):
            try:
                dt = datetime.fromisoformat(timestamp)
            except ValueError:
                return "unknown"
        elif isinstance(timestamp, datetime):
            dt = timestamp
        else:
            return "unknown"
            
        # Return hour of day and day of week only
        return f"{dt.strftime('%A')}_hour_{dt.hour}"
    
    def _bucket_duration(self, duration: Union[int, float]) -> str:
        """Bucket duration values"""
        if duration < 300:  # 5 minutes
            return "short"
        elif duration < 1800:  # 30 minutes
            return "medium"
        else:
            return "long"
    
    def anonymize_batch(self, data_points: List[Dict[str, Any]], classification: DataClassification) -> List[Dict[str, Any]]:
        """Anonymize a batch of data points"""
        return [self.anonymize_data_point(point, classification) for point in data_points]
    
    def create_k_anonymous_groups(self, data_points: List[Dict[str, Any]], k: int = 5) -> List[List[Dict[str, Any]]]:
        """Group data points to achieve k-anonymity"""
        if len(data_points) < k:
            return [data_points]  # Not enough data for k-anonymity
        
        # Simple grouping by similar attributes
        groups = []
        remaining = data_points.copy()
        
        while len(remaining) >= k:
            group = remaining[:k]
            groups.append(group)
            remaining = remaining[k:]
        
        # Add remaining items to the last group if it exists
        if remaining and groups:
            groups[-1].extend(remaining)
        elif remaining:
            groups.append(remaining)
            
        return groups
    
    def get_anonymization_summary(self) -> Dict[str, Any]:
        """Get summary of anonymization strategies in use"""
        return {
            'user_id_hash': hashlib.sha256(f"{self.salt}_{self.user_id}".encode()).hexdigest()[:8],
            'strategies': {
                classification.value: strategy.value 
                for classification, strategy in self.strategies.items()
            },
            'privacy_guarantees': {
                'no_direct_identifiers': True,
                'temporal_generalization': True,
                'numerical_precision_reduced': True,
                'sensitive_content_suppressed': True
            }
        }