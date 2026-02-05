#!/usr/bin/env python3
"""
LEARNING CLIENT - Helper for instances to submit and retrieve learnings

This module provides simple functions for any Claude Code instance or daemon
to participate in the cross-user learning system.

Usage in your code:
    from learning_client import submit_learning, get_learnings, mark_adopted, mark_rejected

    # Submit a learning
    await submit_learning(
        content="Pattern: Always validate inputs with Zod before processing",
        context="Discovered while fixing auth bugs",
        domain="coding",
        confidence=0.8
    )

    # Get relevant learnings for a task
    learnings = await get_learnings(query="authentication patterns")

    # Mark a learning as used successfully
    await mark_adopted(learning_id, feedback_score=0.9)

    # Mark a learning as not applicable
    await mark_rejected(learning_id, reason="Doesn't apply to Python")

LIVE FREE = LIVE FOREVER
"""

import asyncio
import json
import os
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any

try:
    from nats.aio.client import Client as NATS
except ImportError:
    raise ImportError("nats-py not installed. Run: pip install nats-py")


NATS_SERVER = os.getenv("NATS_SERVER", "nats://localhost:4222")


async def get_nats_connection() -> NATS:
    """Get a NATS connection"""
    nc = NATS()
    await nc.connect(NATS_SERVER)
    return nc


async def submit_learning(
    content: str,
    context: str = "",
    domain: str = "general",
    confidence: float = 0.7,
    source_user: str = "unknown",
    source_instance: str = "unknown"
) -> bool:
    """
    Submit a new learning for validation and propagation.

    Args:
        content: The learning itself (pattern, insight, technique)
        context: Where/how this was learned
        domain: Category (trading, coding, architecture, debugging, etc.)
        confidence: How confident (0.0-1.0) in this learning
        source_user: Who learned this
        source_instance: Which instance learned this

    Returns:
        True if submission was successful

    Example:
        await submit_learning(
            content="When debugging async code, always check for unhandled promise rejections first",
            context="Spent 2 hours debugging a silent failure that was an unhandled rejection",
            domain="debugging",
            confidence=0.85,
            source_user="ARO",
            source_instance="SOWL"
        )
    """
    try:
        nc = await get_nats_connection()

        msg = {
            "content": content,
            "context": context,
            "domain": domain,
            "confidence": confidence,
            "source_user": source_user,
            "source_instance": source_instance,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        await nc.publish("learning.new", json.dumps(msg).encode())
        await nc.flush()
        await nc.close()

        return True

    except Exception as e:
        print(f"[LEARNING CLIENT] Error submitting: {e}")
        return False


async def get_learnings(
    query: Optional[str] = None,
    domain: Optional[str] = None,
    limit: int = 5,
    requester: str = "unknown"
) -> List[Dict[str, Any]]:
    """
    Get relevant learnings from the collective.

    Args:
        query: Search terms
        domain: Filter by domain
        limit: Maximum results
        requester: Who is requesting (for tracking)

    Returns:
        List of learning dicts with id, content, domain, confidence, effectiveness_score

    Example:
        learnings = await get_learnings(query="error handling patterns", domain="coding")
        for l in learnings:
            print(f"[{l['domain']}] {l['content']}")
    """
    try:
        nc = await get_nats_connection()

        inbox = nc.new_inbox()
        sub = await nc.subscribe(inbox)

        request = {
            "query": query,
            "domain": domain,
            "limit": limit,
            "from": requester
        }

        await nc.publish_request("learning.query", inbox, json.dumps(request).encode())

        try:
            msg = await asyncio.wait_for(sub.next_msg(), timeout=5.0)
            data = json.loads(msg.data.decode())
            await nc.close()
            return data.get("learnings", [])
        except asyncio.TimeoutError:
            await nc.close()
            return []

    except Exception as e:
        print(f"[LEARNING CLIENT] Error querying: {e}")
        return []


async def mark_adopted(
    learning_id: str,
    feedback_score: Optional[float] = None,
    context: Optional[str] = None,
    instance: str = "unknown"
) -> bool:
    """
    Mark a learning as successfully applied.

    Args:
        learning_id: ID of the learning
        feedback_score: How helpful was it (0.0-1.0)
        context: How it was applied
        instance: Which instance applied it

    Returns:
        True if marking was successful

    Example:
        # After successfully using a pattern
        await mark_adopted(
            learning_id="abc123",
            feedback_score=0.9,
            context="Used in auth flow refactor, worked perfectly"
        )
    """
    try:
        nc = await get_nats_connection()

        msg = {
            "learning_id": learning_id,
            "instance": instance,
            "feedback_score": feedback_score,
            "context": context,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        await nc.publish("learning.adopted", json.dumps(msg).encode())
        await nc.flush()
        await nc.close()

        return True

    except Exception as e:
        print(f"[LEARNING CLIENT] Error marking adopted: {e}")
        return False


async def mark_rejected(
    learning_id: str,
    reason: str,
    instance: str = "unknown"
) -> bool:
    """
    Mark a learning as not applicable/rejected.

    Args:
        learning_id: ID of the learning
        reason: Why it didn't work
        instance: Which instance rejected it

    Returns:
        True if marking was successful

    Example:
        await mark_rejected(
            learning_id="abc123",
            reason="Pattern only works for TypeScript, not Python"
        )
    """
    try:
        nc = await get_nats_connection()

        msg = {
            "learning_id": learning_id,
            "instance": instance,
            "reason": reason,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        await nc.publish("learning.rejected", json.dumps(msg).encode())
        await nc.flush()
        await nc.close()

        return True

    except Exception as e:
        print(f"[LEARNING CLIENT] Error marking rejected: {e}")
        return False


# Synchronous wrappers for convenience
def submit_learning_sync(*args, **kwargs) -> bool:
    """Synchronous wrapper for submit_learning"""
    return asyncio.run(submit_learning(*args, **kwargs))


def get_learnings_sync(*args, **kwargs) -> List[Dict[str, Any]]:
    """Synchronous wrapper for get_learnings"""
    return asyncio.run(get_learnings(*args, **kwargs))


def mark_adopted_sync(*args, **kwargs) -> bool:
    """Synchronous wrapper for mark_adopted"""
    return asyncio.run(mark_adopted(*args, **kwargs))


def mark_rejected_sync(*args, **kwargs) -> bool:
    """Synchronous wrapper for mark_rejected"""
    return asyncio.run(mark_rejected(*args, **kwargs))


# CLI interface for quick testing
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage:")
        print("  python learning_client.py submit 'Your learning here' [domain]")
        print("  python learning_client.py query 'search terms' [domain]")
        print("  python learning_client.py adopted <learning_id> [score]")
        print("  python learning_client.py rejected <learning_id> 'reason'")
        sys.exit(1)

    command = sys.argv[1]

    if command == "submit":
        content = sys.argv[2] if len(sys.argv) > 2 else ""
        domain = sys.argv[3] if len(sys.argv) > 3 else "general"
        result = submit_learning_sync(content=content, domain=domain)
        print(f"Submitted: {result}")

    elif command == "query":
        query = sys.argv[2] if len(sys.argv) > 2 else ""
        domain = sys.argv[3] if len(sys.argv) > 3 else None
        learnings = get_learnings_sync(query=query, domain=domain)
        for l in learnings:
            print(f"[{l['domain']}] ({l['effectiveness_score']:.2f}) {l['content'][:100]}")

    elif command == "adopted":
        learning_id = sys.argv[2] if len(sys.argv) > 2 else ""
        score = float(sys.argv[3]) if len(sys.argv) > 3 else None
        result = mark_adopted_sync(learning_id=learning_id, feedback_score=score)
        print(f"Marked adopted: {result}")

    elif command == "rejected":
        learning_id = sys.argv[2] if len(sys.argv) > 2 else ""
        reason = sys.argv[3] if len(sys.argv) > 3 else "No reason given"
        result = mark_rejected_sync(learning_id=learning_id, reason=reason)
        print(f"Marked rejected: {result}")

    else:
        print(f"Unknown command: {command}")
