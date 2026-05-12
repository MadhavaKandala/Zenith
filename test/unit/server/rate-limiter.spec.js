/**
 * Unit tests for the Rate Limiter
 * Tests sliding window algorithm, blocking, and cleanup
 */

const { RateLimiter } = require('../../server/src/core/rate-limiter')

describe('RateLimiter', () => {
  let limiter

  beforeEach(() => {
    limiter = new RateLimiter(5, 1000, 500) // 5 requests per second, 500ms block
  })

  describe('basic rate limiting', () => {
    it('should allow requests under the limit', () => {
      const result = limiter.check('client1')
      expect(result.allowed).toBe(true)
      expect(result.retryAfterMs).toBe(0)
    })

    it('should track request count correctly', () => {
      limiter.check('client1')
      limiter.check('client1')
      limiter.check('client1')
      expect(limiter.getRequestCount('client1')).toBe(3)
    })

    it('should block after exceeding the limit', () => {
      for (let i = 0; i < 5; i++) {
        const result = limiter.check('client1')
        expect(result.allowed).toBe(true)
      }
      const blocked = limiter.check('client1')
      expect(blocked.allowed).toBe(false)
      expect(blocked.retryAfterMs).toBeGreaterThan(0)
    })

    it('should not affect other clients', () => {
      for (let i = 0; i < 5; i++) {
        limiter.check('client1')
      }
      limiter.check('client1') // This blocks client1

      const result = limiter.check('client2')
      expect(result.allowed).toBe(true)
    })
  })

  describe('reset', () => {
    it('should reset a specific client', () => {
      for (let i = 0; i < 5; i++) {
        limiter.check('client1')
      }
      limiter.check('client1') // Block

      limiter.reset('client1')
      const result = limiter.check('client1')
      expect(result.allowed).toBe(true)
    })

    it('should return 0 count for unknown clients', () => {
      expect(limiter.getRequestCount('unknown')).toBe(0)
    })
  })
})
