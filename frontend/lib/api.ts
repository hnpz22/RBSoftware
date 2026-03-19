import type { ApiError } from './types'

const BASE = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000'

async function request<T>(path: string, init: RequestInit = {}, retry = true): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    credentials: 'include',
    headers: {
      'Content-Type': 'application/json',
      ...init.headers,
    },
    ...init,
  })

  if (res.status === 401 && retry) {
    const refreshRes = await fetch(`${BASE}/auth/refresh`, {
      method: 'POST',
      credentials: 'include',
    })

    if (refreshRes.ok) {
      return request<T>(path, init, false)
    }

    if (typeof window !== 'undefined' && window.location.pathname !== '/login') {
      window.location.href = '/login'
      return new Promise<T>(() => {})
    }

    const err: ApiError = { status: 401, detail: 'Unauthorized' }
    throw err
  }

  if (!res.ok) {
    let detail = res.statusText
    try {
      const body = await res.json()
      detail = body.detail ?? detail
    } catch {}
    const err: ApiError = { status: res.status, detail }
    throw err
  }

  if (res.status === 204) return undefined as T
  return res.json() as Promise<T>
}

export const api = {
  get: <T>(path: string) => request<T>(path),
  post: <T>(path: string, body?: unknown) =>
    request<T>(path, {
      method: 'POST',
      body: body !== undefined ? JSON.stringify(body) : undefined,
    }),
  patch: <T>(path: string, body?: unknown) =>
    request<T>(path, {
      method: 'PATCH',
      body: body !== undefined ? JSON.stringify(body) : undefined,
    }),
  delete: <T>(path: string) => request<T>(path, { method: 'DELETE' }),
  /** Raw fetch — use for binary responses (PDF, etc.). Caller must handle errors. */
  getRaw: (path: string) => fetch(`${BASE}${path}`, { credentials: 'include' }),
}
