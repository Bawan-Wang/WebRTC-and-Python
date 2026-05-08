export async function createWebRtcAnswer(offer, options = {}) {
  const baseUrl = options.baseUrl ?? import.meta.env.VITE_API_BASE_URL ?? ''
  const response = await fetch(`${baseUrl}/api/webrtc/offer`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(offer),
  })

  const body = await response.json().catch(() => null)

  if (!response.ok) {
    const detail = body?.detail
    if (typeof detail === 'string' && detail) {
      throw new Error(detail)
    }

    throw new Error(`Failed to create WebRTC answer (${response.status})`)
  }

  return body
}

export async function fetchBackendHealth(options = {}) {
  const baseUrl = options.baseUrl ?? import.meta.env.VITE_API_BASE_URL ?? ''
  const response = await fetch(`${baseUrl}/health`)
  const body = await response.json().catch(() => null)

  if (!response.ok) {
    throw new Error(`Failed to fetch backend health (${response.status})`)
  }

  return body
}