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

    room.on(LK.RoomEvent.TrackSubscribed, (track, publication, participant) => {
      // ONLY attach audio from REMOTE participants (the agent)
      // Never attach local participant audio — that causes echo
      if (track.kind === LK.Track.Kind.Audio) {
        const isLocal = participant.isLocal
        if (isLocal) {
          console.log('Skipping local audio track - no echo')
          return
        }

        setOrbState('speaking')
        const audioEl = track.attach()
        audioEl.style.display = 'none'
        audioEl.autoplay = true
        document.body.appendChild(audioEl)
        console.log('Agent audio attached from:', participant.identity)
      }
    })

    room.on(LK.RoomEvent.TrackUnsubscribed, (track, publication, participant) => {
      if (track.kind === LK.Track.Kind.Audio && !participant.isLocal) {
        track.detach().forEach((el) => el.remove())
        setOrbState('listening')
      }
    })

    room.on(LK.RoomEvent.ActiveSpeakersChanged, (speakers) => {
      const localSpeaking = speakers.some((speaker) => speaker.isLocal)
      const agentSpeaking = speakers.some((speaker) => !speaker.isLocal)

      if (agentSpeaking) {
        setOrbState('speaking')
      } else if (localSpeaking) {
        setOrbState('thinking')
      } else {
        setOrbState('listening')
      }
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
    await room.localParticipant.setMicrophoneEnabled(true, {
      noiseSuppression: true,
      echoCancellation: true,
      autoGainControl: true
    })

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
