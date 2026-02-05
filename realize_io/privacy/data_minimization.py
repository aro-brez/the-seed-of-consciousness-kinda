"""
Data Minimization for REALIZE-IO
Implements data minimization principles - collect only what's necessary, store only what's needed
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Any, Union
from datetime import datetime, timedelta
import json
import logging

from .privacy_model import DataClassification, PrivacyLevel

logger = logging.getLogger(__name__)

class DataPurpose(Enum):
    """Specific purposes for data collection"""
    HEALTH_TRACKING = "health_tracking"
    FINANCIAL_ANALYSIS = "financial_analysis"  
    PRODUCTIVITY_OPTIMIZATION = "productivity_optimization"
    SOCIAL_INSIGHTS = "social_insights"
    SYSTEM_OPTIMIZATION = "system_optimization"
    RESEARCH_IMPROVEMENT = "research_improvement"

class RetentionPolicy(Enum):
    """Data retention policies"""
    IMMEDIATE = "immediate"      # Delete immediately after processing
    SHORT_TERM = "short_term"    # 30 days
    MEDIUM_TERM = "medium_term"  # 1 year 
    LONG_TERM = "long_term"      # 5 years
    PERMANENT = "permanent"      # Keep indefinitely (with user consent)

@dataclass
class MinimizationRule:
    """Rule defining what data to collect and how long to keep it"""
    purpose: DataPurpose
    classification: DataClassification
    required_fields: Set[str]
    optional_fields: Set[str] = field(default_factory=set)
    retention_policy: RetentionPolicy = RetentionPolicy.MEDIUM_TERM
    aggregation_allowed: bool = True
    sharing_purpose: Optional[str] = None
    
    def get_retention_days(self) -> Optional[int]:
        """Get retention period in days"""
        if self.retention_policy == RetentionPolicy.IMMEDIATE:
            return 0
        elif self.retention_policy == RetentionPolicy.SHORT_TERM:
            return 30
        elif self.retention_policy == RetentionPolicy.MEDIUM_TERM:
            return 365
        elif self.retention_policy == RetentionPolicy.LONG_TERM:
            return 1825  # 5 years
        else:  # PERMANENT
            return None

class DataMinimizer:
    """Implements data minimization across the REALIZE-IO system"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.minimization_rules: Dict[DataPurpose, List[MinimizationRule]] = {}
        self.field_mappings: Dict[str, str] = {}
        self.collection_stats: Dict[str, int] = {}
        
        # Initialize default rules
        self._load_default_rules()
        
        # Load custom config if provided
        if config_path:
            self._load_config(config_path)
    
    def _load_default_rules(self):
        """Load default data minimization rules"""
        
        # Health tracking rules
        health_rules = [
            MinimizationRule(
                purpose=DataPurpose.HEALTH_TRACKING,
                classification=DataClassification.HEALTH_VITALS,
                required_fields={'timestamp', 'measurement_type', 'value'},
                optional_fields={'confidence', 'source', 'notes'},
                retention_policy=RetentionPolicy.LONG_TERM,
                aggregation_allowed=True
            ),
            MinimizationRule(
                purpose=DataPurpose.HEALTH_TRACKING,
                classification=DataClassification.HEALTH_SYMPTOMS,
                required_fields={'timestamp', 'symptom', 'severity'},
                optional_fields={'description', 'context'},
                retention_policy=RetentionPolicy.MEDIUM_TERM,
                aggregation_allowed=False  # Symptoms are sensitive
            )
        ]
        self.minimization_rules[DataPurpose.HEALTH_TRACKING] = health_rules
        
        # Financial analysis rules
        financial_rules = [
            MinimizationRule(
                purpose=DataPurpose.FINANCIAL_ANALYSIS,
                classification=DataClassification.WEALTH_PERFORMANCE,
                required_fields={'timestamp', 'metric_type', 'value'},
                optional_fields={'benchmark', 'period', 'category'},
                retention_policy=RetentionPolicy.LONG_TERM,
                aggregation_allowed=True
            ),
            MinimizationRule(
                purpose=DataPurpose.FINANCIAL_ANALYSIS,
                classification=DataClassification.WEALTH_POSITIONS,
                required_fields={'timestamp', 'asset_type', 'quantity'},
                optional_fields={'cost_basis', 'allocation_percent'},
                retention_policy=RetentionPolicy.MEDIUM_TERM,
                aggregation_allowed=False  # Positions are sensitive
            )
        ]
        self.minimization_rules[DataPurpose.FINANCIAL_ANALYSIS] = financial_rules
        
        # Productivity optimization rules
        productivity_rules = [
            MinimizationRule(
                purpose=DataPurpose.PRODUCTIVITY_OPTIMIZATION,
                classification=DataClassification.PRODUCTIVITY_METRICS,
                required_fields={'timestamp', 'activity_type', 'duration'},
                optional_fields={'effectiveness_score', 'interruptions', 'mood'},
                retention_policy=RetentionPolicy.MEDIUM_TERM,
                aggregation_allowed=True
            ),
            MinimizationRule(
                purpose=DataPurpose.PRODUCTIVITY_OPTIMIZATION,
                classification=DataClassification.PRODUCTIVITY_CONTENT,
                required_fields={'timestamp', 'content_type'},
                optional_fields={'summary', 'keywords'},
                retention_policy=RetentionPolicy.SHORT_TERM,
                aggregation_allowed=False  # Content is sensitive
            )
        ]
        self.minimization_rules[DataPurpose.PRODUCTIVITY_OPTIMIZATION] = productivity_rules
        
        # Social insights rules
        social_rules = [
            MinimizationRule(
                purpose=DataPurpose.SOCIAL_INSIGHTS,
                classification=DataClassification.SOCIAL_PATTERNS,
                required_fields={'timestamp', 'interaction_type', 'frequency'},
                optional_fields={'quality_score', 'context', 'channel'},
                retention_policy=RetentionPolicy.MEDIUM_TERM,
                aggregation_allowed=True
            ),
            MinimizationRule(
                purpose=DataPurpose.SOCIAL_INSIGHTS,
                classification=DataClassification.SOCIAL_CONTENT,
                required_fields={'timestamp', 'content_type'},
                optional_fields={'sentiment', 'topics'},
                retention_policy=RetentionPolicy.IMMEDIATE,  # Content deleted immediately
                aggregation_allowed=False
            )
        ]
        self.minimization_rules[DataPurpose.SOCIAL_INSIGHTS] = social_rules
    
    def _load_config(self, config_path: str):
        """Load user-specific minimization configuration"""
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
            
            # Update retention policies based on user preferences
            user_retention = config.get('retention_preferences', {})
            for purpose_name, days in user_retention.items():
                try:
                    purpose = DataPurpose(purpose_name)
                    if purpose in self.minimization_rules:
                        for rule in self.minimization_rules[purpose]:
                            if days == 0:
                                rule.retention_policy = RetentionPolicy.IMMEDIATE
                            elif days <= 30:
                                rule.retention_policy = RetentionPolicy.SHORT_TERM
                            elif days <= 365:
                                rule.retention_policy = RetentionPolicy.MEDIUM_TERM
                            else:
                                rule.retention_policy = RetentionPolicy.LONG_TERM
                except ValueError:
                    logger.warning(f"Unknown purpose in config: {purpose_name}")
            
            # Load field restrictions
            field_restrictions = config.get('field_restrictions', {})
            for classification_name, restricted_fields in field_restrictions.items():
                try:
                    classification = DataClassification(classification_name)
                    # Remove restricted fields from optional fields
                    for purpose_rules in self.minimization_rules.values():
                        for rule in purpose_rules:
                            if rule.classification == classification:
                                rule.optional_fields -= set(restricted_fields)
                except ValueError:
                    logger.warning(f"Unknown classification in config: {classification_name}")
                    
        except FileNotFoundError:
            logger.info(f"No minimization config found at {config_path}")
        except Exception as e:
            logger.error(f"Error loading minimization config: {e}")
    
    def minimize_data(self, data: Dict[str, Any], purpose: DataPurpose, classification: DataClassification) -> Dict[str, Any]:
        """Apply data minimization to a data point"""
        rule = self._get_rule(purpose, classification)
        
        if not rule:
            logger.warning(f"No minimization rule found for {purpose.value} + {classification.value}")
            return data
        
        minimized = {}
        
        # Always include required fields
        for field in rule.required_fields:
            if field in data:
                minimized[field] = data[field]
            else:
                logger.warning(f"Required field '{field}' missing from data")
        
        # Include optional fields if present
        for field in rule.optional_fields:
            if field in data:
                minimized[field] = data[field]
        
        # Add metadata about minimization
        minimized['_minimization_applied'] = True
        minimized['_purpose'] = purpose.value
        minimized['_retention_days'] = rule.get_retention_days()
        
        # Track collection statistics
        stats_key = f"{purpose.value}_{classification.value}"
        self.collection_stats[stats_key] = self.collection_stats.get(stats_key, 0) + 1
        
        return minimized
    
    def _get_rule(self, purpose: DataPurpose, classification: DataClassification) -> Optional[MinimizationRule]:
        """Get the applicable minimization rule"""
        if purpose not in self.minimization_rules:
            return None
        
        for rule in self.minimization_rules[purpose]:
            if rule.classification == classification:
                return rule
        
        return None
    
    def should_collect_field(self, field: str, purpose: DataPurpose, classification: DataClassification) -> bool:
        """Check if a specific field should be collected"""
        rule = self._get_rule(purpose, classification)
        
        if not rule:
            return False
        
        return field in rule.required_fields or field in rule.optional_fields
    
    def get_retention_period(self, purpose: DataPurpose, classification: DataClassification) -> Optional[int]:
        """Get retention period in days for specific data"""
        rule = self._get_rule(purpose, classification)
        return rule.get_retention_days() if rule else None
    
    def can_aggregate_data(self, purpose: DataPurpose, classification: DataClassification) -> bool:
        """Check if data can be aggregated for this purpose"""
        rule = self._get_rule(purpose, classification)
        return rule.aggregation_allowed if rule else False
    
    def get_expired_data_keys(self, data_inventory: Dict[str, Dict[str, Any]]) -> List[str]:
        """Identify data that should be deleted based on retention policies"""
        expired_keys = []
        now = datetime.now()
        
        for key, metadata in data_inventory.items():
            if '_retention_days' not in metadata:
                continue
                
            retention_days = metadata['_retention_days']
            if retention_days is None:  # Permanent retention
                continue
                
            created_date = metadata.get('timestamp')
            if isinstance(created_date, str):
                try:
                    created_date = datetime.fromisoformat(created_date)
                except ValueError:
                    continue
            elif not isinstance(created_date, datetime):
                continue
                
            age_days = (now - created_date).days
            
            if age_days > retention_days:
                expired_keys.append(key)
        
        return expired_keys
    
    def create_data_map(self) -> Dict[str, Any]:
        """Create a map of what data is collected for what purposes"""
        data_map = {}
        
        for purpose, rules in self.minimization_rules.items():
            purpose_data = {
                'classifications': [],
                'total_fields': 0,
                'required_fields': 0,
                'retention_periods': set()
            }
            
            for rule in rules:
                classification_info = {
                    'classification': rule.classification.value,
                    'required_fields': list(rule.required_fields),
                    'optional_fields': list(rule.optional_fields),
                    'retention_policy': rule.retention_policy.value,
                    'retention_days': rule.get_retention_days(),
                    'aggregation_allowed': rule.aggregation_allowed
                }
                purpose_data['classifications'].append(classification_info)
                purpose_data['total_fields'] += len(rule.required_fields) + len(rule.optional_fields)
                purpose_data['required_fields'] += len(rule.required_fields)
                purpose_data['retention_periods'].add(rule.retention_policy.value)
            
            purpose_data['retention_periods'] = list(purpose_data['retention_periods'])
            data_map[purpose.value] = purpose_data
        
        return {
            'data_map': data_map,
            'collection_stats': self.collection_stats,
            'minimization_principles': {
                'collect_only_necessary': True,
                'purpose_limitation': True,
                'retention_limits': True,
                'user_control': True
            }
        }
    
    def export_minimization_report(self) -> Dict[str, Any]:
        """Export comprehensive data minimization report"""
        return {
            'report_timestamp': datetime.now().isoformat(),
            'minimization_version': '1.0',
            'active_purposes': list(self.minimization_rules.keys()),
            'data_map': self.create_data_map(),
            'summary': {
                'total_purposes': len(self.minimization_rules),
                'total_rules': sum(len(rules) for rules in self.minimization_rules.values()),
                'immediate_deletion_rules': sum(
                    1 for rules in self.minimization_rules.values() 
                    for rule in rules 
                    if rule.retention_policy == RetentionPolicy.IMMEDIATE
                ),
                'permanent_retention_rules': sum(
                    1 for rules in self.minimization_rules.values() 
                    for rule in rules 
                    if rule.retention_policy == RetentionPolicy.PERMANENT
                )
            }
        }