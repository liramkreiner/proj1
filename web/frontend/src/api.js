// Thin fetch wrappers around the FastAPI backend.
// Every call funnels through `request` so error handling is uniform.

async function request(path, options = {}) {
  let response
  try {
    response = await fetch(path, {
      headers: { 'Content-Type': 'application/json' },
      ...options,
    })
  } catch (networkError) {
    throw new Error(`Network error contacting ${path}: ${networkError.message}`)
  }

  const text = await response.text()
  let body = null
  if (text) {
    try {
      body = JSON.parse(text)
    } catch {
      body = text
    }
  }

  if (!response.ok) {
    const detail =
      body && typeof body === 'object' && 'detail' in body ? body.detail : body || response.statusText
    throw new Error(typeof detail === 'string' ? detail : JSON.stringify(detail))
  }
  return body
}

export const api = {
  config: () => request('/api/config'),
  equilibrium: () => request('/api/equilibrium'),
  analyze: (values) => request('/api/analyze', { method: 'POST', body: JSON.stringify({ values }) }),
  simulate: ({ values = null, games, seed = null }) =>
    request('/api/simulate', { method: 'POST', body: JSON.stringify({ values, games, seed }) }),
  startSession: ({ role, seed = null, values = null, total_rounds = 5 }) =>
    request('/api/sessions', {
      method: 'POST',
      body: JSON.stringify({ role, seed, values, total_rounds }),
    }),
  resetSession: (id) => request(`/api/sessions/${id}/reset`, { method: 'POST' }),
  playTurn: (id, zone) =>
    request(`/api/sessions/${id}/turn`, { method: 'POST', body: JSON.stringify({ zone }) }),
}
