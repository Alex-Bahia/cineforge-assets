import { createContext, useContext, useState, useEffect, ReactNode } from 'react'

const VPS_HOST = 'http://167.234.255.202:8765'

export interface User {
  id: string
  name: string
  email: string
  plan: string
  plan_info: {
    name: string
    price_brl: number
    videos_per_month: number
    ai_images: boolean
    voice_cloning: boolean
    deploy_platforms: string[]
  }
  videos_used_this_month: number
}

interface AuthContextType {
  user: User | null
  token: string | null
  loading: boolean
  login: (email: string, password: string) => Promise<void>
  register: (name: string, email: string, password: string, plan: string) => Promise<void>
  logout: () => void
  upgradePlan: (plan: string) => Promise<void>
}

const AuthContext = createContext<AuthContextType | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [token, setToken] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const saved = localStorage.getItem('cf_token')
    if (saved) {
      setToken(saved)
      fetchMe(saved)
    } else {
      setLoading(false)
    }
  }, [])

  async function fetchMe(tok: string) {
    try {
      const res = await fetch(`${VPS_HOST}/auth/me`, {
        headers: { Authorization: `Bearer ${tok}` },
      })
      if (res.ok) {
        const data = await res.json()
        setUser(data)
      } else {
        localStorage.removeItem('cf_token')
        setToken(null)
      }
    } catch {
      // VPS offline — mantém token para retry posterior
    } finally {
      setLoading(false)
    }
  }

  async function login(email: string, password: string) {
    const body = new URLSearchParams({ username: email, password })
    const res = await fetch(`${VPS_HOST}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body,
    })
    if (!res.ok) {
      const err = await res.json()
      throw new Error(err.detail || 'Erro ao fazer login.')
    }
    const data = await res.json()
    setToken(data.access_token)
    setUser(data.user)
    localStorage.setItem('cf_token', data.access_token)
  }

  async function register(name: string, email: string, password: string, plan: string) {
    const res = await fetch(`${VPS_HOST}/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, email, password, plan }),
    })
    if (!res.ok) {
      const err = await res.json()
      throw new Error(err.detail || 'Erro ao cadastrar.')
    }
    const data = await res.json()
    setToken(data.access_token)
    setUser(data.user)
    localStorage.setItem('cf_token', data.access_token)
  }

  function logout() {
    setUser(null)
    setToken(null)
    localStorage.removeItem('cf_token')
  }

  async function upgradePlan(plan: string) {
    if (!token) throw new Error('Não autenticado.')
    const res = await fetch(`${VPS_HOST}/auth/upgrade`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({ plan }),
    })
    if (!res.ok) {
      const err = await res.json()
      throw new Error(err.detail || 'Erro ao atualizar plano.')
    }
    if (token) fetchMe(token)
  }

  return (
    <AuthContext.Provider value={{ user, token, loading, login, register, logout, upgradePlan }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth fora do AuthProvider')
  return ctx
}
