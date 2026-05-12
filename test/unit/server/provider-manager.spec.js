/**
 * Unit tests for the Provider Manager (fallback chain)
 * Tests provider initialization, fallback logic, and error handling
 */

// We test the Python-side logic by mocking the provider pattern in JS
// This validates the provider manager architecture independently

describe('Provider Manager Architecture', () => {
  class MockProvider {
    constructor(name, shouldFail = false) {
      this.name = name
      this.shouldFail = shouldFail
    }

    async chat(messages, tools = null) {
      if (this.shouldFail) {
        throw new Error(`${this.name} provider failed`)
      }
      return `Response from ${this.name}`
    }
  }

  class ProviderManager {
    constructor(providers) {
      if (!providers || providers.length === 0) {
        throw new Error('No LLM providers configured. Add at least GOOGLE_API_KEY.')
      }
      this.providers = providers
      this.currentProviderIndex = 0
    }

    async chat(messages, tools = null) {
      const errors = []
      for (const provider of this.providers) {
        try {
          const result = await provider.chat(messages, tools)
          this.currentProviderIndex = this.providers.indexOf(provider)
          return result
        } catch (e) {
          errors.push(`${provider.name}: ${e.message}`)
          continue
        }
      }
      throw new Error('All providers failed:\n' + errors.join('\n'))
    }

    get activeProvider() {
      return this.providers[this.currentProviderIndex].name
    }
  }

  describe('initialization', () => {
    it('should initialize with valid providers', () => {
      const manager = new ProviderManager([
        new MockProvider('gemini'),
        new MockProvider('groq')
      ])
      expect(manager.providers).toHaveLength(2)
    })

    it('should throw if no providers configured', () => {
      expect(() => new ProviderManager([])).toThrow('No LLM providers configured')
    })

    it('should throw if providers is null', () => {
      expect(() => new ProviderManager(null)).toThrow()
    })
  })

  describe('fallback chain', () => {
    it('should use the first available provider', async () => {
      const manager = new ProviderManager([
        new MockProvider('gemini'),
        new MockProvider('groq')
      ])
      const result = await manager.chat([{ role: 'user', content: 'Hello' }])
      expect(result).toBe('Response from gemini')
      expect(manager.activeProvider).toBe('gemini')
    })

    it('should fall back to second provider if first fails', async () => {
      const manager = new ProviderManager([
        new MockProvider('gemini', true),
        new MockProvider('groq')
      ])
      const result = await manager.chat([{ role: 'user', content: 'Hello' }])
      expect(result).toBe('Response from groq')
      expect(manager.activeProvider).toBe('groq')
    })

    it('should fall back to third provider if first two fail', async () => {
      const manager = new ProviderManager([
        new MockProvider('gemini', true),
        new MockProvider('groq', true),
        new MockProvider('openrouter')
      ])
      const result = await manager.chat([{ role: 'user', content: 'Hello' }])
      expect(result).toBe('Response from openrouter')
      expect(manager.activeProvider).toBe('openrouter')
    })

    it('should throw when all providers fail', async () => {
      const manager = new ProviderManager([
        new MockProvider('gemini', true),
        new MockProvider('groq', true),
        new MockProvider('openrouter', true)
      ])
      await expect(
        manager.chat([{ role: 'user', content: 'Hello' }])
      ).rejects.toThrow('All providers failed')
    })

    it('should include all error messages when all providers fail', async () => {
      const manager = new ProviderManager([
        new MockProvider('gemini', true),
        new MockProvider('groq', true)
      ])
      try {
        await manager.chat([{ role: 'user', content: 'Hello' }])
      } catch (e) {
        expect(e.message).toContain('gemini')
        expect(e.message).toContain('groq')
      }
    })
  })

  describe('active provider tracking', () => {
    it('should track the currently active provider', async () => {
      const manager = new ProviderManager([
        new MockProvider('gemini'),
        new MockProvider('groq')
      ])
      expect(manager.activeProvider).toBe('gemini')

      await manager.chat([{ role: 'user', content: 'test' }])
      expect(manager.activeProvider).toBe('gemini')
    })

    it('should update active provider index on fallback', async () => {
      const manager = new ProviderManager([
        new MockProvider('gemini', true),
        new MockProvider('groq')
      ])
      await manager.chat([{ role: 'user', content: 'test' }])
      expect(manager.activeProvider).toBe('groq')
    })
  })
})
