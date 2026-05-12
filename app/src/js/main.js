import { io } from 'socket.io-client'
import { setOrbState } from './orb.js'
import { forceVoiceTurn, toggleVoice } from './voice.js'

window.handleVoice = toggleVoice
window.forceVoiceTurn = forceVoiceTurn
window.sendQuick = (text) => {
  document.getElementById('text-input').value = text
  window.submitText()
}
window.submitText = () => {
  const input = document.getElementById('text-input')
  const text = input.value.trim()
  if (!text) return

  input.value = ''
  addMsg('YOU', text, 'user')
  logAct('Query sent', true)
  setOrbState('thinking')
  socket.emit('utterance', { client: 'webapp', value: text })
}
window.onKey = (event) => {
  if (event.key === 'Enter') window.submitText()
}
window.clearChat = () => {
  document.getElementById('messages').replaceChildren()
  addMsg('ZENITH', 'Conversation cleared, sir.', 'agent')
}

function updateClock() {
  const now = new Date()
  const opts = { timeZone: 'Asia/Kolkata' }
  const timeNode = document.getElementById('clock-time')
  const dateNode = document.getElementById('clock-date')

  if (timeNode) {
    timeNode.textContent =
      now.toLocaleTimeString('en-IN', { ...opts, hour12: false }) + ' IST'
  }
  if (dateNode) {
    dateNode.textContent = now
      .toLocaleDateString('en-IN', {
        ...opts,
        weekday: 'short',
        day: '2-digit',
        month: 'short',
        year: 'numeric'
      })
      .toUpperCase()
  }
}

function hydrateBackground() {
  const canvas = document.getElementById('bg-canvas')
  if (!canvas) return

  const ctx = canvas.getContext('2d')
  let frameId = 0
  let width = 0
  let height = 0

  const particles = Array.from({ length: 60 }, () => ({
    x: 0,
    y: 0,
    vx: (Math.random() - 0.5) * 0.3,
    vy: (Math.random() - 0.5) * 0.3,
    size: Math.random() * 1.5 + 0.5,
    alpha: Math.random() * 0.4 + 0.1
  }))

  const resize = () => {
    const nextWidth = window.innerWidth
    const nextHeight = window.innerHeight
    if (nextWidth === width && nextHeight === height) return

    width = nextWidth
    height = nextHeight
    canvas.width = width
    canvas.height = height

    for (const particle of particles) {
      particle.x = Math.random() * width
      particle.y = Math.random() * height
    }
  }

  const draw = () => {
    if (document.hidden) {
      frameId = 0
      return
    }

    ctx.clearRect(0, 0, canvas.width, canvas.height)
    for (const particle of particles) {
      particle.x += particle.vx
      particle.y += particle.vy

      if (particle.x < 0) particle.x = canvas.width
      if (particle.x > canvas.width) particle.x = 0
      if (particle.y < 0) particle.y = canvas.height
      if (particle.y > canvas.height) particle.y = 0

      ctx.beginPath()
      ctx.arc(particle.x, particle.y, particle.size, 0, Math.PI * 2)
      ctx.fillStyle = `rgba(0,212,255,${particle.alpha})`
      ctx.fill()
    }

    frameId = requestAnimationFrame(draw)
  }

  resize()
  frameId = requestAnimationFrame(draw)
  window.addEventListener('resize', resize)
  document.addEventListener('visibilitychange', () => {
    if (!document.hidden && !frameId) {
      frameId = requestAnimationFrame(draw)
    }
  })
}

function renderSkills(skills) {
  const list = document.getElementById('skills-list')
  if (!list) return

  list.replaceChildren()
  for (const skill of skills) {
    const tag = document.createElement('div')
    tag.className = 'skill-tag'
    tag.textContent = skill.label.toUpperCase()
    tag.title = skill.description
    list.appendChild(tag)
  }
}

async function loadSystemInfo() {
  try {
    const response = await fetch('/api/v1/info')
    if (!response.ok) return

    const payload = await response.json()
    const providerNode = document.getElementById('sys-provider')
    const sttNode = document.getElementById('sys-stt')
    const ttsNode = document.getElementById('sys-tts')
    const providerChip = document.getElementById('chip-ai')

    if (providerNode) {
      providerNode.textContent = (payload.provider_chain || [])
        .map((item) => String(item).toUpperCase())
        .join(' -> ')
    }
    if (sttNode) {
      sttNode.textContent = payload.stt?.provider || 'disabled'
    }
    if (ttsNode) {
      ttsNode.textContent = payload.tts?.provider || 'disabled'
    }
    if (providerChip) {
      providerChip.innerHTML = '<div class="chip-dot"></div>3-PROVIDER ACTIVE'
    }

    renderSkills(payload.active_skills || [])
  } catch {
    logAct('System info endpoint unavailable')
  }
}

const socket = io()

socket.on('connect', () => {
  socket.emit('init', 'webapp')
  logAct('Core connected', true)
})
socket.on('ready', () => logAct('Command channel ready', true))
socket.on('disconnect', () => logAct('Core disconnected'))

socket.on('answer', (data) => {
  removeTyping()
  const text = typeof data === 'string' ? data : data?.value || data?.answer || JSON.stringify(data)
  addMsg('ZENITH', text, 'agent')
  setOrbState('idle')
  logAct('Response delivered', true)
})

socket.on('is-typing', (data) => {
  const isTyping = typeof data === 'boolean' ? data : data?.value
  if (isTyping) {
    setOrbState('thinking')
    showTyping()
  } else {
    removeTyping()
  }
})

socket.on('zenith:state_change', (data) => setOrbState(data.state))
socket.on('zenith:tool_call', (data) => {
  const status = data.status ? ` (${data.status})` : ''
  logAct(`Tool: ${data.tool || 'unknown'}${status}`, true)
})
socket.on('zenith:activity', (data) => {
  if (data?.message) logAct(data.message)
})

function addMsg(sender, text, type) {
  const container = document.getElementById('messages')
  const row = document.createElement('div')
  row.className = `msg-row ${type}`

  const senderNode = document.createElement('div')
  senderNode.className = 'msg-sender'
  senderNode.textContent = sender

  const bubbleNode = document.createElement('div')
  bubbleNode.className = 'msg-bubble'
  bubbleNode.textContent = text

  row.append(senderNode, bubbleNode)
  container.appendChild(row)
  container.scrollTop = container.scrollHeight
}

let typingEl = null

function showTyping() {
  if (typingEl) return

  const container = document.getElementById('messages')
  typingEl = document.createElement('div')
  typingEl.className = 'msg-row agent'

  const senderNode = document.createElement('div')
  senderNode.className = 'msg-sender'
  senderNode.textContent = 'ZENITH'

  const bubbleNode = document.createElement('div')
  bubbleNode.className = 'msg-bubble'
  const dots = document.createElement('div')
  dots.className = 'typing-dots'
  dots.append(
    document.createElement('span'),
    document.createElement('span'),
    document.createElement('span')
  )

  bubbleNode.appendChild(dots)
  typingEl.append(senderNode, bubbleNode)
  container.appendChild(typingEl)
  container.scrollTop = container.scrollHeight
}

function removeTyping() {
  if (!typingEl) return
  typingEl.remove()
  typingEl = null
}

function logAct(text, highlight = false) {
  const list = document.getElementById('activity-list')
  if (!list) return

  const item = document.createElement('div')
  item.className = 'act-item' + (highlight ? ' highlight' : '')

  const timeNode = document.createElement('div')
  timeNode.className = 'act-time'
  timeNode.textContent = new Date().toLocaleTimeString('en-IN', {
    timeZone: 'Asia/Kolkata',
    hour12: false
  })

  const textNode = document.createElement('div')
  textNode.textContent = text
  item.append(timeNode, textNode)

  list.insertBefore(item, list.firstChild)
  while (list.children.length > 18) {
    list.removeChild(list.lastChild)
  }
}

updateClock()
setInterval(updateClock, 1000)
hydrateBackground()
loadSystemInfo()

setTimeout(() => {
  addMsg(
    'ZENITH',
    'Online. I am Zenith, your personal AI assistant. How can I help you today, sir?',
    'agent'
  )
  logAct('System boot complete', true)
}, 500)
