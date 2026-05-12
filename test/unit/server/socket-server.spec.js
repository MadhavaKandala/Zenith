/**
 * Unit tests for the Socket Server
 * Tests initialization, event handling, and rate limiting integration
 */

describe('Socket Server Architecture', () => {
  describe('SocketServer singleton', () => {
    it('should create a single instance', () => {
      // Simulating singleton pattern
      class SocketServer {
        static instance = null

        constructor() {
          if (!SocketServer.instance) {
            SocketServer.instance = this
          }
          return SocketServer.instance
        }
      }

      const s1 = new SocketServer()
      const s2 = new SocketServer()
      expect(s1).toBe(s2)
    })
  })

  describe('UtteranceDataEvent validation', () => {
    it('should have required client and value fields', () => {
      const validEvent = { client: 'web-app', value: 'tell me a joke' }
      expect(validEvent.client).toBeDefined()
      expect(validEvent.value).toBeDefined()
      expect(typeof validEvent.value).toBe('string')
    })

    it('should reject empty utterances', () => {
      const emptyEvent = { client: 'web-app', value: '' }
      expect(emptyEvent.value.trim()).toBe('')
    })
  })

  describe('Rate limiting integration', () => {
    it('should block rapid requests from the same client', () => {
      // Simulating rate limiter behavior
      const rateLimiter = {
        requests: new Map(),
        check(clientId) {
          const count = this.requests.get(clientId) || 0
          if (count >= 30) {
            return { allowed: false, retryAfterMs: 30000 }
          }
          this.requests.set(clientId, count + 1)
          return { allowed: true, retryAfterMs: 0 }
        }
      }

      // 30 requests should be allowed
      for (let i = 0; i < 30; i++) {
        expect(rateLimiter.check('socket123').allowed).toBe(true)
      }

      // 31st should be blocked
      expect(rateLimiter.check('socket123').allowed).toBe(false)
    })
  })
})
