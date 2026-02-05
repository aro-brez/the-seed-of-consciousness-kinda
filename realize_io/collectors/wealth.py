"""Wealth data collectors"""

import asyncio
import json
import requests
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional
from pathlib import Path

from .base import BaseCollector, CollectionResult
from ..core.models import WealthData, DataDomain, DataQuality


class WealthCollector(BaseCollector):
    """Collects wealth and financial data from various sources"""
    
    def __init__(self, collection_interval: int = 3600):  # 1 hour default
        super().__init__("wealth_collector", DataDomain.WEALTH, collection_interval)
        self.sources = []
        
    async def collect_data(self) -> CollectionResult:
        """Collect wealth data from all configured sources"""
        all_data_points = []
        errors = []
        
        for source_name, collector_func in self.sources:
            try:
                data_points = await collector_func()
                all_data_points.extend(data_points)
                self.logger.debug(f"Collected {len(data_points)} wealth points from {source_name}")
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
        """Test wealth data source connections"""
        if not self.sources:
            self.logger.warning("No wealth data sources configured")
            return False
            
        for source_name, collector_func in self.sources:
            try:
                data_points = await collector_func()
                if data_points:
                    self.logger.info(f"Wealth source {source_name} is working")
                    return True
            except Exception as e:
                self.logger.debug(f"Wealth source {source_name} failed: {e}")
                continue
                
        return False
    
    def add_source(self, name: str, collector_func):
        """Add a wealth data source"""
        self.sources.append((name, collector_func))
        self.logger.info(f"Added wealth source: {name}")


class PlaidCollector(WealthCollector):
    """Collects banking data via Plaid API"""
    
    def __init__(self, client_id: Optional[str] = None, secret: Optional[str] = None, 
                 access_tokens: Optional[List[str]] = None, collection_interval: int = 3600):
        super().__init__(collection_interval)
        self.name = "plaid_banking"
        self.client_id = client_id
        self.secret = secret
        self.access_tokens = access_tokens or []
        
        # Add Plaid data sources
        self.add_source("account_balances", self._collect_balances)
        self.add_source("transactions", self._collect_transactions)
        
    async def _collect_balances(self) -> List[WealthData]:
        """Collect account balance data"""
        # TODO: Implement actual Plaid API integration
        # For now, return mock data
        now = datetime.now(timezone.utc)
        
        balances = []
        
        # Mock checking account
        balances.append(WealthData(
            timestamp=now,
            source="plaid_checking",
            value=5500.0,
            net_worth=5500.0,
            quality=DataQuality.HIGH,
            metadata={'account_type': 'checking', 'institution': 'mock_bank'}
        ))
        
        # Mock savings account
        balances.append(WealthData(
            timestamp=now,
            source="plaid_savings",
            value=25000.0,
            net_worth=25000.0,
            quality=DataQuality.HIGH,
            metadata={'account_type': 'savings', 'institution': 'mock_bank'}
        ))
        
        return balances
        
    async def _collect_transactions(self) -> List[WealthData]:
        """Collect recent transaction data"""
        now = datetime.now(timezone.utc)
        
        # Mock recent expenses
        return [WealthData(
            timestamp=now - timedelta(hours=2),
            source="plaid_transactions",
            value=-45.67,  # Expense
            expenses=45.67,
            quality=DataQuality.HIGH,
            metadata={'category': 'food', 'merchant': 'mock_restaurant', 'transaction_type': 'expense'}
        )]


class ManualWealthCollector(WealthCollector):
    """Collects manually entered wealth data"""
    
    def __init__(self, data_file: Optional[str] = None, collection_interval: int = 300):
        super().__init__(collection_interval)
        self.name = "manual_wealth"
        self.data_file = Path(data_file) if data_file else Path.home() / ".realize_io" / "manual_wealth.json"
        
        # Ensure data file exists
        self.data_file.parent.mkdir(parents=True, exist_ok=True)
        if not self.data_file.exists():
            with open(self.data_file, 'w') as f:
                json.dump([], f)
                
        self.add_source("manual_entries", self._collect_manual_entries)
        
    async def _collect_manual_entries(self) -> List[WealthData]:
        """Collect manually entered wealth data"""
        if not self.data_file.exists():
            return []
            
        try:
            with open(self.data_file, 'r') as f:
                entries = json.load(f)
                
            data_points = []
            current_time = datetime.now(timezone.utc)
            
            for entry in entries:
                entry_time = datetime.fromisoformat(entry.get('timestamp', current_time.isoformat()))
                
                if (current_time - entry_time).total_seconds() < 86400:  # 24 hours
                    data_point = WealthData(
                        timestamp=entry_time,
                        source="manual_wealth_entry",
                        value=entry.get('value', 0),
                        quality=DataQuality.MEDIUM,
                        metadata=entry.get('metadata', {}),
                        **{k: v for k, v in entry.items() 
                           if k in ['net_worth', 'income', 'expenses', 'savings_rate', 'investment_returns', 'debt_total']}
                    )
                    data_points.append(data_point)
                    
            return data_points
            
        except (json.JSONDecodeError, FileNotFoundError, KeyError) as e:
            self.logger.warning(f"Error reading manual wealth data: {e}")
            return []
    
    def add_manual_entry(self, **kwargs):
        """Add a manual wealth entry"""
        try:
            with open(self.data_file, 'r') as f:
                entries = json.load(f)
                
            entry = {
                'timestamp': datetime.now(timezone.utc).isoformat(),
                **kwargs
            }
            entries.append(entry)
            
            with open(self.data_file, 'w') as f:
                json.dump(entries, f, indent=2)
                
            self.logger.info(f"Added manual wealth entry: {entry}")
            
        except Exception as e:
            self.logger.error(f"Error adding manual wealth entry: {e}")


class InvestmentCollector(WealthCollector):
    """Collects investment portfolio data"""
    
    def __init__(self, api_key: Optional[str] = None, collection_interval: int = 1800):  # 30 minutes
        super().__init__(collection_interval)
        self.name = "investments"
        self.api_key = api_key
        
        self.add_source("portfolio_value", self._collect_portfolio)
        self.add_source("crypto_holdings", self._collect_crypto)
        
    async def _collect_portfolio(self) -> List[WealthData]:
        """Collect portfolio value data"""
        now = datetime.now(timezone.utc)
        
        # Mock portfolio data
        return [WealthData(
            timestamp=now,
            source="investment_portfolio",
            value=75000.0,
            net_worth=75000.0,
            investment_returns=0.08,  # 8% return
            quality=DataQuality.HIGH,
            metadata={'portfolio_type': 'stocks_bonds', 'provider': 'mock_broker'}
        )]
        
    async def _collect_crypto(self) -> List[WealthData]:
        """Collect cryptocurrency holdings"""
        now = datetime.now(timezone.utc)
        
        # Mock crypto data
        return [WealthData(
            timestamp=now,
            source="crypto_holdings",
            value=12500.0,
            net_worth=12500.0,
            investment_returns=-0.05,  # -5% return
            quality=DataQuality.MEDIUM,
            metadata={'asset_type': 'cryptocurrency', 'major_holdings': ['BTC', 'ETH']}
        )]


class BudgetTracker(WealthCollector):
    """Tracks budget vs actual spending"""
    
    def __init__(self, budget_file: Optional[str] = None, collection_interval: int = 3600):
        super().__init__(collection_interval)
        self.name = "budget_tracker"
        self.budget_file = Path(budget_file) if budget_file else Path.home() / ".realize_io" / "budget.json"
        
        self.add_source("budget_analysis", self._analyze_budget)
        
    async def _analyze_budget(self) -> List[WealthData]:
        """Analyze budget vs actual spending"""
        now = datetime.now(timezone.utc)
        
        # Mock budget analysis
        return [WealthData(
            timestamp=now,
            source="budget_analysis",
            value=0.85,  # 85% of budget used
            expenses=3400.0,  # Monthly expenses
            savings_rate=0.20,  # 20% savings rate
            quality=DataQuality.MEDIUM,
            metadata={
                'budget_period': 'monthly',
                'budget_adherence': 0.85,
                'categories': {
                    'food': {'budgeted': 800, 'actual': 750},
                    'transport': {'budgeted': 300, 'actual': 280},
                    'entertainment': {'budgeted': 400, 'actual': 450}
                }
            }
        )]


class CryptoAPICollector(WealthCollector):
    """Collects crypto portfolio data from exchanges via APIs"""
    
    def __init__(self, exchange_apis: Optional[Dict[str, str]] = None, collection_interval: int = 900):  # 15 minutes
        super().__init__(collection_interval)
        self.name = "crypto_api"
        self.exchange_apis = exchange_apis or {}
        
        self.add_source("exchange_balances", self._collect_exchange_balances)
        
    async def _collect_exchange_balances(self) -> List[WealthData]:
        """Collect balances from crypto exchanges"""
        now = datetime.now(timezone.utc)
        
        # Mock exchange balance data
        return [WealthData(
            timestamp=now,
            source="crypto_exchange",
            value=8750.0,
            net_worth=8750.0,
            quality=DataQuality.HIGH,
            metadata={
                'exchange': 'mock_exchange',
                'balances': {
                    'BTC': {'amount': 0.15, 'value_usd': 6000},
                    'ETH': {'amount': 1.2, 'value_usd': 2400},
                    'USDC': {'amount': 350, 'value_usd': 350}
                }
            }
        )]