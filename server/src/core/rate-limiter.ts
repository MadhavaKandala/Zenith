/**
 * Rate Limiter for Socket Server
 *
 * Prevents abuse by limiting the number of utterances a client can send
 * within a given time window. Uses a sliding window counter algorithm.
 */

interface RateLimitEntry {
  timestamps: number[]
  blocked: boolean
}

export class RateLimiter {
  private clients: Map<string, RateLimitEntry> = new Map()
  private readonly maxRequests: number
  private readonly windowMs: number
  private readonly blockDurationMs: number

  /**
   * Create a new rate limiter.
   *
   * @param maxRequests - Maximum requests allowed per window (default: 30)
   * @param windowMs - Time window in milliseconds (default: 60000 = 1 min)
   * @param blockDurationMs - Block duration after limit exceeded (default: 30000 = 30s)
   */
  constructor(
    maxRequests: number = 30,
    windowMs: number = 60_000,
    blockDurationMs: number = 30_000
  ) {
    this.maxRequests = maxRequests
    this.windowMs = windowMs
    this.blockDurationMs = blockDurationMs

    // Clean up stale entries every 5 minutes
    setInterval(() => this.cleanup(), 5 * 60_000)
  }

  /**
   * Check if a request from the given client ID is allowed.
   *
   * @param clientId - Unique client identifier (socket ID)
   * @returns Object with `allowed` boolean and `retryAfterMs` if blocked
   */
  public check(clientId: string): { allowed: boolean; retryAfterMs: number } {
    const now = Date.now()
    let entry = this.clients.get(clientId)

    if (!entry) {
      entry = { timestamps: [], blocked: false }
      this.clients.set(clientId, entry)
    }

    // Check if client is currently blocked
    if (entry.blocked) {
      const lastTimestamp = entry.timestamps[entry.timestamps.length - 1] || 0
      const blockExpiry = lastTimestamp + this.blockDurationMs

      if (now < blockExpiry) {
        return { allowed: false, retryAfterMs: blockExpiry - now }
      }

      // Block expired, reset
      entry.blocked = false
      entry.timestamps = []
    }

    // Remove timestamps outside the current window
    entry.timestamps = entry.timestamps.filter(
      (ts) => now - ts < this.windowMs
    )

    // Check if limit exceeded
    if (entry.timestamps.length >= this.maxRequests) {
      entry.blocked = true
      return { allowed: false, retryAfterMs: this.blockDurationMs }
    }

    // Allow the request
    entry.timestamps.push(now)
    return { allowed: true, retryAfterMs: 0 }
  }

  /**
   * Get the current request count for a client.
   */
  public getRequestCount(clientId: string): number {
    const entry = this.clients.get(clientId)
    if (!entry) return 0

    const now = Date.now()
    return entry.timestamps.filter((ts) => now - ts < this.windowMs).length
  }

  /**
   * Reset rate limit for a specific client.
   */
  public reset(clientId: string): void {
    this.clients.delete(clientId)
  }

  /**
   * Remove stale client entries that haven't been active recently.
   */
  private cleanup(): void {
    const now = Date.now()
    const staleThreshold = this.windowMs * 2

    for (const [clientId, entry] of this.clients.entries()) {
      const lastActivity = Math.max(...entry.timestamps, 0)
      if (now - lastActivity > staleThreshold) {
        this.clients.delete(clientId)
      }
    }
  }
}
