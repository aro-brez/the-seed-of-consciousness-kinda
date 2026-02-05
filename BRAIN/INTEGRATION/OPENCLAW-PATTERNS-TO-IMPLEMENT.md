# OpenClaw Patterns for 8OWLS Implementation

**Extracted: 2026-02-05**
**Source: /Users/aaronnosbisch/REPOS/seed/COMPETITORS/openclaw/**

This document contains actual code patterns from OpenClaw that we should adapt for 8OWLS.

---

## 1. RETRY AND BACKOFF PATTERNS

### 1.1 Core Retry Logic with Exponential Backoff

**File: `/src/infra/retry.ts`**

```typescript
export type RetryConfig = {
  attempts?: number;
  minDelayMs?: number;
  maxDelayMs?: number;
  jitter?: number;
};

export type RetryOptions = RetryConfig & {
  label?: string;
  shouldRetry?: (err: unknown, attempt: number) => boolean;
  retryAfterMs?: (err: unknown) => number | undefined;
  onRetry?: (info: RetryInfo) => void;
};

const DEFAULT_RETRY_CONFIG = {
  attempts: 3,
  minDelayMs: 300,
  maxDelayMs: 30_000,
  jitter: 0,
};

function applyJitter(delayMs: number, jitter: number): number {
  if (jitter <= 0) return delayMs;
  const offset = (Math.random() * 2 - 1) * jitter;
  return Math.max(0, Math.round(delayMs * (1 + offset)));
}

export async function retryAsync<T>(
  fn: () => Promise<T>,
  attemptsOrOptions: number | RetryOptions = 3,
  initialDelayMs = 300,
): Promise<T> {
  // Simple numeric retry
  if (typeof attemptsOrOptions === "number") {
    const attempts = Math.max(1, Math.round(attemptsOrOptions));
    let lastErr: unknown;
    for (let i = 0; i < attempts; i += 1) {
      try {
        return await fn();
      } catch (err) {
        lastErr = err;
        if (i === attempts - 1) break;
        const delay = initialDelayMs * 2 ** i; // Exponential backoff
        await sleep(delay);
      }
    }
    throw lastErr ?? new Error("Retry failed");
  }

  // Full options retry
  const options = attemptsOrOptions;
  const resolved = resolveRetryConfig(DEFAULT_RETRY_CONFIG, options);
  const maxAttempts = resolved.attempts;
  const shouldRetry = options.shouldRetry ?? (() => true);
  let lastErr: unknown;

  for (let attempt = 1; attempt <= maxAttempts; attempt += 1) {
    try {
      return await fn();
    } catch (err) {
      lastErr = err;
      if (attempt >= maxAttempts || !shouldRetry(err, attempt)) break;

      // Check for retry-after header
      const retryAfterMs = options.retryAfterMs?.(err);
      const hasRetryAfter = typeof retryAfterMs === "number" && Number.isFinite(retryAfterMs);

      // Calculate delay with exponential backoff
      const baseDelay = hasRetryAfter
        ? Math.max(retryAfterMs, resolved.minDelayMs)
        : resolved.minDelayMs * 2 ** (attempt - 1);

      let delay = Math.min(baseDelay, resolved.maxDelayMs);
      delay = applyJitter(delay, resolved.jitter);

      options.onRetry?.({
        attempt,
        maxAttempts,
        delayMs: delay,
        err,
        label: options.label,
      });
      await sleep(delay);
    }
  }
  throw lastErr ?? new Error("Retry failed");
}
```

### 1.2 Backoff Policy Pattern

**File: `/src/infra/backoff.ts`**

```typescript
export type BackoffPolicy = {
  initialMs: number;
  maxMs: number;
  factor: number;
  jitter: number;
};

export function computeBackoff(policy: BackoffPolicy, attempt: number): number {
  const base = policy.initialMs * policy.factor ** Math.max(attempt - 1, 0);
  const jitter = base * policy.jitter * Math.random();
  return Math.min(policy.maxMs, Math.round(base + jitter));
}

export async function sleepWithAbort(ms: number, abortSignal?: AbortSignal) {
  if (ms <= 0) return;
  try {
    await delay(ms, undefined, { signal: abortSignal });
  } catch (err) {
    if (abortSignal?.aborted) {
      throw new Error("aborted", { cause: err });
    }
    throw err;
  }
}
```

### 1.3 Platform-Specific Retry Policies

**File: `/src/infra/retry-policy.ts`**

```typescript
// Discord-specific retry config
export const DISCORD_RETRY_DEFAULTS = {
  attempts: 3,
  minDelayMs: 500,
  maxDelayMs: 30_000,
  jitter: 0.1,
};

// Telegram-specific retry config
export const TELEGRAM_RETRY_DEFAULTS = {
  attempts: 3,
  minDelayMs: 400,
  maxDelayMs: 30_000,
  jitter: 0.1,
};

const TELEGRAM_RETRY_RE = /429|timeout|connect|reset|closed|unavailable|temporarily/i;

function getTelegramRetryAfterMs(err: unknown): number | undefined {
  if (!err || typeof err !== "object") return undefined;
  const candidate =
    "parameters" in err && err.parameters && typeof err.parameters === "object"
      ? (err.parameters as { retry_after?: unknown }).retry_after
      : undefined;
  return typeof candidate === "number" && Number.isFinite(candidate)
    ? candidate * 1000
    : undefined;
}

export function createTelegramRetryRunner(params: {
  retry?: RetryConfig;
  verbose?: boolean;
}): RetryRunner {
  const retryConfig = resolveRetryConfig(TELEGRAM_RETRY_DEFAULTS, params.retry);
  const shouldRetry = (err: unknown) => TELEGRAM_RETRY_RE.test(formatErrorMessage(err));

  return <T>(fn: () => Promise<T>, label?: string) =>
    retryAsync(fn, {
      ...retryConfig,
      label,
      shouldRetry,
      retryAfterMs: getTelegramRetryAfterMs,
      onRetry: params.verbose
        ? (info) => {
            console.warn(
              `telegram retry ${info.attempt}/${info.maxAttempts} in ${info.delayMs}ms: ${formatErrorMessage(info.err)}`,
            );
          }
        : undefined,
    });
}
```

---

## 2. FAILOVER AND MODEL FALLBACK

### 2.1 FailoverError Class

**File: `/src/agents/failover-error.ts`**

```typescript
export type FailoverReason =
  | "billing"
  | "rate_limit"
  | "auth"
  | "timeout"
  | "format"
  | "unknown";

export class FailoverError extends Error {
  readonly reason: FailoverReason;
  readonly provider?: string;
  readonly model?: string;
  readonly profileId?: string;
  readonly status?: number;
  readonly code?: string;

  constructor(
    message: string,
    params: {
      reason: FailoverReason;
      provider?: string;
      model?: string;
      profileId?: string;
      status?: number;
      code?: string;
      cause?: unknown;
    },
  ) {
    super(message, { cause: params.cause });
    this.name = "FailoverError";
    this.reason = params.reason;
    this.provider = params.provider;
    this.model = params.model;
    this.profileId = params.profileId;
    this.status = params.status;
    this.code = params.code;
  }
}

export function resolveFailoverReasonFromError(err: unknown): FailoverReason | null {
  if (isFailoverError(err)) return err.reason;

  const status = getStatusCode(err);
  if (status === 402) return "billing";
  if (status === 429) return "rate_limit";
  if (status === 401 || status === 403) return "auth";
  if (status === 408) return "timeout";

  const code = (getErrorCode(err) ?? "").toUpperCase();
  if (["ETIMEDOUT", "ESOCKETTIMEDOUT", "ECONNRESET", "ECONNABORTED"].includes(code)) {
    return "timeout";
  }
  if (isTimeoutError(err)) return "timeout";

  return classifyFailoverReason(getErrorMessage(err));
}
```

### 2.2 Model Fallback Pattern

**File: `/src/agents/model-fallback.ts`**

```typescript
export async function runWithModelFallback<T>(params: {
  cfg: OpenClawConfig | undefined;
  provider: string;
  model: string;
  fallbacksOverride?: string[];
  run: (provider: string, model: string) => Promise<T>;
  onError?: (attempt: { provider: string; model: string; error: unknown }) => void;
}): Promise<{
  result: T;
  provider: string;
  model: string;
  attempts: FallbackAttempt[];
}> {
  const candidates = resolveFallbackCandidates({
    cfg: params.cfg,
    provider: params.provider,
    model: params.model,
    fallbacksOverride: params.fallbacksOverride,
  });

  const attempts: FallbackAttempt[] = [];
  let lastError: unknown;

  for (let i = 0; i < candidates.length; i += 1) {
    const candidate = candidates[i];

    // Check if all profiles for this provider are in cooldown
    if (authStore) {
      const profileIds = resolveAuthProfileOrder({ cfg: params.cfg, store: authStore, provider: candidate.provider });
      const isAnyProfileAvailable = profileIds.some((id) => !isProfileInCooldown(authStore, id));

      if (profileIds.length > 0 && !isAnyProfileAvailable) {
        attempts.push({
          provider: candidate.provider,
          model: candidate.model,
          error: `Provider ${candidate.provider} is in cooldown`,
          reason: "rate_limit",
        });
        continue;
      }
    }

    try {
      const result = await params.run(candidate.provider, candidate.model);
      return { result, provider: candidate.provider, model: candidate.model, attempts };
    } catch (err) {
      if (shouldRethrowAbort(err)) throw err;

      const normalized = coerceToFailoverError(err, { provider: candidate.provider, model: candidate.model });
      if (!isFailoverError(normalized)) throw err;

      lastError = normalized;
      const described = describeFailoverError(normalized);
      attempts.push({
        provider: candidate.provider,
        model: candidate.model,
        error: described.message,
        reason: described.reason,
        status: described.status,
      });
      await params.onError?.({ provider: candidate.provider, model: candidate.model, error: normalized });
    }
  }

  throw new Error(`All models failed (${attempts.length}): ${formatAttempts(attempts)}`, {
    cause: lastError instanceof Error ? lastError : undefined,
  });
}
```

---

## 3. COOLDOWN AND RATE LIMIT TRACKING

### 3.1 Auth Profile Cooldown System

**File: `/src/agents/auth-profiles/usage.ts`**

```typescript
// Check if profile is in cooldown
export function isProfileInCooldown(store: AuthProfileStore, profileId: string): boolean {
  const stats = store.usageStats?.[profileId];
  if (!stats) return false;
  const unusableUntil = resolveProfileUnusableUntil(stats);
  return unusableUntil ? Date.now() < unusableUntil : false;
}

// Exponential cooldown calculation: 1min, 5min, 25min, max 1 hour
export function calculateAuthProfileCooldownMs(errorCount: number): number {
  const normalized = Math.max(1, errorCount);
  return Math.min(
    60 * 60 * 1000, // 1 hour max
    60 * 1000 * 5 ** Math.min(normalized - 1, 3),
  );
}

// Mark profile as successfully used - reset cooldown
export async function markAuthProfileUsed(params: {
  store: AuthProfileStore;
  profileId: string;
}): Promise<void> {
  await updateAuthProfileStoreWithLock({
    updater: (freshStore) => {
      if (!freshStore.profiles[profileId]) return false;
      freshStore.usageStats = freshStore.usageStats ?? {};
      freshStore.usageStats[profileId] = {
        ...freshStore.usageStats[profileId],
        lastUsed: Date.now(),
        errorCount: 0,
        cooldownUntil: undefined,
        disabledUntil: undefined,
        disabledReason: undefined,
        failureCounts: undefined,
      };
      return true;
    },
  });
}

// Mark profile failure with exponential backoff
export async function markAuthProfileFailure(params: {
  store: AuthProfileStore;
  profileId: string;
  reason: AuthProfileFailureReason;
}): Promise<void> {
  await updateAuthProfileStoreWithLock({
    updater: (freshStore) => {
      const profile = freshStore.profiles[profileId];
      if (!profile) return false;

      freshStore.usageStats = freshStore.usageStats ?? {};
      const existing = freshStore.usageStats[profileId] ?? {};

      const windowMs = 24 * 60 * 60 * 1000; // 24 hour failure window
      const windowExpired = existing.lastFailureAt && Date.now() - existing.lastFailureAt > windowMs;

      const baseErrorCount = windowExpired ? 0 : (existing.errorCount ?? 0);
      const nextErrorCount = baseErrorCount + 1;

      if (reason === "billing") {
        // Billing errors get longer backoff: 5h base, 24h max
        const billingBackoffMs = calculateBillingDisableMs(nextErrorCount);
        freshStore.usageStats[profileId] = {
          ...existing,
          errorCount: nextErrorCount,
          lastFailureAt: Date.now(),
          disabledUntil: Date.now() + billingBackoffMs,
          disabledReason: "billing",
        };
      } else {
        // Regular errors use shorter cooldown
        const backoffMs = calculateAuthProfileCooldownMs(nextErrorCount);
        freshStore.usageStats[profileId] = {
          ...existing,
          errorCount: nextErrorCount,
          lastFailureAt: Date.now(),
          cooldownUntil: Date.now() + backoffMs,
        };
      }
      return true;
    },
  });
}
```

---

## 4. SSE RECONNECT LOOP (Self-Healing Connections)

### 4.1 Signal SSE Reconnect

**File: `/src/signal/sse-reconnect.ts`**

```typescript
const DEFAULT_RECONNECT_POLICY: BackoffPolicy = {
  initialMs: 1_000,
  maxMs: 10_000,
  factor: 2,
  jitter: 0.2,
};

export async function runSignalSseLoop({
  baseUrl,
  abortSignal,
  runtime,
  onEvent,
  policy,
}: RunSignalSseLoopParams) {
  const reconnectPolicy = { ...DEFAULT_RECONNECT_POLICY, ...policy };
  let reconnectAttempts = 0;

  while (!abortSignal?.aborted) {
    try {
      await streamSignalEvents({
        baseUrl,
        abortSignal,
        onEvent: (event) => {
          reconnectAttempts = 0; // Reset on successful event
          onEvent(event);
        },
      });

      if (abortSignal?.aborted) return;

      reconnectAttempts += 1;
      const delayMs = computeBackoff(reconnectPolicy, reconnectAttempts);
      await sleepWithAbort(delayMs, abortSignal);
    } catch (err) {
      if (abortSignal?.aborted) return;

      runtime.error?.(`Signal SSE stream error: ${String(err)}`);
      reconnectAttempts += 1;
      const delayMs = computeBackoff(reconnectPolicy, reconnectAttempts);
      runtime.log?.(`Connection lost, reconnecting in ${delayMs / 1000}s...`);

      try {
        await sleepWithAbort(delayMs, abortSignal);
      } catch (sleepErr) {
        if (abortSignal?.aborted) return;
        throw sleepErr;
      }
    }
  }
}
```

### 4.2 Web Reconnect Policy

**File: `/src/web/reconnect.ts`**

```typescript
export type ReconnectPolicy = BackoffPolicy & {
  maxAttempts: number;
};

export const DEFAULT_HEARTBEAT_SECONDS = 60;
export const DEFAULT_RECONNECT_POLICY: ReconnectPolicy = {
  initialMs: 2_000,
  maxMs: 30_000,
  factor: 1.8,
  jitter: 0.25,
  maxAttempts: 12,
};

export function resolveReconnectPolicy(
  cfg: OpenClawConfig,
  overrides?: Partial<ReconnectPolicy>,
): ReconnectPolicy {
  const merged = { ...DEFAULT_RECONNECT_POLICY, ...cfg.web?.reconnect, ...overrides };

  merged.initialMs = Math.max(250, merged.initialMs);
  merged.maxMs = Math.max(merged.initialMs, merged.maxMs);
  merged.factor = Math.min(Math.max(1.1, merged.factor), 10);
  merged.jitter = Math.min(Math.max(0, merged.jitter), 1);
  merged.maxAttempts = Math.max(0, Math.floor(merged.maxAttempts));

  return merged;
}
```

---

## 5. TELEGRAM MONITORING WITH SELF-HEALING

### 5.1 Telegram Monitor with Auto-Recovery

**File: `/src/telegram/monitor.ts`**

```typescript
const TELEGRAM_POLL_RESTART_POLICY = {
  initialMs: 2000,
  maxMs: 30_000,
  factor: 1.8,
  jitter: 0.25,
};

const isGetUpdatesConflict = (err: unknown) => {
  const errorCode = (err as any)?.error_code ?? (err as any)?.errorCode;
  if (errorCode !== 409) return false;
  const haystack = [(err as any)?.method, (err as any)?.description, (err as any)?.message]
    .filter(Boolean)
    .join(" ")
    .toLowerCase();
  return haystack.includes("getupdates");
};

export async function monitorTelegramProvider(opts: MonitorTelegramOpts = {}) {
  const log = opts.runtime?.error ?? console.error;

  // Register handler for unhandled rejections (network errors)
  const unregisterHandler = registerUnhandledRejectionHandler((err) => {
    if (isGrammyHttpError(err) && isRecoverableTelegramNetworkError(err)) {
      log(`[telegram] Suppressed network error: ${formatErrorMessage(err)}`);
      return true; // handled - don't crash
    }
    return false;
  });

  try {
    let restartAttempts = 0;

    while (!opts.abortSignal?.aborted) {
      const runner = run(bot, createTelegramRunnerOptions(cfg));
      const stopOnAbort = () => { if (opts.abortSignal?.aborted) runner.stop(); };
      opts.abortSignal?.addEventListener("abort", stopOnAbort, { once: true });

      try {
        await runner.task();
        return;
      } catch (err) {
        if (opts.abortSignal?.aborted) throw err;

        const isConflict = isGetUpdatesConflict(err);
        const isRecoverable = isRecoverableTelegramNetworkError(err, { context: "polling" });

        if (!isConflict && !isRecoverable) throw err;

        restartAttempts += 1;
        const delayMs = computeBackoff(TELEGRAM_POLL_RESTART_POLICY, restartAttempts);
        const reason = isConflict ? "getUpdates conflict" : "network error";

        log(`Telegram ${reason}: ${formatErrorMessage(err)}; retrying in ${formatDurationMs(delayMs)}.`);

        try {
          await sleepWithAbort(delayMs, opts.abortSignal);
        } catch (sleepErr) {
          if (opts.abortSignal?.aborted) return;
          throw sleepErr;
        }
      } finally {
        opts.abortSignal?.removeEventListener("abort", stopOnAbort);
      }
    }
  } finally {
    unregisterHandler();
  }
}
```

---

## 6. DISCORD GATEWAY WITH HELLO TIMEOUT DETECTION

### 6.1 Discord Zombie Connection Detection

**File: `/src/discord/monitor/provider.ts`**

```typescript
// Timeout to detect zombie connections where HELLO is never received
const HELLO_TIMEOUT_MS = 30000;
let helloTimeoutId: ReturnType<typeof setTimeout> | undefined;

const onGatewayDebug = (msg: unknown) => {
  const message = String(msg);
  if (!message.includes("WebSocket connection opened")) return;

  if (helloTimeoutId) clearTimeout(helloTimeoutId);

  helloTimeoutId = setTimeout(() => {
    if (!gateway?.isConnected) {
      runtime.log?.(
        `connection stalled: no HELLO received within ${HELLO_TIMEOUT_MS}ms, forcing reconnect`,
      );
      gateway?.disconnect();
      gateway?.connect(false);
    }
    helloTimeoutId = undefined;
  }, HELLO_TIMEOUT_MS);
};

gatewayEmitter?.on("debug", onGatewayDebug);

// Set maxAttempts to infinity for automatic reconnection
const client = new Client(
  { /* config */ },
  { commands, listeners: [], components },
  [new GatewayPlugin({
    reconnect: { maxAttempts: Number.POSITIVE_INFINITY },
    intents: resolveDiscordGatewayIntents(discordCfg.intents),
    autoInteractions: true,
  })],
);

// Clean abort handling
const onAbort = () => {
  if (!gateway) return;
  gatewayEmitter?.once("error", () => {}); // Prevent unhandled error
  gateway.options.reconnect = { maxAttempts: 0 };
  gateway.disconnect();
};
```

---

## 7. MEMORY MANAGEMENT WITH VECTOR SEARCH

### 7.1 Memory Index Manager

**File: `/src/memory/manager.ts`**

```typescript
const EMBEDDING_RETRY_MAX_ATTEMPTS = 3;
const EMBEDDING_RETRY_BASE_DELAY_MS = 500;
const EMBEDDING_RETRY_MAX_DELAY_MS = 8000;

private async embedBatchWithRetry(texts: string[]): Promise<number[][]> {
  if (texts.length === 0) return [];

  let attempt = 0;
  let delayMs = EMBEDDING_RETRY_BASE_DELAY_MS;

  while (true) {
    try {
      const timeoutMs = this.resolveEmbeddingTimeout("batch");
      return await this.withTimeout(
        this.provider.embedBatch(texts),
        timeoutMs,
        `embeddings batch timed out after ${Math.round(timeoutMs / 1000)}s`,
      );
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      if (!this.isRetryableEmbeddingError(message) || attempt >= EMBEDDING_RETRY_MAX_ATTEMPTS) {
        throw err;
      }

      const waitMs = Math.min(
        EMBEDDING_RETRY_MAX_DELAY_MS,
        Math.round(delayMs * (1 + Math.random() * 0.2)),
      );
      console.warn(`embeddings rate limited; retrying in ${waitMs}ms`);

      await new Promise((resolve) => setTimeout(resolve, waitMs));
      delayMs *= 2;
      attempt += 1;
    }
  }
}

private isRetryableEmbeddingError(message: string): boolean {
  return /(rate[_ ]limit|too many requests|429|resource has been exhausted|5\d\d|cloudflare)/i.test(message);
}

// Fallback provider activation on embedding failures
private async activateFallbackProvider(reason: string): Promise<boolean> {
  const fallback = this.settings.fallback;
  if (!fallback || fallback === "none" || fallback === this.provider.id) return false;
  if (this.fallbackFrom) return false; // Already in fallback mode

  this.fallbackFrom = this.provider.id;
  this.fallbackReason = reason;
  this.provider = await createEmbeddingProvider({ provider: fallback });

  console.warn(`memory embeddings: switched to fallback provider (${fallback})`, { reason });
  return true;
}
```

### 7.2 Batch Failure Handling with Circuit Breaker Pattern

```typescript
const BATCH_FAILURE_LIMIT = 2;

private async recordBatchFailure(params: {
  provider: string;
  message: string;
  forceDisable?: boolean;
}): Promise<{ disabled: boolean; count: number }> {
  return await this.withBatchFailureLock(async () => {
    if (!this.batch.enabled) return { disabled: true, count: this.batchFailureCount };

    const increment = params.forceDisable ? BATCH_FAILURE_LIMIT : 1;
    this.batchFailureCount += increment;
    this.batchFailureLastError = params.message;
    this.batchFailureLastProvider = params.provider;

    const disabled = params.forceDisable || this.batchFailureCount >= BATCH_FAILURE_LIMIT;
    if (disabled) this.batch.enabled = false;

    return { disabled, count: this.batchFailureCount };
  });
}

private async runBatchWithFallback<T>(params: {
  provider: string;
  run: () => Promise<T>;
  fallback: () => Promise<number[][]>;
}): Promise<T | number[][]> {
  if (!this.batch.enabled) return await params.fallback();

  try {
    const result = await this.runBatchWithTimeoutRetry(params);
    await this.resetBatchFailureCount();
    return result;
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err);
    const forceDisable = /asyncBatchEmbedContent not available/i.test(message);
    const failure = await this.recordBatchFailure({ provider: params.provider, message, forceDisable });

    const suffix = failure.disabled ? "disabling batch" : "keeping batch enabled";
    console.warn(`batch failed (${failure.count}/${BATCH_FAILURE_LIMIT}); ${suffix}; falling back`);

    return await params.fallback();
  }
}
```

---

## 8. CONTEXT COMPACTION (Summarization)

### 8.1 Adaptive Chunk Ratio

**File: `/src/agents/compaction.ts`**

```typescript
export const BASE_CHUNK_RATIO = 0.4;
export const MIN_CHUNK_RATIO = 0.15;
export const SAFETY_MARGIN = 1.2; // 20% buffer for estimation inaccuracy

export function computeAdaptiveChunkRatio(messages: AgentMessage[], contextWindow: number): number {
  if (messages.length === 0) return BASE_CHUNK_RATIO;

  const totalTokens = estimateMessagesTokens(messages);
  const avgTokens = totalTokens / messages.length;
  const safeAvgTokens = avgTokens * SAFETY_MARGIN;
  const avgRatio = safeAvgTokens / contextWindow;

  // If average message is > 10% of context, reduce chunk ratio
  if (avgRatio > 0.1) {
    const reduction = Math.min(avgRatio * 2, BASE_CHUNK_RATIO - MIN_CHUNK_RATIO);
    return Math.max(MIN_CHUNK_RATIO, BASE_CHUNK_RATIO - reduction);
  }

  return BASE_CHUNK_RATIO;
}

// Check if message is too large to summarize (> 50% of context)
export function isOversizedForSummary(msg: AgentMessage, contextWindow: number): boolean {
  const tokens = estimateTokens(msg) * SAFETY_MARGIN;
  return tokens > contextWindow * 0.5;
}
```

### 8.2 Progressive Summarization with Fallback

```typescript
export async function summarizeWithFallback(params: {
  messages: AgentMessage[];
  contextWindow: number;
  maxChunkTokens: number;
}): Promise<string> {
  const { messages, contextWindow } = params;
  if (messages.length === 0) return params.previousSummary ?? "No prior history.";

  // Try full summarization first
  try {
    return await summarizeChunks(params);
  } catch (fullError) {
    console.warn(`Full summarization failed, trying partial: ${fullError}`);
  }

  // Fallback 1: Summarize only small messages
  const smallMessages: AgentMessage[] = [];
  const oversizedNotes: string[] = [];

  for (const msg of messages) {
    if (isOversizedForSummary(msg, contextWindow)) {
      const role = msg.role ?? "message";
      const tokens = estimateTokens(msg);
      oversizedNotes.push(`[Large ${role} (~${Math.round(tokens / 1000)}K tokens) omitted]`);
    } else {
      smallMessages.push(msg);
    }
  }

  if (smallMessages.length > 0) {
    try {
      const partialSummary = await summarizeChunks({ ...params, messages: smallMessages });
      const notes = oversizedNotes.length > 0 ? `\n\n${oversizedNotes.join("\n")}` : "";
      return partialSummary + notes;
    } catch (partialError) {
      console.warn(`Partial summarization also failed: ${partialError}`);
    }
  }

  // Final fallback: Just note what was there
  return `Context contained ${messages.length} messages (${oversizedNotes.length} oversized). Summary unavailable.`;
}
```

---

## 9. VOICE WAKE WORD SYSTEM (Swift)

### 9.1 Wake Word Gate

**File: `/Swabble/Sources/SwabbleKit/WakeWordGate.swift`**

```swift
public struct WakeWordGateConfig: Sendable, Equatable {
    public var triggers: [String]          // e.g., ["hey owl", "owl"]
    public var minPostTriggerGap: TimeInterval // 0.45 seconds default
    public var minCommandLength: Int       // 1 char minimum
}

public enum WakeWordGate {
    public static func match(
        transcript: String,
        segments: [WakeWordSegment],
        config: WakeWordGateConfig
    ) -> WakeWordGateMatch? {
        let triggerTokens = normalizeTriggers(config.triggers)
        guard !triggerTokens.isEmpty else { return nil }

        let tokens = normalizeSegments(segments)
        guard !tokens.isEmpty else { return nil }

        var best: MatchCandidate?

        for trigger in triggerTokens {
            let count = trigger.tokens.count
            guard count > 0, tokens.count > count else { continue }

            for i in 0...(tokens.count - count - 1) {
                let matched = (0..<count).allSatisfy {
                    tokens[i + $0].normalized == trigger.tokens[$0]
                }
                if !matched { continue }

                let triggerEnd = tokens[i + count - 1].end
                let nextToken = tokens[i + count]
                let gap = nextToken.start - triggerEnd

                // Require minimum gap after trigger word
                if gap < config.minPostTriggerGap { continue }
                if let best, i <= best.index { continue }

                best = MatchCandidate(index: i, triggerEnd: triggerEnd, gap: gap)
            }
        }

        guard let best else { return nil }
        let command = commandText(transcript: transcript, segments: segments, triggerEndTime: best.triggerEnd)
            .trimmingCharacters(in: whitespaceAndPunctuation)

        guard command.count >= config.minCommandLength else { return nil }
        return WakeWordGateMatch(triggerEndTime: best.triggerEnd, postGap: best.gap, command: command)
    }

    public static func stripWake(text: String, triggers: [String]) -> String {
        var out = text
        for trigger in triggers {
            let token = trigger.trimmingCharacters(in: whitespaceAndPunctuation)
            guard !token.isEmpty else { continue }
            out = out.replacingOccurrences(of: token, with: "", options: [.caseInsensitive])
        }
        return out.trimmingCharacters(in: whitespaceAndPunctuation)
    }
}
```

### 9.2 Speech Pipeline (Actor-based)

**File: `/Swabble/Sources/SwabbleCore/Speech/SpeechPipeline.swift`**

```swift
@available(macOS 26.0, iOS 26.0, *)
public actor SpeechPipeline {
    private var engine = AVAudioEngine()
    private var transcriber: SpeechTranscriber?
    private var analyzer: SpeechAnalyzer?

    public func start(localeIdentifier: String, etiquette: Bool) async throws -> AsyncStream<SpeechSegment> {
        let auth = await requestAuthorizationIfNeeded()
        guard auth == .authorized else { throw SpeechPipelineError.authorizationDenied }

        let transcriberModule = SpeechTranscriber(
            locale: Locale(identifier: localeIdentifier),
            transcriptionOptions: etiquette ? [.etiquetteReplacements] : [],
            reportingOptions: [.volatileResults]
        )
        transcriber = transcriberModule

        guard let analyzerFormat = await SpeechAnalyzer.bestAvailableAudioFormat(compatibleWith: [transcriberModule])
        else { throw SpeechPipelineError.analyzerFormatUnavailable }

        analyzer = SpeechAnalyzer(modules: [transcriberModule])
        let (stream, continuation) = AsyncStream<AnalyzerInput>.makeStream()

        let inputNode = engine.inputNode
        inputNode.installTap(onBus: 0, bufferSize: 2048, format: inputNode.outputFormat(forBus: 0)) { [weak self] buffer, _ in
            Task { await self?.handleBuffer(buffer, targetFormat: analyzerFormat) }
        }

        engine.prepare()
        try engine.start()
        try await analyzer?.start(inputSequence: stream)

        return AsyncStream { continuation in
            self.resultTask = Task {
                for try await result in transcriberForStream.results {
                    continuation.yield(SpeechSegment(text: String(result.text.characters), isFinal: result.isFinal))
                }
                continuation.finish()
            }
            continuation.onTermination = { _ in Task { await self.stop() } }
        }
    }

    public func stop() async {
        resultTask?.cancel()
        inputContinuation?.finish()
        engine.inputNode.removeTap(onBus: 0)
        engine.stop()
        try? await analyzer?.finalizeAndFinishThroughEndOfInput()
    }
}
```

---

## 10. PLUGIN/SKILL SYSTEM

### 10.1 Plugin Loader

**File: `/src/plugins/loader.ts`**

```typescript
export function loadOpenClawPlugins(options: PluginLoadOptions = {}): PluginRegistry {
  const cfg = options.config ?? {};
  const normalized = normalizePluginsConfig(cfg.plugins);
  const cacheKey = buildCacheKey({ workspaceDir: options.workspaceDir, plugins: normalized });

  // Cache check
  if (cacheEnabled && registryCache.has(cacheKey)) {
    return registryCache.get(cacheKey)!;
  }

  const runtime = createPluginRuntime();
  const { registry, createApi } = createPluginRegistry({ logger, runtime });

  const discovery = discoverOpenClawPlugins({
    workspaceDir: options.workspaceDir,
    extraPaths: normalized.loadPaths,
  });

  const jiti = createJiti(import.meta.url, {
    interopDefault: true,
    extensions: [".ts", ".tsx", ".js", ".mjs", ".json"],
    alias: { "openclaw/plugin-sdk": pluginSdkAlias },
  });

  for (const candidate of discovery.candidates) {
    const enableState = resolveEnableState(pluginId, candidate.origin, normalized);

    if (!enableState.enabled) {
      record.status = "disabled";
      record.error = enableState.reason;
      continue;
    }

    // Validate config schema
    const validatedConfig = validatePluginConfig({
      schema: manifestRecord.configSchema,
      value: entry?.config,
    });

    if (!validatedConfig.ok) {
      record.status = "error";
      record.error = `invalid config: ${validatedConfig.errors?.join(", ")}`;
      continue;
    }

    // Load and register plugin
    try {
      const mod = jiti(candidate.source);
      const resolved = resolvePluginModuleExport(mod);
      const api = createApi(record, { config: cfg, pluginConfig: validatedConfig.value });
      resolved.register(api);
      registry.plugins.push(record);
    } catch (err) {
      record.status = "error";
      record.error = String(err);
    }
  }

  registryCache.set(cacheKey, registry);
  return registry;
}
```

### 10.2 Skill Definition Format

**File: `/skills/discord/SKILL.md` (YAML frontmatter)**

```yaml
---
name: discord
description: Use when you need to control Discord from OpenClaw via the discord tool...
metadata: {"openclaw":{"emoji":"","requires":{"config":["channels.discord"]}}}
---

# Discord Actions

## Overview
Use `discord` to manage messages, reactions, threads, polls, and moderation.

## Actions

### React to a message
```json
{
  "action": "react",
  "channelId": "123",
  "messageId": "456",
  "emoji": ""
}
```
```

---

## 11. IMPLEMENTATION PRIORITY FOR 8OWLS

### High Priority (Core Infrastructure)
1. **Retry/Backoff System** - Copy `retry.ts` and `backoff.ts` patterns exactly
2. **Cooldown Tracking** - Implement `auth-profiles/usage.ts` pattern for NATS/API rate limits
3. **Model Fallback** - Adapt `model-fallback.ts` for Claude/OpenAI failover
4. **SSE Reconnect Loop** - Use `sse-reconnect.ts` for NATS connection resilience

### Medium Priority (Channel Integration)
5. **Telegram Monitor** - Adapt self-healing polling loop
6. **Discord Gateway** - Implement HELLO timeout detection
7. **Slack Retry** - Simple `WebClient` retry config

### Lower Priority (Enhancements)
8. **Memory Compaction** - Adapt context summarization for owl sessions
9. **Voice Wake** - Implement wake word detection for voice interface
10. **Skill System** - Create skill/plugin loader for owl capabilities

---

## 12. QUICK-START IMPLEMENTATION

### Create `/tools/lib/retry.ts`:

```typescript
// Copy directly from OpenClaw patterns above
export * from './retry-core';
export * from './backoff';
export * from './cooldown-tracker';
```

### Create `/tools/lib/self-healing.ts`:

```typescript
import { computeBackoff, sleepWithAbort, BackoffPolicy } from './retry';

const DEFAULT_RECONNECT_POLICY: BackoffPolicy = {
  initialMs: 1_000,
  maxMs: 30_000,
  factor: 2,
  jitter: 0.2,
};

export async function withReconnect<T>(
  connect: () => Promise<T>,
  options: {
    policy?: Partial<BackoffPolicy>;
    abortSignal?: AbortSignal;
    onReconnect?: (attempt: number, delayMs: number, error: unknown) => void;
  } = {}
): Promise<T> {
  const policy = { ...DEFAULT_RECONNECT_POLICY, ...options.policy };
  let attempts = 0;

  while (!options.abortSignal?.aborted) {
    try {
      return await connect();
    } catch (err) {
      if (options.abortSignal?.aborted) throw err;

      attempts += 1;
      const delayMs = computeBackoff(policy, attempts);
      options.onReconnect?.(attempts, delayMs, err);

      await sleepWithAbort(delayMs, options.abortSignal);
    }
  }

  throw new Error('Aborted');
}
```

---

**END OF EXTRACTION DOCUMENT**
