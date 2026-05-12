import { VERSION } from './version'

function formatStatusLine(label: string, value: string): string {
  return `${label}: ${value}`
}

function printBridgeSummary(): void {
  console.log('[Zenith] Node.js bridge')
  console.log(formatStatusLine('version', VERSION))
  console.log(formatStatusLine('runtime', process.version))
  console.log(formatStatusLine('status', 'ready'))
  console.log('This bridge is reserved for future Node-side extensions.')
}

printBridgeSummary()
