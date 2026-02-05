"""Encrypted time-series storage for personal data"""

import asyncio
import json
import logging
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional, AsyncIterator
import sqlite3
import aiosqlite
from contextlib import asynccontextmanager

from ..core.models import DataPoint, DataDomain, PersonalState
from ..core.encryption import AESCipher
from ..core.config import config_manager


class EncryptedTimeSeriesStore:
    """Local encrypted time-series storage for personal trajectory data"""
    
    def __init__(self, data_dir: Optional[str] = None, master_key: Optional[bytes] = None):
        self.data_dir = Path(data_dir or config_manager.config.data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.db_path = self.data_dir / "trajectories.db"
        self.cipher = AESCipher(master_key) if master_key else None
        self.logger = logging.getLogger(__name__)
        
        # Initialize database schema
        asyncio.create_task(self._init_database())
    
    async def _init_database(self):
        """Initialize SQLite database schema"""
        async with aiosqlite.connect(self.db_path) as db:
            # Create data_points table
            await db.execute('''
                CREATE TABLE IF NOT EXISTS data_points (
                    id TEXT PRIMARY KEY,
                    timestamp INTEGER NOT NULL,
                    domain TEXT NOT NULL,
                    source TEXT NOT NULL,
                    encrypted_data BLOB NOT NULL,
                    quality TEXT NOT NULL,
                    created_at INTEGER DEFAULT (strftime('%s', 'now'))
                )
            ''')
            
            # Create indices for efficient querying
            await db.execute('CREATE INDEX IF NOT EXISTS idx_timestamp ON data_points (timestamp)')
            await db.execute('CREATE INDEX IF NOT EXISTS idx_domain ON data_points (domain)')
            await db.execute('CREATE INDEX IF NOT EXISTS idx_domain_time ON data_points (domain, timestamp)')
            
            # Create personal_states table for snapshots
            await db.execute('''
                CREATE TABLE IF NOT EXISTS personal_states (
                    id TEXT PRIMARY KEY,
                    timestamp INTEGER NOT NULL,
                    encrypted_state BLOB NOT NULL,
                    created_at INTEGER DEFAULT (strftime('%s', 'now'))
                )
            ''')
            
            await db.commit()
            self.logger.info("Database initialized successfully")
    
    async def store(self, data_point: DataPoint) -> bool:
        """Store a single data point with encryption"""
        try:
            # Serialize and encrypt data
            data_json = json.dumps(data_point.to_dict())
            encrypted_data = self.cipher.encrypt(data_json) if self.cipher else data_json.encode()
            
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute('''
                    INSERT OR REPLACE INTO data_points 
                    (id, timestamp, domain, source, encrypted_data, quality)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    data_point.id,
                    int(data_point.timestamp.timestamp()),
                    data_point.domain.value,
                    data_point.source,
                    encrypted_data,
                    data_point.quality.value
                ))
                await db.commit()
                
            self.logger.debug(f"Stored data point {data_point.id} for domain {data_point.domain.value}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to store data point: {e}")
            return False
    
    async def store_batch(self, data_points: List[DataPoint]) -> int:
        """Store multiple data points efficiently"""
        stored_count = 0
        
        try:
            async with aiosqlite.connect(self.db_path) as db:
                for data_point in data_points:
                    try:
                        data_json = json.dumps(data_point.to_dict())
                        encrypted_data = self.cipher.encrypt(data_json) if self.cipher else data_json.encode()
                        
                        await db.execute('''
                            INSERT OR REPLACE INTO data_points 
                            (id, timestamp, domain, source, encrypted_data, quality)
                            VALUES (?, ?, ?, ?, ?, ?)
                        ''', (
                            data_point.id,
                            int(data_point.timestamp.timestamp()),
                            data_point.domain.value,
                            data_point.source,
                            encrypted_data,
                            data_point.quality.value
                        ))
                        stored_count += 1
                        
                    except Exception as e:
                        self.logger.error(f"Failed to store data point {data_point.id}: {e}")
                
                await db.commit()
                
        except Exception as e:
            self.logger.error(f"Batch store failed: {e}")
            
        self.logger.info(f"Stored {stored_count}/{len(data_points)} data points")
        return stored_count
    
    async def query(self, 
                   domain: Optional[DataDomain] = None,
                   start_time: Optional[datetime] = None,
                   end_time: Optional[datetime] = None,
                   source: Optional[str] = None,
                   limit: Optional[int] = None) -> List[DataPoint]:
        """Query data points with optional filters"""
        
        query_parts = ["SELECT encrypted_data FROM data_points WHERE 1=1"]
        params = []
        
        if domain:
            query_parts.append("AND domain = ?")
            params.append(domain.value)
            
        if start_time:
            query_parts.append("AND timestamp >= ?")
            params.append(int(start_time.timestamp()))
            
        if end_time:
            query_parts.append("AND timestamp <= ?")
            params.append(int(end_time.timestamp()))
            
        if source:
            query_parts.append("AND source = ?")
            params.append(source)
            
        query_parts.append("ORDER BY timestamp DESC")
        
        if limit:
            query_parts.append("LIMIT ?")
            params.append(limit)
        
        query = " ".join(query_parts)
        data_points = []
        
        try:
            async with aiosqlite.connect(self.db_path) as db:
                async with db.execute(query, params) as cursor:
                    async for row in cursor:
                        encrypted_data = row[0]
                        
                        # Decrypt and deserialize
                        if self.cipher:
                            if isinstance(encrypted_data, bytes):
                                data_json = self.cipher.decrypt(encrypted_data)
                            else:
                                data_json = encrypted_data
                        else:
                            data_json = encrypted_data.decode() if isinstance(encrypted_data, bytes) else encrypted_data
                            
                        data_dict = json.loads(data_json)
                        data_points.append(DataPoint.from_dict(data_dict))
                        
        except Exception as e:
            self.logger.error(f"Query failed: {e}")
            
        self.logger.debug(f"Retrieved {len(data_points)} data points")
        return data_points
    
    async def get_latest(self, domain: DataDomain, count: int = 1) -> List[DataPoint]:
        """Get the most recent data points for a domain"""
        return await self.query(domain=domain, limit=count)
    
    async def get_range(self, domain: DataDomain, days: int) -> List[DataPoint]:
        """Get data points from the last N days"""
        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(days=days)
        return await self.query(domain=domain, start_time=start_time, end_time=end_time)
    
    async def store_personal_state(self, state: PersonalState) -> bool:
        """Store a personal state snapshot"""
        try:
            state_json = json.dumps(state.to_dict())
            encrypted_state = self.cipher.encrypt(state_json) if self.cipher else state_json.encode()
            
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute('''
                    INSERT INTO personal_states (id, timestamp, encrypted_state)
                    VALUES (?, ?, ?)
                ''', (
                    str(datetime.now().timestamp()),
                    int(state.timestamp.timestamp()),
                    encrypted_state
                ))
                await db.commit()
                
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to store personal state: {e}")
            return False
    
    async def get_personal_state(self, timestamp: Optional[datetime] = None) -> Optional[PersonalState]:
        """Get personal state snapshot (latest if timestamp not specified)"""
        try:
            query = "SELECT encrypted_state FROM personal_states"
            params = []
            
            if timestamp:
                query += " WHERE timestamp <= ? ORDER BY timestamp DESC LIMIT 1"
                params.append(int(timestamp.timestamp()))
            else:
                query += " ORDER BY timestamp DESC LIMIT 1"
            
            async with aiosqlite.connect(self.db_path) as db:
                async with db.execute(query, params) as cursor:
                    row = await cursor.fetchone()
                    
                    if row:
                        encrypted_state = row[0]
                        
                        if self.cipher:
                            state_json = self.cipher.decrypt(encrypted_state)
                        else:
                            state_json = encrypted_state.decode() if isinstance(encrypted_state, bytes) else encrypted_state
                            
                        state_dict = json.loads(state_json)
                        return PersonalState.from_dict(state_dict)
                        
        except Exception as e:
            self.logger.error(f"Failed to retrieve personal state: {e}")
            
        return None
    
    async def get_statistics(self) -> Dict[str, Any]:
        """Get storage statistics"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                # Count by domain
                domain_counts = {}
                async with db.execute("SELECT domain, COUNT(*) FROM data_points GROUP BY domain") as cursor:
                    async for domain, count in cursor:
                        domain_counts[domain] = count
                
                # Total count and date range
                async with db.execute("SELECT COUNT(*), MIN(timestamp), MAX(timestamp) FROM data_points") as cursor:
                    row = await cursor.fetchone()
                    total_count = row[0] if row else 0
                    min_timestamp = row[1] if row and row[1] else None
                    max_timestamp = row[2] if row and row[2] else None
                
                # Database file size
                db_size = self.db_path.stat().st_size if self.db_path.exists() else 0
                
                return {
                    'total_data_points': total_count,
                    'domain_counts': domain_counts,
                    'date_range': {
                        'earliest': datetime.fromtimestamp(min_timestamp, timezone.utc).isoformat() if min_timestamp else None,
                        'latest': datetime.fromtimestamp(max_timestamp, timezone.utc).isoformat() if max_timestamp else None
                    },
                    'database_size_bytes': db_size,
                    'encryption_enabled': self.cipher is not None
                }
                
        except Exception as e:
            self.logger.error(f"Failed to get statistics: {e}")
            return {'error': str(e)}
    
    async def export_data(self, 
                         domain: Optional[DataDomain] = None, 
                         format: str = 'json') -> Optional[str]:
        """Export data in specified format"""
        try:
            data_points = await self.query(domain=domain)
            
            if format.lower() == 'json':
                return json.dumps([dp.to_dict() for dp in data_points], indent=2, default=str)
            elif format.lower() == 'csv':
                import csv
                import io
                
                output = io.StringIO()
                if data_points:
                    fieldnames = ['timestamp', 'domain', 'source', 'value', 'quality']
                    writer = csv.DictWriter(output, fieldnames=fieldnames)
                    writer.writeheader()
                    
                    for dp in data_points:
                        writer.writerow({
                            'timestamp': dp.timestamp.isoformat(),
                            'domain': dp.domain.value,
                            'source': dp.source,
                            'value': json.dumps(dp.value) if not isinstance(dp.value, (str, int, float)) else dp.value,
                            'quality': dp.quality.value
                        })
                
                return output.getvalue()
            else:
                raise ValueError(f"Unsupported format: {format}")
                
        except Exception as e:
            self.logger.error(f"Export failed: {e}")
            return None
    
    async def cleanup_old_data(self, retention_days: int) -> int:
        """Remove data older than specified days"""
        try:
            cutoff_time = datetime.now(timezone.utc) - timedelta(days=retention_days)
            cutoff_timestamp = int(cutoff_time.timestamp())
            
            async with aiosqlite.connect(self.db_path) as db:
                # Delete old data points
                cursor = await db.execute("DELETE FROM data_points WHERE timestamp < ?", (cutoff_timestamp,))
                deleted_count = cursor.rowcount
                
                # Delete old personal states
                await db.execute("DELETE FROM personal_states WHERE timestamp < ?", (cutoff_timestamp,))
                
                await db.commit()
                
            self.logger.info(f"Cleaned up {deleted_count} old data points")
            return deleted_count
            
        except Exception as e:
            self.logger.error(f"Cleanup failed: {e}")
            return 0