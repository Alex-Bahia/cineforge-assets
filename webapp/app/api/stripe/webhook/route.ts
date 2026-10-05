import { NextRequest, NextResponse } from "next/server"
import type Stripe from "stripe"
import StripeLib from "stripe"

export async function POST(req: NextRequest) {
  const stripeKey = process.env.STRIPE_SECRET_KEY
  const webhookSecret = process.env.STRIPE_WEBHOOK_SECRET

  if (!stripeKey || !webhookSecret) {
    return NextResponse.json({ error: "Stripe não configurado." }, { status: 500 })
  }

  const stripe = new StripeLib(stripeKey)
  const sig = req.headers.get("stripe-signature")
  if (!sig) {
    return NextResponse.json({ error: "Assinatura ausente." }, { status: 400 })
  }

  let event: Stripe.Event
  const body = await req.text()

  try {
    event = stripe.webhooks.constructEvent(body, sig, webhookSecret)
  } catch {
    return NextResponse.json({ error: "Assinatura inválida." }, { status: 400 })
  }

  switch (event.type) {
    case "checkout.session.completed": {
      // TODO: ativar conta do usuário com plano comprado
      const csSession = event.data.object
      console.log("Checkout completo:", csSession)
      break
    }
    case "customer.subscription.deleted": {
      // TODO: desativar acesso do cliente
      const sub = event.data.object
      console.log("Assinatura cancelada:", sub)
      break
    }
    case "invoice.payment_failed": {
      // TODO: notificar cliente sobre falha no pagamento
      const invoice = event.data.object
      console.log("Pagamento falhou:", invoice)
      break
    }
  }

  return NextResponse.json({ received: true })
}
