<template>
  <section class="preview-card">
    <div class="preview-card__header">
      <div>
        <p class="eyebrow">Local Preview</p>
        <h2>攝影機畫面</h2>
      </div>
      <span class="preview-card__state">{{ connectionState }}</span>
    </div>
    <div class="preview-frame">
      <video ref="videoElement" autoplay muted playsinline></video>
      <div v-if="!hasStream" class="preview-placeholder">
        啟動後會在這裡顯示本地攝影機預覽
      </div>
    </div>
  </section>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'

const props = defineProps({
  connectionState: {
    type: String,
    default: 'new',
  },
  stream: {
    type: Object,
    default: null,
  },
})

const emit = defineEmits(['ready'])

const videoElement = ref(null)
const hasStream = computed(() => Boolean(props.stream))

onMounted(() => {
  if (videoElement.value) {
    emit('ready', videoElement.value)
  }
})

watch(
  () => props.stream,
  (stream) => {
    if (videoElement.value) {
      videoElement.value.srcObject = stream ?? null
    }
  },
  { immediate: true },
)
</script>