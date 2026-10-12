"""
CineForge API Server — FastAPI backend para a VPS Hermes (porta 8765).

Expõe os endpoints chamados pelo cockpit React em iai-studios/.
Autenticação JWT integrada (cadastro, login, verificação de plano).

Instalar dependências:
    pip install fastapi uvicorn python-jose[cryptography] passlib[bcrypt] \
                python-multipart sqlitedict

Rodar:
    uvicorn api_server:app --host 0.0.0.0 --port 8765 --reload
"""

from __future__ import annotations

import asyncio
import os
import sys
import uuid
import json
import time
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr

# ── Dependências opcionais ────────────────────────────────────────────────────
try:
    from jose import JWTError, jwt
    _JWT_OK = True
except ImportError:
    _JWT_OK = False
    print("⚠️  python-jose não instalado. Auth desabilitado.")

try:
    from passlib.context import CryptContext
    _BCRYPT_OK = True
except ImportError:
    _BCRYPT_OK = False

try:
    from sqlitedict import SqliteDict
    _DB_OK = True
except ImportError:
    _DB_OK = False
    print("⚠️  sqlitedict não instalado. Usando dict em memória (não persiste).")

# ── Configuração ──────────────────────────────────────────────────────────────
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "TROQUE_ESTA_CHAVE_EM_PRODUCAO_agora123")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24h

JOBS_DIR = Path(os.getenv("JOBS_DIR", "output/jobs"))
JOBS_DIR.mkdir(parents=True, exist_ok=True)

DB_PATH = os.getenv("DB_PATH", "cineforge_users.db")

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("cineforge.api")

# ── App FastAPI ───────────────────────────────────────────────────────────────
app = FastAPI(title="CineForge API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # restrinja em produção ao domínio do cockpit
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Segurança ─────────────────────────────────────────────────────────────────
pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto") if _BCRYPT_OK else None
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)

# ── Banco de dados (SQLite via sqlitedict, ou dict em memória) ────────────────
if _DB_OK:
    _users_db = SqliteDict(DB_PATH, tablename="users", autocommit=True)
    _jobs_db  = SqliteDict(DB_PATH, tablename="jobs",  autocommit=True)
else:
    _users_db: dict = {}
    _jobs_db:  dict = {}

# ── Planos ────────────────────────────────────────────────────────────────────
PLANS = {
    "free": {
        "name": "Free",
        "price_brl": 0,
        "videos_per_month": 3,
        "ai_images": False,
        "voice_cloning": False,
        "deploy_platforms": ["youtube"],
    },
    "creator": {
        "name": "Creator",
        "price_brl": 49,
        "videos_per_month": 30,
        "ai_images": True,
        "voice_cloning": False,
        "deploy_platforms": ["youtube", "instagram", "tiktok"],
    },
    "pro": {
        "name": "Pro",
        "price_brl": 147,
        "videos_per_month": 150,
        "ai_images": True,
        "voice_cloning": True,
        "deploy_platforms": ["youtube", "instagram", "tiktok", "facebook", "google_drive"],
    },
    "studio": {
        "name": "Studio",
        "price_brl": 397,
        "videos_per_month": -1,  # ilimitado
        "ai_images": True,
        "voice_cloning": True,
        "deploy_platforms": ["*"],
    },
}

# ── Modelos Pydantic ──────────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    name: str
    email: str
    password: str
    plan: str = "free"

class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict

class ScriptRequest(BaseModel):
    topic: str
    niche: str = "entretenimento"
    duration_min: int = 5

class AudioRequest(BaseModel):
    text: str
    voice: str = "pt-BR-FranciscaNeural"

class VideoRequest(BaseModel):
    topic: str
    niche: str = "entretenimento"
    use_ai_images: bool = True

class AvatarRequest(BaseModel):
    name: str
    persona: str
    style: str = "realista"

class CompetitorRequest(BaseModel):
    channel_url: str

class TrackRequest(BaseModel):
    mood: str = "epic"
    duration_sec: int = 60

class VoiceCloneRequest(BaseModel):
    voice_name: str
    test_text: str = "Olá, eu sou seu novo clone de voz."

class VisualConfigRequest(BaseModel):
    preset: str = "dark"
    bg_color: str = "15,15,25"
    accent_color: str = "80,160,255"

class DeployRequest(BaseModel):
    video_file: str
    title: str
    description: str = ""
    platform: str = "youtube"

# ── Helpers auth ──────────────────────────────────────────────────────────────

def _hash_password(password: str) -> str:
    if pwd_ctx:
        return pwd_ctx.hash(password)
    return password  # fallback sem hash (dev only)

def _verify_password(plain: str, hashed: str) -> bool:
    if pwd_ctx:
        return pwd_ctx.verify(plain, hashed)
    return plain == hashed

def _create_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def _get_current_user(token: str = Depends(oauth2_scheme)) -> Optional[dict]:
    if not token or not _JWT_OK:
        return None
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            return None
        user = _users_db.get(email)
        return user
    except JWTError:
        return None

# ── Endpoints Auth ────────────────────────────────────────────────────────────

@app.post("/auth/register")
def register(req: RegisterRequest):
    if req.email in _users_db:
        raise HTTPException(status_code=409, detail="E-mail já cadastrado.")
    if req.plan not in PLANS:
        raise HTTPException(status_code=400, detail=f"Plano inválido: {req.plan}")

    user = {
        "id": str(uuid.uuid4()),
        "name": req.name,
        "email": req.email,
        "password_hash": _hash_password(req.password),
        "plan": req.plan,
        "plan_info": PLANS[req.plan],
        "videos_used_this_month": 0,
        "created_at": datetime.utcnow().isoformat(),
    }
    _users_db[req.email] = user
    log.info("Novo usuário: %s (plano %s)", req.email, req.plan)

    token = _create_token({"sub": req.email})
    return {"access_token": token, "token_type": "bearer",
            "user": {k: v for k, v in user.items() if k != "password_hash"}}


@app.post("/auth/login")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = _users_db.get(form_data.username)
    if not user or not _verify_password(form_data.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="E-mail ou senha incorretos.")

    token = _create_token({"sub": user["email"]})
    return {"access_token": token, "token_type": "bearer",
            "user": {k: v for k, v in user.items() if k != "password_hash"}}


@app.get("/auth/me")
def me(current_user: dict = Depends(_get_current_user)):
    if not current_user:
        raise HTTPException(status_code=401, detail="Não autenticado.")
    return {k: v for k, v in current_user.items() if k != "password_hash"}


@app.get("/plans")
def list_plans():
    return PLANS


@app.post("/auth/upgrade")
def upgrade_plan(body: dict, current_user: dict = Depends(_get_current_user)):
    """
    Troca o plano do usuário. Em produção, integrar com Stripe/Pagar.me
    antes de chamar este endpoint.
    """
    if not current_user:
        raise HTTPException(status_code=401, detail="Não autenticado.")
    new_plan = body.get("plan")
    if new_plan not in PLANS:
        raise HTTPException(status_code=400, detail=f"Plano inválido: {new_plan}")

    current_user["plan"] = new_plan
    current_user["plan_info"] = PLANS[new_plan]
    _users_db[current_user["email"]] = current_user
    log.info("Plano atualizado: %s → %s", current_user["email"], new_plan)
    return {"ok": True, "plan": new_plan}

# ── Helpers internos ──────────────────────────────────────────────────────────

def _check_quota(user: Optional[dict]) -> None:
    """Verifica se o usuário pode gerar mais vídeos neste mês."""
    if user is None:
        return  # sem auth = modo dev/local, permite
    plan = PLANS.get(user.get("plan", "free"), PLANS["free"])
    limit = plan["videos_per_month"]
    used  = user.get("videos_used_this_month", 0)
    if limit != -1 and used >= limit:
        raise HTTPException(
            status_code=429,
            detail=f"Limite do plano {plan['name']} atingido ({limit} vídeos/mês). Faça upgrade."
        )

def _increment_usage(user: Optional[dict]) -> None:
    if user is None:
        return
    user["videos_used_this_month"] = user.get("videos_used_this_month", 0) + 1
    _users_db[user["email"]] = user

def _new_job(job_type: str, params: dict) -> str:
    job_id = str(uuid.uuid4())[:8]
    _jobs_db[job_id] = {
        "id": job_id,
        "type": job_type,
        "params": params,
        "status": "processing",
        "progress": 0,
        "created_at": datetime.utcnow().isoformat(),
        "url": None,
        "error": None,
    }
    return job_id

def _update_job(job_id: str, **kwargs):
    job = _jobs_db.get(job_id, {})
    job.update(kwargs)
    _jobs_db[job_id] = job

# ── Módulo 0 — Roteiro ────────────────────────────────────────────────────────

@app.post("/gerar-roteiro")
def gerar_roteiro(req: ScriptRequest, current_user=Depends(_get_current_user)):
    """Gera roteiro de vídeo via Claude/Gemini."""
    sys.path.insert(0, str(Path(__file__).parent))
    try:
        from src.pipeline.scriptwriter_gemini import generate_script
        result = generate_script(
            topic=req.topic,
            niche=req.niche,
            duration_min=req.duration_min,
        )
        return {"ok": True, "roteiro": result}
    except ImportError:
        # Fallback com roteiro de exemplo
        from tools.video_generator import roteiro_exemplo
        return {"ok": True, "roteiro": roteiro_exemplo(req.topic), "source": "exemplo"}
    except Exception as e:
        log.error("gerar_roteiro error: %s", e)
        raise HTTPException(status_code=500, detail=str(e))

# ── Módulo 1 — Trilha Neural ──────────────────────────────────────────────────

@app.post("/gerar-trilha")
def gerar_trilha(req: TrackRequest):
    """Placeholder: integração futura com Higgsfield / Suno / ElevenLabs music."""
    return {
        "ok": True,
        "message": f"Trilha '{req.mood}' de {req.duration_sec}s na fila.",
        "note": "Integração Higgsfield/Suno pendente.",
    }

# ── Módulo 2 — Legacy Cloning (voz) ──────────────────────────────────────────

@app.post("/clonar-voz")
def clonar_voz(req: VoiceCloneRequest):
    """Gera áudio de teste com edge-tts usando a voz solicitada."""
    import asyncio, tempfile
    from pathlib import Path

    async def _gen():
        try:
            import edge_tts
            out = Path(tempfile.mktemp(suffix=".mp3"))
            comm = edge_tts.Communicate(req.test_text, req.voice_name)
            await comm.save(str(out))
            return str(out)
        except Exception as e:
            return None

    path = asyncio.run(_gen())
    if path:
        return {"ok": True, "audio_path": path, "voice": req.voice_name}
    return {"ok": False, "message": "edge-tts falhou ou voz não disponível."}

# ── Módulo 4 — Influencers (avatar) ──────────────────────────────────────────

@app.post("/criar-avatar")
def criar_avatar(req: AvatarRequest):
    """Placeholder: integração futura com Higgsfield AI Influencer."""
    return {
        "ok": True,
        "avatar_id": str(uuid.uuid4())[:8],
        "name": req.name,
        "persona": req.persona,
        "style": req.style,
        "note": "Integração Higgsfield AI Influencer pendente.",
    }

# ── Módulo 5 — DNA Viral (concorrente) ───────────────────────────────────────

@app.post("/analisar-concorrente")
def analisar_concorrente(req: CompetitorRequest):
    """Analisa canal YouTube via Gemini + grounding."""
    sys.path.insert(0, str(Path(__file__).parent))
    try:
        from src.research.gemini_notebook import GeminiNotebook
        nb = GeminiNotebook(
            sources=[req.channel_url],
            title=f"Análise: {req.channel_url}",
        )
        result = nb.query(
            f"Analise este canal YouTube: {req.channel_url}. "
            "Liste: nicho, frequência de posts, tópicos populares, ganchos usados, "
            "oportunidades não exploradas."
        )
        return {
            "ok": True,
            "analysis": result.answer,
            "citations": result.citations,
            "grounded": result.grounded,
        }
    except Exception as e:
        log.error("analisar_concorrente error: %s", e)
        raise HTTPException(status_code=500, detail=str(e))

# ── Módulo 7 — Dublagem ───────────────────────────────────────────────────────

@app.post("/gerar-audio")
def gerar_audio_endpoint(req: AudioRequest):
    """Gera narração MP3 via edge-tts."""
    import asyncio, tempfile
    from pathlib import Path

    async def _gen():
        try:
            import edge_tts
            out = Path(tempfile.mktemp(suffix=".mp3"))
            comm = edge_tts.Communicate(req.text, req.voice)
            await comm.save(str(out))
            return str(out)
        except Exception as e:
            return None

    path = asyncio.run(_gen())
    if path:
        return {"ok": True, "audio_path": path}
    raise HTTPException(status_code=500, detail="edge-tts indisponível.")

# ── Módulo 8 — Edição Tática (vídeo principal) ───────────────────────────────

@app.post("/gerar-video")
def gerar_video(
    req: VideoRequest,
    background_tasks: BackgroundTasks,
    current_user=Depends(_get_current_user),
):
    _check_quota(current_user)

    job_id = _new_job("video", req.dict())

    async def _run(job_id: str, req: VideoRequest):
        try:
            sys.path.insert(0, str(Path(__file__).parent))
            from tools.video_generator import gerar_video_frankenstein, roteiro_exemplo

            # Tenta gerar roteiro real, senão usa exemplo
            try:
                from src.pipeline.scriptwriter_gemini import generate_script
                roteiro = generate_script(topic=req.topic, niche=req.niche)
            except Exception:
                roteiro = roteiro_exemplo(req.topic)

            _update_job(job_id, progress=20)

            # Seta USE_AI_IMAGES temporariamente
            old_env = os.environ.get("USE_AI_IMAGES")
            os.environ["USE_AI_IMAGES"] = "true" if req.use_ai_images else "false"

            _update_job(job_id, progress=30)
            saida = await gerar_video_frankenstein(req.topic, roteiro)

            if old_env is not None:
                os.environ["USE_AI_IMAGES"] = old_env

            video_url = f"/output/{saida.name}"
            _update_job(job_id, status="done", progress=100, url=video_url)
            if current_user:
                _increment_usage(current_user)

        except Exception as e:
            log.error("gerar_video job %s error: %s", job_id, e)
            _update_job(job_id, status="error", error=str(e))

    background_tasks.add_task(asyncio.run, _run(job_id, req))
    return {"ok": True, "job_id": job_id}


@app.get("/status-video/{job_id}")
def status_video(job_id: str):
    job = _jobs_db.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job não encontrado.")
    return job

# ── Módulo 9 — Color Grade ────────────────────────────────────────────────────

@app.post("/configurar-visual")
def configurar_visual(req: VisualConfigRequest):
    """Salva preset de cores para uso no video_generator."""
    presets_path = Path("config/visual_presets.json")
    presets_path.parent.mkdir(exist_ok=True)

    try:
        presets = json.loads(presets_path.read_text()) if presets_path.exists() else {}
    except Exception:
        presets = {}

    presets[req.preset] = {
        "bg_color": req.bg_color,
        "accent_color": req.accent_color,
        "updated_at": datetime.utcnow().isoformat(),
    }
    presets_path.write_text(json.dumps(presets, indent=2))
    return {"ok": True, "preset": req.preset, "config": presets[req.preset]}

# ── Módulo 10 — Render Queue ──────────────────────────────────────────────────

@app.get("/listar-jobs")
def listar_jobs():
    jobs = list(_jobs_db.values())
    # mais recentes primeiro
    jobs.sort(key=lambda j: j.get("created_at", ""), reverse=True)
    return {"jobs": jobs[:50]}

# ── Módulo 11 — Deploy Global ─────────────────────────────────────────────────

@app.post("/deploy-video")
def deploy_video(req: DeployRequest, current_user=Depends(_get_current_user)):
    """
    Placeholder: integração com YouTube Data API / TikTok API / rclone.
    Por agora registra a intenção e retorna estrutura de resposta padrão.
    """
    deploy_id = str(uuid.uuid4())[:8]
    log.info("Deploy solicitado: %s → %s (%s)", req.video_file, req.platform, deploy_id)
    return {
        "ok": True,
        "deploy_id": deploy_id,
        "platform": req.platform,
        "video_file": req.video_file,
        "title": req.title,
        "status": "queued",
        "note": f"Integração {req.platform} em desenvolvimento.",
    }

# ── Health ────────────────────────────────────────────────────────────────────

@app.get("/")
def root():
    return {"status": "ok", "service": "CineForge API", "version": "1.0.0"}

@app.get("/health")
def health():
    return {
        "status": "ok",
        "jwt": _JWT_OK,
        "bcrypt": _BCRYPT_OK,
        "db": _DB_OK,
        "jobs_in_queue": len(_jobs_db),
        "users_registered": len(_users_db),
    }
