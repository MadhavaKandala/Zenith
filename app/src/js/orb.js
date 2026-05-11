const states = ['idle', 'connecting', 'listening', 'thinking', 'speaking']
const visualStates = ['idle', 'listening', 'thinking', 'speaking']
const stateCopy = {
  idle: 'Ready for commands',
  connecting: 'Connecting voice...',
  listening: 'Listening...',
  thinking: 'Processing...',
  speaking: 'Responding...',
}

function getOrb() {
  return document.getElementById('zenith-orb')
}

function getOrbLabel() {
  return document.getElementById('orb-label')
}

export function setOrbState(state) {
  const orb = getOrb()
  const orbLabel = getOrbLabel()
  const safeState = states.includes(state) ? state : 'idle'
  const visualState = safeState === 'connecting' ? 'thinking' : safeState

  if (orb) {
    states.forEach((item) => orb.classList.remove(item))
    visualStates.forEach((item) => orb.classList.remove(item))
    orb.classList.add(visualState)
  }

  document.body.dataset.orbState = safeState
  document.body.className = visualState

  if (orbLabel) {
    orbLabel.textContent = safeState.toUpperCase()
  }

  const orbSub = document.getElementById('orb-sub')
  if (orbSub) {
    orbSub.textContent = stateCopy[safeState] || ''
  }

  const chip = document.getElementById('chip-voice-text')
  const dot = document.querySelector('#chip-voice .chip-dot')
  if (chip) {
    chip.textContent = safeState === 'idle' ? 'VOICE STANDBY' : `VOICE ${safeState.toUpperCase()}`
  }
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
    voiceBtn.classList.toggle(
      'listening-active',
      safeState === 'listening' || safeState === 'speaking'
    )
  }
}

export function initOrb() {
  setOrbState('idle')
}
