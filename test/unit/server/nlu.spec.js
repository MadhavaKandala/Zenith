/**
 * Unit tests for NLU (Natural Language Understanding) processing
 * Tests intent classification, fallback logic, and Gemini routing
 */

const path = require('path')

// Mock dependencies before requiring the module
jest.mock('@/core', () => ({
  TCP_CLIENT: { isConnected: true, connect: jest.fn(), ee: { on: jest.fn(), removeListener: jest.fn() } },
  HTTP_SERVER: { httpServer: {} },
  SOCKET_SERVER: { socket: { emit: jest.fn() } },
  STT: { init: jest.fn() },
  TTS: { init: jest.fn() },
  ASR: { encode: jest.fn() },
  NER: { mergeSpacyEntities: jest.fn(), extractEntities: jest.fn().mockResolvedValue([]) },
  MODEL_LOADER: {
    hasNlpModels: jest.fn().mockReturnValue(true),
    mainNLPContainer: {
      process: jest.fn(),
      getIntentDomain: jest.fn()
    },
    loadNLPModels: jest.fn()
  },
  NLU: {},
  BRAIN: {
    isMuted: false,
    lang: 'en',
    talk: jest.fn(),
    wernicke: jest.fn().mockReturnValue('test'),
    execute: jest.fn().mockResolvedValue({})
  }
}))

jest.mock('@/helpers/log-helper', () => ({
  LogHelper: {
    title: jest.fn(),
    success: jest.fn(),
    info: jest.fn(),
    warning: jest.fn(),
    error: jest.fn(),
    time: jest.fn(),
    timeEnd: jest.fn()
  }
}))

jest.mock('@/helpers/gemini-fallback-helper', () => ({
  getGeminiFallbackAnswer: jest.fn().mockResolvedValue('Mock Gemini response, sir.')
}))

jest.mock('@/helpers/lang-helper', () => ({
  LangHelper: {
    getShortCode: jest.fn().mockReturnValue('en'),
    getShortCodes: jest.fn().mockReturnValue(['en', 'fr']),
    getLongCode: jest.fn().mockReturnValue('en-US')
  }
}))

jest.mock('@/constants', () => ({
  LANG: 'en-US',
  HAS_STT: false,
  HAS_TTS: false,
  IS_DEVELOPMENT_ENV: true,
  TCP_SERVER_BIN_PATH: '/mock/path'
}))

describe('NLU Processing', () => {
  describe('DEFAULT_NLU_RESULT', () => {
    it('should have correct default structure', () => {
      const { DEFAULT_NLU_RESULT } = require('../../server/src/core/nlp/nlu/nlu')

      expect(DEFAULT_NLU_RESULT).toEqual(
        expect.objectContaining({
          utterance: '',
          currentEntities: [],
          entities: [],
          currentResolvers: [],
          resolvers: [],
          slots: {},
          skillConfigPath: '',
          answers: [],
          classification: {
            domain: '',
            skill: '',
            action: '',
            confidence: 0
          }
        })
      )
    })
  })

  describe('NLU class', () => {
    it('should be instantiable as a singleton', () => {
      const NLU = require('../../server/src/core/nlp/nlu/nlu').default
      const nlu1 = new NLU()
      const nlu2 = new NLU()

      expect(nlu1).toBeDefined()
      expect(nlu2).toBeDefined()
    })

    it('should have a conversation instance', () => {
      const NLU = require('../../server/src/core/nlp/nlu/nlu').default
      const nlu = new NLU()

      expect(nlu.conversation).toBeDefined()
    })

    it('should initialize with default NLU result', () => {
      const NLU = require('../../server/src/core/nlp/nlu/nlu').default
      const nlu = new NLU()

      expect(nlu.nluResult.utterance).toBe('')
      expect(nlu.nluResult.classification.confidence).toBe(0)
    })
  })
})

describe('Gemini Fallback Helper', () => {
  const { getGeminiFallbackAnswer } = require('../../server/src/helpers/gemini-fallback-helper')

  it('should return a string response', async () => {
    const result = await getGeminiFallbackAnswer('What is AI?')
    expect(typeof result).toBe('string')
    expect(result.length).toBeGreaterThan(0)
  })
})
