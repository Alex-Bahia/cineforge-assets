import { useState, useEffect, useCallback, useRef } from "react"

const API = import.meta.env.VITE_API_URL ?? "/api"

interface BackendState {
  online: boolean
  jobs: number
  queued: number
  channels: number
  providers: ProviderStatus[]
  lastUpdate: number
}

interface ProviderStatus {
  name: string
  status: "online" | "offline" | "degraded"
  latency_ms?: number
}

const INITIAL: BackendState = {
  online: false,
  jobs: 0,
  queued: 0,
  channels: 0,
  providers: [],
  lastUpdate: 0,
}

async function safeFetch<T>(url: string): Promise<T | null> {
  try {
    const r = await fetch(url, { signal: AbortSignal.timeout(4000) })
    if (!r.ok) return null
    return r.json() as Promise<T>
  } catch {
    return null
  }
}

export function useBackend(pollMs = 15000) {
  const [state, setState] = useState<BackendState>(INITIAL)
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  const refresh = useCallback(async () => {
    const [health, stats, providers] = await Promise.all([
      safeFetch<{ status: string }>(`${API}/health`),
      safeFetch<{ total_jobs: number; queued: number; channels: number }>(`${API}/queue/stats`),
      safeFetch<ProviderStatus[]>(`${API}/providers`),
    ])

    setState({
      online: health?.status === "ok",
      jobs: stats?.total_jobs ?? 0,
      queued: stats?.queued ?? 0,
      channels: stats?.channels ?? 0,
      providers: providers ?? [],
      lastUpdate: Date.now(),
    })
  }, [])

  useEffect(() => {
    refresh()
    timerRef.current = setInterval(refresh, pollMs)
    return () => {
      if (timerRef.current) clearInterval(timerRef.current)
    }
  }, [refresh, pollMs])

  return { ...state, refresh }
}
