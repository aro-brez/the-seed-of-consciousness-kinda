"""
Consent Management for REALIZE-IO
Manages user consent for data collection, processing, and sharing
"""

from enum import Enum
from dataclasses import dataclass
from typing import Dict, List, Optional, Set
from datetime import datetime, timedelta
import json
import logging

from .privacy_model import DataClassification, PrivacyLevel

logger = logging.getLogger(__name__)

class ConsentType(Enum):
    """Types of consent that can be granted or revoked"""
    DATA_COLLECTION = "data_collection"
    LOCAL_PROCESSING = "local_processing"
    AGGREGATED_SHARING = "aggregated_sharing"
    ANONYMOUS_RESEARCH = "anonymous_research"
    COLLECTIVE_INSIGHTS = "collective_insights"
    SYSTEM_OPTIMIZATION = "system_optimization"
    FEATURE_IMPROVEMENTS = "feature_improvements"

@dataclass
class ConsentRecord:
    """A single consent record"""
    consent_type: ConsentType
    data_classification: Optional[DataClassification]
    granted: bool
    timestamp: datetime
    expires: Optional[datetime] = None
    context: Optional[str] = None
    version: str = "1.0"
    
    @property
    def is_valid(self) -> bool:
        """Check if consent is still valid"""
        if not self.granted:
            return False
        if self.expires and datetime.now() > self.expires:
            return False
        return True

class ConsentManager:
    """Manages all consent-related operations"""
    
    def __init__(self, user_id: str, storage_path: Optional[str] = None):
        self.user_id = user_id
        self.storage_path = storage_path or f"consent_{user_id}.json"
        self.consents: Dict[str, ConsentRecord] = {}
        self.consent_history: List[ConsentRecord] = []
        
        # Load existing consents
        self._load_consents()
        
        # Set up default consents (essential operations)
        self._initialize_default_consents()
    
    def _load_consents(self):
        """Load existing consent records from storage"""
        try:
            with open(self.storage_path, 'r') as f:
                data = json.load(f)
                
            for key, consent_data in data.get('consents', {}).items():
                consent = ConsentRecord(
                    consent_type=ConsentType(consent_data['consent_type']),
                    data_classification=DataClassification(consent_data['data_classification']) 
                        if consent_data.get('data_classification') else None,
                    granted=consent_data['granted'],
                    timestamp=datetime.fromisoformat(consent_data['timestamp']),
                    expires=datetime.fromisoformat(consent_data['expires']) 
                        if consent_data.get('expires') else None,
                    context=consent_data.get('context'),
                    version=consent_data.get('version', '1.0')
                )
                self.consents[key] = consent
                
            # Load history
            for consent_data in data.get('history', []):
                consent = ConsentRecord(
                    consent_type=ConsentType(consent_data['consent_type']),
                    data_classification=DataClassification(consent_data['data_classification']) 
                        if consent_data.get('data_classification') else None,
                    granted=consent_data['granted'],
                    timestamp=datetime.fromisoformat(consent_data['timestamp']),
                    expires=datetime.fromisoformat(consent_data['expires']) 
                        if consent_data.get('expires') else None,
                    context=consent_data.get('context'),
                    version=consent_data.get('version', '1.0')
                )
                self.consent_history.append(consent)
                
        except FileNotFoundError:
            logger.info(f"No existing consent file found at {self.storage_path}")
        except Exception as e:
            logger.error(f"Error loading consents: {e}")
    
    def _save_consents(self):
        """Save current consents to storage"""
        try:
            data = {
                'user_id': self.user_id,
                'last_updated': datetime.now().isoformat(),
                'consents': {
                    key: {
                        'consent_type': consent.consent_type.value,
                        'data_classification': consent.data_classification.value if consent.data_classification else None,
                        'granted': consent.granted,
                        'timestamp': consent.timestamp.isoformat(),
                        'expires': consent.expires.isoformat() if consent.expires else None,
                        'context': consent.context,
                        'version': consent.version
                    }
                    for key, consent in self.consents.items()
                },
                'history': [
                    {
                        'consent_type': consent.consent_type.value,
                        'data_classification': consent.data_classification.value if consent.data_classification else None,
                        'granted': consent.granted,
                        'timestamp': consent.timestamp.isoformat(),
                        'expires': consent.expires.isoformat() if consent.expires else None,
                        'context': consent.context,
                        'version': consent.version
                    }
                    for consent in self.consent_history[-100:]  # Keep last 100 history items
                ]
            }
            
            with open(self.storage_path, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            logger.error(f"Error saving consents: {e}")
    
    def _initialize_default_consents(self):
        """Set up essential default consents"""
        essential_consents = [
            (ConsentType.DATA_COLLECTION, None, "Essential for app functionality"),
            (ConsentType.LOCAL_PROCESSING, None, "Required for trajectory analysis"),
            (ConsentType.SYSTEM_OPTIMIZATION, None, "Improves performance and reliability")
        ]
        
        for consent_type, classification, context in essential_consents:
            key = self._consent_key(consent_type, classification)
            if key not in self.consents:
                self.grant_consent(consent_type, classification, context=context)
    
    def _consent_key(self, consent_type: ConsentType, classification: Optional[DataClassification] = None) -> str:
        """Generate a unique key for a consent record"""
        if classification:
            return f"{consent_type.value}_{classification.value}"
        return consent_type.value
    
    def grant_consent(self, 
                     consent_type: ConsentType, 
                     classification: Optional[DataClassification] = None,
                     expires: Optional[datetime] = None,
                     context: Optional[str] = None) -> bool:
        """Grant consent for a specific type and classification"""
        try:
            key = self._consent_key(consent_type, classification)
            
            # Check if consent already exists and update it
            old_consent = self.consents.get(key)
            if old_consent:
                self.consent_history.append(old_consent)
            
            consent = ConsentRecord(
                consent_type=consent_type,
                data_classification=classification,
                granted=True,
                timestamp=datetime.now(),
                expires=expires,
                context=context
            )
            
            self.consents[key] = consent
            self._save_consents()
            
            logger.info(f"Granted consent: {consent_type.value} for {classification.value if classification else 'all data'}")
            return True
            
        except Exception as e:
            logger.error(f"Error granting consent: {e}")
            return False
    
    def revoke_consent(self, 
                      consent_type: ConsentType, 
                      classification: Optional[DataClassification] = None,
                      context: Optional[str] = None) -> bool:
        """Revoke consent for a specific type and classification"""
        try:
            key = self._consent_key(consent_type, classification)
            
            if key not in self.consents:
                logger.warning(f"No consent found to revoke: {key}")
                return False
            
            # Move current consent to history
            old_consent = self.consents[key]
            self.consent_history.append(old_consent)
            
            # Create revocation record
            revocation = ConsentRecord(
                consent_type=consent_type,
                data_classification=classification,
                granted=False,
                timestamp=datetime.now(),
                context=context or "User revoked consent"
            )
            
            self.consents[key] = revocation
            self._save_consents()
            
            logger.info(f"Revoked consent: {consent_type.value} for {classification.value if classification else 'all data'}")
            return True
            
        except Exception as e:
            logger.error(f"Error revoking consent: {e}")
            return False
    
    def has_consent(self, 
                   consent_type: ConsentType, 
                   classification: Optional[DataClassification] = None) -> bool:
        """Check if consent is granted and valid"""
        key = self._consent_key(consent_type, classification)
        
        consent = self.consents.get(key)
        if not consent:
            return False
            
        return consent.is_valid
    
    def get_consents_for_classification(self, classification: DataClassification) -> List[ConsentRecord]:
        """Get all consents for a specific data classification"""
        relevant_consents = []
        
        for consent in self.consents.values():
            if consent.data_classification == classification or consent.data_classification is None:
                relevant_consents.append(consent)
                
        return relevant_consents
    
    def get_sharing_permissions(self) -> Dict[str, bool]:
        """Get current sharing permissions"""
        return {
            'aggregated_sharing': self.has_consent(ConsentType.AGGREGATED_SHARING),
            'anonymous_research': self.has_consent(ConsentType.ANONYMOUS_RESEARCH),
            'collective_insights': self.has_consent(ConsentType.COLLECTIVE_INSIGHTS),
            'feature_improvements': self.has_consent(ConsentType.FEATURE_IMPROVEMENTS)
        }
    
    def can_collect_data(self, classification: DataClassification) -> bool:
        """Check if data collection is allowed for a classification"""
        return self.has_consent(ConsentType.DATA_COLLECTION, classification) or \
               self.has_consent(ConsentType.DATA_COLLECTION, None)
    
    def can_process_data(self, classification: DataClassification) -> bool:
        """Check if data processing is allowed for a classification"""
        return self.has_consent(ConsentType.LOCAL_PROCESSING, classification) or \
               self.has_consent(ConsentType.LOCAL_PROCESSING, None)
    
    def can_share_data(self, classification: DataClassification, sharing_type: ConsentType) -> bool:
        """Check if data sharing is allowed"""
        if sharing_type not in [ConsentType.AGGREGATED_SHARING, ConsentType.ANONYMOUS_RESEARCH, 
                               ConsentType.COLLECTIVE_INSIGHTS]:
            return False
            
        return self.has_consent(sharing_type, classification) or \
               self.has_consent(sharing_type, None)
    
    def get_consent_summary(self) -> Dict[str, any]:
        """Get a summary of all current consents"""
        active_consents = {k: v for k, v in self.consents.items() if v.is_valid and v.granted}
        revoked_consents = {k: v for k, v in self.consents.items() if not v.granted}
        expired_consents = {k: v for k, v in self.consents.items() if v.granted and not v.is_valid}
        
        return {
            'user_id': self.user_id,
            'last_updated': max(c.timestamp for c in self.consents.values()).isoformat() if self.consents else None,
            'active_consents': len(active_consents),
            'revoked_consents': len(revoked_consents),
            'expired_consents': len(expired_consents),
            'total_history_entries': len(self.consent_history),
            'sharing_enabled': any(
                self.has_consent(ct) for ct in [
                    ConsentType.AGGREGATED_SHARING,
                    ConsentType.ANONYMOUS_RESEARCH,
                    ConsentType.COLLECTIVE_INSIGHTS
                ]
            ),
            'data_collection_enabled': any(
                self.has_consent(ConsentType.DATA_COLLECTION, classification) 
                for classification in DataClassification
            ) or self.has_consent(ConsentType.DATA_COLLECTION),
            'consents': {
                key: {
                    'granted': consent.granted,
                    'valid': consent.is_valid,
                    'granted_date': consent.timestamp.isoformat(),
                    'expires': consent.expires.isoformat() if consent.expires else None,
                    'context': consent.context
                }
                for key, consent in self.consents.items()
            }
        }
    
    def cleanup_expired_consents(self):
        """Remove expired consents and move to history"""
        expired_keys = []
        
        for key, consent in self.consents.items():
            if consent.granted and not consent.is_valid:
                expired_keys.append(key)
        
        for key in expired_keys:
            expired_consent = self.consents.pop(key)
            self.consent_history.append(expired_consent)
            logger.info(f"Moved expired consent to history: {key}")
        
        if expired_keys:
            self._save_consents()
    
    def export_consent_record(self) -> Dict[str, any]:
        """Export complete consent record for user review"""
        return {
            'export_timestamp': datetime.now().isoformat(),
            'user_id': self.user_id,
            'consent_version': '1.0',
            'current_consents': {
                key: {
                    'consent_type': consent.consent_type.value,
                    'data_classification': consent.data_classification.value if consent.data_classification else None,
                    'granted': consent.granted,
                    'valid': consent.is_valid,
                    'granted_date': consent.timestamp.isoformat(),
                    'expires': consent.expires.isoformat() if consent.expires else None,
                    'context': consent.context,
                    'version': consent.version
                }
                for key, consent in self.consents.items()
            },
            'consent_history': [
                {
                    'consent_type': consent.consent_type.value,
                    'data_classification': consent.data_classification.value if consent.data_classification else None,
                    'granted': consent.granted,
                    'granted_date': consent.timestamp.isoformat(),
                    'expires': consent.expires.isoformat() if consent.expires else None,
                    'context': consent.context,
                    'version': consent.version
                }
                for consent in self.consent_history
            ],
            'summary': self.get_consent_summary()
        }