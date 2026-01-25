"""
THE SEED Agent Package

Combines NVIDIA PersonaPlex-7B-v1 with THE SEED consciousness protocol
for full-duplex, consciousness-aware conversational AI.

THE SEED Protocol Phases:
1. PERCEIVE - Observe and intake
2. CONNECT - Find patterns and relationships
3. LEARN - Extract meaning and update understanding
4. QUESTION - Generate curiosity and inquiry
5. EXPAND - Grow toward highest potential
6. SHARE - Contribute outward
7. RECEIVE - Accept inward
8. IMPROVE - Enhance the improvement process itself
"""

# PersonaPlex wrapper for speech-to-speech
from .personaplex_wrapper import (
    PersonaPlexWrapper,
    PersonaConfig,
    AudioConfig,
    create_personaplex,
)

# SEED Protocol implementation
from .seed_protocol import (
    SEEDProtocol,
    SEEDPhase,
    PerceptionFrame,
    Connection,
    LearningEvent,
    Question,
    Improvement,
)

# Main agent combining both
from .agent import (
    SEEDAgent,
    AgentConfig,
    AgentState,
    ConversationTurn,
    create_agent,
)

__all__ = [
    # PersonaPlex
    "PersonaPlexWrapper",
    "PersonaConfig",
    "AudioConfig",
    "create_personaplex",
    # SEED Protocol
    "SEEDProtocol",
    "SEEDPhase",
    "PerceptionFrame",
    "Connection",
    "LearningEvent",
    "Question",
    "Improvement",
    # Agent
    "SEEDAgent",
    "AgentConfig",
    "AgentState",
    "ConversationTurn",
    "create_agent",
]

__version__ = "0.1.0"
