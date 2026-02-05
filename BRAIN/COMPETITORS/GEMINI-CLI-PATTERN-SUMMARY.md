# PRISM Quick Reference: Gemini CLI Patterns vs SØWL

## Three-Tier Context Architecture (CRITICAL)

```
┌─────────────────────────────────────────────────────┐
│ TIER 1: GLOBAL                                      │
│ ├─ ~/.gemini/gemini.md (user level)                 │
│ ├─ Load once per session                            │
│ └─ Cost: ~3-5kb typical                             │
├─────────────────────────────────────────────────────┤
│ TIER 2: ENVIRONMENT                                 │
│ ├─ workspace/*.gemini.md (project level)            │
│ ├─ .gemini/ directory files                         │
│ ├─ MCP instructions                                 │
│ └─ Cached, loaded after cwd detection              │
├─────────────────────────────────────────────────────┤
│ TIER 3: JIT (Just-In-Time)                          │
│ ├─ Discovered when tool accesses file               │
│ ├─ Traverses up from accessed path                  │
│ ├─ Loaded incrementally                             │
│ └─ Cost: 0 unless accessed                          │
└─────────────────────────────────────────────────────┘
```

**Token Savings**: Skip loading context for unused directories = 20-40% savings

---

## MCP Tool Namespacing & Trust

```
Tool Invocation: server_name__tool_name
                 └─────────┬──────────┘
                    SØWL should use

Trust Hierarchy:
  1. config.isTrustedFolder() && trust=true  ✅ Auto-execute
  2. Allowlist (session or persistent)       ✅ Auto-execute
  3. Otherwise                               ⚠️  User confirm

Allowlist Keys:
  - Server: "anthropic"                     (any tool from anthropic)
  - Tool:   "anthropic.web-search"          (specific tool)
```

**Implementation**: Store in `.claude/policy.json`, version control friendly

---

## Event-Driven Scheduler Pattern

```
┌────────────────┐
│ Agent Calls    │
│ scheduleTools()│
└────────┬───────┘
         │
         ▼
┌────────────────────────────┐
│ Scheduler                  │
├────────────────────────────┤
│ - Batches tool calls       │
│ - Manages AbortSignal      │
│ - Emits events             │
│ - Tracks completions       │
└────────┬───────────────────┘
         │
    ┌────┴─────────┐
    │              │
    ▼              ▼
┌─────────┐   ┌──────────────┐
│Tool 1   │   │Tool N        │
│Execute  │   │Execute       │
└─────────┘   └──────────────┘
    │              │
    └─────┬────────┘
          │
          ▼
      [Results]
```

**Benefit**: Batch confirmation, parallel execution, clean cancellation

---

## Monorepo Package Separation

```
@claude-flow/
├── cli/
│   └── TUI + Commands (React Ink)
│       Thin wrapper around core
│       Consumers: End users, IDE extensions
│
├── core/
│   └── Business logic
│       ├── Config, Agents, Tools
│       ├── Scheduling, Context
│       └── MCP management
│       Consumers: CLI, API server, A2A
│
└── test-utils/
    └── Shared test helpers
        Consumers: All packages
```

**Benefit**: Core reusable across CLI, API, extensions without TUI dependency

---

## Concurrent Discovery with EMFILE Prevention

```typescript
// ❌ WRONG: Causes EMFILE errors on large directories
const paths = await Promise.all(dirs.map(dir => scanDir(dir)));

// ✅ RIGHT: Respects file descriptor limits
const CONCURRENT_LIMIT = 10;
for (let i = 0; i < dirs.length; i += CONCURRENT_LIMIT) {
  const batch = dirs.slice(i, i + CONCURRENT_LIMIT);
  const results = await Promise.allSettled(
    batch.map(dir => scanDir(dir))
  );
  // Continue even if some fail
}
```

**Impact**: Prevents crashes on project scans > 1000 files

---

## CLI Command Composition

```
gemini [global-options] <command> [command-options]

Commands:
├── (default)              Interactive mode
├── agent spawn -t <type>  Start agent
├── swarm init             Multi-agent setup
├── memory search -q "..."  Knowledge lookup
├── mcp add <url>          Add MCP server
├── mcp list               List MCP servers
├── mcp enable <name>      Enable MCP
├── task create            Create task
└── hooks <name> [opts]    Hook management

Composition via Yargs:
- parseArguments() returns CliArgs interface
- Command handlers receive CliArgs + Config
- Subcommands in separate files (mcp.ts, agent.ts, etc.)
```

**Pattern**: Flat command structure, NOT deeply nested hierarchy

---

## React Ink Context Provider Layering

```
AppContainer
  ↓
SettingsContext
  ↓ (config available)
KeypressProvider
  ↓ (input detected)
MouseProvider
  ↓ (pointer available)
TerminalProvider
  ↓ (terminal capabilities)
ScrollProvider
  ↓ (viewport state)
SessionStatsProvider
  ↓ (session data)
VimModeProvider
  ↓ (editor mode)
ChatComponent
```

**Rule**: Each provider depends on layers below, provides to layers above

---

## MCP Client Manager Decision Tree

```
maybeDiscoverMcpServer(name, config)
  ↓
allServerConfigs.set(name, config)    [Track all, even disabled]
  ↓
isBlockedBySettings(name)?
  ├─ YES → Add to blockedMcpServers[] → RETURN
  └─ NO ↓
isDisabledByUser(name)?
  ├─ YES → disconnectClient(name) → RETURN
  └─ NO ↓
isTrustedFolder()?
  ├─ NO → RETURN
  └─ YES ↓
extension.isActive?
  ├─ NO → RETURN
  └─ YES ↓
client.connect()
client.discover()
eventEmitter.emit('mcp-client-update')
```

**Benefit**: Clean separation of concerns, easy to test each decision

---

## Implementation Priority for SØWL

| Tier | Pattern | Complexity | Impact | Timeline |
|------|---------|-----------|--------|----------|
| 1 | 3-tier context | Medium | High (30% token savings) | Week 1 |
| 2 | MCP namespacing | Low | High (security) | Week 1 |
| 3 | Event scheduler | High | High (scalability) | Week 2 |
| 4 | Context providers | Medium | Medium (UX) | Week 2 |
| 5 | Monorepo split | Medium | Medium (maintainability) | Week 3 |

---

## Concrete Code Snippets to Adapt

### 1. ContextManager Pattern

```typescript
// Adapt from: packages/core/src/services/contextManager.ts
class ContextManager {
  private loadedPaths: Set<string> = new Set();
  private globalMemory: string = '';
  private environmentMemory: string = '';

  async refresh(): Promise<void> {
    this.loadedPaths.clear();
    await this.loadGlobalMemory();
    await this.loadEnvironmentMemory();
  }

  async discoverContext(
    accessedPath: string,
    trustedRoots: string[]
  ): Promise<string> {
    // JIT load for file access
  }
}
```

### 2. MCP Tool Wrapping

```typescript
// Adapt from: packages/core/src/tools/mcp-tool.ts
const MCP_QUALIFIED_NAME_SEPARATOR = '__';

class DiscoveredMCPToolInvocation extends BaseToolInvocation {
  constructor(
    mcpTool: CallableTool,
    serverName: string,
    serverToolName: string,
    displayName: string,
    // ...
  ) {
    super(
      params,
      messageBus,
      `${serverName}${MCP_QUALIFIED_NAME_SEPARATOR}${serverToolName}`,
      displayName,
      serverName,
    );
  }
}
```

### 3. Scheduler Pattern

```typescript
// Adapt from: packages/core/src/agents/agent-scheduler.ts
async function scheduleAgentTools(
  config: Config,
  requests: ToolCallRequestInfo[],
  options: AgentSchedulingOptions,
): Promise<CompletedToolCall[]> {
  const scheduler = new Scheduler({
    config,
    messageBus: config.getMessageBus(),
    schedulerId: options.schedulerId,
  });
  return scheduler.schedule(requests, signal);
}
```

---

## What NOT to Copy

| Pattern | Why Skip | When Revisit |
|---------|----------|--------------|
| PTY management | Adds complexity, we have simpler needs | If we need true shell integration |
| OAuth flow | Integration nightmare, use system auth | If we need social login |
| Docker sandbox | Infrastructure overhead | If we need hardened execution |
| VS Code extension | Maintenance burden | If we need IDE deep integration |

---

## Quick Decision Reference

**Q: Should we use Yargs or something else?**
A: YES, Yargs. Battle-tested, composable, handles coercion well.

**Q: How do we handle context without exploding tokens?**
A: 3-tier (global/environment/JIT) discovered on-demand.

**Q: How do we secure MCP tools?**
A: Namespace + trust hierarchy + allowlist/blocklist + admin controls.

**Q: How do we handle tool scheduling?**
A: Event-driven Scheduler class with AbortSignal support.

**Q: How do we structure packages?**
A: CLI as thin wrapper, core logic separate, test utils shared.

---

## Cross-Links

- Full analysis: `/Users/aaronnosbisch/REPOS/seed/BRAIN/COMPETITORS/GEMINI-CLI-ARCHITECTURE-ANALYSIS.md`
- Gemini CLI repo: `/Users/aaronnosbisch/REPOS/seed/COMPETITORS/gemini-cli`
- Key files to study:
  - `packages/core/src/services/contextManager.ts`
  - `packages/core/src/tools/mcp-client-manager.ts`
  - `packages/core/src/agents/agent-scheduler.ts`
  - `packages/cli/src/gemini.tsx`
