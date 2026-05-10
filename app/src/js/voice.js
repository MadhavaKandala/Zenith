import * as LK from 'livekit-client'

import { setOrbState } from './orb.js'

let room = null
let isConnected = false

export async function toggleVoice() {
  if (isConnected) {
    await disconnectVoice()
    return
  }
  await connectVoice()
}

async function connectVoice() {
  const btn = document.getElementById('zenith-mic-btn')
  try {
    // Fetch token from backend
    const res = await fetch('/api/livekit-token')
    if (!res.ok) throw new Error('Token fetch failed: ' + res.status)
    const { token, url } = await res.json()

    console.log(
      'LiveKit loaded:',
      !!LK,
      Object.keys(LK).filter((k) => k.toLowerCase().includes('livekit'))
    )
    if (!LK) throw new Error('LiveKit client not loaded')

    room = new LK.Room({ adaptiveStream: true })

    // Agent audio -> orb speaking
    room.on(LK.RoomEvent.TrackSubscribed, (track) => {
      if (track.kind === LK.Track.Kind.Audio) {
        setOrbState('speaking')
        const el = track.attach()
        el.style.display = 'none'
        document.body.appendChild(el)
      }
    })

    room.on(LK.RoomEvent.TrackUnsubscribed, () => {
      setOrbState('listening')
    })

    room.on(LK.RoomEvent.Disconnected, () => {
      isConnected = false
      setOrbState('idle')
      if (btn) {
        btn.textContent = '◉ VOICE'
        btn.classList.remove('mic-active')
      }
    })

    await room.connect(url, token)
    await room.localParticipant.setMicrophoneEnabled(true)

    isConnected = true
    setOrbState('listening')
    if (btn) {
      btn.textContent = '⊗ DISCONNECT'
      btn.classList.add('mic-active')
    }
  } catch (err) {
    console.error('Voice connect error:', err)
    setOrbState('idle')
    if (btn) btn.textContent = '◉ VOICE'
    alert(
      'Voice connection failed: ' +
        err.message +
        '\n\nMake sure:\n1. Voice agent is running (uv run python agent.py dev)\n2. LiveKit keys are set in .env'
    )
  }
}

async function disconnectVoice() {
  if (room) {
    await room.disconnect()
    room = null
  }
  isConnected = false
  setOrbState('idle')
  const btn = document.getElementById('zenith-mic-btn')
  if (btn) {
    btn.textContent = '◉ VOICE'
    btn.classList.remove('mic-active')
  }
}
