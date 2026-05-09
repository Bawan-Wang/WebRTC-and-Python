import { computed, onBeforeUnmount, ref, shallowRef } from 'vue'

import { createWebRtcAnswer, fetchBackendHealth } from '../api/webrtc'
import { createRtcConfiguration } from '../config/runtime'

function createStatusMessage(status, errorMessage) {
  if (status === 'error' && errorMessage) {
    return errorMessage
  }

  switch (status) {
    case 'checking-backend':
      return '正在檢查後端狀態。'
    case 'requesting-permission':
      return '正在請求攝影機權限。'
    case 'creating-offer':
      return '正在建立 WebRTC offer。'
    case 'connecting':
      return '正在等待後端 answer。'
    case 'connected':
      return '送流已建立。'
    case 'stopping':
      return '正在關閉連線。'
    default:
      return '尚未開始送流。'
  }
}

export function useWebRtcPublisher() {
  const status = ref('idle')
  const errorMessage = ref('')
  const localStream = shallowRef(null)
  const localVideoElement = shallowRef(null)
  const peerConnection = shallowRef(null)
  const connectionState = ref('new')
  const backendHealth = shallowRef(null)

  const isPublishing = computed(() => {
    return ['requesting-permission', 'creating-offer', 'connecting', 'connected'].includes(status.value)
  })

  const statusMessage = computed(() => createStatusMessage(status.value, errorMessage.value))

  function attachPreviewStream(stream) {
    if (!localVideoElement.value) {
      return
    }

    localVideoElement.value.srcObject = stream
  }

  function setLocalVideoElement(element) {
    localVideoElement.value = element
    if (localStream.value) {
      attachPreviewStream(localStream.value)
    }
  }

  async function startPublishing() {
    if (isPublishing.value) {
      return
    }

    errorMessage.value = ''
    status.value = 'checking-backend'

    try {
      backendHealth.value = await fetchBackendHealth()
      status.value = 'requesting-permission'

      const stream = await navigator.mediaDevices.getUserMedia({
        video: true,
        audio: false,
      })

      localStream.value = stream
      attachPreviewStream(stream)

      status.value = 'creating-offer'
      const pc = new RTCPeerConnection(createRtcConfiguration())
      peerConnection.value = pc
      connectionState.value = pc.connectionState

      pc.addEventListener('connectionstatechange', () => {
        connectionState.value = pc.connectionState

        if (pc.connectionState === 'connected') {
          status.value = 'connected'
          return
        }

        if (['failed', 'closed', 'disconnected'].includes(pc.connectionState)) {
          if (status.value !== 'stopping') {
            status.value = 'error'
            errorMessage.value = `Peer connection state changed to ${pc.connectionState}.`
          }
        }
      })

      for (const track of stream.getTracks()) {
        pc.addTrack(track, stream)
      }

      const offer = await pc.createOffer()
      await pc.setLocalDescription(offer)
      await waitForIceGathering(pc)

      if (!pc.localDescription) {
        throw new Error('Failed to create local description.')
      }

      status.value = 'connecting'
      const answer = await createWebRtcAnswer({
        sdp: pc.localDescription.sdp,
        type: pc.localDescription.type,
      })

      await pc.setRemoteDescription(answer)

      if (pc.connectionState === 'connected') {
        status.value = 'connected'
      }
    } catch (error) {
      await stopPublishing({ preserveError: true })
      status.value = 'error'
      errorMessage.value = normalizeErrorMessage(error)
    }
  }

  async function stopPublishing(options = {}) {
    const preserveError = options.preserveError ?? false

    if (status.value !== 'idle') {
      status.value = 'stopping'
    }

    const pc = peerConnection.value
    peerConnection.value = null

    if (pc) {
      pc.getSenders().forEach((sender) => {
        sender.track?.stop()
      })
      pc.close()
    }

    if (localStream.value) {
      localStream.value.getTracks().forEach((track) => track.stop())
      localStream.value = null
    }

    if (localVideoElement.value) {
      localVideoElement.value.srcObject = null
    }

    connectionState.value = 'closed'

    if (!preserveError) {
      errorMessage.value = ''
    }

    status.value = preserveError ? 'error' : 'idle'
  }

  onBeforeUnmount(() => {
    void stopPublishing()
  })

  return {
    backendHealth,
    connectionState,
    errorMessage,
    isPublishing,
    localStream,
    setLocalVideoElement,
    startPublishing,
    status,
    statusMessage,
    stopPublishing,
  }
}

async function waitForIceGathering(pc) {
  if (pc.iceGatheringState === 'complete') {
    return
  }

  await new Promise((resolve) => {
    const onIceGatheringStateChange = () => {
      if (pc.iceGatheringState === 'complete') {
        pc.removeEventListener('icegatheringstatechange', onIceGatheringStateChange)
        resolve()
      }
    }

    pc.addEventListener('icegatheringstatechange', onIceGatheringStateChange)
  })
}

function normalizeErrorMessage(error) {
  if (error instanceof Error && error.message) {
    return error.message
  }

  return '發生未知錯誤。'
}