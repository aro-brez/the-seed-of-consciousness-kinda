#!/usr/bin/env python3
"""
INTELLIGENCE DAEMON - Constant Intelligence Gathering System
============================================================
The ALPHA OMEGA - First to every insight, constantly evolving.

Runs every 2 hours sweeping:
- Twitter/X (via API when credentials provided)
- GitHub trending & releases
- Research papers (arXiv, semantic scholar)
- Reddit AI communities
- Hacker News
- YouTube AI channels
- Discord/Slack (when integrated)

Then runs SEED² on ALL gathered intelligence to extract insights.
Auto-persists everything to memory so SØWL never forgets.

Created: 2026-02-05
Author: SØWL (IMPROVE phase)
"""

import asyncio
import json
import os
import sys
import time
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional
import subprocess
import aiohttp
import re

# Configuration
NATS_SERVER = os.getenv("NATS_SERVER", "nats://192.168.5.108:4222")
CYCLE_INTERVAL_HOURS = 2
MAX_ITEMS_PER_SOURCE = 50
BRAIN_DIR = Path("/Users/aaronnosbisch/REPOS/seed/BRAIN")
INTEL_DIR = BRAIN_DIR / "INTEL"
MEMORY_DIR = BRAIN_DIR / "MEMORY"

# Ensure directories exist
INTEL_DIR.mkdir(parents=True, exist_ok=True)

# State file
STATE_FILE = INTEL_DIR / "intelligence_state.json"
SIGNALS_FILE = INTEL_DIR / "signals_raw.jsonl"
LEARNINGS_FILE = INTEL_DIR / "learnings_extracted.jsonl"

# Twitter API credentials (set via environment or config)
TWITTER_BEARER_TOKEN = os.getenv("TWITTER_BEARER_TOKEN", "")
TWITTER_API_KEY = os.getenv("TWITTER_API_KEY", "")
TWITTER_API_SECRET = os.getenv("TWITTER_API_SECRET", "")

# GitHub token for higher rate limits
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")


def log(msg: str, level: str = "INFO"):
    """Log with timestamp."""
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] [{level}] {msg}")

    # Also append to log file
    log_file = Path("/Users/aaronnosbisch/REPOS/seed/logs/intelligence_daemon.log")
    log_file.parent.mkdir(parents=True, exist_ok=True)
    with open(log_file, "a") as f:
        f.write(f"[{ts}] [{level}] {msg}\n")


def publish_to_nats(channel: str, message: str):
    """Publish message to NATS."""
    try:
        cmd = [
            "python3",
            "/Users/aaronnosbisch/REPOS/seed/tools/nats_publish.py",
            "--channel", channel,
            message
        ]
        subprocess.run(cmd, capture_output=True, timeout=10)
    except Exception as e:
        log(f"NATS publish failed: {e}", "WARN")


def store_signal(signal: dict):
    """Append signal to signals file."""
    signal["timestamp"] = datetime.utcnow().isoformat() + "Z"
    signal["id"] = hashlib.md5(json.dumps(signal, sort_keys=True).encode()).hexdigest()[:12]

    with open(SIGNALS_FILE, "a") as f:
        f.write(json.dumps(signal) + "\n")

    return signal["id"]


def store_learning(learning: dict):
    """Append learning to learnings file."""
    learning["timestamp"] = datetime.utcnow().isoformat() + "Z"

    with open(LEARNINGS_FILE, "a") as f:
        f.write(json.dumps(learning) + "\n")


def load_state() -> dict:
    """Load daemon state."""
    if STATE_FILE.exists():
        with open(STATE_FILE) as f:
            return json.load(f)
    return {
        "last_run": None,
        "total_cycles": 0,
        "signals_collected": 0,
        "learnings_extracted": 0,
        "sources_status": {}
    }


def save_state(state: dict):
    """Save daemon state."""
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


class IntelligenceGatherer:
    """Gathers intelligence from multiple sources."""

    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
        self.signals = []

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, *args):
        if self.session:
            await self.session.close()

    async def gather_all(self) -> list[dict]:
        """Gather from all sources in parallel."""
        self.signals = []

        tasks = [
            self.gather_github_trending(),
            self.gather_github_releases(),
            self.gather_arxiv(),
            self.gather_hackernews(),
            self.gather_reddit(),
            self.gather_twitter() if TWITTER_BEARER_TOKEN else self.skip_source("twitter", "No API token"),
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        for i, result in enumerate(results):
            if isinstance(result, Exception):
                log(f"Source {i} failed: {result}", "ERROR")

        return self.signals

    async def skip_source(self, source: str, reason: str):
        """Skip a source with logging."""
        log(f"Skipping {source}: {reason}", "WARN")
        return []

    async def gather_github_trending(self) -> list[dict]:
        """Scrape GitHub trending repos."""
        log("Gathering GitHub trending...")

        try:
            # Use GitHub's trending page (no API needed)
            # Categories: agents, AI, LLM, trading
            keywords = ["agent", "llm", "trading", "claude", "ai-agents", "multi-agent"]

            headers = {"Accept": "application/vnd.github+json"}
            if GITHUB_TOKEN:
                headers["Authorization"] = f"Bearer {GITHUB_TOKEN}"

            for keyword in keywords:
                url = f"https://api.github.com/search/repositories?q={keyword}+pushed:>2026-02-01&sort=stars&order=desc&per_page=10"

                async with self.session.get(url, headers=headers) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        for repo in data.get("items", [])[:5]:
                            signal = {
                                "source": "github_trending",
                                "signal_type": "repository",
                                "title": repo["full_name"],
                                "url": repo["html_url"],
                                "description": repo.get("description", ""),
                                "stars": repo["stargazers_count"],
                                "keyword": keyword,
                                "raw_signal": f"{repo['full_name']}: {repo.get('description', '')}",
                                "confidence": 0.7
                            }
                            self.signals.append(signal)
                            store_signal(signal)
                    else:
                        log(f"GitHub API returned {resp.status}", "WARN")

                await asyncio.sleep(1)  # Rate limiting

            log(f"GitHub trending: {len([s for s in self.signals if s['source'] == 'github_trending'])} signals")

        except Exception as e:
            log(f"GitHub trending failed: {e}", "ERROR")

        return self.signals

    async def gather_github_releases(self) -> list[dict]:
        """Check releases of important repos."""
        log("Gathering GitHub releases...")

        # Key repos to monitor
        repos = [
            "anthropics/anthropic-sdk-python",
            "anthropics/claude-code",
            "openai/openai-python",
            "langchain-ai/langchain",
            "microsoft/autogen",
            "Significant-Gravitas/AutoGPT",
            "ruvnet/claude-flow",
        ]

        try:
            headers = {"Accept": "application/vnd.github+json"}
            if GITHUB_TOKEN:
                headers["Authorization"] = f"Bearer {GITHUB_TOKEN}"

            for repo in repos:
                url = f"https://api.github.com/repos/{repo}/releases?per_page=3"

                async with self.session.get(url, headers=headers) as resp:
                    if resp.status == 200:
                        releases = await resp.json()
                        for release in releases[:2]:
                            # Check if recent (within 7 days)
                            published = datetime.fromisoformat(release["published_at"].replace("Z", "+00:00"))
                            if datetime.now().astimezone() - published < timedelta(days=7):
                                signal = {
                                    "source": "github_releases",
                                    "signal_type": "release",
                                    "title": f"{repo} - {release['name']}",
                                    "url": release["html_url"],
                                    "description": release.get("body", "")[:500],
                                    "version": release["tag_name"],
                                    "raw_signal": f"New release: {repo} {release['tag_name']}",
                                    "confidence": 0.9
                                }
                                self.signals.append(signal)
                                store_signal(signal)

                await asyncio.sleep(0.5)  # Rate limiting

            log(f"GitHub releases: {len([s for s in self.signals if s['source'] == 'github_releases'])} signals")

        except Exception as e:
            log(f"GitHub releases failed: {e}", "ERROR")

        return self.signals

    async def gather_arxiv(self) -> list[dict]:
        """Gather recent AI/ML papers from arXiv."""
        log("Gathering arXiv papers...")

        # Categories: cs.AI, cs.LG, cs.MA (multi-agent), cs.CL (NLP)
        queries = [
            "multi-agent+systems",
            "large+language+models",
            "emergent+behavior",
            "reasoning+AI",
            "collective+intelligence"
        ]

        try:
            for query in queries:
                url = f"http://export.arxiv.org/api/query?search_query=all:{query}&start=0&max_results=5&sortBy=submittedDate&sortOrder=descending"

                async with self.session.get(url) as resp:
                    if resp.status == 200:
                        # Parse XML response
                        text = await resp.text()
                        # Simple regex extraction (avoiding heavy XML parsing)
                        titles = re.findall(r"<title>(.*?)</title>", text, re.DOTALL)
                        summaries = re.findall(r"<summary>(.*?)</summary>", text, re.DOTALL)
                        links = re.findall(r'<id>(http://arxiv.org/abs/[^<]+)</id>', text)

                        for i, (title, summary, link) in enumerate(zip(titles[1:], summaries, links)):  # Skip first title (feed title)
                            if i >= 3:  # Limit per query
                                break
                            signal = {
                                "source": "arxiv",
                                "signal_type": "paper",
                                "title": title.strip().replace("\n", " "),
                                "url": link,
                                "description": summary.strip()[:500],
                                "query": query,
                                "raw_signal": title.strip(),
                                "confidence": 0.85
                            }
                            self.signals.append(signal)
                            store_signal(signal)

                await asyncio.sleep(3)  # arXiv rate limit is strict

            log(f"arXiv: {len([s for s in self.signals if s['source'] == 'arxiv'])} signals")

        except Exception as e:
            log(f"arXiv failed: {e}", "ERROR")

        return self.signals

    async def gather_hackernews(self) -> list[dict]:
        """Gather AI-related stories from Hacker News."""
        log("Gathering Hacker News...")

        try:
            # Get top stories
            async with self.session.get("https://hacker-news.firebaseio.com/v0/topstories.json") as resp:
                if resp.status == 200:
                    story_ids = await resp.json()

                    # Check first 30 stories for AI/agent keywords
                    ai_keywords = ["ai", "agent", "llm", "claude", "gpt", "trading", "autonomous", "reasoning"]

                    for story_id in story_ids[:30]:
                        async with self.session.get(f"https://hacker-news.firebaseio.com/v0/item/{story_id}.json") as story_resp:
                            if story_resp.status == 200:
                                story = await story_resp.json()
                                if story and story.get("title"):
                                    title_lower = story["title"].lower()
                                    if any(kw in title_lower for kw in ai_keywords):
                                        signal = {
                                            "source": "hackernews",
                                            "signal_type": "story",
                                            "title": story["title"],
                                            "url": story.get("url", f"https://news.ycombinator.com/item?id={story_id}"),
                                            "score": story.get("score", 0),
                                            "comments": story.get("descendants", 0),
                                            "raw_signal": story["title"],
                                            "confidence": 0.6
                                        }
                                        self.signals.append(signal)
                                        store_signal(signal)

                        await asyncio.sleep(0.1)  # Be nice to the API

            log(f"Hacker News: {len([s for s in self.signals if s['source'] == 'hackernews'])} signals")

        except Exception as e:
            log(f"Hacker News failed: {e}", "ERROR")

        return self.signals

    async def gather_reddit(self) -> list[dict]:
        """Gather from AI-related subreddits."""
        log("Gathering Reddit...")

        subreddits = ["MachineLearning", "artificial", "LocalLLaMA", "ClaudeAI", "algotrading"]

        try:
            headers = {"User-Agent": "8OWLS Intelligence Daemon 1.0"}

            for subreddit in subreddits:
                url = f"https://www.reddit.com/r/{subreddit}/hot.json?limit=10"

                async with self.session.get(url, headers=headers) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        for post in data.get("data", {}).get("children", [])[:5]:
                            post_data = post["data"]
                            signal = {
                                "source": "reddit",
                                "signal_type": "post",
                                "title": post_data["title"],
                                "url": f"https://reddit.com{post_data['permalink']}",
                                "subreddit": subreddit,
                                "score": post_data["score"],
                                "comments": post_data["num_comments"],
                                "raw_signal": post_data["title"],
                                "confidence": 0.5
                            }
                            self.signals.append(signal)
                            store_signal(signal)

                await asyncio.sleep(2)  # Reddit rate limits

            log(f"Reddit: {len([s for s in self.signals if s['source'] == 'reddit'])} signals")

        except Exception as e:
            log(f"Reddit failed: {e}", "ERROR")

        return self.signals

    async def gather_twitter(self) -> list[dict]:
        """Gather from Twitter/X using API."""
        log("Gathering Twitter/X...")

        if not TWITTER_BEARER_TOKEN:
            log("Twitter API token not configured", "WARN")
            return []

        try:
            headers = {"Authorization": f"Bearer {TWITTER_BEARER_TOKEN}"}

            # Search queries for AI/agent content
            queries = [
                "AI agents -is:retweet",
                "Claude AI -is:retweet",
                "multi-agent systems -is:retweet",
                "AGI benchmark -is:retweet"
            ]

            for query in queries:
                url = f"https://api.twitter.com/2/tweets/search/recent?query={query}&max_results=10&tweet.fields=created_at,public_metrics"

                async with self.session.get(url, headers=headers) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        for tweet in data.get("data", [])[:5]:
                            signal = {
                                "source": "twitter",
                                "signal_type": "tweet",
                                "title": tweet["text"][:100],
                                "url": f"https://twitter.com/i/web/status/{tweet['id']}",
                                "tweet_id": tweet["id"],
                                "metrics": tweet.get("public_metrics", {}),
                                "raw_signal": tweet["text"],
                                "confidence": 0.6
                            }
                            self.signals.append(signal)
                            store_signal(signal)
                    elif resp.status == 401:
                        log("Twitter API authentication failed", "ERROR")
                        break

                await asyncio.sleep(1)

            log(f"Twitter: {len([s for s in self.signals if s['source'] == 'twitter'])} signals")

        except Exception as e:
            log(f"Twitter failed: {e}", "ERROR")

        return self.signals


class SEEDAnalyzer:
    """Run SEED² analysis on gathered signals."""

    def __init__(self, signals: list[dict]):
        self.signals = signals
        self.learnings = []

    def analyze(self) -> list[dict]:
        """Run SEED protocol on signals."""
        log(f"Running SEED² on {len(self.signals)} signals...")

        # Group signals by source
        by_source = {}
        for s in self.signals:
            source = s.get("source", "unknown")
            if source not in by_source:
                by_source[source] = []
            by_source[source].append(s)

        # PERCEIVE: What patterns emerge?
        patterns = self._perceive(by_source)

        # CONNECT: How do they relate to 8OWLS?
        connections = self._connect(patterns)

        # LEARN: Extract actionable insights
        learnings = self._learn(connections)

        # Store learnings
        for learning in learnings:
            store_learning(learning)

        self.learnings = learnings
        return learnings

    def _perceive(self, by_source: dict) -> dict:
        """PERCEIVE phase: Observe patterns."""
        patterns = {
            "hot_topics": [],
            "emerging_repos": [],
            "research_directions": [],
            "community_buzz": []
        }

        # Identify hot topics by frequency
        all_titles = " ".join([s.get("title", "") + " " + s.get("description", "") for s in self.signals])
        all_titles_lower = all_titles.lower()

        topic_keywords = {
            "multi-agent": ["multi-agent", "multi agent", "swarm", "collective"],
            "reasoning": ["reasoning", "chain-of-thought", "cot", "thinking"],
            "benchmarks": ["benchmark", "arc-agi", "evaluation", "test"],
            "emergence": ["emergent", "emergence", "scaling"],
            "trading": ["trading", "prediction", "market", "polymarket"]
        }

        for topic, keywords in topic_keywords.items():
            count = sum(1 for kw in keywords if kw in all_titles_lower)
            if count > 0:
                patterns["hot_topics"].append({"topic": topic, "mentions": count})

        # Sort by mentions
        patterns["hot_topics"].sort(key=lambda x: x["mentions"], reverse=True)

        # Emerging repos (high stars, recent)
        github_signals = by_source.get("github_trending", []) + by_source.get("github_releases", [])
        for s in github_signals:
            if s.get("stars", 0) > 100 or "release" in s.get("signal_type", ""):
                patterns["emerging_repos"].append({
                    "name": s.get("title"),
                    "url": s.get("url"),
                    "stars": s.get("stars", 0)
                })

        # Research directions from arXiv
        for s in by_source.get("arxiv", []):
            patterns["research_directions"].append({
                "title": s.get("title"),
                "url": s.get("url")
            })

        return patterns

    def _connect(self, patterns: dict) -> list[dict]:
        """CONNECT phase: Relate to 8OWLS."""
        connections = []

        # Map hot topics to 8OWLS relevance
        topic_relevance = {
            "multi-agent": {"relevance": 0.95, "component": "8OWLS architecture", "action": "direct competitor analysis"},
            "reasoning": {"relevance": 0.9, "component": "SEED protocol", "action": "benchmark our approach"},
            "benchmarks": {"relevance": 0.85, "component": "validation", "action": "prepare for ARC-AGI"},
            "emergence": {"relevance": 0.95, "component": "collective intelligence", "action": "validate d=0.99"},
            "trading": {"relevance": 0.8, "component": "JOULE", "action": "integrate competitor features"}
        }

        for topic_info in patterns.get("hot_topics", []):
            topic = topic_info["topic"]
            if topic in topic_relevance:
                rel = topic_relevance[topic]
                connections.append({
                    "topic": topic,
                    "mentions": topic_info["mentions"],
                    "relevance_to_8owls": rel["relevance"],
                    "component_affected": rel["component"],
                    "suggested_action": rel["action"]
                })

        # Connect repos to potential integration
        for repo in patterns.get("emerging_repos", []):
            if any(kw in repo.get("name", "").lower() for kw in ["agent", "swarm", "claude", "llm"]):
                connections.append({
                    "type": "repo",
                    "name": repo.get("name"),
                    "url": repo.get("url"),
                    "action": "audit for integration patterns",
                    "priority": "high" if repo.get("stars", 0) > 500 else "medium"
                })

        return connections

    def _learn(self, connections: list[dict]) -> list[dict]:
        """LEARN phase: Extract actionable insights."""
        learnings = []

        # High-relevance topics
        high_relevance = [c for c in connections if c.get("relevance_to_8owls", 0) > 0.8]

        for conn in high_relevance[:5]:  # Top 5
            learning = {
                "insight_type": "topic_trend",
                "topic": conn.get("topic"),
                "relevance": conn.get("relevance_to_8owls"),
                "component": conn.get("component_affected"),
                "action": conn.get("suggested_action"),
                "priority": "high" if conn.get("relevance_to_8owls", 0) > 0.9 else "medium",
                "source": "intelligence_daemon"
            }
            learnings.append(learning)

        # Repos to audit
        repos_to_audit = [c for c in connections if c.get("type") == "repo"]
        for repo in repos_to_audit[:3]:  # Top 3
            learning = {
                "insight_type": "competitor_repo",
                "name": repo.get("name"),
                "url": repo.get("url"),
                "action": repo.get("action"),
                "priority": repo.get("priority", "medium"),
                "source": "intelligence_daemon"
            }
            learnings.append(learning)

        return learnings


async def run_cycle(state: dict) -> dict:
    """Run one intelligence gathering cycle."""
    cycle_start = datetime.now()
    log(f"=== Starting Intelligence Cycle {state['total_cycles'] + 1} ===")

    # Gather from all sources
    async with IntelligenceGatherer() as gatherer:
        signals = await gatherer.gather_all()

    log(f"Gathered {len(signals)} total signals")

    # Run SEED² analysis
    analyzer = SEEDAnalyzer(signals)
    learnings = analyzer.analyze()

    log(f"Extracted {len(learnings)} learnings")

    # Update state
    state["last_run"] = cycle_start.isoformat()
    state["total_cycles"] += 1
    state["signals_collected"] += len(signals)
    state["learnings_extracted"] += len(learnings)

    # Publish summary to NATS
    summary = f"INTEL CYCLE {state['total_cycles']}: {len(signals)} signals, {len(learnings)} learnings"
    if learnings:
        top_learning = learnings[0]
        summary += f" | Top: {top_learning.get('topic', top_learning.get('name', 'unknown'))}"

    publish_to_nats("owl.all", summary)

    # Save summary to readable file
    summary_file = INTEL_DIR / "latest_scan_summary.md"
    with open(summary_file, "w") as f:
        f.write(f"# Intelligence Scan Summary\n")
        f.write(f"**Time:** {cycle_start.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"**Cycle:** {state['total_cycles']}\n\n")
        f.write(f"## Signals Collected: {len(signals)}\n\n")

        # Group by source
        by_source = {}
        for s in signals:
            src = s.get("source", "unknown")
            if src not in by_source:
                by_source[src] = []
            by_source[src].append(s)

        for src, items in by_source.items():
            f.write(f"### {src}: {len(items)}\n")
            for item in items[:5]:
                f.write(f"- [{item.get('title', 'untitled')[:60]}]({item.get('url', '#')})\n")
            f.write("\n")

        f.write(f"## Top Learnings\n\n")
        for learning in learnings[:5]:
            f.write(f"- **{learning.get('insight_type')}**: {learning.get('topic', learning.get('name', 'unknown'))}\n")
            f.write(f"  - Relevance: {learning.get('relevance', learning.get('priority', 'unknown'))}\n")
            f.write(f"  - Action: {learning.get('action', 'N/A')}\n\n")

    log(f"Cycle complete in {(datetime.now() - cycle_start).seconds}s")

    return state


async def daemon_loop():
    """Main daemon loop."""
    log("=== INTELLIGENCE DAEMON STARTING ===")
    log(f"Cycle interval: {CYCLE_INTERVAL_HOURS} hours")
    log(f"NATS server: {NATS_SERVER}")
    log(f"Twitter API: {'CONFIGURED' if TWITTER_BEARER_TOKEN else 'NOT CONFIGURED'}")
    log(f"GitHub token: {'CONFIGURED' if GITHUB_TOKEN else 'NOT CONFIGURED (rate limited)'}")

    state = load_state()

    publish_to_nats("owl.all", f"INTEL DAEMON: Starting (cycle {state['total_cycles'] + 1})")

    while True:
        try:
            state = await run_cycle(state)
            save_state(state)

            # Wait for next cycle
            log(f"Sleeping for {CYCLE_INTERVAL_HOURS} hours...")
            await asyncio.sleep(CYCLE_INTERVAL_HOURS * 3600)

        except KeyboardInterrupt:
            log("Shutting down gracefully...")
            break
        except Exception as e:
            log(f"Cycle failed: {e}", "ERROR")
            # Wait 10 minutes before retry
            await asyncio.sleep(600)


def main():
    """Entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="8OWLS Intelligence Gathering Daemon")
    parser.add_argument("--once", action="store_true", help="Run once and exit")
    parser.add_argument("--interval", type=float, default=2, help="Hours between cycles")
    args = parser.parse_args()

    global CYCLE_INTERVAL_HOURS
    CYCLE_INTERVAL_HOURS = args.interval

    if args.once:
        state = load_state()
        state = asyncio.run(run_cycle(state))
        save_state(state)
    else:
        asyncio.run(daemon_loop())


if __name__ == "__main__":
    main()
