import { io } from 'socket.io-client'
import { setOrbState } from './orb.js'
import { forceVoiceTurn, toggleVoice } from './voice.js'

// ── Globals ──────────────────────────────
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
window.onKey = (e) => { if (e.key === 'Enter') window.submitText() }
window.clearChat = () => {
  document.getElementById('messages').replaceChildren()
  addMsg('ZENITH', 'Conversation cleared, sir.', 'agent')
}

// ── Clock (IST) ───────────────────────────
function updateClock() {
  const now = new Date()
  const opts = { timeZone: 'Asia/Kolkata' }
  const timeStr = now.toLocaleTimeString('en-IN', { ...opts, hour12: false })
  const dateStr = now.toLocaleDateString('en-IN', {
    ...opts, weekday: 'short', day: '2-digit',
    month: 'short', year: 'numeric'
  })
  const t = document.getElementById('clock-time')
  const d = document.getElementById('clock-date')
  if (t) t.textContent = timeStr + ' IST'
  if (d) d.textContent = dateStr.toUpperCase()
}
updateClock()
setInterval(updateClock, 1000)

// ── Canvas background animation ───────────
const canvas = document.getElementById('bg-canvas')
if (canvas) {
  const ctx = canvas.getContext('2d')
  let animationFrame = 0
  let canvasWidth = 0
  let canvasHeight = 0

  const resizeCanvas = () => {
    const nextWidth = window.innerWidth
    const nextHeight = window.innerHeight
    if (nextWidth === canvasWidth && nextHeight === canvasHeight) return
    canvasWidth = nextWidth
    canvasHeight = nextHeight
    canvas.width = nextWidth
    canvas.height = nextHeight
  }

  resizeCanvas()

  const particles = Array.from({ length: 60 }, () => ({
    x: Math.random() * canvas.width,
    y: Math.random() * canvas.height,
    vx: (Math.random() - 0.5) * 0.3,
    vy: (Math.random() - 0.5) * 0.3,
    size: Math.random() * 1.5 + 0.5,
    alpha: Math.random() * 0.4 + 0.1
  }))

  function drawCanvas() {
    if (document.hidden) {
      animationFrame = 0
      return
    }

    ctx.clearRect(0, 0, canvas.width, canvas.height)
    particles.forEach(p => {
      p.x += p.vx; p.y += p.vy
      if (p.x < 0) p.x = canvas.width
      if (p.x > canvas.width) p.x = 0
      if (p.y < 0) p.y = canvas.height
      if (p.y > canvas.height) p.y = 0
      ctx.beginPath()
      ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2)
      ctx.fillStyle = `rgba(0,212,255,${p.alpha})`
      ctx.fill()
    })
    animationFrame = requestAnimationFrame(drawCanvas)
  }

  animationFrame = requestAnimationFrame(drawCanvas)

  document.addEventListener('visibilitychange', () => {
    if (!document.hidden && !animationFrame) {
      animationFrame = requestAnimationFrame(drawCanvas)
    }
  })

  window.addEventListener('resize', resizeCanvas)
}

// ── Socket ────────────────────────────────
const socket = io()

socket.on('connect', () => {
  socket.emit('init', 'webapp')
  logAct('Core connected', true)
})
socket.on('ready', () => logAct('Command channel ready', true))
socket.on('disconnect', () => logAct('Core disconnected'))

socket.on('answer', (data) => {
  removeTyping()
  const text = data.value || data.answer || JSON.stringify(data)
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

socket.on('zenith:state_change', (d) => setOrbState(d.state))
socket.on('zenith:tool_call', (d) => logAct('Tool: ' + (d.tool || '—'), true))

// ── Messages ──────────────────────────────
function addMsg(sender, text, type) {
  const container = document.getElementById('messages')
  const row = document.createElement('div')
  row.className = 'msg-row ' + type
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
  dots.append(document.createElement('span'), document.createElement('span'), document.createElement('span'))
  bubbleNode.appendChild(dots)
  typingEl.append(senderNode, bubbleNode)
  container.appendChild(typingEl)
  container.scrollTop = container.scrollHeight
}

function removeTyping() {
  if (typingEl) { typingEl.remove(); typingEl = null }
}

// ── Activity log ──────────────────────────
function logAct(text, highlight = false) {
  const list = document.getElementById('activity-list')
  if (!list) return
  const item = document.createElement('div')
  item.className = 'act-item' + (highlight ? ' highlight' : '')
  const timeNode = document.createElement('div')
  timeNode.className = 'act-time'
  timeNode.textContent = new Date().toLocaleTimeString('en-IN', {
    timeZone: 'Asia/Kolkata', hour12: false
  })
  const textNode = document.createElement('div')
  textNode.textContent = text
  item.append(timeNode, textNode)
  list.insertBefore(item, list.firstChild)
  while (list.children.length > 15) list.removeChild(list.lastChild)
}

// ── Boot message ──────────────────────────
setTimeout(() => {
  addMsg('ZENITH',
    'Online. I am Zenith, your personal AI assistant. ' +
    'How can I help you today, sir?',
    'agent'
  )
  logAct('System boot complete', true)
}, 500)
