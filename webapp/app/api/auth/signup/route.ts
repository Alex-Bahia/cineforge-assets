import { NextRequest, NextResponse } from "next/server"
import Stripe from "stripe"

const PLAN_PRICE_IDS: Record<string, string> = {
  starter: process.env.STRIPE_PRICE_STARTER ?? "",
  pro: process.env.STRIPE_PRICE_PRO ?? "",
  agency: process.env.STRIPE_PRICE_AGENCY ?? "",
}

export async function POST(req: NextRequest) {
  const { name, email, password, plan } = await req.json()

  if (!name || !email || !password) {
    return NextResponse.json({ error: "Todos os campos são obrigatórios." }, { status: 400 })
  }
  if (password.length < 8) {
    return NextResponse.json({ error: "A senha deve ter no mínimo 8 caracteres." }, { status: 400 })
  }

  // TODO: criar usuário no banco de dados

  const stripeKey = process.env.STRIPE_SECRET_KEY
  if (!stripeKey) {
    // Sem Stripe configurado: redirecionar direto ao dashboard (modo dev)
    return NextResponse.json({ ok: true })
  }

  const priceId = PLAN_PRICE_IDS[plan]
  if (!priceId) {
    return NextResponse.json({ error: "Plano inválido." }, { status: 400 })
  }

  const stripe = new Stripe(stripeKey)
  const appUrl = process.env.NEXT_PUBLIC_APP_URL ?? "http://localhost:3000"

  const session = await stripe.checkout.sessions.create({
    mode: "subscription",
    customer_email: email,
    line_items: [{ price: priceId, quantity: 1 }],
    subscription_data: { trial_period_days: 7 },
    success_url: `${appUrl}/dashboard?session_id={CHECKOUT_SESSION_ID}`,
    cancel_url: `${appUrl}/signup?plan=${plan}&canceled=true`,
    metadata: { name, plan },
  })

  return NextResponse.json({ checkoutUrl: session.url })
}
