import { setOrbState } from './orb.js'

const VOICE_STORAGE_KEY = 'zenith.voicePreset'
const VOICE_STORAGE_VERSION_KEY = 'zenith.voicePresetVersion'
const VOICE_STORAGE_VERSION = '3'
let lastVoiceEventMessage = ''

const VOICE_PRESETS = [
  {
    id: 'en-US-Chirp3-HD-Achernar',
    label: 'Google Cloud',
    note: 'Low-latency Google Cloud TTS voice for the LiveKit response channel.'
  }
]

function byId(id) {
  return document.getElementById(id)
}

function formatLabel(value) {
  return String(value || '')
    .replace(/[-_]+/g, ' ')
    .trim()
    .replace(/\b\w/g, (char) => char.toUpperCase())
}

function getStoredVoiceId() {
  try {
    if (
      window.localStorage.getItem(VOICE_STORAGE_VERSION_KEY) !==
      VOICE_STORAGE_VERSION
    ) {
      window.localStorage.removeItem(VOICE_STORAGE_KEY)
      window.localStorage.setItem(
        VOICE_STORAGE_VERSION_KEY,
        VOICE_STORAGE_VERSION
      )
      return null
    }

    return window.localStorage.getItem(VOICE_STORAGE_KEY)
  } catch {
    return null
  }
}

function storeVoiceId(id) {
  try {
    window.localStorage.setItem(VOICE_STORAGE_KEY, id)
  } catch {
    // Ignore localStorage failures in private browsing contexts.
  }
}

export function getSelectedVoicePreset() {
  const storedId = getStoredVoiceId()
  const preset = VOICE_PRESETS.find((item) => item.id === storedId)
  return preset || VOICE_PRESETS[0]
}

export function syncVoicePresetUi() {
  const preset = getSelectedVoicePreset()
  storeVoiceId(preset.id)
  return preset
}

export function setVoiceConnectionState(state) {
  document.body.dataset.voiceConnection = String(state || 'offline').toLowerCase()
  const forceTurnBtn = byId('voice-send-btn')
  if (forceTurnBtn) {
    forceTurnBtn.disabled = !['connected', 'reconnecting'].includes(
      String(state || 'offline').toLowerCase()
    )
  }
}

export function setForceTurnButtonState(mode) {
  const button = byId('voice-send-btn')
  if (!button) return

  if (mode === 'paused') {
    button.textContent = 'RESUME MIC'
    button.disabled = false
    button.classList.add('paused')
    return
  }

  button.textContent = 'ANSWER NOW'
  button.classList.remove('paused')
  button.disabled = mode === 'disabled'
}

export function setVoiceStatus(state, detail) {
  const safeState = state || 'idle'
  const activity = byId('voice-activity-state')

  setOrbState(safeState)
  if (activity) activity.textContent = formatLabel(safeState).toUpperCase()
  if (detail) {
    const eventNode = byId('voice-last-event')
    if (eventNode && !eventNode.textContent) {
      eventNode.textContent = detail
    }
  }

  document.body.dataset.voiceState = safeState.toLowerCase()
}

export function setVoiceRoom(_roomName) {}

function prependActivity(message, highlight = false) {
  const list = byId('activity-list')
  if (!list || !message) return

  const item = document.createElement('div')
  item.className = 'act-item' + (highlight ? ' highlight' : '')

  const timeNode = document.createElement('div')
  timeNode.className = 'act-time'
  timeNode.textContent = new Date().toLocaleTimeString('en-IN', {
    timeZone: 'Asia/Kolkata',
    hour12: false
  })

  const textNode = document.createElement('div')
  textNode.textContent = message
  item.append(timeNode, textNode)
  list.insertBefore(item, list.firstChild)

  while (list.children.length > 15) {
    list.removeChild(list.lastChild)
  }
}

export function setLastVoiceEvent(message, options = {}) {
  const { persist = true } = options
  const node = byId('voice-last-event')
  if (node) {
    node.textContent = message
  }

  if (persist && message && message !== lastVoiceEventMessage) {
    prependActivity(message)
  }

  lastVoiceEventMessage = message
}

export function setMicButtonState(active) {
  const btn = byId('zenith-mic-btn') || byId('voice-btn')
  if (!btn) return

  const jarvisText = byId('voice-btn-text')
  if (jarvisText) {
    jarvisText.textContent = active ? 'END VOICE' : 'ACTIVATE VOICE'
    btn.classList.toggle('active', active)
    if (!active) {
      btn.classList.remove('listening-active')
    }
    return
  }

  btn.textContent = active ? 'END SESSION' : 'START VOICE'
  btn.classList.toggle('mic-active', active)
}

export function updateTranscript(role, text) {
  const node =
    role === 'user' ? byId('voice-transcript-user') : byId('voice-transcript-agent')
  if (node) {
    node.textContent = text
    node.title = text
  }
}

export function setComposerVoiceTranscript(text, options = {}) {
  const input = byId('text-input')
  if (!input || !text) return

  const { final = false } = options
  const isManualEntryActive =
    document.activeElement === input && input.value.trim()
  if (isManualEntryActive) return

  input.value = text
  input.title = text
  input.dataset.voiceDraft = 'true'

  const clearVoiceDraftMarker = () => {
    delete input.dataset.voiceDraft
    input.removeEventListener('input', clearVoiceDraftMarker)
  }
  input.addEventListener('input', clearVoiceDraftMarker)

  if (final) {
    window.setTimeout(() => {
      if (input.dataset.voiceDraft === 'true' && input.value === text) {
        input.value = ''
        input.title = ''
        delete input.dataset.voiceDraft
      }
    }, 1800)
  }
}

export function clearComposerVoiceTranscript() {
  const input = byId('text-input')
  if (!input || input.dataset.voiceDraft !== 'true') return

  input.value = ''
  input.title = ''
  delete input.dataset.voiceDraft
}

export function addVoiceHistory(title, body) {
  prependActivity(`${title}: ${body}`, true)
}

export function appendVoiceBubble(role, text) {
  if (!text) return

  const messages = byId('messages')
  if (!messages) return

  const row = document.createElement('div')
  row.className = `msg-row ${role === 'user' ? 'user' : 'agent'}`

  const sender = document.createElement('div')
  sender.className = 'msg-sender'
  sender.textContent = role === 'user' ? 'YOU' : 'ZENITH'

  const bubble = document.createElement('div')
  bubble.className = 'msg-bubble'
  bubble.textContent = text

  row.append(sender, bubble)
  messages.appendChild(row)
  messages.scrollTop = messages.scrollHeight
}
