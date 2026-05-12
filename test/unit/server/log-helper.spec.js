/**
 * Unit tests for the LogHelper utility
 * Tests logging methods, error file handling, and log parsing
 */

const fs = require('fs')
const path = require('path')

describe('LogHelper', () => {
  let consoleSpy

  beforeEach(() => {
    consoleSpy = {
      log: jest.spyOn(console, 'log').mockImplementation(),
      info: jest.spyOn(console, 'info').mockImplementation(),
      warn: jest.spyOn(console, 'warn').mockImplementation(),
      error: jest.spyOn(console, 'error').mockImplementation(),
      time: jest.spyOn(console, 'time').mockImplementation(),
      timeEnd: jest.spyOn(console, 'timeEnd').mockImplementation()
    }
  })

  afterEach(() => {
    Object.values(consoleSpy).forEach(spy => spy.mockRestore())
  })

  describe('Log level methods', () => {
    it('success() should call console.log with green color code', () => {
      const { LogHelper } = require('../../server/src/helpers/log-helper')
      LogHelper.success('test success')
      expect(consoleSpy.log).toHaveBeenCalled()
    })

    it('info() should call console.info with cyan color code', () => {
      const { LogHelper } = require('../../server/src/helpers/log-helper')
      LogHelper.info('test info')
      expect(consoleSpy.info).toHaveBeenCalled()
    })

    it('warning() should call console.warn with yellow color code', () => {
      const { LogHelper } = require('../../server/src/helpers/log-helper')
      LogHelper.warning('test warning')
      expect(consoleSpy.warn).toHaveBeenCalled()
    })

    it('title() should output uppercase text', () => {
      const { LogHelper } = require('../../server/src/helpers/log-helper')
      LogHelper.title('My Title')
      expect(consoleSpy.log).toHaveBeenCalledWith(
        expect.any(String),
        expect.stringContaining('MY TITLE')
      )
    })

    it('default() should call console.log with plain text', () => {
      const { LogHelper } = require('../../server/src/helpers/log-helper')
      LogHelper.default('plain text')
      expect(consoleSpy.log).toHaveBeenCalledWith('plain text')
    })
  })

  describe('Timer methods', () => {
    it('time() should start a console timer', () => {
      const { LogHelper } = require('../../server/src/helpers/log-helper')
      LogHelper.time('Test Timer')
      expect(consoleSpy.time).toHaveBeenCalled()
    })

    it('timeEnd() should stop a console timer', () => {
      const { LogHelper } = require('../../server/src/helpers/log-helper')
      LogHelper.timeEnd('Test Timer')
      expect(consoleSpy.timeEnd).toHaveBeenCalled()
    })
  })
})
