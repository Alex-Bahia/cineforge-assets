/**
 * Cliente da API CineForge — usa o proxy Next.js /api/backend/*
 * Substitua BASE_PATH por "" para chamar o FastAPI diretamente (ex: mobile).
 */
const BASE_PATH = "/api/backend"

async function request<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const res = await fetch(`${BASE_PATH}${path}`, {
    headers: { "Content-Type": "application/json", ...options.headers },
    ...options,
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ error: res.statusText }))
    throw new Error(err.error ?? err.detail ?? res.statusText)
  }
  return res.json()
}

// ─── Health ─────────────────────────────────────────────────────────────────
export const getHealth = () => request<{ ok: boolean; version: string }>("/health")

// ─── Jobs ────────────────────────────────────────────────────────────────────
export interface Job {
  job_id: string
  topic: string
  niche: string
  status: "pending" | "running" | "done" | "failed" | "retry"
  channel_id: string
  created_at: number
  started_at: number | null
  finished_at: number | null
  output_path: string | null
  error: string | null
  attempts: number
  priority: number
  opportunity_score: number
  estimated_cost_usd: number
}

export const listJobs = (params?: { status?: string; niche?: string; limit?: number }) => {
  const qs = new URLSearchParams(params as Record<string, string>).toString()
  return request<{ jobs: Job[]; total: number }>(`/jobs${qs ? "?" + qs : ""}`)
}

export const createJob = (body: {
  topic?: string
  niche?: string
  language?: string
  market?: string
  channel_id?: string
  duration_min?: number
  video_provider?: string
  priority?: number
}) => request<{ ok: boolean; job_id: string; job: Job }>("/jobs", { method: "POST", body: JSON.stringify(body) })

export const cancelJob = (jobId: string) =>
  request<{ ok: boolean }>(`/jobs/${jobId}`, { method: "DELETE" })

export const getQueueStats = () => request<{ pending: number; running: number; done: number; failed: number; jobs: Job[] }>("/queue/stats")

// ─── Channels ────────────────────────────────────────────────────────────────
export interface Channel {
  channel_id: string
  source: "file" | "env"
  config_file?: string
}

export const listChannels = () => request<{ channels: Channel[]; total: number }>("/channels")

export const getChannelQuota = (channelId: string) =>
  request<{ channel_id: string; used_today: number; remaining_today: number; can_upload: boolean; daily_limit: number }>(`/channels/${channelId}/quota`)

// ─── Scan ────────────────────────────────────────────────────────────────────
export const scanOpportunities = (niche: string, limit = 5) =>
  request<{ ok: boolean; topics: string[]; jobs_created: number }>("/scan", {
    method: "POST",
    body: JSON.stringify({ niche, limit }),
  })

// ─── Downloader ──────────────────────────────────────────────────────────────
export const startDownloader = (body: {
  url: string
  niche: string
  min_views?: number
  max_videos?: number
}) => request<{ ok: boolean; task_id: string }>("/downloader/start", { method: "POST", body: JSON.stringify(body) })

export const getDownloaderStatus = (taskId: string) =>
  request<{ status: string; downloaded?: number; error?: string }>(`/downloader/status/${taskId}`)

export interface EditModel {
  niche: string
  source_videos: number
  avg_scene_duration_sec: number
  scenes_per_minute: number
  hook_duration_sec: number
  speech_pct: number
  has_bgm: boolean
}

export const listEditModels = () => request<{ models: EditModel[] }>("/downloader/models")

// ─── Niche Strategist ────────────────────────────────────────────────────────
export interface NicheOpportunity {
  keyword: string
  scores: { search_volume: number; competition: number; opportunity: number }
  cpm_estimate: number
  opportunity_score: number
  monetization_options: string[]
}

export const getNicheOpportunities = (niche = "finance_dark", market = "US", limit = 10) =>
  request<{ niche: string; market: string; opportunities: NicheOpportunity[] }>(
    `/niche/opportunities?niche=${niche}&market=${market}&limit=${limit}`
  )

export const auditCtr = (body: { ctr_estimate: number; avg_view_duration_pct: number; niche: string }) =>
  request<{
    ctr_estimate: number
    ctr_target: number
    avg_view_duration_pct: number
    quadrant: string
    issues: string[]
    recommendations: string[]
    priority_actions: string[]
  }>("/niche/audit", { method: "POST", body: JSON.stringify(body) })

export const generateBrief = (body: { keyword: string; niche: string; market: string; cpm_estimate: number }) =>
  request<Record<string, unknown>>("/niche/brief", { method: "POST", body: JSON.stringify(body) })

export const getWeeklyReport = (niche = "finance_dark", market = "US") =>
  request<{ niche: string; market: string; report: string }>(`/niche/report?niche=${niche}&market=${market}`)

// ─── Providers ───────────────────────────────────────────────────────────────
export interface ProviderStatus {
  available: boolean
  models?: string[]
  error?: string
}

export const getProvidersStatus = () =>
  request<Record<string, ProviderStatus>>("/providers/status")
