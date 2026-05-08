<template>
  <main class="page-shell">
    <section class="hero-panel">
      <div class="hero-panel__content">
        <p class="eyebrow">Vue 3 + Vite Publisher</p>
        <h1>瀏覽器攝影機送流到 Python 後端</h1>
        <p class="hero-copy">
          這個頁面會呼叫 <code>getUserMedia()</code> 擷取本地攝影機，建立 WebRTC offer，
          並送到 FastAPI 的 <code>/api/webrtc/offer</code>。
        </p>
        <div class="action-row">
          <button class="button button--primary" :disabled="isPublishing" @click="startPublishing">
            開始送流
          </button>
          <button class="button button--secondary" :disabled="!isPublishing" @click="stopPublishing">
            停止送流
          </button>
        </div>
      </div>
      <div class="status-panel">
        <div class="status-chip" :data-state="status">
          <span class="status-chip__dot"></span>
          {{ statusLabel }}
        </div>
        <dl class="status-grid">
          <div>
            <dt>Peer State</dt>
            <dd>{{ connectionState }}</dd>
          </div>
          <div>
            <dt>Backend Health</dt>
            <dd>{{ backendHealthText }}</dd>
          </div>
        </dl>
        <p v-if="status !== 'error'" class="status-copy">{{ statusMessage }}</p>
        <p v-if="errorMessage" class="error-banner">{{ errorMessage }}</p>
      </div>
    </section>

    <section class="content-grid">
      <LocalPreview
        :connection-state="connectionState"
        :stream="localStream"
        @ready="setLocalVideoElement"
      />

      <section class="guide-card">
        <p class="eyebrow">Manual Steps</p>
        <h2>驗證順序</h2>
        <ol>
          <li>先啟動 <code>backend.app:app</code>。</li>
          <li>打開此頁，允許瀏覽器攝影機權限。</li>
          <li>點擊「開始送流」，等待連線狀態變成 connected。</li>
          <li>觀察後端 log 是否開始接收 frame。</li>
        </ol>
        <p class="guide-note">
          第一版只做單向 video publisher，不包含 audio、裝置切換或遠端回放。
        </p>
      </section>
    </section>
  </main>
</template>

<script setup>
import { computed } from 'vue'

import LocalPreview from '../components/LocalPreview.vue'
import { useWebRtcPublisher } from '../composables/useWebRtcPublisher'

const {
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
} = useWebRtcPublisher()

const statusLabel = computed(() => {
  switch (status.value) {
    case 'checking-backend':
      return 'Checking Backend'
    case 'requesting-permission':
      return 'Requesting Camera'
    case 'creating-offer':
      return 'Creating Offer'
    case 'connecting':
      return 'Connecting'
    case 'connected':
      return 'Connected'
    case 'stopping':
      return 'Stopping'
    case 'error':
      return 'Error'
    default:
      return 'Idle'
  }
})

const backendHealthText = computed(() => {
  if (!backendHealth.value) {
    return 'unknown'
  }

  return `${backendHealth.value.status} / activePeers=${backendHealth.value.activePeers}`
})
</script>