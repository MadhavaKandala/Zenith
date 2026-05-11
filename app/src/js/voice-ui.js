import { setOrbState } from './orb.js'

const VOICE_STORAGE_KEY = 'zenith.voicePreset'
const MAX_VOICE_HISTORY_ITEMS = 14

const VOICE_PRESETS = [
  {
    id: 'ErXwobaYiN019PkySvjV',
    label: 'Antoni',
    note: 'Crisp male voice, good for command responses and fast tool confirmations.'
  },
  {
    id: '21m00Tcm4TlvDq8ikWAM',
    label: 'Rachel',
    note: 'Clear female voice with a polished assistant tone and strong sentence flow.'
  },
  {
    id: 'EXAVITQu4vr4xnSDxMaL',
    label: 'Bella',
    note: 'Warmer female voice with a softer delivery for longer answers.'
  },
  {
    id: 'MF3mGyEYCl7XYWbV9V6O',
    label: 'Elli',
    note: 'Calm female voice with an even, human presentation.'
  },
  {
    id: 'TxGEqnHWrfWFTfGW9XjX',
    label: 'Josh',
    note: 'Deeper male voice with a steadier command-center feel.'
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

export function getVoicePresets() {
  return VOICE_PRESETS.slice()
}

export function getSelectedVoicePreset() {
  const storedId = getStoredVoiceId()
  const preset = VOICE_PRESETS.find((item) => item.id === storedId)
  return preset || VOICE_PRESETS[0]
}

export function initVoiceUi() {
  const selector = byId('voice-selector')
  if (!selector || selector.dataset.ready === 'true') {
    syncVoicePresetUi()
    return
  }

  const fragment = document.createDocumentFragment()
  for (const preset of VOICE_PRESETS) {
    const option = document.createElement('option')
    option.value = preset.id
    option.textContent = preset.label
    fragment.appendChild(option)
  }

  selector.replaceChildren(fragment)
  selector.dataset.ready = 'true'
  selector.addEventListener('change', () => {
    storeVoiceId(selector.value)
    const preset = getSelectedVoicePreset()
    renderVoicePreset(preset)
    addVoiceHistory(
      'Voice preset updated',
      `${preset.label} selected. Reconnect voice to apply the new ElevenLabs speaker.`
    )
  })

  syncVoicePresetUi()
  setVoiceConnectionState('offline')
  setVoiceStatus(
    'idle',
    'Press start voice to create a LiveKit room and route speech through Zenith.'
  )
  setLastVoiceEvent('Standing by for a voice session.')
}

export function syncVoicePresetUi() {
  const preset = getSelectedVoicePreset()
  const selector = byId('voice-selector')
  if (selector && selector.value !== preset.id) {
    selector.value = preset.id
  }
  renderVoicePreset(preset)
}

function renderVoicePreset(preset) {
  const note = byId('voice-voice-note')
  const currentVoice = byId('voice-telemetry-voice')
  if (note) {
    note.textContent = `${preset.label} is active. ${preset.note}`
  }
  if (currentVoice) {
    currentVoice.textContent = preset.label
  }
}

export function setVoiceConnectionState(state) {
  const formatted = formatLabel(state || 'offline')
  const tag = byId('voice-connection-state')
  const connection = byId('voice-telemetry-connection')
  const pill = byId('voice-mode-pill')

  if (tag) tag.textContent = formatted
  if (connection) connection.textContent = formatted
  if (pill) {
    pill.textContent =
      formatted.toLowerCase() === 'connected' ? 'VOICE LIVE' : `VOICE ${formatted.toUpperCase()}`
  }

  document.body.dataset.voiceConnection = String(state || 'offline').toLowerCase()
}

export function setVoiceStatus(state, detail) {
  const safeState = state || 'idle'
  const formatted = formatLabel(safeState)
  const status = byId('voice-telemetry-state')
  const activity = byId('voice-activity-state')
  const detailNode = byId('voice-status-detail')

  setOrbState(safeState)
  if (status) status.textContent = formatted
  if (activity) activity.textContent = formatted
  if (detailNode && detail) detailNode.textContent = detail

  document.body.dataset.voiceState = safeState.toLowerCase()
}

export function setVoiceRoom(roomName) {
  const roomNode = byId('voice-telemetry-room')
  if (roomNode) {
    roomNode.textContent = roomName || 'Awaiting session'
  }
}

export function setLastVoiceEvent(message) {
  const node = byId('voice-last-event')
  if (node) {
    node.textContent = message
  }
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

  if (active) {
    btn.textContent = '⊗ END SESSION'
    btn.classList.add('mic-active')
  } else {
    btn.textContent = '◉ START VOICE'
    btn.classList.remove('mic-active')
  }
}

export function updateTranscript(role, text) {
  const node = role === 'user' ? byId('voice-transcript-user') : byId('voice-transcript-agent')
  if (node) {
    node.textContent = text
  }
}

export function addVoiceHistory(title, body) {
  const history = byId('voice-history')
  if (!history) return

  const item = document.createElement('div')
  item.className = 'voice-history-item'

  const titleNode = document.createElement('span')
  titleNode.className = 'voice-history-title'
  titleNode.textContent = title

  const bodyNode = document.createElement('p')
  bodyNode.className = 'voice-history-body'
  bodyNode.textContent = body

  item.append(titleNode, bodyNode)
  history.prepend(item)

  while (history.children.length > MAX_VOICE_HISTORY_ITEMS) {
    history.removeChild(history.lastChild)
  }
}

export function appendVoiceBubble(role, text) {
  const feed = byId('feed')
  const noBubbleMessage = byId('no-bubble')

  if (!feed || !text) return

  const container = document.createElement('div')
  const bubble = document.createElement('p')

  container.className = `bubble-container ${role === 'user' ? 'me' : 'leon'}`
  bubble.className = 'bubble'
  bubble.textContent = text

  container.appendChild(bubble)
  feed.appendChild(container)

  if (noBubbleMessage && !noBubbleMessage.classList.contains('hide')) {
    noBubbleMessage.classList.add('hide')
  }

  feed.scrollTo({ top: feed.scrollHeight, behavior: 'smooth' })
}
