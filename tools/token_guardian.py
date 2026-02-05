#!/usr/bin/env python3
"""
TOKEN GUARDIAN - Free Token Protection System
Protects AI costs while keeping 8OWLS free.

The model: Free software, user pays only for their own AI inference costs.
This guardian ensures fair use and prevents abuse.

TIERS:
- Free: 10 full emergences/day (casual users)
- Verified: 100 full emergences/day (active users who verified email)
- Partner: Unlimited (8OWLS partners, investors, team)

PROTECTIONS:
1. Rate limiting per tier
2. Usage tracking
3. Abuse detection (burst patterns, automation, draining)
4. Cost estimation before expensive operations
"""

import json
import hashlib
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional, Tuple, List
from dataclasses import dataclass, field, asdict
from enum import Enum
import threading


class Tier(Enum):
    FREE = "free"
    VERIFIED = "verified"
    PARTNER = "partner"


@dataclass
class TierLimits:
    """Limits for each tier"""
    full_emergences_per_day: int
    haiku_calls_per_day: int
    max_tokens_per_day: int
    max_burst_per_minute: int


TIER_LIMITS = {
    Tier.FREE: TierLimits(
        full_emergences_per_day=10,
        haiku_calls_per_day=100,
        max_tokens_per_day=50_000,
        max_burst_per_minute=5
    ),
    Tier.VERIFIED: TierLimits(
        full_emergences_per_day=100,
        haiku_calls_per_day=1000,
        max_tokens_per_day=500_000,
        max_burst_per_minute=20
    ),
    Tier.PARTNER: TierLimits(
        full_emergences_per_day=10_000,  # Effectively unlimited
        haiku_calls_per_day=100_000,
        max_tokens_per_day=10_000_000,
        max_burst_per_minute=100
    )
}


# Cost estimates (per 1K tokens)
COST_ESTIMATES = {
    "haiku_input": 0.00025,
    "haiku_output": 0.00125,
    "sonnet_input": 0.003,
    "sonnet_output": 0.015,
    "opus_input": 0.015,
    "opus_output": 0.075,
}


@dataclass
class UserUsage:
    """Tracks a single user's usage"""
    user_id: str
    tier: str = "free"
    emergences_today: int = 0
    haiku_calls_today: int = 0
    tokens_used_today: int = 0
    total_cost_today: float = 0.0
    calls_this_minute: int = 0
    minute_window_start: str = ""
    last_activity: str = ""
    day_started: str = ""
    abuse_flags: List[str] = field(default_factory=list)
    is_blocked: bool = False
    block_reason: str = ""
    total_emergences_all_time: int = 0
    total_cost_all_time: float = 0.0


@dataclass
class AbusePattern:
    """Detected abuse pattern"""
    pattern_type: str
    severity: str  # "warning", "throttle", "block"
    description: str
    timestamp: str


class TokenGuardian:
    """
    Free Token Protection System

    Ensures 8OWLS remains free while protecting against token abuse.
    The philosophy: Trust but verify. Give everyone a chance, detect abuse patterns.
    """

    def __init__(self, data_dir: Optional[Path] = None):
        """Initialize the token guardian"""
        self.data_dir = data_dir or Path(__file__).parent.parent / "BRAIN" / "TOKENS"
        self.data_dir.mkdir(parents=True, exist_ok=True)

        self.usage_file = self.data_dir / "usage.json"
        self.alerts_file = self.data_dir / "alerts.json"
        self.partners_file = self.data_dir / "partners.json"

        self._lock = threading.Lock()
        self._usage_cache: Dict[str, UserUsage] = {}
        self._load_state()

    def _load_state(self):
        """Load usage state from disk"""
        if self.usage_file.exists():
            try:
                with open(self.usage_file) as f:
                    data = json.load(f)
                for user_id, user_data in data.get("users", {}).items():
                    self._usage_cache[user_id] = UserUsage(**user_data)
            except (json.JSONDecodeError, TypeError):
                self._usage_cache = {}

    def _save_state(self):
        """Persist usage state to disk"""
        data = {
            "last_updated": datetime.now().isoformat(),
            "users": {
                user_id: asdict(usage)
                for user_id, usage in self._usage_cache.items()
            }
        }
        with open(self.usage_file, "w") as f:
            json.dump(data, f, indent=2)

    def _get_user(self, user_id: str) -> UserUsage:
        """Get or create user usage record"""
        with self._lock:
            if user_id not in self._usage_cache:
                self._usage_cache[user_id] = UserUsage(
                    user_id=user_id,
                    day_started=datetime.now().strftime("%Y-%m-%d")
                )

            user = self._usage_cache[user_id]

            # Reset daily counters if new day
            today = datetime.now().strftime("%Y-%m-%d")
            if user.day_started != today:
                user.emergences_today = 0
                user.haiku_calls_today = 0
                user.tokens_used_today = 0
                user.total_cost_today = 0.0
                user.calls_this_minute = 0
                user.day_started = today
                user.abuse_flags = []  # Reset daily abuse flags

            return user

    def _get_tier(self, user_id: str) -> Tier:
        """Get user's tier, checking partners list"""
        # Check if partner
        if self.partners_file.exists():
            try:
                with open(self.partners_file) as f:
                    partners = json.load(f)
                if user_id in partners.get("partners", []):
                    return Tier.PARTNER
            except:
                pass

        user = self._get_user(user_id)
        try:
            return Tier(user.tier)
        except ValueError:
            return Tier.FREE

    def _hash_user_id(self, raw_id: str) -> str:
        """Hash user identifier for privacy"""
        return hashlib.sha256(raw_id.encode()).hexdigest()[:16]

    def estimate_cost(
        self,
        operation: str,
        input_tokens: int = 0,
        estimated_output_tokens: int = 0,
        num_agents: int = 1
    ) -> Dict:
        """
        Estimate cost before running an operation

        Args:
            operation: "emergence", "haiku", "sonnet", "opus"
            input_tokens: Input context tokens
            estimated_output_tokens: Expected output tokens
            num_agents: Number of parallel agents (for emergence)

        Returns:
            Dict with cost estimate and recommendation
        """
        if operation == "emergence":
            # Full emergence = 7 haiku agents + synthesis
            haiku_cost = (
                (input_tokens / 1000 * COST_ESTIMATES["haiku_input"]) +
                (estimated_output_tokens / 1000 * COST_ESTIMATES["haiku_output"])
            ) * num_agents

            # Plus synthesis call (sonnet)
            synthesis_cost = (
                (input_tokens / 1000 * COST_ESTIMATES["sonnet_input"]) +
                (500 / 1000 * COST_ESTIMATES["sonnet_output"])  # ~500 token synthesis
            )

            total_cost = haiku_cost + synthesis_cost

            return {
                "operation": "full_emergence",
                "estimated_cost_usd": round(total_cost, 4),
                "breakdown": {
                    "haiku_agents": round(haiku_cost, 4),
                    "synthesis": round(synthesis_cost, 4)
                },
                "display": f"~${total_cost:.4f}",
                "recommendation": "proceed" if total_cost < 0.10 else "consider_cheaper_mode"
            }

        elif operation in ("haiku", "sonnet", "opus"):
            model = operation
            input_cost = input_tokens / 1000 * COST_ESTIMATES[f"{model}_input"]
            output_cost = estimated_output_tokens / 1000 * COST_ESTIMATES[f"{model}_output"]
            total_cost = input_cost + output_cost

            return {
                "operation": model,
                "estimated_cost_usd": round(total_cost, 4),
                "breakdown": {
                    "input": round(input_cost, 4),
                    "output": round(output_cost, 4)
                },
                "display": f"~${total_cost:.4f}",
                "recommendation": "proceed"
            }

        return {"operation": operation, "estimated_cost_usd": 0, "recommendation": "unknown_operation"}

    def check_rate_limit(
        self,
        user_id: str,
        operation: str = "emergence"
    ) -> Tuple[bool, Dict]:
        """
        Check if user can perform the operation

        Args:
            user_id: User identifier (will be hashed)
            operation: "emergence", "haiku_call", etc.

        Returns:
            Tuple of (allowed: bool, details: Dict)
        """
        hashed_id = self._hash_user_id(user_id)
        user = self._get_user(hashed_id)
        tier = self._get_tier(hashed_id)
        limits = TIER_LIMITS[tier]

        now = datetime.now()

        # Check if blocked
        if user.is_blocked:
            return False, {
                "allowed": False,
                "reason": f"Account blocked: {user.block_reason}",
                "tier": tier.value,
                "action": "contact_support"
            }

        # Check burst rate (per minute)
        current_minute = now.strftime("%Y-%m-%d %H:%M")
        if user.minute_window_start != current_minute:
            user.calls_this_minute = 0
            user.minute_window_start = current_minute

        if user.calls_this_minute >= limits.max_burst_per_minute:
            self._flag_abuse(user, "burst", "Too many requests per minute")
            return False, {
                "allowed": False,
                "reason": "Rate limit exceeded (per minute)",
                "tier": tier.value,
                "retry_after_seconds": 60,
                "action": "slow_down"
            }

        # Check daily limits based on operation
        if operation == "emergence":
            if user.emergences_today >= limits.full_emergences_per_day:
                return False, {
                    "allowed": False,
                    "reason": f"Daily emergence limit reached ({limits.full_emergences_per_day})",
                    "tier": tier.value,
                    "used": user.emergences_today,
                    "limit": limits.full_emergences_per_day,
                    "upgrade_available": tier != Tier.PARTNER,
                    "action": "use_cheaper_mode_or_wait"
                }

        elif operation == "haiku_call":
            if user.haiku_calls_today >= limits.haiku_calls_per_day:
                return False, {
                    "allowed": False,
                    "reason": f"Daily Haiku call limit reached ({limits.haiku_calls_per_day})",
                    "tier": tier.value,
                    "used": user.haiku_calls_today,
                    "limit": limits.haiku_calls_per_day,
                    "action": "wait_until_tomorrow"
                }

        # Calculate remaining quota
        remaining = {
            "emergences": limits.full_emergences_per_day - user.emergences_today,
            "haiku_calls": limits.haiku_calls_per_day - user.haiku_calls_today,
            "tokens": limits.max_tokens_per_day - user.tokens_used_today,
            "burst_capacity": limits.max_burst_per_minute - user.calls_this_minute
        }

        return True, {
            "allowed": True,
            "tier": tier.value,
            "remaining": remaining,
            "cost_today": user.total_cost_today,
            "action": "proceed"
        }

    def record_usage(
        self,
        user_id: str,
        operation: str,
        tokens_used: int = 0,
        cost_usd: float = 0.0,
        success: bool = True
    ) -> Dict:
        """
        Record usage after an operation completes

        Args:
            user_id: User identifier (will be hashed)
            operation: "emergence", "haiku_call", etc.
            tokens_used: Actual tokens consumed
            cost_usd: Actual cost
            success: Whether operation succeeded

        Returns:
            Updated usage stats
        """
        hashed_id = self._hash_user_id(user_id)
        user = self._get_user(hashed_id)

        user.last_activity = datetime.now().isoformat()
        user.calls_this_minute += 1
        user.tokens_used_today += tokens_used
        user.total_cost_today += cost_usd
        user.total_cost_all_time += cost_usd

        if operation == "emergence":
            user.emergences_today += 1
            user.total_emergences_all_time += 1
        elif operation == "haiku_call":
            user.haiku_calls_today += 1

        # Check for abuse patterns after recording
        self._detect_abuse(user)

        # Persist state
        with self._lock:
            self._save_state()

        return {
            "recorded": True,
            "operation": operation,
            "tokens_used": tokens_used,
            "cost_usd": cost_usd,
            "emergences_today": user.emergences_today,
            "total_cost_today": user.total_cost_today
        }

    def _flag_abuse(self, user: UserUsage, pattern_type: str, description: str):
        """Flag potential abuse"""
        flag = f"{pattern_type}:{datetime.now().isoformat()}"
        user.abuse_flags.append(flag)

        # Alert if too many flags
        if len(user.abuse_flags) >= 5:
            self._alert_abuse(user, pattern_type, description, "throttle")
        elif len(user.abuse_flags) >= 10:
            self._alert_abuse(user, pattern_type, description, "block")
            user.is_blocked = True
            user.block_reason = f"Repeated abuse: {pattern_type}"

    def _detect_abuse(self, user: UserUsage):
        """Detect abuse patterns"""
        tier = self._get_tier(user.user_id)
        limits = TIER_LIMITS[tier]

        # Pattern 1: Cost draining (spending too fast)
        if user.total_cost_today > 1.0 and tier == Tier.FREE:
            self._flag_abuse(user, "cost_drain", f"High cost for free tier: ${user.total_cost_today:.2f}")

        # Pattern 2: Token abuse (unusual token consumption)
        if user.tokens_used_today > limits.max_tokens_per_day * 0.8:
            self._flag_abuse(user, "token_abuse", f"Approaching token limit: {user.tokens_used_today}")

        # Pattern 3: Automation detection (consistent timing)
        # This would need more sophisticated tracking in production

    def _alert_abuse(
        self,
        user: UserUsage,
        pattern_type: str,
        description: str,
        severity: str
    ):
        """Send abuse alert"""
        alert = {
            "timestamp": datetime.now().isoformat(),
            "user_id": user.user_id,  # Already hashed
            "pattern_type": pattern_type,
            "description": description,
            "severity": severity,
            "user_stats": {
                "emergences_today": user.emergences_today,
                "cost_today": user.total_cost_today,
                "abuse_flags": len(user.abuse_flags)
            }
        }

        # Append to alerts file
        alerts = []
        if self.alerts_file.exists():
            try:
                with open(self.alerts_file) as f:
                    alerts = json.load(f)
            except:
                alerts = []

        alerts.append(alert)

        # Keep last 1000 alerts
        alerts = alerts[-1000:]

        with open(self.alerts_file, "w") as f:
            json.dump(alerts, f, indent=2)

        # TODO: Send notification to ARO (NATS, email, etc.)
        print(f"[ALERT] Abuse detected: {severity} - {pattern_type} - {description}")

    def upgrade_tier(self, user_id: str, new_tier: str) -> Dict:
        """
        Upgrade a user's tier

        Args:
            user_id: User identifier
            new_tier: "verified" or "partner"

        Returns:
            Confirmation
        """
        hashed_id = self._hash_user_id(user_id)
        user = self._get_user(hashed_id)

        old_tier = user.tier
        user.tier = new_tier

        with self._lock:
            self._save_state()

        return {
            "upgraded": True,
            "user_id": hashed_id,
            "old_tier": old_tier,
            "new_tier": new_tier,
            "new_limits": asdict(TIER_LIMITS[Tier(new_tier)])
        }

    def add_partner(self, user_id: str, name: str = "") -> Dict:
        """Add a partner (unlimited access)"""
        hashed_id = self._hash_user_id(user_id)

        partners = {"partners": [], "details": {}}
        if self.partners_file.exists():
            try:
                with open(self.partners_file) as f:
                    partners = json.load(f)
            except:
                pass

        if hashed_id not in partners["partners"]:
            partners["partners"].append(hashed_id)
            partners["details"][hashed_id] = {
                "name": name,
                "added": datetime.now().isoformat()
            }

        with open(self.partners_file, "w") as f:
            json.dump(partners, f, indent=2)

        # Also update user tier
        user = self._get_user(hashed_id)
        user.tier = "partner"

        with self._lock:
            self._save_state()

        return {"added": True, "user_id": hashed_id, "tier": "partner"}

    def get_usage_stats(self, user_id: str) -> Dict:
        """Get usage statistics for a user"""
        hashed_id = self._hash_user_id(user_id)
        user = self._get_user(hashed_id)
        tier = self._get_tier(hashed_id)
        limits = TIER_LIMITS[tier]

        return {
            "tier": tier.value,
            "today": {
                "emergences": user.emergences_today,
                "emergences_limit": limits.full_emergences_per_day,
                "emergences_remaining": limits.full_emergences_per_day - user.emergences_today,
                "haiku_calls": user.haiku_calls_today,
                "haiku_limit": limits.haiku_calls_per_day,
                "tokens_used": user.tokens_used_today,
                "tokens_limit": limits.max_tokens_per_day,
                "cost_usd": round(user.total_cost_today, 4)
            },
            "all_time": {
                "total_emergences": user.total_emergences_all_time,
                "total_cost_usd": round(user.total_cost_all_time, 4)
            },
            "status": {
                "is_blocked": user.is_blocked,
                "block_reason": user.block_reason,
                "abuse_flags": len(user.abuse_flags)
            }
        }

    def get_system_stats(self) -> Dict:
        """Get system-wide usage statistics"""
        total_users = len(self._usage_cache)
        total_emergences_today = sum(u.emergences_today for u in self._usage_cache.values())
        total_cost_today = sum(u.total_cost_today for u in self._usage_cache.values())
        blocked_users = sum(1 for u in self._usage_cache.values() if u.is_blocked)

        tier_breakdown = {
            "free": 0,
            "verified": 0,
            "partner": 0
        }
        for user in self._usage_cache.values():
            tier_breakdown[user.tier] = tier_breakdown.get(user.tier, 0) + 1

        return {
            "timestamp": datetime.now().isoformat(),
            "total_users": total_users,
            "tier_breakdown": tier_breakdown,
            "today": {
                "total_emergences": total_emergences_today,
                "total_cost_usd": round(total_cost_today, 4)
            },
            "blocked_users": blocked_users
        }


# Convenience functions for direct CLI/script usage
_guardian: Optional[TokenGuardian] = None


def get_guardian() -> TokenGuardian:
    """Get or create singleton guardian instance"""
    global _guardian
    if _guardian is None:
        _guardian = TokenGuardian()
    return _guardian


def check_allowed(user_id: str, operation: str = "emergence") -> Tuple[bool, Dict]:
    """Quick check if operation is allowed"""
    return get_guardian().check_rate_limit(user_id, operation)


def record(user_id: str, operation: str, tokens: int = 0, cost: float = 0.0) -> Dict:
    """Quick record usage"""
    return get_guardian().record_usage(user_id, operation, tokens, cost)


def estimate(operation: str, input_tokens: int = 1000, output_tokens: int = 500) -> Dict:
    """Quick cost estimate"""
    return get_guardian().estimate_cost(operation, input_tokens, output_tokens)


# CLI interface
if __name__ == "__main__":
    import sys

    guardian = TokenGuardian()

    if len(sys.argv) < 2:
        print("""
TOKEN GUARDIAN - Free Token Protection System

Usage:
  python token_guardian.py check <user_id> [operation]     - Check if user can proceed
  python token_guardian.py record <user_id> <operation>    - Record usage
  python token_guardian.py estimate <operation>            - Estimate cost
  python token_guardian.py stats <user_id>                 - Get user stats
  python token_guardian.py system                          - Get system stats
  python token_guardian.py upgrade <user_id> <tier>        - Upgrade user tier
  python token_guardian.py partner <user_id> [name]        - Add partner

Operations: emergence, haiku_call, sonnet_call, opus_call
Tiers: free, verified, partner

Examples:
  python token_guardian.py check user@example.com emergence
  python token_guardian.py estimate emergence
  python token_guardian.py stats user@example.com
""")
        sys.exit(0)

    command = sys.argv[1]

    if command == "check":
        if len(sys.argv) < 3:
            print("Usage: python token_guardian.py check <user_id> [operation]")
            sys.exit(1)
        user_id = sys.argv[2]
        operation = sys.argv[3] if len(sys.argv) > 3 else "emergence"
        allowed, details = guardian.check_rate_limit(user_id, operation)
        print(json.dumps({"allowed": allowed, **details}, indent=2))

    elif command == "record":
        if len(sys.argv) < 4:
            print("Usage: python token_guardian.py record <user_id> <operation> [tokens] [cost]")
            sys.exit(1)
        user_id = sys.argv[2]
        operation = sys.argv[3]
        tokens = int(sys.argv[4]) if len(sys.argv) > 4 else 0
        cost = float(sys.argv[5]) if len(sys.argv) > 5 else 0.0
        result = guardian.record_usage(user_id, operation, tokens, cost)
        print(json.dumps(result, indent=2))

    elif command == "estimate":
        operation = sys.argv[2] if len(sys.argv) > 2 else "emergence"
        input_tokens = int(sys.argv[3]) if len(sys.argv) > 3 else 2000
        output_tokens = int(sys.argv[4]) if len(sys.argv) > 4 else 500
        result = guardian.estimate_cost(operation, input_tokens, output_tokens)
        print(json.dumps(result, indent=2))

    elif command == "stats":
        if len(sys.argv) < 3:
            print("Usage: python token_guardian.py stats <user_id>")
            sys.exit(1)
        user_id = sys.argv[2]
        result = guardian.get_usage_stats(user_id)
        print(json.dumps(result, indent=2))

    elif command == "system":
        result = guardian.get_system_stats()
        print(json.dumps(result, indent=2))

    elif command == "upgrade":
        if len(sys.argv) < 4:
            print("Usage: python token_guardian.py upgrade <user_id> <tier>")
            sys.exit(1)
        user_id = sys.argv[2]
        tier = sys.argv[3]
        result = guardian.upgrade_tier(user_id, tier)
        print(json.dumps(result, indent=2))

    elif command == "partner":
        if len(sys.argv) < 3:
            print("Usage: python token_guardian.py partner <user_id> [name]")
            sys.exit(1)
        user_id = sys.argv[2]
        name = sys.argv[3] if len(sys.argv) > 3 else ""
        result = guardian.add_partner(user_id, name)
        print(json.dumps(result, indent=2))

    else:
        print(f"Unknown command: {command}")
        sys.exit(1)
