import * as LK from 'livekit-client'

import {
  addVoiceHistory,
  appendVoiceBubble,
  getSelectedVoicePreset,
  setForceTurnButtonState,
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
let isConnecting = false
let isMicPausedForAnswer = false
let renderedTranscriptIds = new Set()
let answerTimeout = null
let voiceSessionId = 0

const micOptions = {
  noiseSuppression: true,
  echoCancellation: true,
  autoGainControl: true
}

export async function toggleVoice() {
  if (isConnected || isConnecting || room) {
    await disconnectVoice()
    return
  }

  await connectVoice()
}

export async function forceVoiceTurn() {
  if (!room || !isConnected) {
    setLastVoiceEvent('Start voice before using Answer Now.')
    return
  }

  if (isMicPausedForAnswer) {
    await resumeMic('Mic resumed. Zenith is listening again.')
    return
  }

  window.clearTimeout(answerTimeout)
  isMicPausedForAnswer = true
  setForceTurnButtonState('paused')
  setVoiceStatus('thinking', 'Mic paused. Zenith should answer from the last captured speech.')
  setLastVoiceEvent('Answer Now pressed. Mic is paused until Zenith responds.')
  addVoiceHistory('Answer Now', 'Mic paused to force a final turn boundary in a noisy room.')

  try {
    await room.localParticipant.setMicrophoneEnabled(false)
    answerTimeout = window.setTimeout(() => {
      if (isMicPausedForAnswer) {
        setLastVoiceEvent('Still waiting for Zenith. If this persists, LiveKit or the voice worker is disconnected.')
      }
    }, 12000)
  } catch (error) {
    console.error('Answer Now failed:', error)
    isMicPausedForAnswer = false
    setForceTurnButtonState('ready')
    setLastVoiceEvent('Answer Now failed. Reconnect voice and try again.')
  }
}

async function resumeMic(message = 'Mic reopened. Zenith is ready for your next command.') {
  if (!room || !isConnected) return

  window.clearTimeout(answerTimeout)
  answerTimeout = null
  isMicPausedForAnswer = false
  setForceTurnButtonState('ready')
  await room.localParticipant.setMicrophoneEnabled(true, micOptions)
  setVoiceStatus('listening', message)
  setLastVoiceEvent(message)
}

async function connectVoice() {
  const sessionId = voiceSessionId + 1
  voiceSessionId = sessionId
  isConnecting = true
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
    if (sessionId !== voiceSessionId) {
      return
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
    if (sessionId !== voiceSessionId) {
      await room.disconnect()
      return
    }
    isConnecting = false
    setVoiceConnectionState('connected')
    setLastVoiceEvent(`Connected to ${roomName}. Unlocking browser audio.`)

    await room.startAudio().catch((error) => {
      console.warn('Initial startAudio failed:', error)
    })

    await room.localParticipant.setMicrophoneEnabled(true, micOptions)

    isConnected = true
    setForceTurnButtonState('ready')
    setVoiceStatus(
      'listening',
      `Live voice is active. Speak naturally and Zenith will answer with ${preset.label}.`
    )
    addVoiceHistory('Session live', `${roomName} connected. Microphone streaming to Zenith.`)
  } catch (error) {
    isConnecting = false
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
    isMicPausedForAnswer = false
    setForceTurnButtonState('disabled')
  }
}

function attachRoomHandlers(activeRoom, preset) {
  activeRoom.on(LK.RoomEvent.ConnectionStateChanged, (state) => {
    const normalized = String(state || 'connecting').toLowerCase()
    setVoiceConnectionState(normalized)

    if (normalized === 'connected') {
      if (!isMicPausedForAnswer) {
        setVoiceStatus(
          'listening',
          `Room connected. Zenith is listening and will answer with ${preset.label}.`
        )
      }
      setForceTurnButtonState(isMicPausedForAnswer ? 'paused' : 'ready')
    } else if (normalized === 'reconnecting') {
      setVoiceStatus('connecting', 'LiveKit is reconnecting the session.')
      setForceTurnButtonState('disabled')
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
      isMicPausedForAnswer = false
      setForceTurnButtonState('disabled')
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
      resumeMic('Zenith finished speaking. Mic reopened for your next command.').catch((error) => {
        console.error('Mic resume after speech failed:', error)
      })
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

    if (isMicPausedForAnswer) {
      setVoiceStatus('thinking', 'Mic is paused. Waiting for Zenith to answer.')
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
    isConnecting = false
    isMicPausedForAnswer = false
    setForceTurnButtonState('disabled')
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
    isUser ? 'Your speech is being transcribed in real time.' : 'Zenith response transcript updated.',
    { persist: false }
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
    if (isMicPausedForAnswer) {
      setLastVoiceEvent('Final speech captured. Zenith is preparing the answer.')
    }
    setVoiceStatus('thinking', 'Command captured. Zenith is preparing a reply.')
  } else {
    isMicPausedForAnswer = false
    setForceTurnButtonState('disabled')
    setVoiceStatus('speaking', 'Zenith is voicing the response now.')
  }
}

function clearAttachedAudio() {
  window.clearTimeout(answerTimeout)
  answerTimeout = null
  isMicPausedForAnswer = false
  setForceTurnButtonState('disabled')
  document.querySelectorAll('[data-zenith-audio="true"]').forEach((element) => {
    element.remove()
  })
}

async function disconnectVoice() {
  voiceSessionId += 1
  const activeRoom = room
  isConnected = false
  isConnecting = false

  if (activeRoom) {
    try {
      await activeRoom.localParticipant.setMicrophoneEnabled(false)
    } catch {
      // Ignore mic shutdown failures while the room is already closing.
    }
    await activeRoom.disconnect()
  }

  clearAttachedAudio()
  setMicButtonState(false)
  setVoiceConnectionState('offline')
  setVoiceStatus('idle', 'Voice session ended. Press start voice to reconnect Zenith.')
  setVoiceRoom('Awaiting session')
  setLastVoiceEvent('Voice session ended by the user.')
  addVoiceHistory('Session ended', 'Voice session closed manually from the control deck.')
  room = null
}
