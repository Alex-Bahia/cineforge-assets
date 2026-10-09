/**
 * Proxy transparente: /api/backend/* → CINEFORGE_API_URL/api/*
 *
 * Todos os métodos (GET, POST, PUT, DELETE) são repassados com body e headers.
 * O Next.js não precisa saber nada dos endpoints — é um pass-through.
 */
import { NextRequest, NextResponse } from "next/server"

const BACKEND = process.env.CINEFORGE_API_URL ?? "http://localhost:8765"

async function proxy(req: NextRequest, { params }: { params: Promise<{ path: string[] }> }) {
  const { path } = await params
  const targetPath = "/api/" + path.join("/")
  const url = new URL(req.url)
  const target = `${BACKEND}${targetPath}${url.search}`

  const headers = new Headers()
  headers.set("Content-Type", req.headers.get("Content-Type") ?? "application/json")
  headers.set("Accept", "application/json")

  const init: RequestInit = { method: req.method, headers }
  if (req.method !== "GET" && req.method !== "HEAD") {
    init.body = await req.text()
  }

  try {
    const res = await fetch(target, init)
    const body = await res.text()
    return new NextResponse(body, {
      status: res.status,
      headers: { "Content-Type": res.headers.get("Content-Type") ?? "application/json" },
    })
  } catch (err) {
    return NextResponse.json(
      { error: "Backend CineForge indisponível. Verifique se o servidor Python está rodando.", detail: String(err) },
      { status: 503 }
    )
  }
}

export { proxy as GET, proxy as POST, proxy as PUT, proxy as DELETE, proxy as PATCH }
