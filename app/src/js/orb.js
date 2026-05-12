const states = new Set(['idle', 'connecting', 'listening', 'thinking', 'speaking'])
const stateCopy = {
  idle: 'Ready for commands',
  connecting: 'Connecting voice...',
  listening: 'Listening...',
  thinking: 'Processing...',
  speaking: 'Responding...'
}

export function setOrbState(state) {
  const safeState = states.has(state) ? state : 'idle'
  const visualState = safeState === 'connecting' ? 'thinking' : safeState

  document.body.dataset.orbState = safeState
  document.body.className = visualState

  const orbLabel = document.getElementById('orb-label')
  if (orbLabel) {
    orbLabel.textContent = safeState.toUpperCase()
  }

  const orbSub = document.getElementById('orb-sub')
  if (orbSub) {
    orbSub.textContent = stateCopy[safeState] || ''
  }

  const chip = document.getElementById('chip-voice-text')
  if (chip) {
    chip.textContent = safeState === 'idle' ? 'VOICE STANDBY' : `VOICE ${safeState.toUpperCase()}`
  }

  const dot = document.querySelector('#chip-voice .chip-dot')
  if (dot) {
    dot.classList.toggle('inactive', safeState === 'idle')
  }

  const sysVoice = document.getElementById('sys-voice')
  if (sysVoice) {
    sysVoice.textContent = safeState === 'idle' ? 'STANDBY' : safeState.toUpperCase()
  }

  const voiceBtn = document.getElementById('voice-btn')
  if (voiceBtn) {
    voiceBtn.classList.toggle('active', safeState !== 'idle')
    voiceBtn.classList.toggle('listening-active', ['listening', 'speaking'].includes(safeState))
  }
}
