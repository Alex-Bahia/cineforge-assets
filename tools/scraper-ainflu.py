"""
Scraper/interceptor para ainflu.ai
Roda via: python tools/scraper-ainflu.py

Captura:
  - Todas as chamadas de API (XHR/fetch)
  - Rotas/páginas do app
  - Tokens de autenticação (headers)
  - Estrutura do HTML de cada página
  - Endpoints do backend inferidos dos JS bundles

Requisitos: playwright, httpx
  pip install playwright httpx
  playwright install chromium
"""

import asyncio
import json
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

from playwright.async_api import async_playwright

BASE_URL = "https://ainflu.ai"
OUTPUT_DIR = Path("tools/ainflu_output")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Rotas a visitar (ajuste se precisar de login)
PAGES_TO_VISIT = [
    "/",
    "/pricing",
    "/features",
    "/about",
    "/blog",
    "/login",
    "/register",
    "/dashboard",
    "/app",
]

captured_requests = []
captured_responses = []
js_api_endpoints = set()


def extract_api_patterns(js_text: str) -> list[str]:
    """Extrai endpoints de API de JS minificado."""
    patterns = [
        r'["\'](/api/[^"\']+)["\']',
        r'["\'](https?://[^"\']+/api/[^"\']+)["\']',
        r'fetch\(["\']([^"\']+)["\']',
        r'axios\.[a-z]+\(["\']([^"\']+)["\']',
        r'baseURL[:\s=]+["\']([^"\']+)["\']',
        r'API_URL[:\s=]+["\']([^"\']+)["\']',
        r'NEXT_PUBLIC_[A-Z_]+[:\s=]+["\']([^"\']+)["\']',
        r'VITE_[A-Z_]+[:\s=]+["\']([^"\']+)["\']',
    ]
    found = []
    for pattern in patterns:
        found.extend(re.findall(pattern, js_text))
    return found


async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            executable_path="/opt/pw-browsers/chromium",  # VPS: remova esta linha
        )
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            viewport={"width": 1920, "height": 1080},
        )

        # Interceptar todas as requisições
        async def on_request(request):
            if any(x in request.url for x in [".png", ".jpg", ".ico", ".woff", ".svg"]):
                return
            entry = {
                "url": request.url,
                "method": request.method,
                "headers": dict(request.headers),
                "post_data": request.post_data,
                "resource_type": request.resource_type,
            }
            captured_requests.append(entry)

            # Detectar chamadas de API
            if request.resource_type in ("xhr", "fetch"):
                print(f"  [API] {request.method} {request.url}")

        async def on_response(response):
            if response.request.resource_type in ("xhr", "fetch"):
                try:
                    body = await response.json()
                    entry = {
                        "url": response.url,
                        "status": response.status,
                        "headers": dict(response.headers),
                        "body": body,
                    }
                    captured_responses.append(entry)
                except Exception:
                    pass

            # Extrair endpoints de arquivos JS
            if response.request.resource_type == "script":
                try:
                    text = await response.text()
                    found = extract_api_patterns(text)
                    js_api_endpoints.update(found)
                except Exception:
                    pass

        page = await context.new_page()
        page.on("request", on_request)
        page.on("response", on_response)

        pages_data = {}

        for route in PAGES_TO_VISIT:
            url = BASE_URL + route
            print(f"\n[>] Visitando: {url}")
            try:
                await page.goto(url, wait_until="networkidle", timeout=30000)
                await page.wait_for_timeout(2000)

                # Screenshot
                screenshot_path = OUTPUT_DIR / f"page{route.replace('/', '_') or '_home'}.png"
                await page.screenshot(path=str(screenshot_path), full_page=True)

                # HTML da página
                html = await page.content()
                html_path = OUTPUT_DIR / f"page{route.replace('/', '_') or '_home'}.html"
                html_path.write_text(html, encoding="utf-8")

                # Links internos
                links = await page.eval_on_selector_all(
                    "a[href]",
                    "els => els.map(e => e.href)"
                )
                internal_links = [l for l in links if BASE_URL in l]

                # Textos visíveis (h1, h2, p)
                texts = await page.eval_on_selector_all(
                    "h1, h2, h3, p, button, [class*='price'], [class*='plan']",
                    "els => els.map(e => e.innerText.trim()).filter(t => t.length > 3)"
                )

                pages_data[route] = {
                    "url": url,
                    "final_url": page.url,
                    "internal_links": internal_links[:30],
                    "text_content": texts[:50],
                }
                print(f"  [OK] {len(texts)} elementos de texto, {len(internal_links)} links internos")

            except Exception as e:
                print(f"  [ERRO] {e}")
                pages_data[route] = {"error": str(e)}

        await browser.close()

        # ── Consolidar resultados ──────────────────────────────────────────────

        # APIs chamadas (XHR/fetch)
        api_calls = [r for r in captured_requests if r["resource_type"] in ("xhr", "fetch")]
        unique_api_endpoints = list({r["url"] for r in api_calls})

        # Domínios externos detectados
        all_urls = [r["url"] for r in captured_requests]
        external_domains = set()
        for url in all_urls:
            parsed = urlparse(url)
            if parsed.netloc and BASE_URL.split("//")[1] not in parsed.netloc:
                external_domains.add(parsed.scheme + "://" + parsed.netloc)

        report = {
            "target": BASE_URL,
            "pages_visited": pages_data,
            "api_calls": {
                "total_requests": len(captured_requests),
                "api_xhr_fetch": len(api_calls),
                "unique_endpoints": sorted(unique_api_endpoints),
                "endpoints_from_js": sorted(js_api_endpoints),
            },
            "external_services": sorted(external_domains),
            "auth_hints": {
                "cookies": [],  # preencher via page.context.cookies()
                "auth_headers": [
                    r["headers"].get("authorization", "")
                    for r in captured_requests
                    if r["headers"].get("authorization")
                ][:5],
            },
            "api_responses_sample": captured_responses[:20],
        }

        out_file = OUTPUT_DIR / "report.json"
        out_file.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"\n[✓] Relatório salvo em: {out_file}")

        # Resumo no terminal
        print("\n" + "=" * 60)
        print("RESUMO")
        print("=" * 60)
        print(f"Páginas visitadas : {len(pages_data)}")
        print(f"Requisições totais: {len(captured_requests)}")
        print(f"Chamadas de API   : {len(api_calls)}")
        print(f"Endpoints únicos  : {len(unique_api_endpoints)}")
        print(f"Endpoints via JS  : {len(js_api_endpoints)}")
        print(f"Serviços externos : {len(external_domains)}")

        if unique_api_endpoints:
            print("\nENDPOINTS DE API DETECTADOS:")
            for ep in sorted(unique_api_endpoints)[:20]:
                print(f"  {ep}")

        if external_domains:
            print("\nSERVIÇOS EXTERNOS (stack tecnológico):")
            for d in sorted(external_domains):
                print(f"  {d}")


if __name__ == "__main__":
    asyncio.run(run())
