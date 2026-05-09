import { runtimeConfig } from '../config/runtime'

export async function createWebRtcAnswer(offer, options = {}) {
  const baseUrl = options.baseUrl ?? runtimeConfig.apiBaseUrl
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
  const baseUrl = options.baseUrl ?? runtimeConfig.apiBaseUrl
  let response

  try {
    response = await fetch(`${baseUrl}/health`)
  } catch (error) {
    throw new Error('Backend health check failed. Verify backend.app is running and reachable.')
  }

  const body = await response.json().catch(() => null)

  if (!response.ok) {
    throw new Error(
      `Backend health check failed (${response.status}). Verify backend.app is running and reachable.`,
    )
  }

  return body
}