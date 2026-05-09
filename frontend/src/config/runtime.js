function normalizeString(value) {
  return typeof value === 'string' ? value.trim() : ''
}

function parseIceServers(rawValue) {
  const normalized = normalizeString(rawValue)
  if (!normalized) {
    return []
  }

  if (normalized.startsWith('[')) {
    const payload = JSON.parse(normalized)
    if (!Array.isArray(payload)) {
      throw new Error('VITE_WEBRTC_ICE_SERVERS must be a JSON array.')
    }

    return payload.map(normalizeIceServer)
  }

  return normalized
    .split(',')
    .map((url) => url.trim())
    .filter(Boolean)
    .map((url) => ({ urls: url }))
}

function normalizeIceServer(server) {
  if (typeof server === 'string') {
    return { urls: server }
  }

  if (!server || typeof server !== 'object') {
    throw new Error('VITE_WEBRTC_ICE_SERVERS entries must be strings or objects.')
  }

  const { urls, username, credential } = server
  const urlsAreValid =
    typeof urls === 'string' ||
    (Array.isArray(urls) && urls.length > 0 && urls.every((value) => typeof value === 'string'))

  if (!urlsAreValid) {
    throw new Error('VITE_WEBRTC_ICE_SERVERS entries must include a string or string[] urls field.')
  }

  const normalized = { urls }

  if (typeof username === 'string' && username) {
    normalized.username = username
  }

  if (typeof credential === 'string' && credential) {
    normalized.credential = credential
  }

  return normalized
}

function cloneIceServers(iceServers) {
  return iceServers.map((server) => ({
    ...server,
    urls: Array.isArray(server.urls) ? [...server.urls] : server.urls,
  }))
}

export const runtimeConfig = {
  apiBaseUrl: normalizeString(import.meta.env.VITE_API_BASE_URL),
  iceServers: parseIceServers(import.meta.env.VITE_WEBRTC_ICE_SERVERS),
}

export function createRtcConfiguration() {
  return {
    iceServers: cloneIceServers(runtimeConfig.iceServers),
  }
}