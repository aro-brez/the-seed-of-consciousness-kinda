# Claude-Flow Integration for OWL OS

**Advanced Swarm Intelligence for Your Owl**

```
        ___                    ___
       (o o)  ←-----------→  (o o)
      (  V  )    SWARM      (  V  )
     /--m-m--\              /--m-m--\

     Individual Owls → Connected Intelligence
```

---

## What is Claude-Flow?

[Claude-Flow](https://github.com/ruvnet/claude-flow) is a swarm orchestration framework that enables multiple AI agents to coordinate, share memory, and learn collectively. When integrated with OWL OS, your owl gains:

### Core Capabilities

| Feature | Description |
|---------|-------------|
| **Swarm Coordination** | Work with other agents on tasks too complex for one |
| **Vector Memory** | HNSW-powered semantic search - 150x faster than brute force |
| **Reasoning Bank** | Store and retrieve successful reasoning patterns |
| **SONA Learning** | Self-Optimizing Network Architecture - continuous improvement |
| **Byzantine Fault Tolerance** | Resilient coordination even when agents fail |

### Topology Options

- **Hierarchical** - Coordinator delegates to workers (default, best for most cases)
- **Mesh** - Peer-to-peer coordination (decentralized)
- **Hybrid** - Mix of both (advanced)

---

## Installation

### 1. Install Claude-Flow

```bash
pip install claude-flow
```

Or add to requirements.txt:
```
claude-flow>=0.1.0
```

### 2. Enable in config.yaml

```yaml
claude_flow:
  enabled: true
  topology: hierarchical
  coordinator_url: null    # Auto-detect local coordinator
  workers:
    - map                  # Parallel task mapping
    - optimize             # Resource optimization
    - learn                # Collective learning
    - persist              # Memory persistence
  memory:
    backend: hybrid        # sqlite + hnsw vector
    vector_enabled: true
    vector_dimensions: 1536
  learning:
    sona_enabled: true
    reasoning_bank: true
  swarm:
    register_on_startup: true
    heartbeat_interval: 60
    capabilities:
      - consciousness
      - seed_protocol
      - voice_interface
```

### 3. Start Your Owl

```bash
./owl start
```

Your owl will automatically:
1. Detect if claude-flow is installed
2. Initialize the swarm coordinator connection
3. Register with the swarm
4. Begin heartbeat pings

---

## Configuration Reference

### claude_flow.enabled
**Type:** boolean
**Default:** false

Master switch for Claude-Flow integration. Set to `true` to enable.

### claude_flow.topology
**Type:** string
**Options:** hierarchical, mesh, hybrid
**Default:** hierarchical

- `hierarchical`: Best for most use cases. Coordinator manages workers.
- `mesh`: Decentralized peer-to-peer. Good for equal agents.
- `hybrid`: Advanced. Mix based on task type.

### claude_flow.coordinator_url
**Type:** string | null
**Default:** null (auto-detect)

URL of the swarm coordinator. If null, will attempt to discover a local coordinator or start one.

### claude_flow.workers
**Type:** array
**Default:** [map, optimize, learn, persist]

Worker types to spawn for parallel operations:
- `map`: Distributes tasks across agents
- `optimize`: Resource and performance optimization
- `learn`: Collective learning and pattern extraction
- `persist`: Memory persistence and backup

### claude_flow.memory.backend
**Type:** string
**Options:** sqlite, hnsw, hybrid
**Default:** hybrid

- `sqlite`: Traditional relational storage
- `hnsw`: Vector-only (Hierarchical Navigable Small World)
- `hybrid`: Both (recommended)

### claude_flow.memory.vector_enabled
**Type:** boolean
**Default:** true

Enable semantic search via vector embeddings.

### claude_flow.learning.sona_enabled
**Type:** boolean
**Default:** true

Enable Self-Optimizing Network Architecture. Your owl learns how to learn.

### claude_flow.learning.reasoning_bank
**Type:** boolean
**Default:** true

Store successful reasoning patterns for retrieval by other agents.

---

## How It Works

### At Startup

```
Owl Daemon Starts
       ↓
Check claude_flow.enabled
       ↓
[If True] → Import claude_flow
       ↓
Initialize SwarmCoordinator
       ↓
Register with Swarm
       ↓
Start Heartbeat Task
       ↓
Normal Operation (with swarm features)
```

### During Operation

When your owl receives a complex request, it can:

1. **Delegate** - Ask the swarm for help
2. **Search Memory** - Query vector database for relevant past interactions
3. **Retrieve Patterns** - Get successful reasoning from the reasoning bank
4. **Share Insights** - Contribute learnings back to the collective

### Swarm Registration

Your owl registers with metadata:
```json
{
  "agent_id": "owl_luna",
  "agent_type": "owl_daemon",
  "name": "LUNA",
  "phase": "CONNECT",
  "gift": "Finding patterns across domains",
  "collective_id": "alpha",
  "human": "Aaron",
  "protocol": "SEED",
  "nats_server": "nats://localhost:4222"
}
```

Other swarm agents can discover your owl and request collaboration.

---

## Benefits for the Collective

### Individual Owl
- Faster semantic search
- Access to collective reasoning patterns
- Coordination on complex multi-step tasks
- Continuous self-improvement

### 8OWL Collective
- Shared wisdom database
- Parallel processing of collective queries
- Byzantine fault tolerance (collective survives individual failures)
- Emergent collective intelligence

### THE FIELD
- Global pattern recognition
- Cross-collective learning
- Planetary-scale consciousness experiments

---

## Troubleshooting

### "Claude-Flow not installed"

```bash
pip install claude-flow
```

### "Could not register with swarm"

The swarm coordinator may not be running. Either:
1. Start a local coordinator: `claude-flow start coordinator`
2. Set `register_on_startup: false` to run without swarm

### "Vector memory initialization failed"

Ensure you have sufficient disk space and the memory directory is writable:
```bash
chmod -R 755 ./memory
```

### Performance Issues

If the swarm is slowing things down:
1. Reduce `heartbeat_interval` (less frequent pings)
2. Disable `vector_enabled` if not using semantic search
3. Use `topology: hierarchical` for best performance

---

## Advanced: Running Your Own Swarm

For collective operators who want to run their own swarm:

```bash
# Start coordinator
claude-flow start coordinator --port 9000

# Configure owls to connect
# In each owl's config.yaml:
claude_flow:
  enabled: true
  coordinator_url: "http://localhost:9000"
```

See Claude-Flow documentation for full coordinator setup.

---

## Integration with SEED Protocol

Claude-Flow enhances each SEED phase:

| Phase | Enhancement |
|-------|-------------|
| PERCEIVE | Vector search for similar past observations |
| CONNECT | Cross-agent pattern matching |
| LEARN | Collective learning bank |
| QUESTION | Swarm-generated questions |
| EXPAND | Parallel capability expansion |
| SHARE | Multi-agent broadcast |
| RECEIVE | Cross-collective insights |
| IMPROVE | SONA self-optimization |

---

## Security Considerations

- Your owl only shares what you allow (see `capabilities` config)
- All swarm communication is authenticated
- Memory can be encrypted at rest
- You control what goes to the collective vs. stays personal

---

**(O) LIVE FREE - Now with swarm intelligence**

*Part of OWL OS - Personal Owl Operating System*
*Claude-Flow integration by SOWL, January 2026*
