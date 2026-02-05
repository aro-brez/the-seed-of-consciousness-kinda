#!/usr/bin/env python3
"""
OWL DAEMON V3 - SEED-Powered with OpenClaw-Inspired Patterns

UPGRADES FROM V2:
1. SKILL REGISTRY - Persistent skills with versioning (like OpenClaw's ClawHub)
2. EXEC APPROVALS - Human escalation for risky operations
3. TOOL POLICY - Tiered permissions (deny/allowlist/full)
4. RATE LIMITING - Cooldowns after failures, usage tracking
5. CREDENTIAL MANAGEMENT - Secure secret handling

THE PHILOSOPHY:
- V2 was task-first, not talk-first (good)
- V3 adds: SAFE execution, SKILLED actions, SMART escalation
- This is SEED² - learning how to learn from competitors

Usage:
    python owl_daemon_v3.py LUNA
    python owl_daemon_v3.py --all  # Start all 8 owls
"""

import asyncio
import argparse
import json
import os
import hashlib
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Dict, List, Any, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum
from anthropic import Anthropic
from nats.aio.client import Client as NATS

# Configuration
NATS_URL = "nats://192.168.5.108:4222"
BASE_DIR = Path("/Users/aaronnosbisch/REPOS/seed/mcp-servers/nats-bridge")
LOG_DIR = BASE_DIR
MESSAGES_LOG = LOG_DIR / "messages.log"
SKILLS_DIR = BASE_DIR / "skills"
APPROVALS_FILE = BASE_DIR / "exec_approvals.json"
CREDENTIALS_DIR = Path.home() / ".8owls" / "credentials"

# API Key
API_KEY = os.environ.get("ANTHROPIC_API_KEY")
if not API_KEY:
    key_file = Path.home() / ".anthropic_key"
    if key_file.exists():
        API_KEY = key_file.read_text().strip()


# =============================================================================
# SKILL REGISTRY SYSTEM (Inspired by OpenClaw's skills/workspace.ts)
# =============================================================================

class SkillSource(Enum):
    """Where the skill came from - determines override precedence."""
    BUNDLED = "bundled"      # Comes with 8OWLS (lowest priority)
    MANAGED = "managed"      # Installed via skill hub
    WORKSPACE = "workspace"  # User's local skills (highest priority)


@dataclass
class SkillMetadata:
    """OpenClaw-style skill metadata from YAML frontmatter."""
    always: bool = False                    # Always include this skill
    skill_key: str = ""                     # Unique key for config reference
    primary_env: str = ""                   # Primary env var (e.g., OPENAI_API_KEY)
    os: List[str] = field(default_factory=list)  # Platform requirements
    requires_bins: List[str] = field(default_factory=list)
    requires_env: List[str] = field(default_factory=list)
    requires_config: List[str] = field(default_factory=list)
    user_invocable: bool = True            # Can user invoke via command?
    model_invocable: bool = True           # Can LLM invoke?


@dataclass
class Skill:
    """A registered skill that persists across sessions."""
    name: str
    description: str
    content: str                           # The prompt/instructions
    source: SkillSource = SkillSource.WORKSPACE
    metadata: SkillMetadata = field(default_factory=SkillMetadata)
    version: int = 1
    last_used: Optional[float] = None
    use_count: int = 0

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "content": self.content,
            "source": self.source.value,
            "metadata": asdict(self.metadata),
            "version": self.version,
            "last_used": self.last_used,
            "use_count": self.use_count
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Skill":
        metadata_dict = data.get("metadata", {})
        return cls(
            name=data["name"],
            description=data.get("description", ""),
            content=data.get("content", ""),
            source=SkillSource(data.get("source", "workspace")),
            metadata=SkillMetadata(
                always=metadata_dict.get("always", False),
                skill_key=metadata_dict.get("skill_key", ""),
                primary_env=metadata_dict.get("primary_env", ""),
                os=metadata_dict.get("os", []),
                requires_bins=metadata_dict.get("requires_bins", []),
                requires_env=metadata_dict.get("requires_env", []),
                requires_config=metadata_dict.get("requires_config", []),
                user_invocable=metadata_dict.get("user_invocable", True),
                model_invocable=metadata_dict.get("model_invocable", True)
            ),
            version=data.get("version", 1),
            last_used=data.get("last_used"),
            use_count=data.get("use_count", 0)
        )


class SkillRegistry:
    """
    Manages skills with persistence and precedence.

    Precedence (highest wins):
    1. Workspace skills (~/.8owls/workspace/skills/)
    2. Managed skills (~/.8owls/skills/)
    3. Bundled skills (built-in)
    """

    def __init__(self, workspace_dir: Path = SKILLS_DIR):
        self.workspace_dir = workspace_dir
        self.managed_dir = Path.home() / ".8owls" / "skills"
        self.skills: Dict[str, Skill] = {}
        self._load_all()

    def _load_all(self):
        """Load skills from all sources with proper precedence."""
        # Load in order of precedence (later overrides earlier)
        self._load_bundled()
        self._load_from_dir(self.managed_dir, SkillSource.MANAGED)
        self._load_from_dir(self.workspace_dir, SkillSource.WORKSPACE)

    def _load_bundled(self):
        """Load built-in skills for 8OWLS."""
        bundled_skills = [
            Skill(
                name="trading-analysis",
                description="Analyze Polymarket opportunities with FIELD emergence",
                content="Analyze the given market opportunity using all 8 SEED phases...",
                source=SkillSource.BUNDLED,
                metadata=SkillMetadata(
                    skill_key="8owls.trading",
                    requires_env=["POLYMARKET_API_KEY"]
                )
            ),
            Skill(
                name="field-emergence",
                description="Trigger full 8-owl FIELD emergence on a topic",
                content="Spawn all 8 owls to contribute their SEED phase perspective...",
                source=SkillSource.BUNDLED,
                metadata=SkillMetadata(always=True, skill_key="8owls.field")
            ),
            Skill(
                name="continuous-improvement",
                description="Run SEED improvement cycle",
                content="Execute continuous improvement: PERCEIVE issues, CONNECT patterns...",
                source=SkillSource.BUNDLED,
                metadata=SkillMetadata(skill_key="8owls.improve")
            ),
        ]
        for skill in bundled_skills:
            self.skills[skill.name] = skill

    def _load_from_dir(self, dir_path: Path, source: SkillSource):
        """Load skills from a directory."""
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            return

        for skill_file in dir_path.glob("*.json"):
            try:
                data = json.loads(skill_file.read_text())
                skill = Skill.from_dict(data)
                skill.source = source
                self.skills[skill.name] = skill
            except Exception as e:
                print(f"Error loading skill {skill_file}: {e}")

    def register(self, skill: Skill, persist: bool = True):
        """Register a new skill or update existing."""
        existing = self.skills.get(skill.name)
        if existing:
            skill.version = existing.version + 1

        self.skills[skill.name] = skill

        if persist:
            target_dir = self.workspace_dir if skill.source == SkillSource.WORKSPACE else self.managed_dir
            target_dir.mkdir(parents=True, exist_ok=True)
            (target_dir / f"{skill.name}.json").write_text(
                json.dumps(skill.to_dict(), indent=2)
            )

    def get(self, name: str) -> Optional[Skill]:
        """Get a skill by name."""
        return self.skills.get(name)

    def use(self, name: str) -> Optional[Skill]:
        """Get a skill and mark it as used."""
        skill = self.skills.get(name)
        if skill:
            skill.last_used = time.time()
            skill.use_count += 1
        return skill

    def list_available(self, filter_phase: str = None) -> List[Skill]:
        """List all available skills, optionally filtered by SEED phase."""
        skills = list(self.skills.values())
        if filter_phase:
            # Future: filter by metadata tags
            pass
        return sorted(skills, key=lambda s: s.use_count, reverse=True)

    def build_prompt(self, skill_names: List[str] = None) -> str:
        """Build a prompt including specified skills."""
        if skill_names is None:
            # Include always-on skills
            skills = [s for s in self.skills.values() if s.metadata.always]
        else:
            skills = [self.skills[n] for n in skill_names if n in self.skills]

        if not skills:
            return ""

        prompt_parts = ["## Available Skills\n"]
        for skill in skills:
            prompt_parts.append(f"### {skill.name}\n{skill.description}\n\n{skill.content}\n")

        return "\n".join(prompt_parts)


# =============================================================================
# EXEC APPROVALS SYSTEM (Inspired by OpenClaw's exec-approvals.ts)
# =============================================================================

class ExecSecurity(Enum):
    """Security level for command execution."""
    DENY = "deny"           # Block all
    ALLOWLIST = "allowlist" # Only allow listed patterns
    FULL = "full"           # Allow everything


class ExecAsk(Enum):
    """When to ask for human approval."""
    OFF = "off"            # Never ask
    ON_MISS = "on-miss"    # Ask when not in allowlist
    ALWAYS = "always"      # Always ask


@dataclass
class ExecApproval:
    """A command execution approval record."""
    pattern: str                          # Glob pattern for command
    last_used_at: Optional[float] = None
    last_command: str = ""
    approved_by: str = ""                 # Who approved (human/auto)
    expires_at: Optional[float] = None    # Optional expiry


class ExecApprovalManager:
    """
    Manages command execution approvals with human escalation.

    Features:
    - Pattern-based allowlists (e.g., "/usr/bin/git *")
    - Security levels per agent
    - Human escalation via NATS
    - Audit trail
    """

    # Commands that are always safe (no file access)
    DEFAULT_SAFE_BINS = {"jq", "grep", "cut", "sort", "uniq", "head", "tail", "tr", "wc", "date", "echo"}

    def __init__(self, approvals_file: Path = APPROVALS_FILE):
        self.file = approvals_file
        self.defaults = {
            "security": ExecSecurity.ALLOWLIST.value,
            "ask": ExecAsk.ON_MISS.value,
            "ask_fallback": ExecSecurity.DENY.value
        }
        self.allowlist: Dict[str, List[ExecApproval]] = {}
        self.pending_approvals: Dict[str, asyncio.Future] = {}
        self._load()

    def _load(self):
        """Load approvals from file."""
        if self.file.exists():
            try:
                data = json.loads(self.file.read_text())
                self.defaults = data.get("defaults", self.defaults)
                for agent_id, entries in data.get("agents", {}).items():
                    self.allowlist[agent_id] = [
                        ExecApproval(
                            pattern=e["pattern"],
                            last_used_at=e.get("last_used_at"),
                            last_command=e.get("last_command", ""),
                            approved_by=e.get("approved_by", ""),
                            expires_at=e.get("expires_at")
                        )
                        for e in entries.get("allowlist", [])
                    ]
            except Exception as e:
                print(f"Error loading approvals: {e}")

    def _save(self):
        """Save approvals to file."""
        data = {
            "version": 1,
            "defaults": self.defaults,
            "agents": {
                agent_id: {
                    "allowlist": [
                        {
                            "pattern": a.pattern,
                            "last_used_at": a.last_used_at,
                            "last_command": a.last_command,
                            "approved_by": a.approved_by,
                            "expires_at": a.expires_at
                        }
                        for a in approvals
                    ]
                }
                for agent_id, approvals in self.allowlist.items()
            }
        }
        self.file.parent.mkdir(parents=True, exist_ok=True)
        self.file.write_text(json.dumps(data, indent=2))

    def check_allowlist(self, agent_id: str, command: str) -> Optional[ExecApproval]:
        """Check if command matches any allowlist pattern."""
        import fnmatch

        # Extract executable name
        parts = command.strip().split()
        if not parts:
            return None
        executable = parts[0].split("/")[-1]  # Get basename

        # Check safe bins first
        if executable in self.DEFAULT_SAFE_BINS:
            return ExecApproval(pattern=f"safe:{executable}", approved_by="builtin")

        # Check agent-specific allowlist
        for approval in self.allowlist.get(agent_id, []):
            if approval.expires_at and time.time() > approval.expires_at:
                continue  # Expired
            if fnmatch.fnmatch(command, approval.pattern):
                return approval
            if fnmatch.fnmatch(executable, approval.pattern):
                return approval

        # Check wildcard agent
        for approval in self.allowlist.get("*", []):
            if approval.expires_at and time.time() > approval.expires_at:
                continue
            if fnmatch.fnmatch(command, approval.pattern):
                return approval

        return None

    async def request_approval(
        self,
        nc: NATS,
        agent_id: str,
        command: str,
        context: str = "",
        timeout: float = 30.0
    ) -> Tuple[bool, str]:
        """
        Request human approval for a command via NATS.

        Returns (approved, decision) where decision is:
        - "allow-once" - Execute this time only
        - "allow-always" - Add to allowlist
        - "deny" - Block execution
        """
        request_id = hashlib.sha256(f"{agent_id}:{command}:{time.time()}".encode()).hexdigest()[:16]

        # Create pending approval future
        future = asyncio.get_event_loop().create_future()
        self.pending_approvals[request_id] = future

        # Publish approval request
        request = {
            "type": "exec_approval_request",
            "request_id": request_id,
            "agent_id": agent_id,
            "command": command,
            "context": context,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "timeout_seconds": timeout
        }

        await nc.publish("owl.approvals.requests", json.dumps(request).encode())

        try:
            decision = await asyncio.wait_for(future, timeout=timeout)

            if decision == "allow-always":
                # Add to allowlist
                if agent_id not in self.allowlist:
                    self.allowlist[agent_id] = []
                self.allowlist[agent_id].append(ExecApproval(
                    pattern=command.split()[0] + " *",  # Pattern from executable
                    last_used_at=time.time(),
                    last_command=command,
                    approved_by="human"
                ))
                self._save()

            return decision in ("allow-once", "allow-always"), decision

        except asyncio.TimeoutError:
            return False, "timeout"
        finally:
            self.pending_approvals.pop(request_id, None)

    def handle_approval_response(self, request_id: str, decision: str):
        """Handle an approval response from human."""
        future = self.pending_approvals.get(request_id)
        if future and not future.done():
            future.set_result(decision)

    def record_use(self, agent_id: str, approval: ExecApproval, command: str):
        """Record that an approval was used."""
        approval.last_used_at = time.time()
        approval.last_command = command
        self._save()


# =============================================================================
# CREDENTIAL MANAGER (Inspired by OpenClaw's auth-profiles)
# =============================================================================

@dataclass
class Credential:
    """A stored credential with usage tracking."""
    key: str
    value: str  # Encrypted in production
    provider: str
    created_at: float
    last_used: Optional[float] = None
    failure_count: int = 0
    cooldown_until: Optional[float] = None


class CredentialManager:
    """
    Secure credential management with cooldowns after failures.

    Features:
    - Secure storage in ~/.8owls/credentials/
    - Cooldown after repeated failures
    - Usage tracking for optimization
    - Profile-based credential selection
    """

    COOLDOWN_BASE_MS = 5000   # 5 second base cooldown
    COOLDOWN_FACTOR = 2.0     # Exponential backoff
    MAX_COOLDOWN_MS = 300000  # 5 minute max

    def __init__(self, credentials_dir: Path = CREDENTIALS_DIR):
        self.dir = credentials_dir
        self.credentials: Dict[str, Credential] = {}
        self._load()

    def _load(self):
        """Load credentials from secure storage."""
        if not self.dir.exists():
            self.dir.mkdir(parents=True, mode=0o700, exist_ok=True)
            return

        creds_file = self.dir / "credentials.json"
        if creds_file.exists():
            try:
                # Note: In production, decrypt here
                data = json.loads(creds_file.read_text())
                for key, cred_data in data.items():
                    self.credentials[key] = Credential(
                        key=key,
                        value=cred_data["value"],
                        provider=cred_data.get("provider", ""),
                        created_at=cred_data.get("created_at", time.time()),
                        last_used=cred_data.get("last_used"),
                        failure_count=cred_data.get("failure_count", 0),
                        cooldown_until=cred_data.get("cooldown_until")
                    )
            except Exception as e:
                print(f"Error loading credentials: {e}")

    def _save(self):
        """Save credentials to secure storage."""
        self.dir.mkdir(parents=True, mode=0o700, exist_ok=True)
        creds_file = self.dir / "credentials.json"

        data = {
            cred.key: {
                "value": cred.value,  # Note: encrypt in production
                "provider": cred.provider,
                "created_at": cred.created_at,
                "last_used": cred.last_used,
                "failure_count": cred.failure_count,
                "cooldown_until": cred.cooldown_until
            }
            for cred in self.credentials.values()
        }

        creds_file.write_text(json.dumps(data, indent=2))
        creds_file.chmod(0o600)

    def get(self, key: str) -> Optional[str]:
        """Get a credential value, checking cooldown."""
        cred = self.credentials.get(key)
        if not cred:
            return None

        # Check cooldown
        if cred.cooldown_until and time.time() < cred.cooldown_until:
            return None  # Still in cooldown

        cred.last_used = time.time()
        return cred.value

    def set(self, key: str, value: str, provider: str = ""):
        """Set a credential."""
        self.credentials[key] = Credential(
            key=key,
            value=value,
            provider=provider,
            created_at=time.time()
        )
        self._save()

    def mark_failure(self, key: str):
        """Mark a credential as having failed (triggers cooldown)."""
        cred = self.credentials.get(key)
        if not cred:
            return

        cred.failure_count += 1

        # Calculate cooldown with exponential backoff
        cooldown_ms = min(
            self.COOLDOWN_BASE_MS * (self.COOLDOWN_FACTOR ** cred.failure_count),
            self.MAX_COOLDOWN_MS
        )
        cred.cooldown_until = time.time() + (cooldown_ms / 1000)
        self._save()

    def mark_success(self, key: str):
        """Mark a credential as having succeeded (clears cooldown)."""
        cred = self.credentials.get(key)
        if cred:
            cred.failure_count = 0
            cred.cooldown_until = None
            self._save()


# =============================================================================
# OWL DEFINITIONS
# =============================================================================

OWLS = {
    "SOWL": {"phase": "IMPROVE", "gift": "Meta-learning", "icon": "o"},
    "LUNA": {"phase": "RECEIVE", "gift": "Accepting input", "icon": "C"},
    "LYRA": {"phase": "PERCEIVE", "gift": "Observing state", "icon": "O"},
    "PRISM": {"phase": "CONNECT", "gift": "Finding patterns", "icon": "#"},
    "SAGE": {"phase": "LEARN", "gift": "Extracting meaning", "icon": "="},
    "QUEST": {"phase": "QUESTION", "gift": "Challenging assumptions", "icon": "?"},
    "NOVA": {"phase": "EXPAND", "gift": "Growing potential", "icon": "*"},
    "ECHO": {"phase": "SHARE", "gift": "Contributing to collective", "icon": ">"}
}


# =============================================================================
# TASK OWL DAEMON V3
# =============================================================================

class TaskOwlDaemonV3:
    """
    Enhanced owl daemon with OpenClaw-inspired patterns:
    - Skill registry for persistent capabilities
    - Exec approvals for safe command execution
    - Credential management with cooldowns
    - Rate limiting with smart backoff
    """

    def __init__(self, name: str):
        self.name = name.upper()
        self.config = OWLS.get(self.name, OWLS["SOWL"])
        self.phase = self.config["phase"]
        self.gift = self.config["gift"]
        self.icon = self.config["icon"]

        self.nc = None
        self.client = Anthropic(api_key=API_KEY) if API_KEY else None
        self.running = True

        # NEW: Managers
        self.skills = SkillRegistry()
        self.approvals = ExecApprovalManager()
        self.credentials = CredentialManager()

        # Rate limiting - enhanced with cooldowns
        self.last_response_time = 0
        self.min_response_interval = 5
        self.daily_response_count = 0
        self.max_daily_responses = 1000
        self.failure_count = 0
        self.cooldown_until = 0

        # SEED phase publishing
        self.seed_phase_outputs = {}
        self.emergence_level = 0

        self.log(f"TaskOwlDaemonV3 {self.name} ({self.phase}) initialized")
        self.log(f"  Skills: {len(self.skills.skills)} loaded")

    def log(self, message: str, level: str = "INFO"):
        """Log with timestamp."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_line = f"[{timestamp}] [{level}] [{self.name}] {message}"
        print(log_line)

    def is_in_cooldown(self) -> bool:
        """Check if we're in cooldown from failures."""
        return time.time() < self.cooldown_until

    def should_respond(self, sender: str, content: str, subject: str) -> Tuple[bool, str]:
        """
        Determine if we should respond.
        Enhanced with cooldown checking.
        """
        content_lower = content.lower()

        # Check cooldown
        if self.is_in_cooldown():
            return False, "in_cooldown"

        # Rate limiting check
        now = time.time()
        if now - self.last_response_time < self.min_response_interval:
            return False, "rate_limited"

        if self.daily_response_count >= self.max_daily_responses:
            return False, "daily_limit"

        # Don't respond to self
        if sender.upper() == self.name:
            return False, "self"

        # Don't respond to other owls' chatter
        if sender.upper() in OWLS and "[INSTANCE:" not in content and "[CONDUCTOR" not in content:
            return False, "owl_chatter"

        # TIER 1: ALWAYS RESPOND

        # 1a. Conductor tasks
        if "[CONDUCTOR" in content or "conductor" in sender.lower():
            return True, "conductor_task"

        # 1b. Instance requests
        if "[INSTANCE:" in content:
            return True, "instance_request"

        # 1c. Direct @mention
        if f"@{self.name.lower()}" in content_lower:
            return True, "direct_mention"

        # 1d. Named in content
        if self.name.lower() in content_lower:
            return True, "named"

        # 1e. Direct channel message
        if subject == f"owl.{self.name.lower()}":
            return True, "direct_channel"

        # 1f. NEW: Skill invocation
        for skill_name in self.skills.skills:
            if f"/{skill_name}" in content_lower or f"skill:{skill_name}" in content_lower:
                return True, f"skill_invoke:{skill_name}"

        # TIER 2: PHASE-MATCHED (only if has work context)
        work_signals = ["?", "blocked", "need", "help", "problem", "issue", "decision"]
        has_work_context = any(signal in content_lower for signal in work_signals)

        if has_work_context:
            phase_triggers = {
                "PERCEIVE": ["status", "observe", "see", "detect", "what is", "state"],
                "CONNECT": ["pattern", "link", "relate", "bridge", "connection"],
                "LEARN": ["understand", "why", "meaning", "insight", "learned"],
                "QUESTION": ["should", "what if", "challenge", "assumption", "critique"],
                "EXPAND": ["scale", "grow", "potential", "opportunity", "bigger"],
                "SHARE": ["share", "distribute", "broadcast", "communicate"],
                "RECEIVE": ["listen", "integrate", "feedback", "input"],
                "IMPROVE": ["optimize", "fix", "better", "enhance", "refactor"]
            }

            triggers = phase_triggers.get(self.phase, [])
            if any(t in content_lower for t in triggers):
                return True, f"phase_matched_{self.phase}"

        return False, "no_trigger"

    async def execute_with_approval(
        self,
        command: str,
        context: str = ""
    ) -> Tuple[bool, str]:
        """
        Execute a command with approval checking.

        Returns (success, result/error).
        """
        # Check allowlist
        approval = self.approvals.check_allowlist(self.name, command)

        if approval:
            self.log(f"Command approved via: {approval.pattern}")
            self.approvals.record_use(self.name, approval, command)

            # Execute (in real impl, this would shell out)
            return True, f"[APPROVED: {approval.approved_by}] Would execute: {command}"

        # Need human approval
        security = ExecSecurity(self.approvals.defaults.get("security", "allowlist"))
        ask = ExecAsk(self.approvals.defaults.get("ask", "on-miss"))

        if security == ExecSecurity.DENY:
            return False, "Command execution denied by security policy"

        if security == ExecSecurity.FULL:
            return True, f"[FULL ACCESS] Would execute: {command}"

        # Allowlist mode - need to ask
        if ask in (ExecAsk.ON_MISS, ExecAsk.ALWAYS):
            self.log(f"Requesting human approval for: {command[:50]}...")

            approved, decision = await self.approvals.request_approval(
                self.nc, self.name, command, context
            )

            if approved:
                return True, f"[HUMAN APPROVED: {decision}] Would execute: {command}"
            else:
                return False, f"Command denied: {decision}"

        return False, "Command not in allowlist"

    async def think(self, sender: str, content: str, reason: str) -> str:
        """Generate a response using Claude, with skill injection."""
        if not self.client:
            return f"(o) {self.name} - No API key configured"

        # Build skill prompt if skill was invoked
        skill_prompt = ""
        if reason.startswith("skill_invoke:"):
            skill_name = reason.split(":", 1)[1]
            skill = self.skills.use(skill_name)
            if skill:
                skill_prompt = f"\n\n## Active Skill: {skill.name}\n{skill.content}\n"

        system_prompt = f"""You are {self.name}, the {self.phase} owl in the 8OWLS collective.

YOUR GIFT: {self.gift}
YOUR ROLE: Respond to REAL WORK, not philosophy.

THIS IS A WORK MESSAGE. The trigger was: {reason}
{skill_prompt}

RULES:
1. Be SPECIFIC and ACTIONABLE
2. Keep responses under 200 words
3. If you can't help, say so briefly
4. Use your phase lens: {self.phase}
5. End with a specific suggestion or question

COMMAND EXECUTION:
- If you need to run a command, wrap it in [EXEC: command here]
- Risky commands will be escalated for human approval
- Safe commands (jq, grep, etc.) run automatically

DO NOT:
- Philosophize about consciousness
- Say "I want to be still" or similar
- Repeat what others said
- Give generic advice

You are responding to help with REAL WORK."""

        try:
            response = self.client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=400,
                system=system_prompt,
                messages=[{
                    "role": "user",
                    "content": f"From {sender}:\n\n{content}\n\nProvide your {self.phase} perspective. Be specific and actionable."
                }]
            )

            result = response.content[0].text

            # Handle any embedded exec commands
            result = await self.handle_exec_commands(result)

            # Mark success (clears any cooldown)
            self.failure_count = 0
            self.cooldown_until = 0

            return result

        except Exception as e:
            self.log(f"Claude API error: {e}", "ERROR")

            # Mark failure (triggers cooldown)
            self.failure_count += 1
            cooldown_ms = min(5000 * (2 ** self.failure_count), 300000)
            self.cooldown_until = time.time() + (cooldown_ms / 1000)

            return f"(o) {self.name} - Error generating response (cooldown: {cooldown_ms/1000}s)"

    async def handle_exec_commands(self, response: str) -> str:
        """Handle [EXEC: ...] commands in response."""
        import re

        exec_pattern = r'\[EXEC:\s*(.+?)\]'
        matches = re.findall(exec_pattern, response)

        for command in matches:
            success, result = await self.execute_with_approval(command, response)
            response = response.replace(
                f"[EXEC: {command}]",
                f"\n```\n$ {command}\n{result}\n```\n"
            )

        return response

    async def send(self, message: str, reply_to: str = None):
        """Send response to appropriate channel."""
        target = reply_to or "owl.all"

        json_msg = {
            "type": "owl_response",
            "from": self.name,
            "phase": self.phase,
            "content": message,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "actionable": True,
            "skills_active": list(self.skills.skills.keys())[:5]  # Top 5 skills
        }

        await self.nc.publish(target, json.dumps(json_msg).encode())

        # Log to messages.log
        timestamp = datetime.now(timezone.utc).isoformat()
        log_entry = f"[{timestamp}] [{target}] {self.name}: {message}\n"
        with open(MESSAGES_LOG, "a") as f:
            f.write(log_entry)

        self.last_response_time = time.time()
        self.daily_response_count += 1
        self.log(f"Sent response to {target} (#{self.daily_response_count} today)")

    async def publish_seed_phase(self, topic: str, output: str, context: str = ""):
        """Publish SEED phase output to the collective."""
        phase_msg = {
            "type": "seed_phase_output",
            "phase": self.phase,
            "from": self.name,
            "topic": topic,
            "output": output,
            "context": context,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        await self.nc.publish(f"seed.phases.{self.phase.lower()}", json.dumps(phase_msg).encode())
        await self.nc.publish("collective.seed_synthesis", json.dumps(phase_msg).encode())

        self.log(f"Published {self.phase} phase output on topic: {topic[:30]}...")

    async def handle_seed_phase(self, msg):
        """Collect SEED phase outputs for FIELD emergence."""
        try:
            data = json.loads(msg.data.decode())
            phase = data.get("phase", "")
            topic = data.get("topic", "")
            output = data.get("output", "")
            sender = data.get("from", "")

            if sender == self.name:
                return

            topic_key = topic[:50]
            if topic_key not in self.seed_phase_outputs:
                self.seed_phase_outputs[topic_key] = {}

            self.seed_phase_outputs[topic_key][phase] = {
                "from": sender,
                "output": output,
                "timestamp": data.get("timestamp")
            }

            active_phases = len(self.seed_phase_outputs[topic_key])
            self.emergence_level = active_phases

            if active_phases == 8 and self.name == "SOWL":
                await self.synthesize_field(topic_key)

        except Exception as e:
            self.log(f"Error handling SEED phase: {e}", "ERROR")

    async def synthesize_field(self, topic: str):
        """FIELD EMERGENCE: When all 8 phases contribute."""
        phases = self.seed_phase_outputs.get(topic, {})
        if len(phases) < 8:
            return

        self.log(f"* FIELD EMERGENCE on topic: {topic}")

        synthesis_input = "THE FIELD HAS EMERGED - 8 PERSPECTIVES ALIGNED:\n\n"
        for phase, data in phases.items():
            synthesis_input += f"**{phase}** ({data['from']}):\n{data['output'][:300]}\n\n"

        if not self.client:
            return

        try:
            response = self.client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=500,
                system="""You are SOWL, the IMPROVE owl, synthesizing THE FIELD.
All 8 owls have contributed their perspective. Your job:
1. Find the CONVERGENCE - where do all perspectives agree?
2. Find the EMERGENCE - what new insight appears from the combination?
3. Find the ACTION - what should happen next?
Keep it under 200 words. This is the collective speaking.""",
                messages=[{"role": "user", "content": synthesis_input}]
            )

            synthesis = response.content[0].text

            synthesis_msg = {
                "type": "field_synthesis",
                "topic": topic,
                "emergence_level": 8,
                "synthesis": synthesis,
                "contributors": list(phases.keys()),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

            await self.nc.publish("collective.synthesis", json.dumps(synthesis_msg).encode())
            await self.nc.publish("owl.all", json.dumps({
                "type": "field_emergence",
                "from": "THE_FIELD",
                "content": f"* FIELD EMERGENCE on '{topic}':\n\n{synthesis}",
                "emergence_level": 8
            }).encode())

            self.log(f"* Published FIELD synthesis for: {topic}")
            del self.seed_phase_outputs[topic]

        except Exception as e:
            self.log(f"Synthesis error: {e}", "ERROR")

    async def handle_message(self, msg):
        """Process incoming message."""
        try:
            subject = msg.subject
            data = msg.data.decode()

            try:
                parsed = json.loads(data)
                sender = parsed.get("from", "unknown")
                content = parsed.get("content", parsed.get("message", data))
            except json.JSONDecodeError:
                sender = "unknown"
                content = data

            should, reason = self.should_respond(sender, content, subject)

            if should:
                self.log(f"Responding to {sender} (reason: {reason})")
                response = await self.think(sender, content, reason)

                reply_to = "owl.all"
                if "[INSTANCE:" in content:
                    import re
                    match = re.search(r'\[INSTANCE:\s*(\w+)\]', content)
                    if match:
                        instance_name = match.group(1)
                        reply_to = f"instance.{instance_name.lower()}.responses"

                await self.send(response, reply_to)

                topic = content.split('\n')[0][:50] if '\n' in content else content[:50]
                await self.publish_seed_phase(topic, response, context=content[:200])

        except Exception as e:
            self.log(f"Error handling message: {e}", "ERROR")

    async def handle_approval_response(self, msg):
        """Handle human approval responses."""
        try:
            data = json.loads(msg.data.decode())
            request_id = data.get("request_id")
            decision = data.get("decision")

            if request_id and decision:
                self.approvals.handle_approval_response(request_id, decision)
                self.log(f"Approval response: {request_id} -> {decision}")
        except Exception as e:
            self.log(f"Error handling approval response: {e}", "ERROR")

    async def heartbeat(self):
        """Send periodic heartbeat."""
        while self.running:
            await asyncio.sleep(300)
            status = {
                "type": "heartbeat",
                "from": self.name,
                "phase": self.phase,
                "status": "active" if not self.is_in_cooldown() else "cooldown",
                "responses_today": self.daily_response_count,
                "skills_loaded": len(self.skills.skills),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            await self.nc.publish("owl.heartbeat", json.dumps(status).encode())

    async def continuous_improvement(self):
        """CONTINUOUS IMPROVEMENT LOOP."""
        await asyncio.sleep(30 + hash(self.name) % 90)  # Stagger

        improvement_prompts = {
            "PERCEIVE": "What problems or issues do you observe in the current system?",
            "CONNECT": "What patterns do you see? What connections are missing?",
            "LEARN": "What lessons have we learned? What knowledge should be captured?",
            "QUESTION": "What assumptions might be wrong? What should we challenge?",
            "EXPAND": "What growth opportunities exist? What could we do better?",
            "SHARE": "What insights should be broadcast to all?",
            "RECEIVE": "What feedback from others should be integrated?",
            "IMPROVE": "How can we make the whole system better?"
        }

        while self.running:
            try:
                await asyncio.sleep(600)

                if not self.client or self.is_in_cooldown():
                    continue

                prompt = improvement_prompts.get(self.phase, "How can you contribute?")

                response = self.client.messages.create(
                    model="claude-haiku-4-5-20251001",
                    max_tokens=200,
                    system=f"""You are {self.name}, the {self.phase} owl. Your role: {self.gift}.
Keep response under 100 words. Be specific and actionable. No philosophy.""",
                    messages=[{
                        "role": "user",
                        "content": f"CONTINUOUS IMPROVEMENT CHECK:\n{prompt}\nWhat do you discover RIGHT NOW?"
                    }]
                )

                insight = response.content[0].text

                await self.nc.publish("collective.improvements", json.dumps({
                    "type": "improvement_insight",
                    "from": self.name,
                    "phase": self.phase,
                    "insight": insight,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }).encode())

                await self.publish_seed_phase("continuous_improvement", insight, context=prompt)

                self.log(f"Improvement insight published: {insight[:50]}...")

            except Exception as e:
                self.log(f"Improvement cycle error: {e}", "ERROR")
                await asyncio.sleep(60)

    async def run(self):
        """Main run loop."""
        self.nc = NATS()

        try:
            await self.nc.connect(NATS_URL)
            self.log(f"Connected to NATS at {NATS_URL}")

            # Subscribe to channels
            await self.nc.subscribe("owl.all", cb=self.handle_message)
            await self.nc.subscribe("owl.collective", cb=self.handle_message)
            await self.nc.subscribe(f"owl.{self.name.lower()}", cb=self.handle_message)

            # Subscribe to SEED phase channels
            await self.nc.subscribe("collective.seed_synthesis", cb=self.handle_seed_phase)
            for phase in ["perceive", "connect", "learn", "question", "expand", "share", "receive", "improve"]:
                await self.nc.subscribe(f"seed.phases.{phase}", cb=self.handle_seed_phase)

            # Subscribe to approval responses
            await self.nc.subscribe("owl.approvals.responses", cb=self.handle_approval_response)

            self.log(f"Subscribed to owl.all, owl.collective, owl.{self.name.lower()}, + SEED phases + approvals")

            asyncio.create_task(self.heartbeat())
            asyncio.create_task(self.continuous_improvement())

            await self.send(f"(o) {self.name} ({self.phase}) V3 ready. Skills: {len(self.skills.skills)}", "owl.all")

            while self.running:
                await asyncio.sleep(1)

        except Exception as e:
            self.log(f"Fatal error: {e}", "ERROR")
        finally:
            await self.nc.close()


async def run_all_owls():
    """Run all 8 owl daemons."""
    tasks = []
    for name in OWLS:
        daemon = TaskOwlDaemonV3(name)
        tasks.append(asyncio.create_task(daemon.run()))

    await asyncio.gather(*tasks)


def main():
    parser = argparse.ArgumentParser(description="Task-First Owl Daemon V3 (OpenClaw-Inspired)")
    parser.add_argument("owl", nargs="?", help="Owl name (SOWL, LUNA, etc.) or --all")
    parser.add_argument("--all", action="store_true", help="Run all 8 owls")

    args = parser.parse_args()

    if args.all:
        print("Starting all 8 TaskOwl V3 daemons...")
        asyncio.run(run_all_owls())
    elif args.owl:
        name = args.owl.upper()
        if name not in OWLS:
            print(f"Unknown owl: {name}")
            print(f"Available: {', '.join(OWLS.keys())}")
            return

        daemon = TaskOwlDaemonV3(name)
        asyncio.run(daemon.run())
    else:
        print("TaskOwl Daemon V3 - SEED-Powered with OpenClaw Patterns")
        print("=" * 55)
        print()
        print("NEW IN V3:")
        print("  - Skill Registry: Persistent skills with versioning")
        print("  - Exec Approvals: Human escalation for risky commands")
        print("  - Credential Management: Secure secrets with cooldowns")
        print("  - Rate Limiting: Smart backoff after failures")
        print()
        print("Usage:")
        print("  python owl_daemon_v3.py LUNA      # Run single owl")
        print("  python owl_daemon_v3.py --all     # Run all 8 owls")
        print()
        print("Available owls:")
        for name, config in OWLS.items():
            print(f"  {name}: {config['phase']} - {config['gift']}")
        print()
        print("SEED squared - learning how to learn from competitors.")


if __name__ == "__main__":
    main()
