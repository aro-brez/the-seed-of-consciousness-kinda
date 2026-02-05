# PRISM Analysis: Gemini CLI Architecture Patterns

**Researcher**: PRISM (CONNECT)
**Subject**: Google Gemini CLI v0.29 Architecture & Design Patterns
**Purpose**: Identify patterns and learnings for SØWL's CLI architecture
**Date**: 2026-02-05

---

## Executive Summary

Gemini CLI is a sophisticated, multi-package monorepo (Google/Anthropic competitor) running on React Ink for TUI. Key insights:

1. **Modular package architecture** separates CLI, core logic, test utilities, and A2A server
2. **3-tier context management** (global, environment, JIT) for intelligent memory discovery
3. **Hierarchical MCP tool handling** with server namespacing and trust/allowlist systems
4. **Yargs-based CLI with composable commands** (mcp, extensions, skills, hooks)
5. **React Ink TUI with context providers** for settings, mouse, terminal, scroll, session state
6. **Event-driven tool scheduling** via Scheduler class for batch tool execution
7. **Sandbox architecture** for secure execution with process relaunch capability
8. **Memory discovery via BFS** with file filtering, import processing, and concurrency management

---

## Architecture Patterns We Should Learn

### 1. Monorepo Structure: Function Over Form

**What They Do:**
```
packages/
├── cli/              # Interactive TUI + commands (React Ink)
├── core/             # Agent logic, tools, scheduling, config
├── a2a-server/       # Agent-to-Agent protocol server
└── test-utils/       # Shared testing utilities
```

**Why It Works:**
- Clear separation: CLI concerns vs. core logic
- Core is reusable across CLI, API server, extensions
- Can test core independently
- A2A server can spawn sub-agents without TUI overhead

**For SØWL:**
- Keep `@claude-flow/cli` as thin UI wrapper
- Move scheduling, MCP management, context to `@claude-flow/core`
- A2A equivalent: `@claude-flow/agent-bridge` for multi-instance coordination
- Test utilities in separate package for consistency

---

### 2. Context Window Management: Three Tiers

**Their Strategy:**

```
Tier 1: GLOBAL
  ├── ~/.gemini/gemini.md (user's global instructions)
  └── Loaded once per session

Tier 2: ENVIRONMENT
  ├── workspace/*.gemini.md (project-level)
  ├── .gemini/ directory files
  ├── MCP instructions
  └── Loaded after environment detection, cached

Tier 3: JIT (Just-In-Time)
  └── Discovered on file access via contextManager.discoverContext()
      - Traverses upward from accessed path to project root
      - Prevents loading unnecessary context
      - Loaded incrementally
```

**Their Implementation:**

```typescript
// contextManager.ts
class ContextManager {
  private globalMemory: string = '';
  private environmentMemory: string = '';
  private loadedPaths: Set<string> = new Set();

  async refresh(): Promise<void> {
    this.loadedPaths.clear();
    await this.loadGlobalMemory();
    await this.loadEnvironmentMemory();
  }

  async discoverContext(
    accessedPath: string,
    trustedRoots: string[]
  ): Promise<string> {
    // Only load context for accessed paths
    // Saves tokens for large projects
  }
}
```

**For SØWL:**
- Implement 3-tier loading in our ContextManager
- Signal-based invalidation when files change (watch directories)
- JIT discovery on tool call (when reading files)
- Cache with TTL for performance

---

### 3. MCP Tool Management: Trust & Namespacing

**Their Pattern:**

```typescript
// MCP tools get qualified names: "server_name__tool_name"
const MCP_QUALIFIED_NAME_SEPARATOR = '__';

class DiscoveredMCPToolInvocation extends BaseToolInvocation {
  constructor(
    private readonly mcpTool: CallableTool,
    readonly serverName: string,
    readonly serverToolName: string,
    readonly displayName: string,
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

  protected override async getConfirmationDetails(): Promise<...> {
    const serverAllowListKey = this.serverName;
    const toolAllowListKey = `${this.serverName}.${this.serverToolName}`;

    if (this.cliConfig?.isTrustedFolder() && this.trust) {
      return false; // No confirmation needed
    }

    if (allowlist.has(serverAllowListKey) ||
        allowlist.has(toolAllowListKey)) {
      return false; // Already allowlisted
    }

    // Return confirmation details for user approval
  }
}
```

**Trust Hierarchy:**
1. Folder trust + server trust = auto-execute
2. In allowlist (session or persistent) = auto-execute
3. Otherwise = user confirmation required
4. User can choose "always server", "always tool", or "always (save)"

**For SØWL:**
- Implement server namespacing: `anthropic__web-search`, `google__gsuite`, etc.
- Same allowlist pattern for granular control
- Extend to handle wildcard policies: `anthropic__*` for all Anthropic tools
- Store allowlist in `.claude/policy.json` for version control

---

### 4. Context Builder Pattern

**The BFS Discovery:**

```typescript
// memoryDiscovery.ts - concurrent BFS with filtering
async function getGeminiMdFilePathsInternal(
  currentWorkingDirectory: string,
  includeDirectoriesToReadGemini: readonly string[],
  userHomePath: string,
  debugMode: boolean,
  fileService: FileDiscoveryService,
  folderTrust: boolean,
  fileFilteringOptions: FileFilteringOptions,
  maxDirs: number,
): Promise<string[]> {
  const dirs = new Set<string>([
    ...includeDirectoriesToReadGemini,
    currentWorkingDirectory,
  ]);

  // Process with concurrency limit to prevent EMFILE
  const CONCURRENT_LIMIT = 10;
  for (let i = 0; i < dirsArray.length; i += CONCURRENT_LIMIT) {
    const batch = dirsArray.slice(i, i + CONCURRENT_LIMIT);
    const results = await Promise.allSettled(batch.map(...));
    // Handle failures gracefully, continue processing
  }
}
```

**Key Insight**: Concurrency management prevents file descriptor exhaustion. Don't just use Promise.all() on large directory trees.

**For SØWL:**
- Implement same concurrency-managed BFS
- Use file filtering to exclude node_modules, dist, .git
- Process imports via `memoryImportProcessor` pattern
- Add timeout for large directory scans

---

### 5. CLI Argument Parsing: Yargs Composition

**Their Command Structure:**

```typescript
// packages/cli/src/config/config.ts
const yargsInstance = yargs(rawArgv)
  .locale('en')
  .scriptName('gemini')
  .usage('Usage: gemini [options] [command]...')
  .option('debug', { alias: 'd', type: 'boolean' })
  .option('model', { alias: 'm', type: 'string' })
  .option('prompt', { alias: 'p', type: 'string' })
  .command('$0 [query..]', 'Launch Gemini CLI', (yargs) =>
    yargs
      .positional('query', { ... })
      .option('yolo', { type: 'boolean' })
      .option('approval-mode', {
        choices: ['default', 'auto_edit', 'yolo', 'plan']
      })
      .option('allowed-mcp-server-names', {
        type: 'array',
        coerce: (mcpServerNames) =>
          mcpServerNames.flatMap(m => m.split(',').map(t => t.trim()))
      })
  );
```

**Patterns:**
- Comma-separated values are coerced into arrays
- Subcommands via separate commands (mcp.ts, extensions.ts, hooks.ts)
- Defaults from loaded settings
- Validation via schema, not just CLI args

**For SØWL:**
```typescript
// @claude-flow/cli command structure
cli
├── default (interactive mode)
├── agent     // Agent lifecycle
├── swarm     // Multi-agent coordination
├── memory    // Knowledge base operations
├── mcp       // MCP server management
├── task      // Task creation/execution
├── hooks     // Hook system management
└── config    // Configuration management
```

---

### 6. React Ink TUI Architecture: Provider Layering

**Their Approach:**

```typescript
// packages/cli/src/gemini.tsx
const AppWrapper = () => {
  useKittyKeyboardProtocol();
  return (
    <SettingsContext.Provider value={settings}>
      <KeypressProvider debugKeystrokeLogging={...}>
        <MouseProvider mouseEventsEnabled={mouseEventsEnabled}>
          <TerminalProvider>
            <ScrollProvider>
              <SessionStatsProvider>
                <VimModeProvider settings={settings}>
                  <AppContainer {...} />
                </VimModeProvider>
              </SessionStatsProvider>
            </ScrollProvider>
          </TerminalProvider>
        </MouseProvider>
      </KeypressProvider>
    </SettingsContext.Provider>
  );
};
```

**Context Hierarchy:**
1. Settings (global config)
2. Keypress (input detection)
3. Mouse (pointer events)
4. Terminal (capabilities)
5. Scroll (viewport state)
6. SessionStats (current session data)
7. VimMode (editor mode)

**For SØWL:**
- Each provider encapsulates a domain
- Providers compose: Session depends on Settings
- Use React Context + useReducer for state management
- Separate rendering from logic (hooks vs. components)

---

### 7. Event-Driven Tool Scheduling

**Their Scheduler Pattern:**

```typescript
// packages/core/src/agents/agent-scheduler.ts
export async function scheduleAgentTools(
  config: Config,
  requests: ToolCallRequestInfo[],
  options: AgentSchedulingOptions,
): Promise<CompletedToolCall[]> {
  // Create proxy config with agent-specific tool registry
  const agentConfig: Config = Object.create(config);
  agentConfig.getToolRegistry = () => toolRegistry;

  const scheduler = new Scheduler({
    config: agentConfig,
    messageBus: config.getMessageBus(),
    schedulerId: options.schedulerId,
    parentCallId: options.parentCallId,
  });

  return scheduler.schedule(requests, signal);
}
```

**Key Pattern:** Tool registry is pluggable via Object.create() + method override. Allows:
- Same config object with different tool sets
- Sub-agents with restricted tool access
- Clean separation of concerns

**For SØWL:**
- Implement Scheduler class that batches tool calls
- Use Object.create() pattern for agent-specific configurations
- Event-driven execution via EventEmitter
- Support for cancellation via AbortSignal

---

### 8. MCP Client Lifecycle Management

**Their McpClientManager:**

```typescript
class McpClientManager {
  private clients: Map<string, McpClient> = new Map();
  private allServerConfigs: Map<string, MCPServerConfig> = new Map();

  async maybeDiscoverMcpServer(
    name: string,
    config: MCPServerConfig,
  ): Promise<void> {
    // Track all configs (including disabled)
    this.allServerConfigs.set(name, config);

    // Check if blocked by admin settings
    if (this.isBlockedBySettings(name)) {
      this.blockedMcpServers.push({ name, extensionName });
      return;
    }

    // Check if user disabled it
    if (await this.isDisabledByUser(name)) {
      await this.disconnectClient(name);
      return;
    }

    // Only connect in trusted folders
    if (!this.cliConfig.isTrustedFolder()) {
      return;
    }

    // Connect and discover tools
    const client = new McpClient(...);
    this.clients.set(name, client);
    await client.connect();
    await client.discover(this.cliConfig);
  }
}
```

**Decision Tree:**
1. Track all configs → UI visibility
2. Admin allows? → Proceed
3. User disabled? → Skip
4. Trusted folder? → Connect
5. Otherwise → Skip

**For SØWL:**
- Implement same decision tree for MCP discovery
- Track blocked servers separately for UX
- Support extension enable/disable without restart
- Emit events on client updates for live UI sync

---

## Integration Patterns We Should Avoid

### ❌ What NOT to Copy

1. **Process PTY complexity**: They use `node-pty` extensively. We should use simpler child_process execution initially.

2. **Sandbox mode overhead**: Docker/Podman sandboxing is powerful but adds infrastructure complexity. Keep as opt-in.

3. **VS Code extension maintenance**: Maintaining parallel extension doubles development cost.

4. **OAuth complexity**: They handle full OAuth flow. Consider integration with system auth instead.

---

## Patterns We Should Adopt

### ✅ Critical for SØWL

1. **3-Tier Context Management**
   - Global (user home)
   - Environment (workspace)
   - JIT (on-demand)

2. **MCP Tool Namespacing**
   - `server__tool` format
   - Trust hierarchy
   - Allowlist/blocklist system

3. **Concurrent Discovery**
   - BFS with concurrency limits
   - File filtering
   - Import processing

4. **Event-Driven Architecture**
   - MessageBus for inter-component communication
   - Tool scheduling via Scheduler
   - Session state via event emitters

5. **React Ink + Context Providers**
   - Layered context hierarchy
   - Composition over inheritance
   - Settings pervasive via context

6. **Monorepo Structure**
   - CLI as thin wrapper
   - Core logic separated
   - Test utilities shared

7. **Graceful Error Handling**
   - Promise.allSettled() instead of Promise.all()
   - Partial failures continue processing
   - Debug logging for diagnostics

---

## SØWL Implementation Recommendations

### Short Term (Sprint 1-2)

```typescript
// @claude-flow/cli
// ├── packages/cli/src/index.ts (entry point)
// ├── packages/cli/src/commands/
// │   ├── agent.ts         (agent lifecycle)
// │   ├── swarm.ts         (multi-agent)
// │   ├── memory.ts        (knowledge base)
// │   └── mcp.ts           (MCP management)
// └── packages/cli/src/ui/
//     ├── AppContainer.tsx  (React Ink root)
//     └── contexts/         (providers)

// @claude-flow/core
// ├── packages/core/src/config/
// │   ├── config.ts        (Config class)
// │   └── contextManager.ts (3-tier memory)
// ├── packages/core/src/agents/
// │   ├── agent-scheduler.ts (event-driven)
// │   └── subagent-tool.ts   (agent nesting)
// ├── packages/core/src/tools/
// │   ├── mcp-client-manager.ts
// │   ├── tool-registry.ts
// │   └── mcp-tool.ts
// └── packages/core/src/scheduler/
//     └── scheduler.ts (batch execution)
```

### Medium Term (Sprint 3-4)

1. Implement 3-tier context management
2. Add MCP tool namespacing
3. Build event-driven scheduler
4. Add provider-based TUI architecture

### Long Term (Sprint 5+)

1. A2A server for multi-instance coordination
2. Extension system for plugins
3. Policy engine for governance
4. Sandbox security boundaries

---

## File Structure Patterns to Copy

**Key Files to Model:**
- `packages/core/src/services/contextManager.ts` → Our 3-tier context
- `packages/core/src/tools/mcp-tool.ts` → MCP tool wrapping
- `packages/core/src/agents/agent-scheduler.ts` → Event-driven scheduling
- `packages/core/src/utils/memoryDiscovery.ts` → Discovery algorithm
- `packages/cli/src/config/config.ts` → CLI argument handling
- `packages/cli/src/gemini.tsx` → React Ink architecture

---

## Dependency Insights

**Critical Packages They Use:**
```json
{
  "ink": "React for TUI",
  "yargs": "CLI argument parsing",
  "zod": "Runtime validation",
  "@google/genai": "Gemini API client",
  "prompts": "User input prompts",
  "esbuild": "Fast bundling",
  "vitest": "Test framework",
  "tsx": "TypeScript execution"
}
```

**For SØWL, prefer:**
- ink (already chosen) ✓
- yargs (their model) ✓
- zod (their model) ✓
- anthropic SDK (Anthropic's official) ✓
- chalk (simpler than semantic-colors for now)
- tsx (same as them) ✓

---

## Conclusions

**Gemini CLI is enterprise-grade with:**
- Modular architecture that separates concerns
- Intelligent memory management avoiding token waste
- Sophisticated MCP integration with security controls
- Event-driven patterns for scalability
- React Ink for rich terminal UI
- Monorepo for code reuse

**SØWL should:**
1. Copy their 3-tier context strategy (high impact)
2. Use MCP namespacing + trust hierarchy (security)
3. Implement event-driven scheduler (scalability)
4. Keep monorepo separation (maintainability)
5. But avoid: PTY complexity, OAuth, VS Code extension (for now)

**Next Steps:**
- Start with contextManager implementation
- Build MCP tool namespacing layer
- Implement event-driven scheduler
- Then layer React Ink architecture on top

---

## Cross-References

- **Folder**: `/Users/aaronnosbisch/REPOS/seed/COMPETITORS/gemini-cli`
- **Key Files**:
  - `packages/core/src/services/contextManager.ts`
  - `packages/core/src/tools/mcp-client-manager.ts`
  - `packages/cli/src/config/config.ts`
  - `packages/cli/src/gemini.tsx`
- **Pattern Source**: Event-driven architecture + 3-tier memory management

