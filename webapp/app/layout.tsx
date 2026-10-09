import type { Metadata } from "next"
import { Geist, Geist_Mono } from "next/font/google"
import "./globals.css"

const geistSans = Geist({ variable: "--font-geist-sans", subsets: ["latin"] })
const geistMono = Geist_Mono({ variable: "--font-geist-mono", subsets: ["latin"] })

export const metadata: Metadata = {
  title: "CineForge — Fábrica de Vídeos Virais com IA",
  description: "Gere canais do YouTube lucrativos com vídeos produzidos por IA. Nichos de alto CPM, narrativa 2ª pessoa, upload automático.",
  keywords: ["youtube automação", "vídeos IA", "canal youtube", "fal.ai", "veo3", "monetização youtube"],
  openGraph: {
    title: "CineForge — Fábrica de Vídeos Virais com IA",
    description: "Automatize sua produção de vídeos do YouTube com IA de ponta.",
    type: "website",
  },
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="pt-BR" className={`${geistSans.variable} ${geistMono.variable}`}>
      <body className="antialiased">{children}</body>
    </html>
  )
}
