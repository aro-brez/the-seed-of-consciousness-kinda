"""
Privacy Model for REALIZE-IO
Core privacy framework defining data classification, access levels, and protection mechanisms
"""

from enum import Enum, IntEnum
from dataclasses import dataclass
from typing import Dict, List, Optional, Set, Any
from datetime import datetime, timedelta
import json
import logging

logger = logging.getLogger(__name__)

class PrivacyLevel(IntEnum):
    """Privacy levels in order of increasing protection"""
    PUBLIC = 1      # Anonymized aggregated data shareable publicly
    COLLECTIVE = 2  # Shareable within 8OWLS collective (anonymized)
    PERSONAL = 3    # Local processing only, no sharing
    SENSITIVE = 4   # Encrypted at rest, special handling required
    RESTRICTED = 5  # Highest protection, minimal processing

class DataClassification(Enum):
    """Data classification categories"""
    HEALTH_VITALS = "health_vitals"           # Heart rate, sleep, steps
    HEALTH_SYMPTOMS = "health_symptoms"       # Symptoms, conditions, medical
    WEALTH_PERFORMANCE = "wealth_performance" # Returns, profit/loss ratios
    WEALTH_POSITIONS = "wealth_positions"     # Specific holdings, amounts
    PRODUCTIVITY_METRICS = "productivity_metrics" # Focus time, completion rates
    PRODUCTIVITY_CONTENT = "productivity_content" # Actual work content
    SOCIAL_PATTERNS = "social_patterns"       # Interaction frequency, network size
    SOCIAL_CONTENT = "social_content"         # Messages, conversations
    SYSTEM_METADATA = "system_metadata"       # Timestamps, version info

# Default privacy levels for each data classification
DEFAULT_CLASSIFICATIONS = {
    DataClassification.HEALTH_VITALS: PrivacyLevel.PERSONAL,
    DataClassification.HEALTH_SYMPTOMS: PrivacyLevel.SENSITIVE,
    DataClassification.WEALTH_PERFORMANCE: PrivacyLevel.COLLECTIVE,
    DataClassification.WEALTH_POSITIONS: PrivacyLevel.RESTRICTED,
    DataClassification.PRODUCTIVITY_METRICS: PrivacyLevel.COLLECTIVE,
    DataClassification.PRODUCTIVITY_CONTENT: PrivacyLevel.SENSITIVE,
    DataClassification.SOCIAL_PATTERNS: PrivacyLevel.PERSONAL,
    DataClassification.SOCIAL_CONTENT: PrivacyLevel.RESTRICTED,
    DataClassification.SYSTEM_METADATA: PrivacyLevel.PUBLIC
}

@dataclass
class PrivacyRule:
    """A privacy rule defining how data should be handled"""
    classification: DataClassification
    privacy_level: PrivacyLevel
    retention_days: Optional[int] = None
    anonymization_required: bool = True
    encryption_required: bool = True
    sharing_allowed: bool = False
    logging_allowed: bool = True
    
    def allows_operation(self, operation: str, context: Dict[str, Any] = None) -> bool:
        """Check if an operation is allowed under this privacy rule"""
        context = context or {}
        
        if operation == "share":
            return self.sharing_allowed and self.privacy_level <= PrivacyLevel.COLLECTIVE
        elif operation == "log":
            return self.logging_allowed and self.privacy_level <= PrivacyLevel.PERSONAL
        elif operation == "process":
            return True  # All data can be processed locally
        elif operation == "export":
            return True  # User owns their data
        elif operation == "analyze":
            return self.privacy_level <= PrivacyLevel.PERSONAL
        else:
            return False

@dataclass
class DataPoint:
    """A single data point with privacy metadata"""
    id: str
    value: Any
    classification: DataClassification
    timestamp: datetime
    source: str
    metadata: Dict[str, Any]
    
    @property
    def privacy_level(self) -> PrivacyLevel:
        """Get the privacy level for this data point"""
        return DEFAULT_CLASSIFICATIONS.get(self.classification, PrivacyLevel.SENSITIVE)
    
    @property
    def privacy_rule(self) -> PrivacyRule:
        """Get the privacy rule that applies to this data point"""
        return PrivacyRule(
            classification=self.classification,
            privacy_level=self.privacy_level,
            anonymization_required=self.privacy_level >= PrivacyLevel.PERSONAL,
            encryption_required=self.privacy_level >= PrivacyLevel.PERSONAL,
            sharing_allowed=self.privacy_level <= PrivacyLevel.COLLECTIVE,
            logging_allowed=self.privacy_level <= PrivacyLevel.PERSONAL
        )

class PrivacyModel:
    """Central privacy model for REALIZE-IO"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.rules: Dict[DataClassification, PrivacyRule] = {}
        self.user_overrides: Dict[str, PrivacyLevel] = {}
        self.audit_trail: List[Dict[str, Any]] = []
        
        # Load default rules
        self._load_default_rules()
        
        # Load user configuration if available
        if config_path:
            self._load_user_config(config_path)
    
    def _load_default_rules(self):
        """Load default privacy rules"""
        for classification, level in DEFAULT_CLASSIFICATIONS.items():
            self.rules[classification] = PrivacyRule(
                classification=classification,
                privacy_level=level,
                retention_days=365,  # 1 year default retention
                anonymization_required=level >= PrivacyLevel.PERSONAL,
                encryption_required=level >= PrivacyLevel.PERSONAL,
                sharing_allowed=level <= PrivacyLevel.COLLECTIVE,
                logging_allowed=level <= PrivacyLevel.PERSONAL
            )
    
    def _load_user_config(self, config_path: str):
        """Load user privacy configuration overrides"""
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
                
            for class_name, level_name in config.get('privacy_overrides', {}).items():
                try:
                    classification = DataClassification(class_name)
                    privacy_level = PrivacyLevel[level_name.upper()]
                    self.user_overrides[classification.value] = privacy_level
                    
                    # Update the rule
                    if classification in self.rules:
                        self.rules[classification].privacy_level = privacy_level
                        self.rules[classification].sharing_allowed = privacy_level <= PrivacyLevel.COLLECTIVE
                        self.rules[classification].encryption_required = privacy_level >= PrivacyLevel.PERSONAL
                        
                except (ValueError, KeyError) as e:
                    logger.warning(f"Invalid privacy override: {class_name}={level_name}, {e}")
                    
        except FileNotFoundError:
            logger.info(f"No privacy config found at {config_path}, using defaults")
        except Exception as e:
            logger.error(f"Error loading privacy config: {e}")
    
    def get_privacy_rule(self, classification: DataClassification) -> PrivacyRule:
        """Get privacy rule for a data classification"""
        return self.rules.get(classification, PrivacyRule(
            classification=classification,
            privacy_level=PrivacyLevel.SENSITIVE,
            anonymization_required=True,
            encryption_required=True,
            sharing_allowed=False
        ))
    
    def can_operation(self, data_point: DataPoint, operation: str, context: Dict[str, Any] = None) -> bool:
        """Check if an operation is allowed on a data point"""
        rule = self.get_privacy_rule(data_point.classification)
        allowed = rule.allows_operation(operation, context)
        
        # Log the access attempt
        self._audit_log(data_point, operation, allowed, context)
        
        return allowed
    
    def classify_data(self, data: Dict[str, Any], source: str) -> DataClassification:
        """Automatically classify data based on content and source"""
        
        # Check source patterns
        if source.startswith('apple_health'):
            if any(key in data for key in ['heart_rate', 'steps', 'sleep_hours']):
                return DataClassification.HEALTH_VITALS
            else:
                return DataClassification.HEALTH_SYMPTOMS
                
        elif source.startswith('joule') or 'trading' in source:
            if any(key in data for key in ['win_rate', 'profit_factor', 'daily_pnl']):
                return DataClassification.WEALTH_PERFORMANCE
            else:
                return DataClassification.WEALTH_POSITIONS
                
        elif source.startswith('nats') or 'productivity' in source:
            if any(key in data for key in ['focus_time', 'completion_rate']):
                return DataClassification.PRODUCTIVITY_METRICS
            else:
                return DataClassification.PRODUCTIVITY_CONTENT
                
        elif 'social' in source or 'communication' in source:
            if any(key in data for key in ['interaction_count', 'network_size']):
                return DataClassification.SOCIAL_PATTERNS
            else:
                return DataClassification.SOCIAL_CONTENT
        
        # Default to system metadata
        return DataClassification.SYSTEM_METADATA
    
    def get_sharing_policy(self) -> Dict[str, Any]:
        """Get current sharing policy summary"""
        shareable_categories = []
        local_only_categories = []
        
        for classification, rule in self.rules.items():
            if rule.sharing_allowed:
                shareable_categories.append(classification.value)
            else:
                local_only_categories.append(classification.value)
        
        return {
            'last_updated': datetime.now().isoformat(),
            'shareable_anonymized': shareable_categories,
            'local_only': local_only_categories,
            'user_controls': 'full',
            'data_portability': 'complete',
            'deletion_rights': 'immediate'
        }
    
    def _audit_log(self, data_point: DataPoint, operation: str, allowed: bool, context: Dict[str, Any] = None):
        """Log privacy-related operations for audit trail"""
        audit_entry = {
            'timestamp': datetime.now().isoformat(),
            'data_classification': data_point.classification.value,
            'operation': operation,
            'allowed': allowed,
            'privacy_level': data_point.privacy_level.name,
            'context_type': type(context).__name__ if context else None
        }
        
        self.audit_trail.append(audit_entry)
        
        # Keep only last 1000 audit entries
        if len(self.audit_trail) > 1000:
            self.audit_trail = self.audit_trail[-1000:]
    
    def export_privacy_report(self) -> Dict[str, Any]:
        """Export comprehensive privacy report for user review"""
        return {
            'model_version': '1.0',
            'generated_at': datetime.now().isoformat(),
            'privacy_rules': {
                classification.value: {
                    'privacy_level': rule.privacy_level.name,
                    'sharing_allowed': rule.sharing_allowed,
                    'encryption_required': rule.encryption_required,
                    'retention_days': rule.retention_days
                }
                for classification, rule in self.rules.items()
            },
            'user_overrides': self.user_overrides,
            'recent_audit_entries': self.audit_trail[-100:] if self.audit_trail else [],
            'sharing_summary': self.get_sharing_policy()
        }