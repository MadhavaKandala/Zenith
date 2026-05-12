/**
 * Unit tests for the YAML Configuration Loader
 * Tests config loading, environment variable resolution, and schema validation
 */

describe('Config Loader', () => {
  describe('Environment Variable Resolution', () => {
    const ENV_PATTERN = /^\$\{([A-Z0-9_]+)\}$/

    function resolveEnv(value, envVars = {}) {
      if (typeof value === 'object' && value !== null && !Array.isArray(value)) {
        return Object.fromEntries(
          Object.entries(value).map(([k, v]) => [k, resolveEnv(v, envVars)])
        )
      }
      if (Array.isArray(value)) {
        return value.map(item => resolveEnv(item, envVars))
      }
      if (typeof value === 'string') {
        const match = value.trim().match(ENV_PATTERN)
        if (match) {
          return envVars[match[1]] || ''
        }
      }
      return value
    }

    it('should resolve simple environment variables', () => {
      const result = resolveEnv('${GOOGLE_API_KEY}', {
        GOOGLE_API_KEY: 'test-key-123'
      })
      expect(result).toBe('test-key-123')
    })

    it('should resolve nested object values', () => {
      const config = {
        llm: {
          gemini: { api_key: '${GOOGLE_API_KEY}' },
          groq: { api_key: '${GROQ_API_KEY}' }
        }
      }
      const result = resolveEnv(config, {
        GOOGLE_API_KEY: 'google-key',
        GROQ_API_KEY: 'groq-key'
      })
      expect(result.llm.gemini.api_key).toBe('google-key')
      expect(result.llm.groq.api_key).toBe('groq-key')
    })

    it('should resolve array values', () => {
      const config = { fallback: ['${PROVIDER_1}', '${PROVIDER_2}'] }
      const result = resolveEnv(config, {
        PROVIDER_1: 'groq',
        PROVIDER_2: 'openrouter'
      })
      expect(result.fallback).toEqual(['groq', 'openrouter'])
    })

    it('should return empty string for unset env vars', () => {
      const result = resolveEnv('${UNDEFINED_VAR}', {})
      expect(result).toBe('')
    })

    it('should not modify non-env-var strings', () => {
      const result = resolveEnv('plain-string', {})
      expect(result).toBe('plain-string')
    })

    it('should not modify numbers', () => {
      const result = resolveEnv(1337)
      expect(result).toBe(1337)
    })

    it('should not modify booleans', () => {
      const result = resolveEnv(true)
      expect(result).toBe(true)
    })

    it('should not modify null', () => {
      const result = resolveEnv(null)
      expect(result).toBeNull()
    })
  })

  describe('Config Schema Validation', () => {
    const REQUIRED_SECTIONS = ['server', 'voice', 'llm', 'personality', 'skills', 'memory', 'ui']

    function validateConfig(config) {
      const errors = []
      for (const section of REQUIRED_SECTIONS) {
        if (!config[section]) {
          errors.push(`Missing required section: ${section}`)
        }
      }
      if (config.server && !config.server.port) {
        errors.push('Missing server.port')
      }
      if (config.llm && !config.llm.primary) {
        errors.push('Missing llm.primary provider')
      }
      if (config.memory && !config.memory.db_type) {
        errors.push('Missing memory.db_type')
      }
      return errors
    }

    it('should validate a complete config', () => {
      const config = {
        server: { port: 1337, data_dir: '~/.zenith' },
        voice: { stt_provider: 'groq_whisper', language: 'en-US' },
        llm: { primary: 'gemini', fallback: ['groq', 'openrouter'] },
        personality: { name: 'Zenith', style: 'friday' },
        skills: { enabled: true, nlp_confidence_threshold: 0.6 },
        memory: { db_type: 'tinydb', db_path: '~/.zenith/zenith.db' },
        ui: { theme: 'stark', port: 1337 }
      }
      const errors = validateConfig(config)
      expect(errors).toHaveLength(0)
    })

    it('should detect missing sections', () => {
      const config = { server: { port: 1337 } }
      const errors = validateConfig(config)
      expect(errors.length).toBeGreaterThan(0)
      expect(errors.some(e => e.includes('voice'))).toBeTruthy()
    })

    it('should detect missing server.port', () => {
      const config = {
        server: {},
        voice: {}, llm: { primary: 'gemini' },
        personality: {}, skills: {}, memory: { db_type: 'tinydb' }, ui: {}
      }
      const errors = validateConfig(config)
      expect(errors.some(e => e.includes('server.port'))).toBeTruthy()
    })

    it('should detect missing llm.primary', () => {
      const config = {
        server: { port: 1337 },
        voice: {}, llm: {},
        personality: {}, skills: {}, memory: { db_type: 'tinydb' }, ui: {}
      }
      const errors = validateConfig(config)
      expect(errors.some(e => e.includes('llm.primary'))).toBeTruthy()
    })
  })
})
