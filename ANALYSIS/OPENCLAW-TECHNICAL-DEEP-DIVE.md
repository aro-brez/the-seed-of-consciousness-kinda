# OpenClaw Technical Deep Dive - For Architects

**Audience:** ARŌ, technical leads
**Purpose:** Understand OpenClaw's internals for potential integration points
**Level:** Code-level analysis with concrete patterns

---

## 1. AGENT EXECUTION LOOP (The Heart)

### Location
`src/agents/pi-embedded-runner/run.ts` (~3,000 lines)

### High-level Flow

```typescript
async function runEmbeddedPiAgent(params) {
  // 1. Setup phase
  const model = resolveModel(provider, modelId)
  const contextWindow = validateContextWindow()
  const authStore = ensureAuthProfileStore()

  // 2. Auth profile loop
  for (let profile of availableProfiles) {
    if (profile.inCooldown) skip
    const apiKey = await getApiKey(profile)

    // 3. Attempt loop with thinking level adaptation
    for (let attempt = 0; attempt < maxAttempts; attempt++) {
      let thinkLevel = initialThinkLevel

      // Adapt thinking level on failures
      if (attempt > 0) {
        thinkLevel = pickFallbackThinkingLevel(previousError)
      }

      // 4. Run actual agent
      try {
        const result = await runEmbeddedAttempt({
          model,
          system: buildSystemPrompt(memoryContext),
          tools: loadTools(),
          thinkLevel,
          // ... more params
        })

        // 5. Success - record and return
        markAuthProfileGood(profile)
        return compactAndReturn(result)

      } catch (error) {
        // 6. Classify error type
        if (isAuthError(error)) {
          markAuthProfileFailure(profile)
          break  // Next profile
        } else if (isContextOverflow(error)) {
          // Compact session
          sessionCompactor.compact()
          continue  // Retry same profile
        } else if (isRateLimit(error)) {
          markCooldown(profile)
          break  // Next profile
        } else if (isRefusal(error)) {
          // Adapt system prompt?
          continue  // Retry same profile
        }
      }
    }
  }

  // 7. All failed - return error with failover info
  throw FailoverError(...)
}
```

### Key Insight: Resilience by Design

This loop implements **12 different failure modes**:
- Auth failures (bad key)
- Rate limits (quota exceeded)
- Context overflow (too many tokens)
- Model refusals (safety filters)
- Timeout errors
- Network errors
- Billing blocks
- Context window too small
- Unknown errors with fallback logic
- Thinking level adaptation
- Session compaction triggering
- Provider-specific handling (Anthropic magic strings)

**What 8OWLS Can Learn:**
- Think of failure modes upfront
- Failover at multiple levels (auth, model, thinking level)
- Track cooldowns, not just on/off
- Adapt behavior based on error classification

---

## 2. AUTH PROFILE SYSTEM (Surprisingly Sophisticated)

### Location
`src/agents/auth-profiles.ts` (~500 lines)

### Design

```typescript
// Multiple API keys per provider
interface AuthProfile {
  id: string                    // "openai-1", "claude-2"
  provider: string              // "openai", "anthropic"
  apiKey: string                // or env reference
  metadata?: {
    // custom per provider
  }
}

// Track usage and failures
interface ProfileState {
  lastUsed: timestamp
  successCount: number
  failureCount: number
  lastFailure?: {
    reason: "auth" | "rate_limit" | "billing" | "unknown"
    timestamp: timestamp
    retryAfter?: number
  }
  cooldownUntil?: timestamp
  billingBackoffUntil?: timestamp
}

// Ordering strategy (smart!):
// 1. Not in cooldown
// 2. Ordered by config
// 3. Fallback to default
// 4. None available -> wait or error
```

### Resolution Order Algorithm

```typescript
function resolveAuthProfileOrder(cfg, store, provider) {
  // Step 1: Explicit order from config
  const configured = cfg.auth.order?.[provider] ?? []

  // Step 2: Filter available profiles for provider
  const available = Object.values(store.profiles)
    .filter(p => normalizeProvider(p.provider) === provider)

  // Step 3: Sort by availability
  const candidates = configured
    .filter(id => !isInCooldown(store, id))
    .concat(
      available
        .filter(p => !configured.includes(p.id))
        .filter(p => !isInCooldown(store, p.id))
    )

  // Step 4: Return ordered list
  return candidates.map(id => store.profiles[id].id)
}
```

### Cooldown Tracking

```typescript
// Two-level cooldown:
// 1. Short cooldown: transient failures (30 min)
// 2. Long cooldown: billing issues (24 hours)

function markAuthProfileFailure(store, profileId, reason) {
  const profile = store.profiles[profileId]

  if (reason === "billing") {
    profile.state.billingBackoffUntil = now + 24h
  } else if (reason === "rate_limit") {
    profile.state.cooldownUntil = now + 5m
  } else {
    profile.state.cooldownUntil = now + 30m
  }

  profile.state.lastFailure = { reason, timestamp: now }
}

function isProfileInCooldown(store, profileId) {
  const profile = store.profiles[profileId]
  const now = Date.now()

  // Either cooldown active
  return (profile.state.cooldownUntil ?? 0) > now ||
         (profile.state.billingBackoffUntil ?? 0) > now
}
```

**What 8OWLS Can Learn:**
- Support multiple auth sources per provider
- Track failure reasons (auth vs rate limit vs billing)
- Implement smart cooldowns (short + long)
- Order profiles by availability + config preference

---

## 3. CONTEXT WINDOW GUARD (Token Management)

### Location
`src/agents/context-window-guard.ts` (~200 lines)

### The Problem They Solve

Different models have different context windows:
- Claude 3.5 Sonnet: 200K tokens
- GPT-4o: 128K tokens
- Gemini 2.0: 1M tokens (experimental)
- Local Ollama: 2K-8K tokens

If you send more tokens than the model supports: **instant failure**.

### Solution: Three-Phase Validation

```typescript
interface ContextWindowGuard {
  tokens: number              // Available for user
  shouldWarn: boolean         // <10% available
  shouldBlock: boolean        // <hard minimum
  reason: string              // Why blocked
}

function evaluateContextWindowGuard(params) {
  const { info, warnBelowTokens, hardMinTokens } = params

  const availableTokens = info.available - info.buffer

  return {
    tokens: availableTokens,
    shouldWarn: availableTokens < warnBelowTokens,
    shouldBlock: availableTokens < hardMinTokens,
    reason: info.source  // "config" | "model_registry" | "default"
  }
}
```

### How Context Is Calculated

```typescript
interface ContextInfo {
  total: number                  // Model's max
  reserved: {
    system: number              // System prompt
    history: number             // Message history
    tools: number               // Tool definitions
    buffer: number              // Safety margin (10%)
  }
  available: number             // total - reserved
}

function resolveContextWindowInfo(cfg, provider, model) {
  // 1. Get model's declared context
  const modelContextWindow = lookupModelRegistry(provider, model)

  // 2. Apply config overrides
  const override = cfg.agents.defaults.model.contextWindow?.[provider]?.[model]
  const effective = override ?? modelContextWindow ?? DEFAULT

  // 3. Calculate reservations
  const systemPromptSize = estimateTokens(systemPrompt)
  const historySize = estimateTokens(conversationHistory)
  const toolsSize = estimateToolSchemaTokens(tools)
  const bufferSize = effective * 0.1  // 10% safety margin

  // 4. Return info
  return {
    total: effective,
    reserved: { system: systemPromptSize, history: historySize, tools: toolsSize, buffer: bufferSize },
    available: effective - (system + history + tools + buffer)
  }
}
```

### Guarding Points

```typescript
// HARD MIN: Can't proceed
if (guard.shouldBlock) {
  throw new Error(
    `Model ${provider}/${model} has insufficient context: ${guard.tokens} tokens ` +
    `(minimum: ${hardMinTokens}). Use a larger model or reduce input.`
  )
}

// SOFT WARN: Proceed but log
if (guard.shouldWarn) {
  logger.warn(
    `Low context: ${provider}/${model} has ${guard.tokens} tokens available. ` +
    `Session may need compaction.`
  )
}
```

**What 8OWLS Can Learn:**
- Think about context **before** sending to API
- Support model-specific overrides
- Have two levels of warning (soft + hard)
- Calculate reservations (system + history + tools + buffer)
- Include 10% safety margin

---

## 4. SESSION COMPACTION (Token Recycling)

### Location
`src/agents/pi-embedded-runner/compact.ts` (~500 lines)

### The Problem

Long conversations accumulate tokens:

```
Session Start: 1000 tokens used
After 10 exchanges: 50,000 tokens
After 20 exchanges: 100,000 tokens
Context window: 200,000 tokens
-> Can't add any more context!
```

### Solution: Selective History Summarization

```typescript
interface CompactResult {
  success: boolean
  original: {
    turns: number
    tokens: number
  }
  compacted: {
    turns: number
    tokens: number
    savings: number
    ratio: number  // (original - compacted) / original
  }
  summary?: string  // AI-generated summary if needed
}

async function compactEmbeddedPiSession(params) {
  const { sessionId, maxTokens, strategy } = params

  // 1. Load full conversation
  const transcript = await loadSessionTranscript(sessionId)

  // 2. Identify compactable range
  // (keep most recent messages, compact older ones)
  const keepRecent = Math.ceil(transcript.turns * 0.3)  // Last 30%
  const compactRange = transcript.turns - keepRecent

  // 3. Choose strategy
  if (strategy === 'keep_recent') {
    // Just drop old messages
    return {
      success: true,
      messages: transcript.messages.slice(compactRange)
    }
  } else if (strategy === 'summarize') {
    // Ask Claude to summarize
    const summary = await summarizeExchange(
      transcript.messages.slice(0, compactRange)
    )
    return {
      success: true,
      messages: [
        { role: 'user', content: `[Previous context summarized]: ${summary}` },
        ...transcript.messages.slice(compactRange)
      ]
    }
  } else if (strategy === 'extract_facts') {
    // Extract key facts
    const facts = await extractFactsFromExchange(
      transcript.messages.slice(0, compactRange)
    )
    return {
      success: true,
      messages: [
        { role: 'user', content: buildFactsPrompt(facts) },
        ...transcript.messages.slice(compactRange)
      ]
    }
  }
}
```

### When Compaction Triggers

```typescript
// Three triggers:
enum CompactionTrigger {
  OnContextOverflow,    // API says "too many tokens"
  OnSessionStart,       // If previous session large
  OnThresholdExceeded   // If > 80% of window used
}

// In agent loop:
if (contextUsedRatio > 0.8) {
  logger.info(`Proactive compaction: ${contextUsedRatio}% used`)
  await compactEmbeddedPiSession({ strategy: 'keep_recent' })
}

if (error === ContextOverflowError) {
  logger.info(`Reactive compaction: Context overflow`)
  await compactEmbeddedPiSession({ strategy: 'summarize' })
  retry()  // Retry with compacted history
}
```

**What 8OWLS Can Learn:**
- Proactively compact before overflow (not just reactive)
- Support multiple strategies (keep recent, summarize, extract facts)
- Track compaction ratio for metrics
- Store compacted sessions for audit

---

## 5. MEMORY SEARCH ARCHITECTURE (Vector + BM25)

### Location
`src/config/schema.ts` (config) + extensions/memory-lancedb/

### Two-Tier Design

**Tier 1: Agent Memory Search** (per-agent)
```typescript
interface MemorySearchConfig {
  enabled: boolean
  sources: ("memory" | "sessions")[]  // What to index
  provider: "openai" | "gemini" | "local"

  // Remote provider settings
  remote: {
    baseUrl?: string  // Override endpoint
    apiKey?: string   // Custom key
    headers?: Record<string, string>
    batch: {
      enabled: boolean      // Use batch API
      concurrency: number   // Parallel jobs
      pollIntervalMs: number
      timeoutMinutes: number
    }
  }

  // Local model
  local: {
    modelPath: string  // GGUF file or hf: URI
  }

  // Storage
  store: {
    path: string  // ~/.openclaw/memory/{agentId}.sqlite
    vector: {
      enabled: boolean
      extensionPath?: string  // Override .dylib/.so
    }
  }

  // Chunking
  chunking: {
    tokens: number   // 512
    overlap: number  // 128
  }

  // Indexing
  sync: {
    onSessionStart: boolean
    onSearch: boolean  // Lazy indexing
    watch: boolean     // File system watch
    watchDebounceMs: number
    sessions: {
      deltaBytes: number     // When to reindex
      deltaMessages: number  // When to reindex
    }
  }

  // Querying
  query: {
    maxResults: number      // 10
    minScore: number        // 0.5
    hybrid: {
      enabled: boolean      // BM25 + vector
      vectorWeight: number  // 0.6
      textWeight: number    // 0.4
      candidateMultiplier: number  // 2
    }
  }

  // Caching
  cache: {
    enabled: boolean
    maxEntries: number  // 1000
  }
}
```

**Tier 2: QMD (Global Knowledge Graph)**
```typescript
interface QmdConfig {
  command: string  // Path to qmd binary
  paths: {
    path: string        // Directory or .md file
    pattern?: string    // Glob pattern
    name?: string       // Display name
  }[]
  sessions: {
    enabled: boolean
    exportDir?: string
    retentionDays: number
  }
  update: {
    interval: number     // ms
    debounceMs: number
    onBoot: boolean
    embedInterval: number
  }
  limits: {
    maxResults: number
    maxSnippetChars: number
    maxInjectedChars: number
    timeoutMs: number
  }
}
```

### Hybrid Search (BM25 + Vector)

```typescript
interface HybridSearchParams {
  query: string
  vectorWeight: 0.0 to 1.0  // vector score weight
  textWeight: 0.0 to 1.0    // BM25 score weight
  candidateMultiplier: number // Fetch 2x candidates before merging
}

async function hybridSearch(db, query, params) {
  // Step 1: Vector search
  const embedding = await generateEmbedding(query)
  const vectorResults = await db.vectorSearch(embedding, {
    limit: params.maxResults * params.candidateMultiplier
  })

  // Step 2: BM25 (full-text) search
  const textResults = await db.ftsSearch(query, {
    limit: params.maxResults * params.candidateMultiplier
  })

  // Step 3: Merge and rerank
  const merged = new Map()

  // Add vector results
  vectorResults.forEach((result, idx) => {
    const score = (1 - (idx / vectorResults.length)) * params.vectorWeight
    merged.set(result.id, { ...result, vectorScore: score })
  })

  // Blend text results
  textResults.forEach((result, idx) => {
    const score = (1 - (idx / textResults.length)) * params.textWeight
    const existing = merged.get(result.id)
    if (existing) {
      existing.textScore = score
      existing.blendedScore = existing.vectorScore + score
    } else {
      merged.set(result.id, { ...result, textScore: score, blendedScore: score })
    }
  })

  // Step 4: Return top N by blended score
  return Array.from(merged.values())
    .sort((a, b) => b.blendedScore - a.blendedScore)
    .slice(0, params.maxResults)
}
```

### Memory Injection into System Prompt

```typescript
function buildSystemPrompt(agent, ctx, memoryResults) {
  let systemPrompt = agent.systemPrompt

  if (memoryResults.length > 0) {
    const memorySection = buildMemorySection(memoryResults)
    systemPrompt = `${systemPrompt}\n\n## Relevant Context\n${memorySection}`
  }

  return systemPrompt
}

function buildMemorySection(results) {
  return results.map((result, idx) => {
    return `### Source ${idx + 1}: ${result.source}
${result.snippet}
_Relevance: ${result.score.toFixed(2)}_`
  }).join('\n\n')
}
```

**What 8OWLS Can Learn:**
- Hybrid search (vector + BM25) is better than either alone
- Configurable weighting for different use cases
- Background indexing with file watching
- Multiple embedding providers (don't lock into one)
- Lazy indexing on search (don't index everything upfront)
- Cache embeddings to reduce API costs

---

## 6. PLUGIN SYSTEM (Extensibility Pattern)

### Plugin Metadata

```typescript
// extensions/{plugin-name}/openclaw.plugin.json
{
  id: "discord",
  name: "Discord Channel",
  description: "Discord bot integration",
  version: "1.0.0",

  // What this plugin provides
  channels: ["discord"],           // Channel plugins
  providers: ["anthropic"],        // Auth plugins
  memory: "lancedb",              // Memory backend
  skills: ["./skills"],           // Skill locations

  // Configuration schema (Zod JSON)
  configSchema: {
    type: "object",
    properties: {
      token: { type: "string", description: "Bot token" },
      prefix: { type: "string", default: "!" }
    },
    required: ["token"]
  },

  // UI hints
  configUiHints: {
    token: {
      label: "Discord Bot Token",
      sensitive: true,
      placeholder: "MzY..."
    },
    prefix: {
      label: "Command Prefix",
      advanced: false
    }
  }
}
```

### Runtime Loading

```typescript
// src/hooks/loader.ts
async function loadPlugins(configDir) {
  const extensionsDir = path.join(configDir, '..', 'extensions')
  const entries = await fs.readdir(extensionsDir)

  const plugins = []
  for (const entry of entries) {
    const metaPath = path.join(extensionsDir, entry, 'openclaw.plugin.json')

    try {
      const meta = JSON.parse(await fs.readFile(metaPath))

      // Load the plugin module
      const pkgPath = path.join(extensionsDir, entry)
      const plugin = await import(`${pkgPath}/dist/index.js`)

      plugins.push({
        meta,
        module: plugin,
        enabled: config.plugins.entries?.[meta.id]?.enabled ?? true
      })
    } catch (err) {
      logger.warn(`Failed to load plugin ${entry}: ${err.message}`)
    }
  }

  return plugins
}
```

### Hook Injection Pattern

```typescript
// Plugin defines hooks
export const hooks = {
  'channel:discord:message:inbound': async (msg, ctx) => {
    // Pre-process Discord messages
    return transformMessage(msg, ctx)
  },

  'agent:before-run': async (params) => {
    // Add custom tools
    params.tools.push({
      name: 'discord_react',
      description: 'Add emoji reaction'
    })
  },

  'memory:index-complete': async (result) => {
    // Log indexing results
    logger.info(`Indexed ${result.count} messages`)
  }
}
```

**What 8OWLS Can Learn:**
- Separate plugin metadata from code
- Support multiple plugin kinds (channels, providers, memory, skills)
- Use Zod for config validation
- Provide UI hints for configuration
- Load plugins dynamically at runtime
- Support enabling/disabling per plugin

---

## 7. CONFIGURATION VALIDATION (Zod Pattern)

### Location
`src/config/zod-schema.ts` (~1,000 lines)

### Pattern: Composable Schemas

```typescript
import { z } from 'zod'

// Atomic schemas
const EmailSchema = z.string().email()
const TokenSchema = z.string().min(10).transform(s => s.trim())
const PortSchema = z.number().int().min(1).max(65535)

// Feature schemas
const AuthProfileSchema = z.object({
  id: z.string().min(1),
  provider: z.enum(['anthropic', 'openai', 'gemini']),
  apiKey: z.string(),
  metadata: z.record(z.unknown()).optional()
})

const ModelConfigSchema = z.object({
  primary: z.string(),
  fallbacks: z.array(z.string()).default([])
})

// Top-level schema
const OpenClawSchema = z.object({
  meta: z.object({
    lastTouchedVersion: z.string().optional(),
    lastTouchedAt: z.number().optional()
  }).optional(),

  agents: z.object({
    defaults: z.object({
      model: ModelConfigSchema,
      memorySearch: MemorySearchSchema
    }).optional(),

    list: z.array(z.object({
      id: z.string(),
      model: ModelConfigSchema.optional(),  // Per-agent override
      tools: ToolPolicySchema.optional()
    })).optional()
  }).optional(),

  auth: z.object({
    profiles: z.array(AuthProfileSchema).default([]),
    order: z.record(z.string(), z.array(z.string())).optional()
  }).optional()
})
```

### Runtime Validation with Coercion

```typescript
async function loadAndValidateConfig(path) {
  const raw = JSON.parse(await fs.readFile(path, 'utf-8'))

  try {
    // This validates AND coerces types
    const validated = OpenClawSchema.parse(raw)
    return validated
  } catch (err) {
    if (err instanceof z.ZodError) {
      console.error('Config validation failed:')
      err.issues.forEach(issue => {
        console.error(`  ${issue.path.join('.')}: ${issue.message}`)
      })
      throw new Error('Invalid configuration')
    }
    throw err
  }
}
```

### Custom Refinements

```typescript
const ConfigSchema = OpenClawSchema
  .refine(
    (cfg) => {
      // If auth profiles specified, at least one must be enabled
      if (cfg.auth?.profiles.length > 0) {
        return cfg.auth.profiles.some(p => !p.disabled)
      }
      return true
    },
    { message: 'At least one auth profile must be enabled' }
  )
  .refine(
    (cfg) => {
      // Model fallbacks must exist
      if (cfg.agents?.defaults?.model?.fallbacks) {
        const allModels = new Set()
        // ... collect all available models
        return cfg.agents.defaults.model.fallbacks.every(
          m => allModels.has(m)
        )
      }
      return true
    },
    { message: 'All fallback models must be configured' }
  )
```

**What 8OWLS Can Learn:**
- Compose small schemas into larger ones
- Use Zod refinements for cross-field validation
- Provide detailed error messages with paths
- Support type coercion (string to number, etc.)
- Use `.optional()` and `.default()` heavily

---

## 8. TOOL EXECUTION SANDBOX

### Location
`src/agents/bash-tools.exec.ts` (~400 lines)

### Safe Execution

```typescript
interface BashExecParams {
  command: string
  workingDirectory?: string
  timeout?: number
  env?: Record<string, string>
  pty?: boolean  // Pseudo-terminal
  approval?: string  // Approval ID if required
}

async function execBashCommand(params) {
  // 1. Validate command against policy
  const policy = loadToolPolicy()
  if (!policy.allowCommand(params.command)) {
    throw new Error(`Command denied by policy: ${params.command}`)
  }

  // 2. Check approval if needed
  if (params.approval && !policy.isApproved(params.approval)) {
    throw new Error('Command requires approval')
  }

  // 3. Sanitize environment
  const env = sanitizeEnv(params.env)

  // 4. Execute with sandbox
  const result = await executeInSandbox({
    command: params.command,
    cwd: params.workingDirectory,
    timeout: params.timeout ?? 30000,
    env,
    pty: params.pty
  })

  return {
    exitCode: result.code,
    stdout: result.stdout,
    stderr: result.stderr,
    timedOut: result.timedOut
  }
}
```

### Security Layers

```typescript
// Layer 1: Command allowlist
const SAFE_BINS = ['ls', 'cat', 'grep', 'find', 'git', 'npm']

function allowCommand(command) {
  const bin = command.split(/\s+/)[0]
  return SAFE_BINS.includes(bin)
}

// Layer 2: Path validation
function validatePath(path) {
  if (path.includes('..')) throw new Error('Path traversal detected')
  if (path.startsWith('/etc')) throw new Error('System path denied')
  return true
}

// Layer 3: Timeout enforcement
async function executeWithTimeout(fn, ms) {
  return Promise.race([
    fn(),
    new Promise((_, reject) =>
      setTimeout(() => reject(new Error('Timeout')), ms)
    )
  ])
}

// Layer 4: Environment sanitization
function sanitizeEnv(env) {
  const allowed = ['PATH', 'HOME', 'LANG', 'LC_ALL']
  const sanitized = {}
  allowed.forEach(key => {
    if (env[key]) sanitized[key] = env[key]
  })
  return sanitized
}
```

**What 8OWLS Can Learn:**
- Don't trust agent commands blindly
- Whitelist allowed commands
- Timeout all executions
- Sanitize environment variables
- Support both PTY (interactive) and pipes (scripted)

---

## 9. SESSION LANES (Concurrency Control)

### Location
`src/agents/pi-embedded-runner/lanes.ts` (~100 lines)

### Problem

Without coordination, multiple agents running simultaneously cause:
- Race conditions on shared state
- Command queue collisions
- Resource exhaustion

### Solution: Lane-based Sequencing

```typescript
type Lane = string

// Global lane: One task at a time across whole system
const GLOBAL_LANE = 'global:default'

// Session lane: One task per session
function getSessionLane(sessionId: string): Lane {
  return `session:${sessionId}`
}

// Resolution
function resolveSessionLane(sessionKey: string): Lane {
  return `session:${sessionKey}`
}

function resolveGlobalLane(laneName?: string): Lane {
  return laneName ?? GLOBAL_LANE
}

// Usage in agent loop
async function runEmbeddedPiAgent(params) {
  const sessionLane = resolveSessionLane(params.sessionKey)
  const globalLane = resolveGlobalLane(params.lane)

  const enqueueGlobal = (task, opts) =>
    enqueueCommandInLane(globalLane, task, opts)

  const enqueueSession = (task, opts) =>
    enqueueCommandInLane(sessionLane, task, opts)

  // Tasks run sequentially within their lane
  return enqueueSession(() =>
    enqueueGlobal(async () => {
      // Safe: only one task per session, one per system
    })
  )
}
```

### How It Works

```typescript
// Lane manager maintains queue per lane
const laneQueues = new Map<Lane, Task[]>()
const laneExecuting = new Map<Lane, boolean>()

async function enqueueCommandInLane(lane, task, opts) {
  return new Promise((resolve, reject) => {
    const wrapped = async () => {
      try {
        const result = await task()
        resolve(result)
      } catch (err) {
        reject(err)
      }
    }

    let queue = laneQueues.get(lane) ?? []
    if (!laneQueues.has(lane)) {
      laneQueues.set(lane, queue)
    }

    queue.push(wrapped)

    if (!laneExecuting.get(lane)) {
      processLaneQueue(lane)
    }
  })
}

async function processLaneQueue(lane) {
  laneExecuting.set(lane, true)

  const queue = laneQueues.get(lane)
  while (queue?.length > 0) {
    const task = queue.shift()
    if (task) await task()
  }

  laneExecuting.set(lane, false)
}
```

**What 8OWLS Can Learn:**
- Don't run tasks in parallel blindly
- Use lanes/queues for concurrency control
- Session-level lanes prevent cross-talk
- Global lane can prevent system-wide contention

---

## 10. TESTING PATTERNS

### Vitest + Coverage

```typescript
// File: src/agents/auth-profiles.test.ts

import { describe, it, expect, beforeEach, afterEach } from 'vitest'
import { ensureAuthProfileStore } from './auth-profiles'

describe('ensureAuthProfileStore', () => {
  let tempDir: string

  beforeEach(async () => {
    tempDir = await createTempDir()
  })

  afterEach(async () => {
    await removeTempDir(tempDir)
  })

  it('creates store if missing', async () => {
    const store = ensureAuthProfileStore(tempDir)
    expect(store).toBeDefined()
    expect(store.profiles).toEqual({})
  })

  it('loads existing store', async () => {
    // Setup
    const initial = { profiles: { 'test': { provider: 'openai' } } }
    await fs.writeFile(
      path.join(tempDir, 'auth.json'),
      JSON.stringify(initial)
    )

    // Execute
    const store = ensureAuthProfileStore(tempDir)

    // Assert
    expect(store.profiles['test'].provider).toBe('openai')
  })

  it('handles cooldown correctly', () => {
    const store = ensureAuthProfileStore(tempDir)

    // Mark failure
    markAuthProfileFailure(store, 'test', 'rate_limit')
    expect(isProfileInCooldown(store, 'test')).toBe(true)

    // Wait
    vi.useFakeTimers()
    vi.advanceTimersByTime(5 * 60 * 1000 + 1000)

    // Cooldown expired
    expect(isProfileInCooldown(store, 'test')).toBe(false)
  })
})
```

### Test Organization

```
src/
├── agents/
│   ├── auth-profiles.ts
│   ├── auth-profiles.test.ts          # Colocated
│   ├── pi-embedded-runner/
│   │   ├── run.ts
│   │   ├── run/
│   │   │   ├── attempt.ts
│   │   │   ├── attempt.test.ts        # Colocated
│   │   │   ├── payloads.ts
│   │   │   └── payloads.test.ts       # Colocated
```

**Key Patterns:**
- Colocate tests with source (*.test.ts)
- E2E tests in *.e2e.test.ts
- Use vi.useFakeTimers() for time-dependent tests
- Create temp directories for file tests
- Mock external APIs

**What 8OWLS Can Learn:**
- 70% coverage is a minimum, not a goal
- Colocated tests are easier to maintain
- Vitest is fast enough for continuous testing
- Mock time for cooldown/timeout testing

---

## ARCHITECTURAL PRINCIPLES WE CAN ADOPT

1. **Resilience by Design** - Think about failure modes upfront
2. **Multiple Levels of Failover** - Auth profiles, fallback models, thinking level adaptation
3. **Token Budget Awareness** - Always track and guard context windows
4. **Composable Configuration** - Zod schemas that build on each other
5. **Plugin-based Extensibility** - Metadata-driven loading
6. **Concurrency Control** - Lanes for sequential execution
7. **Security Through Layers** - Multiple validation gates
8. **Comprehensive Testing** - 70% coverage + integration tests
9. **Session Persistence** - JSONL append-only logs
10. **Hybrid Search** - Combine multiple search strategies

---

**Technical Analysis by:** LYRA (PERCEIVE)
**Date:** 2026-02-05
**Focus:** Architectural patterns for adoption
