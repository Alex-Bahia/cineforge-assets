import { NextRequest, NextResponse } from "next/server"
import { cookies } from "next/headers"

export async function POST(req: NextRequest) {
  const { email, password } = await req.json()

  if (!email || !password) {
    return NextResponse.json({ error: "E-mail e senha são obrigatórios." }, { status: 400 })
  }

  // TODO: substituir por autenticação real com banco de dados
  // Por enquanto, aceita qualquer login válido para demo
  if (password.length < 8) {
    return NextResponse.json({ error: "Credenciais inválidas." }, { status: 401 })
  }

  const cookieStore = await cookies()
  cookieStore.set("cineforge_session", Buffer.from(`${email}:demo`).toString("base64"), {
    httpOnly: true,
    secure: process.env.NODE_ENV === "production",
    sameSite: "lax",
    maxAge: 60 * 60 * 24 * 7, // 7 dias
    path: "/",
  })

  return NextResponse.json({ ok: true })
}
