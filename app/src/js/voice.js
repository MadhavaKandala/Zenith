import * as LK from 'livekit-client'

import {
  addVoiceHistory,
  appendVoiceBubble,
  getSelectedVoicePreset,
  setLastVoiceEvent,
  setMicButtonState,
  setVoiceConnectionState,
  setVoiceRoom,
  setVoiceStatus,
  syncVoicePresetUi,
  updateTranscript
} from './voice-ui.js'

let room = null
let isConnected = false
let renderedTranscriptIds = new Set()

export async function toggleVoice() {
  if (isConnected) {
    await disconnectVoice()
    return
  }

  await connectVoice()
}

async function connectVoice() {
  syncVoicePresetUi()
  const preset = getSelectedVoicePreset()

  try {
    setMicButtonState(true)
    setVoiceConnectionState('connecting')
    setVoiceStatus(
      'connecting',
      `Opening a live room and preparing ${preset.label} for Zenith's reply.`
    )
    setLastVoiceEvent('Requesting a LiveKit session token from Zenith.')
    addVoiceHistory(
      'Session requested',
      `Starting a voice session with the ${preset.label} ElevenLabs preset.`
    )

    const params = new URLSearchParams({
      voiceId: preset.id,
      voiceLabel: preset.label
    })
    const res = await fetch(`/api/livekit-token?${params.toString()}`)
    if (!res.ok) {
      throw new Error(`Token fetch failed: ${res.status}`)
    }

    const { token, url, room: roomName } = await res.json()
    if (!LK?.Room) {
      throw new Error('LiveKit client failed to load')
    }

    renderedTranscriptIds = new Set()
    updateTranscript('user', 'Your spoken words will appear here as Zenith hears them.')
    updateTranscript(
      'agent',
      `Zenith will answer with the ${preset.label} voice once the room is live.`
    )
    setVoiceRoom(roomName)
    setLastVoiceEvent(`Joining ${roomName}.`)

    room = new LK.Room({
      adaptiveStream: true,
      dynacast: true
    })

    attachRoomHandlers(room, preset)

    await room.connect(url, token)
    setVoiceConnectionState('connected')
    setLastVoiceEvent(`Connected to ${roomName}. Unlocking browser audio.`)

    await room.startAudio().catch((error) => {
      console.warn('Initial startAudio failed:', error)
    })

    await room.localParticipant.setMicrophoneEnabled(true, {
      noiseSuppression: true,
      echoCancellation: true,
      autoGainControl: true
    })

    isConnected = true
    setVoiceStatus(
      'listening',
      `Live voice is active. Speak naturally and Zenith will answer with ${preset.label}.`
    )
    addVoiceHistory('Session live', `${roomName} connected. Microphone streaming to Zenith.`)
  } catch (error) {
    console.error('Voice connect error:', error)
    setVoiceConnectionState('offline')
    setVoiceStatus(
      'idle',
      'Voice connection failed. Restart the voice worker if the problem persists.'
    )
    setMicButtonState(false)
    setVoiceRoom('Awaiting session')
    setLastVoiceEvent(
      `Voice connection failed: ${error instanceof Error ? error.message : String(error)}`
    )
    addVoiceHistory(
      'Voice error',
      error instanceof Error ? error.message : 'Unknown voice connection error.'
    )
    if (room) {
      await room.disconnect()
      room = null
    }
    isConnected = false
  }
}

function attachRoomHandlers(activeRoom, preset) {
  activeRoom.on(LK.RoomEvent.ConnectionStateChanged, (state) => {
    const normalized = String(state || 'connecting').toLowerCase()
    setVoiceConnectionState(normalized)

    if (normalized === 'connected') {
      setVoiceStatus(
        'listening',
        `Room connected. Zenith is listening and will answer with ${preset.label}.`
      )
    } else if (normalized === 'reconnecting') {
      setVoiceStatus('connecting', 'LiveKit is reconnecting the session.')
    }

    setLastVoiceEvent(`Room state changed to ${normalized}.`)
  })

  activeRoom.on(LK.RoomEvent.AudioPlaybackStatusChanged, async () => {
    if (activeRoom.canPlaybackAudio) {
      setLastVoiceEvent('Browser audio output is unlocked.')
      return
    }

    setLastVoiceEvent('Browser blocked audio playback. Retrying inside the active voice session.')
    try {
      await activeRoom.startAudio()
      setLastVoiceEvent('Audio playback unlocked after retry.')
    } catch (error) {
      console.error('LiveKit startAudio retry failed:', error)
      addVoiceHistory(
        'Playback blocked',
        'Browser autoplay rules blocked audio. Click Start Voice again if Zenith stays silent.'
      )
    }
  })

  activeRoom.on(LK.RoomEvent.ParticipantConnected, (participant) => {
    if (participant.isLocal) return

    setLastVoiceEvent(`Zenith joined as ${participant.identity}.`)
    addVoiceHistory('Agent connected', `${participant.identity} entered the room.`)
  })

  activeRoom.on(LK.RoomEvent.ParticipantDisconnected, (participant) => {
    if (participant.isLocal) return

    setVoiceStatus('listening', 'Zenith audio track paused. Waiting for the next response.')
    setLastVoiceEvent(`${participant.identity} disconnected from the room.`)
    addVoiceHistory('Agent disconnected', `${participant.identity} left the room.`)
  })

  activeRoom.on(LK.RoomEvent.TrackSubscribed, async (track, _publication, participant) => {
    if (track.kind !== LK.Track.Kind.Audio || participant.isLocal) {
      return
    }

    const audioEl = track.attach()
    audioEl.autoplay = true
    audioEl.muted = false
    audioEl.playsInline = true
    audioEl.dataset.zenithAudio = 'true'
    audioEl.style.display = 'none'
    document.body.appendChild(audioEl)

    try {
      await activeRoom.startAudio()
      await audioEl.play()
      setVoiceStatus('speaking', `Zenith is speaking now with the ${preset.label} preset.`)
      setLastVoiceEvent(`Remote audio track attached from ${participant.identity}.`)
      addVoiceHistory('Audio online', `Receiving Zenith audio from ${participant.identity}.`)
    } catch (error) {
      console.error('Agent audio play failed:', error)
      setLastVoiceEvent('Audio track arrived, but the browser refused playback.')
      addVoiceHistory(
        'Audio blocked',
        'The agent published audio, but the browser blocked playback. Reconnect if it stays silent.'
      )
    }
  })

  activeRoom.on(LK.RoomEvent.TrackUnsubscribed, (track, _publication, participant) => {
    if (track.kind === LK.Track.Kind.Audio && !participant.isLocal) {
      track.detach().forEach((element) => element.remove())
      setVoiceStatus('listening', 'Zenith finished speaking and is ready for your next command.')
      setLastVoiceEvent(`Remote audio track removed for ${participant.identity}.`)
    }
  })

  activeRoom.on(LK.RoomEvent.ActiveSpeakersChanged, (speakers) => {
    const localSpeaking = speakers.some((speaker) => speaker.isLocal)
    const remoteSpeaking = speakers.some((speaker) => !speaker.isLocal)

    if (remoteSpeaking) {
      setVoiceStatus('speaking', `Zenith is delivering the reply with ${preset.label}.`)
      return
    }

    if (localSpeaking) {
      setVoiceStatus('listening', 'Listening to your voice input now.')
      return
    }

    if (isConnected) {
      setVoiceStatus('listening', 'Session open. Zenith is ready for the next command.')
    }
  })

  activeRoom.on(
    LK.RoomEvent.TranscriptionReceived,
    (segments, participant) => handleTranscriptSegments(segments, participant)
  )

  activeRoom.on(LK.RoomEvent.Disconnected, () => {
    isConnected = false
    setMicButtonState(false)
    setVoiceConnectionState('offline')
    setVoiceStatus('idle', 'Voice session closed. Press start voice to reconnect.')
    setVoiceRoom('Awaiting session')
    setLastVoiceEvent('Live voice session disconnected.')
    addVoiceHistory('Session closed', 'Live voice room disconnected.')
    clearAttachedAudio()
    room = null
  })
}

function handleTranscriptSegments(segments, participant) {
  const text = segments
    .map((segment) => segment.text.trim())
    .filter(Boolean)
    .join(' ')
    .trim()

  if (!text) return

  const isUser = participant?.isLocal ?? false
  updateTranscript(isUser ? 'user' : 'agent', text)
  setLastVoiceEvent(
    isUser ? 'Your speech is being transcribed in real time.' : 'Zenith response transcript updated.'
  )

  const finalSegments = segments.filter(
    (segment) => segment.final && !renderedTranscriptIds.has(segment.id)
  )
  if (finalSegments.length === 0) {
    return
  }

  for (const segment of finalSegments) {
    renderedTranscriptIds.add(segment.id)
  }

  const finalText = finalSegments
    .map((segment) => segment.text.trim())
    .filter(Boolean)
    .join(' ')
    .trim()

  if (!finalText) return

  appendVoiceBubble(isUser ? 'user' : 'agent', finalText)
  addVoiceHistory(isUser ? 'You said' : 'Zenith replied', finalText)

  if (isUser) {
    setVoiceStatus('thinking', 'Command captured. Zenith is preparing a reply.')
  } else {
    setVoiceStatus('speaking', 'Zenith is voicing the response now.')
  }
}

function clearAttachedAudio() {
  document.querySelectorAll('[data-zenith-audio="true"]').forEach((element) => {
    element.remove()
  })
}

async function disconnectVoice() {
  if (room) {
    await room.disconnect()
    return
  }

  isConnected = false
  clearAttachedAudio()
  setMicButtonState(false)
  setVoiceConnectionState('offline')
  setVoiceStatus('idle', 'Voice session ended. Press start voice to reconnect Zenith.')
  setVoiceRoom('Awaiting session')
  setLastVoiceEvent('Voice session ended by the user.')
  addVoiceHistory('Session ended', 'Voice session closed manually from the control deck.')
}
