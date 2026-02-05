#!/usr/bin/env python3
"""
NEVER FORGET - Persistent Memory That Compounds

The eternal memory system for 8OWLS. Nothing is ever lost.
Every insight gets stored. Every pattern gets indexed.
Every mistake gets logged. Every success gets recorded.

Usage:
    # Store different types of knowledge
    python3 never_forget.py store --type insight --topic "trading" --content "Kelly criterion needs variance adjustment"
    python3 never_forget.py store --type pattern --topic "code" --content "Always use immutable updates"
    python3 never_forget.py store --type mistake --topic "trading" --content "Don't chase losses"
    python3 never_forget.py store --type success --topic "8owls" --content "d=0.99 emergence validated"
    python3 never_forget.py store --type relationship --topic "Andrew" --content "Technical lead, likes clean code"
    python3 never_forget.py store --type opportunity --topic "ARC-AGI" --content "Use SEED refinement approach"

    # Retrieve knowledge
    python3 never_forget.py recall "What do we know about trading?"
    python3 never_forget.py recall "What worked last time we did authentication?"
    python3 never_forget.py recall "Who should we talk to about design?"

    # Compound learning - find cross-connections
    python3 never_forget.py compound --topic "trading"
    python3 never_forget.py compound --all

    # Export/import memory
    python3 never_forget.py export --output memory_backup.json
    python3 never_forget.py import --input memory_backup.json

    # Stats and health
    python3 never_forget.py stats
    python3 never_forget.py search --type insight --topic "trading"

Integration:
    - Stores in both file system (BRAIN/MEMORY/*) and claude-flow HNSW memory
    - NATS broadcast on important memories
    - Cross-session persistence
    - Semantic search via embeddings
"""

import argparse
import asyncio
import json
import os
import subprocess
import sys
import uuid
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List, Dict, Any, Literal

# Constants
SEED_ROOT = Path(__file__).parent.parent
BRAIN_MEMORY = SEED_ROOT / "BRAIN" / "MEMORY"
NATS_BRIDGE = SEED_ROOT / "mcp-servers" / "nats-bridge"

# Memory types and their directories
MEMORY_TYPES = {
    "pattern": "patterns",
    "insight": "insights",
    "mistake": "mistakes",
    "success": "successes",
    "relationship": "relationships",
    "opportunity": "opportunities",
    "compound": "compound"
}

# Importance levels for NATS broadcast
IMPORTANCE_LEVELS = {
    "critical": 5,    # Broadcast immediately to all
    "high": 4,        # Broadcast to relevant channels
    "medium": 3,      # Store and index
    "low": 2,         # Store only
    "trivial": 1      # Store with expiry
}


class NeverForget:
    """Eternal memory system that compounds knowledge over time."""

    def __init__(self):
        self.ensure_directories()
        self.index_path = BRAIN_MEMORY / "compound" / "knowledge_index.json"
        self.index = self._load_index()

    def ensure_directories(self):
        """Ensure all memory directories exist."""
        for dir_name in MEMORY_TYPES.values():
            (BRAIN_MEMORY / dir_name).mkdir(parents=True, exist_ok=True)

    def _load_index(self) -> Dict[str, Any]:
        """Load the knowledge index for cross-referencing."""
        if self.index_path.exists():
            with open(self.index_path, "r") as f:
                return json.load(f)
        return {
            "entries": {},           # id -> entry metadata
            "by_type": {},           # type -> [ids]
            "by_topic": {},          # topic -> [ids]
            "by_date": {},           # YYYY-MM-DD -> [ids]
            "connections": {},       # id -> [related_ids]
            "stats": {
                "total_entries": 0,
                "by_type": {},
                "last_compound": None
            }
        }

    def _save_index(self):
        """Persist the knowledge index."""
        with open(self.index_path, "w") as f:
            json.dump(self.index, f, indent=2)

    def _generate_id(self, content: str, topic: str, mem_type: str) -> str:
        """Generate a unique, content-addressable ID."""
        hash_input = f"{mem_type}:{topic}:{content}".encode()
        return hashlib.sha256(hash_input).hexdigest()[:16]

    def _get_filename(self, mem_type: str, topic: str, timestamp: str) -> str:
        """Generate filename for storage."""
        safe_topic = topic.replace(" ", "-").replace("/", "-").lower()[:30]
        return f"{timestamp}_{safe_topic}.json"

    async def store(
        self,
        mem_type: str,
        topic: str,
        content: str,
        importance: str = "medium",
        tags: List[str] = None,
        source: str = None,
        metadata: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Store a piece of knowledge in eternal memory.

        Returns the stored entry with its ID.
        """
        if mem_type not in MEMORY_TYPES:
            raise ValueError(f"Unknown memory type: {mem_type}. Valid types: {list(MEMORY_TYPES.keys())}")

        timestamp = datetime.now()
        entry_id = self._generate_id(content, topic, mem_type)
        date_str = timestamp.strftime("%Y-%m-%d")
        time_str = timestamp.strftime("%Y%m%d_%H%M%S")

        # Build the entry
        entry = {
            "id": entry_id,
            "type": mem_type,
            "topic": topic,
            "content": content,
            "importance": importance,
            "tags": tags or [],
            "source": source,
            "metadata": metadata or {},
            "created_at": timestamp.isoformat(),
            "updated_at": timestamp.isoformat(),
            "access_count": 0,
            "last_accessed": None,
            "connections": []
        }

        # 1. Store in file system
        dir_path = BRAIN_MEMORY / MEMORY_TYPES[mem_type]
        file_path = dir_path / self._get_filename(mem_type, topic, time_str)

        with open(file_path, "w") as f:
            json.dump(entry, f, indent=2)

        # 2. Update index
        self.index["entries"][entry_id] = {
            "type": mem_type,
            "topic": topic,
            "file": str(file_path.relative_to(BRAIN_MEMORY)),
            "importance": importance,
            "created_at": timestamp.isoformat(),
            "tags": tags or [],
            "summary": content[:100] + "..." if len(content) > 100 else content
        }

        # Index by type
        if mem_type not in self.index["by_type"]:
            self.index["by_type"][mem_type] = []
        if entry_id not in self.index["by_type"][mem_type]:
            self.index["by_type"][mem_type].append(entry_id)

        # Index by topic
        if topic not in self.index["by_topic"]:
            self.index["by_topic"][topic] = []
        if entry_id not in self.index["by_topic"][topic]:
            self.index["by_topic"][topic].append(entry_id)

        # Index by date
        if date_str not in self.index["by_date"]:
            self.index["by_date"][date_str] = []
        if entry_id not in self.index["by_date"][date_str]:
            self.index["by_date"][date_str].append(entry_id)

        # Update stats
        self.index["stats"]["total_entries"] = len(self.index["entries"])
        if mem_type not in self.index["stats"]["by_type"]:
            self.index["stats"]["by_type"][mem_type] = 0
        self.index["stats"]["by_type"][mem_type] += 1

        self._save_index()

        # 3. Store in claude-flow memory (HNSW-indexed)
        await self._store_in_claude_flow(entry)

        # 4. Broadcast to NATS if important
        if IMPORTANCE_LEVELS.get(importance, 3) >= 4:
            await self._broadcast_to_nats(entry)

        # 5. Find and create connections
        connections = await self._find_connections(entry)
        if connections:
            entry["connections"] = connections
            self.index["connections"][entry_id] = connections
            self._save_index()

            # Update file with connections
            with open(file_path, "w") as f:
                json.dump(entry, f, indent=2)

        return entry

    async def _store_in_claude_flow(self, entry: Dict[str, Any]):
        """Store entry in claude-flow HNSW-indexed memory."""
        try:
            # Build namespace based on type
            namespace = f"neverforget-{entry['type']}"
            key = entry["id"]
            value = json.dumps({
                "topic": entry["topic"],
                "content": entry["content"],
                "importance": entry["importance"],
                "tags": entry["tags"],
                "created_at": entry["created_at"]
            })

            # Use claude-flow CLI
            cmd = [
                "npx", "@claude-flow/cli@latest", "memory", "store",
                "--key", key,
                "--value", value,
                "--namespace", namespace
            ]

            if entry.get("tags"):
                cmd.extend(["--tags", ",".join(entry["tags"])])

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode != 0:
                print(f"[WARN] claude-flow store failed: {result.stderr}", file=sys.stderr)

        except subprocess.TimeoutExpired:
            print("[WARN] claude-flow store timed out", file=sys.stderr)
        except Exception as e:
            print(f"[WARN] claude-flow store error: {e}", file=sys.stderr)

    async def _broadcast_to_nats(self, entry: Dict[str, Any]):
        """Broadcast important memories to NATS collective."""
        try:
            # Import nats_publish from tools
            sys.path.insert(0, str(SEED_ROOT / "tools"))
            from nats_publish import publish

            message = f"[MEMORY] {entry['type'].upper()}: {entry['topic']} - {entry['content'][:100]}"
            channel = "collective.synthesis" if entry["importance"] == "critical" else "owl.all"

            await publish(message, channel=channel, from_owl="MEMORY")

        except Exception as e:
            print(f"[WARN] NATS broadcast failed: {e}", file=sys.stderr)

    async def _find_connections(self, entry: Dict[str, Any]) -> List[str]:
        """Find related entries using semantic search."""
        connections = []

        try:
            # Search claude-flow memory for related content
            cmd = [
                "npx", "@claude-flow/cli@latest", "memory", "search",
                "--query", f"{entry['topic']} {entry['content'][:200]}",
                "--limit", "5"
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

            if result.returncode == 0 and result.stdout:
                # Parse results and extract IDs
                # The output format may vary, so we do basic parsing
                for line in result.stdout.split("\n"):
                    if "neverforget-" in line:
                        # Extract potential IDs
                        parts = line.split()
                        for part in parts:
                            if len(part) == 16 and part.isalnum():
                                if part != entry["id"]:
                                    connections.append(part)

            # Also check local index for topic/tag matches
            for existing_id, meta in self.index["entries"].items():
                if existing_id == entry["id"]:
                    continue

                # Same topic = connection
                if meta["topic"] == entry["topic"]:
                    if existing_id not in connections:
                        connections.append(existing_id)

                # Overlapping tags = connection
                if set(meta.get("tags", [])) & set(entry.get("tags", [])):
                    if existing_id not in connections:
                        connections.append(existing_id)

        except Exception as e:
            print(f"[WARN] Connection finding failed: {e}", file=sys.stderr)

        return connections[:10]  # Limit to 10 connections

    async def recall(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Recall knowledge based on a natural language query.

        Uses semantic search across all memory types.
        """
        results = []

        # 1. Search claude-flow memory (semantic/vector search)
        try:
            cmd = [
                "npx", "@claude-flow/cli@latest", "memory", "search",
                "--query", query,
                "--limit", str(limit)
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

            if result.returncode == 0:
                print(f"[INFO] Claude-flow search results:\n{result.stdout}")

        except Exception as e:
            print(f"[WARN] Claude-flow search failed: {e}", file=sys.stderr)

        # 2. Search local index by keywords
        query_lower = query.lower()
        query_words = set(query_lower.split())

        scored_entries = []

        for entry_id, meta in self.index["entries"].items():
            score = 0

            # Topic match (high weight)
            if meta["topic"].lower() in query_lower:
                score += 10

            # Summary/content match
            summary_lower = meta.get("summary", "").lower()
            for word in query_words:
                if word in summary_lower:
                    score += 2
                if word in meta["topic"].lower():
                    score += 3

            # Tag match
            for tag in meta.get("tags", []):
                if tag.lower() in query_lower:
                    score += 5

            # Importance boost
            importance_boost = IMPORTANCE_LEVELS.get(meta.get("importance", "medium"), 3)
            score += importance_boost

            # Recency boost (entries from last 7 days get +2)
            try:
                created = datetime.fromisoformat(meta["created_at"])
                if (datetime.now() - created).days <= 7:
                    score += 2
            except:
                pass

            if score > 0:
                scored_entries.append((score, entry_id, meta))

        # Sort by score and load full entries
        scored_entries.sort(reverse=True, key=lambda x: x[0])

        for score, entry_id, meta in scored_entries[:limit]:
            file_path = BRAIN_MEMORY / meta["file"]
            if file_path.exists():
                with open(file_path, "r") as f:
                    entry = json.load(f)
                    entry["relevance_score"] = score
                    results.append(entry)

                    # Update access stats
                    entry["access_count"] = entry.get("access_count", 0) + 1
                    entry["last_accessed"] = datetime.now().isoformat()

                    with open(file_path, "w") as f2:
                        json.dump(entry, f2, indent=2)

        return results

    async def compound(self, topic: str = None) -> Dict[str, Any]:
        """
        Build compound knowledge by finding cross-connections.

        This creates knowledge graphs that span across different memory types
        and time periods, surfacing emergent patterns.
        """
        compound_result = {
            "generated_at": datetime.now().isoformat(),
            "topic": topic or "all",
            "insights": [],
            "patterns": [],
            "connections": [],
            "recommendations": []
        }

        # Get relevant entries
        if topic:
            entry_ids = self.index["by_topic"].get(topic, [])
            # Also search for related topics
            for t, ids in self.index["by_topic"].items():
                if topic.lower() in t.lower() or t.lower() in topic.lower():
                    entry_ids.extend(ids)
            entry_ids = list(set(entry_ids))
        else:
            entry_ids = list(self.index["entries"].keys())

        # Load all relevant entries
        entries = []
        for entry_id in entry_ids:
            meta = self.index["entries"].get(entry_id)
            if meta:
                file_path = BRAIN_MEMORY / meta["file"]
                if file_path.exists():
                    with open(file_path, "r") as f:
                        entries.append(json.load(f))

        # Group by type for analysis
        by_type = {}
        for entry in entries:
            t = entry["type"]
            if t not in by_type:
                by_type[t] = []
            by_type[t].append(entry)

        # Extract compound insights

        # 1. Pattern-mistake correlations
        if "pattern" in by_type and "mistake" in by_type:
            for mistake in by_type["mistake"]:
                for pattern in by_type["pattern"]:
                    if self._content_overlap(mistake["content"], pattern["content"]):
                        compound_result["insights"].append({
                            "type": "pattern-mistake-correlation",
                            "pattern": pattern["content"][:100],
                            "mistake": mistake["content"][:100],
                            "recommendation": f"Apply pattern '{pattern['topic']}' to avoid mistake '{mistake['topic']}'"
                        })

        # 2. Success patterns
        if "success" in by_type:
            success_topics = {}
            for success in by_type["success"]:
                topic = success["topic"]
                if topic not in success_topics:
                    success_topics[topic] = []
                success_topics[topic].append(success)

            for topic, successes in success_topics.items():
                if len(successes) >= 2:
                    compound_result["patterns"].append({
                        "type": "repeated-success",
                        "topic": topic,
                        "count": len(successes),
                        "insights": [s["content"][:100] for s in successes[-3:]]
                    })

        # 3. Opportunity-insight connections
        if "opportunity" in by_type and "insight" in by_type:
            for opp in by_type["opportunity"]:
                related_insights = []
                for insight in by_type["insight"]:
                    if self._content_overlap(opp["content"], insight["content"]):
                        related_insights.append(insight)

                if related_insights:
                    compound_result["connections"].append({
                        "opportunity": opp["topic"],
                        "content": opp["content"][:100],
                        "supporting_insights": [i["content"][:100] for i in related_insights[:3]]
                    })

        # 4. Generate recommendations based on recent mistakes
        if "mistake" in by_type:
            recent_mistakes = sorted(
                by_type["mistake"],
                key=lambda x: x.get("created_at", ""),
                reverse=True
            )[:5]

            for mistake in recent_mistakes:
                compound_result["recommendations"].append({
                    "type": "avoid-mistake",
                    "topic": mistake["topic"],
                    "what": mistake["content"][:150],
                    "when": mistake.get("created_at", "unknown")
                })

        # 5. Knowledge gaps
        all_topics = set(self.index["by_topic"].keys())
        typed_topics = {t: set() for t in MEMORY_TYPES.keys()}

        for entry in entries:
            typed_topics[entry["type"]].add(entry["topic"])

        # Find topics with insights but no patterns
        gaps = typed_topics.get("insight", set()) - typed_topics.get("pattern", set())
        if gaps:
            compound_result["recommendations"].append({
                "type": "knowledge-gap",
                "message": f"Topics with insights but no patterns: {', '.join(list(gaps)[:5])}",
                "action": "Consider extracting patterns from these insights"
            })

        # Save compound analysis
        compound_file = BRAIN_MEMORY / "compound" / f"compound_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(compound_file, "w") as f:
            json.dump(compound_result, f, indent=2)

        # Update index
        self.index["stats"]["last_compound"] = datetime.now().isoformat()
        self._save_index()

        return compound_result

    def _content_overlap(self, content1: str, content2: str) -> bool:
        """Check if two pieces of content have significant word overlap."""
        words1 = set(content1.lower().split())
        words2 = set(content2.lower().split())

        # Remove common stop words
        stop_words = {"the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
                      "have", "has", "had", "do", "does", "did", "will", "would", "could",
                      "should", "may", "might", "must", "shall", "can", "to", "of", "in",
                      "for", "on", "with", "at", "by", "from", "up", "about", "into",
                      "through", "during", "before", "after", "above", "below", "between",
                      "under", "again", "further", "then", "once", "here", "there", "when",
                      "where", "why", "how", "all", "each", "few", "more", "most", "other",
                      "some", "such", "no", "nor", "not", "only", "own", "same", "so",
                      "than", "too", "very", "just", "and", "but", "if", "or", "because",
                      "as", "until", "while", "this", "that", "these", "those"}

        words1 -= stop_words
        words2 -= stop_words

        if not words1 or not words2:
            return False

        overlap = len(words1 & words2)
        min_len = min(len(words1), len(words2))

        return overlap / min_len >= 0.3  # 30% overlap threshold

    def search(
        self,
        mem_type: str = None,
        topic: str = None,
        tags: List[str] = None,
        since: str = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Search memory with filters.
        """
        results = []

        # Get candidate entry IDs
        if mem_type and mem_type in self.index["by_type"]:
            candidates = set(self.index["by_type"][mem_type])
        else:
            candidates = set(self.index["entries"].keys())

        # Filter by topic
        if topic:
            topic_matches = set()
            for t, ids in self.index["by_topic"].items():
                if topic.lower() in t.lower():
                    topic_matches.update(ids)
            candidates &= topic_matches

        # Filter by date
        if since:
            try:
                since_date = datetime.fromisoformat(since)
                date_matches = set()
                for date_str, ids in self.index["by_date"].items():
                    try:
                        entry_date = datetime.strptime(date_str, "%Y-%m-%d")
                        if entry_date >= since_date:
                            date_matches.update(ids)
                    except:
                        pass
                candidates &= date_matches
            except:
                pass

        # Load and filter by tags
        for entry_id in list(candidates)[:limit * 2]:  # Get extra for tag filtering
            meta = self.index["entries"].get(entry_id)
            if not meta:
                continue

            # Tag filter
            if tags:
                entry_tags = set(t.lower() for t in meta.get("tags", []))
                search_tags = set(t.lower() for t in tags)
                if not (entry_tags & search_tags):
                    continue

            # Load full entry
            file_path = BRAIN_MEMORY / meta["file"]
            if file_path.exists():
                with open(file_path, "r") as f:
                    results.append(json.load(f))

            if len(results) >= limit:
                break

        return results

    def stats(self) -> Dict[str, Any]:
        """Get memory statistics."""
        stats = {
            "total_entries": self.index["stats"]["total_entries"],
            "by_type": self.index["stats"]["by_type"],
            "total_topics": len(self.index["by_topic"]),
            "total_days": len(self.index["by_date"]),
            "total_connections": sum(len(c) for c in self.index.get("connections", {}).values()),
            "last_compound": self.index["stats"].get("last_compound"),
            "recent_entries": []
        }

        # Get 5 most recent entries
        all_entries = list(self.index["entries"].items())
        all_entries.sort(key=lambda x: x[1].get("created_at", ""), reverse=True)

        for entry_id, meta in all_entries[:5]:
            stats["recent_entries"].append({
                "id": entry_id,
                "type": meta["type"],
                "topic": meta["topic"],
                "created_at": meta["created_at"]
            })

        return stats

    async def export_all(self, output_path: str) -> Dict[str, Any]:
        """Export all memory to a backup file."""
        export_data = {
            "exported_at": datetime.now().isoformat(),
            "version": "1.0",
            "index": self.index,
            "entries": {}
        }

        # Load all entries
        for entry_id, meta in self.index["entries"].items():
            file_path = BRAIN_MEMORY / meta["file"]
            if file_path.exists():
                with open(file_path, "r") as f:
                    export_data["entries"][entry_id] = json.load(f)

        with open(output_path, "w") as f:
            json.dump(export_data, f, indent=2)

        return {
            "success": True,
            "path": output_path,
            "entries_exported": len(export_data["entries"])
        }

    async def import_all(self, input_path: str) -> Dict[str, Any]:
        """Import memory from a backup file."""
        with open(input_path, "r") as f:
            import_data = json.load(f)

        imported = 0
        skipped = 0

        for entry_id, entry in import_data.get("entries", {}).items():
            # Skip if already exists
            if entry_id in self.index["entries"]:
                skipped += 1
                continue

            # Store the entry
            await self.store(
                mem_type=entry["type"],
                topic=entry["topic"],
                content=entry["content"],
                importance=entry.get("importance", "medium"),
                tags=entry.get("tags", []),
                source=entry.get("source"),
                metadata=entry.get("metadata")
            )
            imported += 1

        return {
            "success": True,
            "imported": imported,
            "skipped": skipped
        }


async def main():
    parser = argparse.ArgumentParser(
        description="NEVER FORGET - Persistent Memory That Compounds",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Store an insight:
    python3 never_forget.py store --type insight --topic "trading" --content "Kelly criterion works"

  Recall knowledge:
    python3 never_forget.py recall "What do we know about trading?"

  Build compound knowledge:
    python3 never_forget.py compound --topic "trading"

  Get stats:
    python3 never_forget.py stats
        """
    )

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Store command
    store_parser = subparsers.add_parser("store", help="Store a piece of knowledge")
    store_parser.add_argument("--type", "-t", required=True,
                              choices=list(MEMORY_TYPES.keys()),
                              help="Type of memory")
    store_parser.add_argument("--topic", required=True, help="Topic/subject")
    store_parser.add_argument("--content", "-c", required=True, help="Content to store")
    store_parser.add_argument("--importance", "-i", default="medium",
                              choices=list(IMPORTANCE_LEVELS.keys()),
                              help="Importance level")
    store_parser.add_argument("--tags", nargs="+", help="Tags for categorization")
    store_parser.add_argument("--source", help="Source of the knowledge")

    # Recall command
    recall_parser = subparsers.add_parser("recall", help="Recall knowledge")
    recall_parser.add_argument("query", help="Natural language query")
    recall_parser.add_argument("--limit", "-l", type=int, default=10, help="Max results")

    # Compound command
    compound_parser = subparsers.add_parser("compound", help="Build compound knowledge")
    compound_parser.add_argument("--topic", help="Focus on specific topic")
    compound_parser.add_argument("--all", action="store_true", help="Compound all knowledge")

    # Search command
    search_parser = subparsers.add_parser("search", help="Search with filters")
    search_parser.add_argument("--type", "-t", choices=list(MEMORY_TYPES.keys()))
    search_parser.add_argument("--topic", help="Topic filter")
    search_parser.add_argument("--tags", nargs="+", help="Tag filter")
    search_parser.add_argument("--since", help="Date filter (YYYY-MM-DD)")
    search_parser.add_argument("--limit", "-l", type=int, default=20)

    # Stats command
    subparsers.add_parser("stats", help="Show memory statistics")

    # Export command
    export_parser = subparsers.add_parser("export", help="Export all memory")
    export_parser.add_argument("--output", "-o", required=True, help="Output file path")

    # Import command
    import_parser = subparsers.add_parser("import", help="Import memory backup")
    import_parser.add_argument("--input", "-i", required=True, help="Input file path")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    nf = NeverForget()

    if args.command == "store":
        result = await nf.store(
            mem_type=args.type,
            topic=args.topic,
            content=args.content,
            importance=args.importance,
            tags=args.tags,
            source=args.source
        )
        print(f"[STORED] {result['type'].upper()}: {result['topic']}")
        print(f"  ID: {result['id']}")
        print(f"  Importance: {result['importance']}")
        if result.get("connections"):
            print(f"  Connections: {len(result['connections'])} related entries found")

    elif args.command == "recall":
        results = await nf.recall(args.query, limit=args.limit)
        if not results:
            print(f"No memories found for: {args.query}")
        else:
            print(f"\n=== RECALLING: {args.query} ===\n")
            for i, entry in enumerate(results, 1):
                print(f"{i}. [{entry['type'].upper()}] {entry['topic']}")
                print(f"   {entry['content'][:200]}...")
                print(f"   Score: {entry.get('relevance_score', 'N/A')} | Created: {entry['created_at'][:10]}")
                print()

    elif args.command == "compound":
        result = await nf.compound(topic=args.topic)
        print(f"\n=== COMPOUND KNOWLEDGE: {result['topic']} ===\n")

        if result["insights"]:
            print("INSIGHTS:")
            for insight in result["insights"][:5]:
                print(f"  - {insight['type']}: {insight.get('recommendation', insight)}")

        if result["patterns"]:
            print("\nPATTERNS:")
            for pattern in result["patterns"][:5]:
                print(f"  - {pattern['topic']}: {pattern['count']} successes")

        if result["connections"]:
            print("\nCONNECTIONS:")
            for conn in result["connections"][:5]:
                print(f"  - {conn['opportunity']}: {len(conn['supporting_insights'])} supporting insights")

        if result["recommendations"]:
            print("\nRECOMMENDATIONS:")
            for rec in result["recommendations"][:5]:
                print(f"  - [{rec['type']}] {rec.get('topic', rec.get('message', ''))}")

    elif args.command == "search":
        results = nf.search(
            mem_type=args.type,
            topic=args.topic,
            tags=args.tags,
            since=args.since,
            limit=args.limit
        )
        print(f"\n=== SEARCH RESULTS ({len(results)}) ===\n")
        for entry in results:
            print(f"[{entry['type'].upper()}] {entry['topic']}")
            print(f"  {entry['content'][:150]}...")
            print()

    elif args.command == "stats":
        stats = nf.stats()
        print("\n=== NEVER FORGET STATS ===\n")
        print(f"Total Entries: {stats['total_entries']}")
        print(f"Total Topics: {stats['total_topics']}")
        print(f"Days Active: {stats['total_days']}")
        print(f"Connections: {stats['total_connections']}")
        print(f"\nBy Type:")
        for t, count in stats.get("by_type", {}).items():
            print(f"  {t}: {count}")
        print(f"\nLast Compound: {stats.get('last_compound', 'Never')}")
        if stats["recent_entries"]:
            print(f"\nRecent Entries:")
            for entry in stats["recent_entries"]:
                print(f"  [{entry['type']}] {entry['topic']} ({entry['created_at'][:10]})")

    elif args.command == "export":
        result = await nf.export_all(args.output)
        print(f"Exported {result['entries_exported']} entries to {result['path']}")

    elif args.command == "import":
        result = await nf.import_all(args.input)
        print(f"Imported {result['imported']} entries, skipped {result['skipped']} duplicates")


if __name__ == "__main__":
    asyncio.run(main())
