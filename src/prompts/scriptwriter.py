"""Prompt templates for Gemini scriptwriting."""

SYSTEM_PROMPT = """\
Você é um roteirista especialista em canais dark do YouTube brasileiro.
Seu estilo é investigativo, tenso, com narração em primeira pessoa ou terceira pessoa impessoal.
Use linguagem acessível mas impactante. Evite clichês óbvios.
Sempre estruture o vídeo para maximizar retenção: gancho forte + desenvolvimento + plot twist + CTA.
"""

SCRIPT_PROMPT = """\
Crie um roteiro completo para um vídeo YouTube dark de {duration_min} minutos sobre:
**TEMA**: {topic}
**TOM**: {tone}
**PÚBLICO**: Brasileiro adulto, curioso por histórias sombrias, crimes, mistérios ou fenômenos inexplicáveis.

Retorne SOMENTE um JSON válido com este schema exato (sem markdown, sem explicação):
{{
  "titulo": "título chamativo SEO com palavra-chave no início (máx 70 chars)",
  "descricao": "descrição YouTube de 200 palavras com keyword natural, 3 parágrafos",
  "tags": ["tag1", "tag2", "tag3", "...até 15 tags relevantes"],
  "thumbnail_text": "texto impactante para thumbnail (máx 5 palavras, caps)",
  "gancho_inicial": "frase de abertura impactante para os primeiros 5 segundos",
  "duracao_estimada_segundos": 0,
  "cenas": [
    {{
      "id": 1,
      "texto_narracao": "texto completo que será narrado nesta cena",
      "prompt_visual": "descrição em inglês para buscar imagem/vídeo no Pexels/Pixabay (seja específico: dark forest at night, abandoned building interior, etc.)",
      "duracao_segundos": 6,
      "emocao": "suspense|medo|curiosidade|choque|tristeza|raiva",
      "texto_legenda_destaque": "palavra ou frase de impacto para mostrar na tela (opcional)"
    }}
  ]
}}

Requisitos obrigatórios:
- Primeira cena = gancho (máx 8 segundos, pergunta ou afirmação chocante)
- Troca de imagem a cada 4-6 segundos para manter retenção
- Mínimo de {min_scenes} cenas, máximo de {max_scenes} cenas
- Última cena = CTA pedindo like, inscrição e comentário
- prompt_visual SEMPRE em inglês, específico e visual
- duracao_estimada_segundos = soma de todos os duracao_segundos das cenas
"""

TITLE_VARIANTS_PROMPT = """\
Gere 5 variações de títulos alternativos para o vídeo sobre "{topic}".
Cada título deve ter ângulo diferente (curiosidade, medo, revelação, polêmica, pessoal).
Retorne apenas JSON: {{"titulos": ["título1", "título2", ...]}}
"""

THUMBNAIL_PROMPT = """\
Descreva em inglês um prompt detalhado para gerar a thumbnail do vídeo "{title}".
A thumbnail deve ser: dramática, alto contraste, com face expressiva ou símbolo visual forte.
Retorne apenas JSON: {{"prompt_thumbnail": "descrição detalhada em inglês"}}
"""
