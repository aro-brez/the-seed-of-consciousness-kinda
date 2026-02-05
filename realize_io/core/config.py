"""Configuration management for REALIZE-IO"""

import os
from pathlib import Path
from typing import Dict, Any, Optional
import json
import logging
from dataclasses import dataclass, asdict
from datetime import datetime


@dataclass 
class DataSourceConfig:
    """Configuration for a data source"""
    name: str
    enabled: bool = True
    collection_interval: int = 300  # seconds
    api_endpoint: Optional[str] = None
    credentials_key: Optional[str] = None
    last_sync: Optional[datetime] = None
    

@dataclass
class RealizeConfig:
    """Main configuration for REALIZE-IO system"""
    
    # Paths
    data_dir: str = "~/.realize_io/data"
    cache_dir: str = "~/.realize_io/cache" 
    log_dir: str = "~/.realize_io/logs"
    
    # Encryption
    encryption_key_path: str = "~/.realize_io/master.key"
    
    # Collection settings
    collection_interval: int = 300  # Default 5 minutes
    batch_size: int = 1000
    
    # Privacy settings
    anonymize_data: bool = True
    data_retention_days: int = 365
    
    # API settings
    api_port: int = 8080
    api_host: str = "localhost"
    
    # NATS integration
    nats_enabled: bool = True
    nats_servers: list = None
    
    def __post_init__(self):
        if self.nats_servers is None:
            self.nats_servers = ["nats://localhost:4222"]
            
        # Expand paths
        self.data_dir = str(Path(self.data_dir).expanduser())
        self.cache_dir = str(Path(self.cache_dir).expanduser())
        self.log_dir = str(Path(self.log_dir).expanduser())
        self.encryption_key_path = str(Path(self.encryption_key_path).expanduser())


class ConfigManager:
    """Manages REALIZE-IO configuration"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or str(Path("~/.realize_io/config.json").expanduser())
        self.config = self.load_config()
        self.data_sources: Dict[str, DataSourceConfig] = {}
        self.setup_logging()
        
    def load_config(self) -> RealizeConfig:
        """Load configuration from file or create default"""
        config_file = Path(self.config_path)
        
        if config_file.exists():
            try:
                with open(config_file) as f:
                    config_dict = json.load(f)
                return RealizeConfig(**config_dict)
            except Exception as e:
                logging.warning(f"Failed to load config: {e}, using defaults")
                
        return RealizeConfig()
        
    def save_config(self):
        """Save current configuration to file"""
        config_file = Path(self.config_path)
        config_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(config_file, 'w') as f:
            json.dump(asdict(self.config), f, indent=2, default=str)
            
    def setup_logging(self):
        """Setup logging configuration"""
        log_dir = Path(self.config.log_dir)
        log_dir.mkdir(parents=True, exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_dir / 'realize_io.log'),
                logging.StreamHandler()
            ]
        )
        
    def setup_directories(self):
        """Create necessary directories"""
        for dir_path in [self.config.data_dir, self.config.cache_dir, self.config.log_dir]:
            Path(dir_path).mkdir(parents=True, exist_ok=True)
            
    def add_data_source(self, name: str, config: DataSourceConfig):
        """Add a data source configuration"""
        self.data_sources[name] = config
        
    def get_data_source(self, name: str) -> Optional[DataSourceConfig]:
        """Get data source configuration"""
        return self.data_sources.get(name)
        
    def list_data_sources(self) -> Dict[str, DataSourceConfig]:
        """List all configured data sources"""
        return self.data_sources.copy()


# Global config instance
config_manager = ConfigManager()