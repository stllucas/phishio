"""Módulo principal da API FastAPI para detecção de phishing."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pydantic import BaseModel, Field
from google.oauth2 import service_account
import requests
from google.api_core.client_options import ClientOptions
from google.cloud import firestore
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import RedirectResponse
from core.GeoLocator import get_location_by_ip
from core.SearchEngine import SearchEngine
from core.Config import SECRETS_FILE
import asyncio
import hashlib
import logging
from datetime import datetime
from zoneinfo import ZoneInfo
from typing import Optional

os.environ["GRPC_PYTHON_BUILD_SYSTEM_OPENSSL"] = "1"
os.environ["GOOGLE_AUTH_HTTPLIB2_MAX_RETRIES"] = "5"

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("PhishioAPI")

logging.getLogger("urllib3.connectionpool").setLevel(logging.ERROR)

TRUSTED_PROXIES = {"127.0.0.1", "::1", "206.189.204.241", "172.17.0.1"}

logger.info("Iniciando o carregamento prévio do Motor Vetorial")
search_engine = SearchEngine()

app = FastAPI(
    title="Phishio API",
    description="API para detecção híbrida de phishing (Firestore Cache + Motor Vetorial).",
    version="1.0.0",
)

ALLOWED_ORIGINS = [
    "http://localhost",
    "http://127.0.0.1",
    "chrome-extension://eobfgpgnhgjfdfoiahbpnegncokaebmo",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_origin_regex=r"^chrome-extension://.*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

try:
    if not SECRETS_FILE.exists():
        raise FileNotFoundError(
            f"Arquivo de credenciais não encontrado em: {SECRETS_FILE.resolve()}. Verifique se o arquivo 'secrets' está na pasta 'runtime'."
        )

    adapter = requests.adapters.HTTPAdapter(pool_connections=100, pool_maxsize=100)
    session = requests.Session()
    session.mount("https://", adapter)

    gcp_credentials = service_account.Credentials.from_service_account_file(
        SECRETS_FILE
    )

    db = firestore.AsyncClient(
        credentials=gcp_credentials, client_options=ClientOptions()
    )
    logger.info(
        "Cliente Firestore inicializado com sucesso a partir do arquivo de credenciais."
    )
except Exception as e:
    logger.critical(f"Falha ao inicializar o cliente Firestore: {e}")
    db = None


class CheckUrlRequest(BaseModel):
    """Payload esperado para a verificação de URL."""

    url: Optional[str] = Field(
        ..., description="A URL completa da página a ser analisada."
    )
    dom: Optional[str] = Field(
        default="", description="O conteúdo textual (DOM) da página."
    )
    content: Optional[str] = Field(
        default="", description="O conteúdo de texto extraído da página (innerText)."
    )


class CheckUrlResponse(BaseModel):
    """Resposta da análise da URL."""

    status: str = Field(
        ...,
        description="O veredito da análise: 'safe', 'suspicious', 'phishing', ou 'needs_content'.",
    )
    score: float = Field(..., description="O score de confiança do veredito.")


class ReportRequest(BaseModel):
    """Payload esperado para o reporte de uma URL pelo usuário."""

    url: str = Field(..., description="A URL da página que está sendo reportada.")
    voto: int = Field(
        ...,
        description="O voto do usuário: 1 para phishing, -1 para seguro.",
        ge=-1,
        le=1,
    )


class ReportResponse(BaseModel):
    """Resposta do reporte de URL."""

    message: str = Field(..., description="Mensagem de confirmação do reporte.")
    new_status: str = Field(
        ..., description="O novo status operacional da URL após o reporte."
    )
    new_score: float = Field(..., description="O novo score de consenso da URL.")


def generate_firestore_id(url: str) -> str:
    """
    Normaliza a URL para garantir Cache HIT independente de protocolo ou subdomínio 'www'.
    Seguindo a lógica de desduplicação da Seção 3.1 do TCC.
    """
    u = url.lower().strip()

    u = u.replace("https://", "").replace("http://", "").replace("www.", "")

    u = u.split("?")[0].split("#")[0]

    u = u.rstrip("/")

    return hashlib.sha256(u.encode("utf-8")).hexdigest()


async def log_vote_audit(url_id: str, voto: int, novo_status: str):
    """
    Função utilitária assíncrona para registrar o log de auditoria de votos.
    """
    timestamp = datetime.now(ZoneInfo("America/Sao_Paulo")).strftime(
        "%Y-%m-%d %H:%M:%S"
    )
    log_entry = f"{timestamp} | [SUCCESS] Incremento Concluído | ID: {url_id} | Voto: {voto} | Novo Status: {novo_status}\n"

    def write_log():
        with open("audit_votes.log", "a", encoding="utf-8") as f:
            f.write(log_entry)

    await asyncio.to_thread(write_log)


@app.get("/extension")
async def redirecionar_avaliadores():
    """
    Rota para redirecionar a banca de avaliadores do TCC usando endpoint próprio (DuckDNS) para a Landing Page no GitHub Pages.
    """
    logger.info(
        "[TCC] Avaliador acessou o site da extensão. Redirecionando para o GitHub Pages."
    )
    return RedirectResponse(
        url="https://pedroluckeroth.github.io/Site-Phishio-TCC-Extension/",
        status_code=301,
    )


@app.post("/check_url", response_model=CheckUrlResponse)
async def check_url(request: CheckUrlRequest):
    """Verifica o status de segurança de uma URL validando no Cache do Firestore ou acionando a análise vetorial."""
    if not db:
        raise HTTPException(
            status_code=503, detail="Serviço de banco de dados indisponível."
        )

    try:
        doc_id = generate_firestore_id(request.url)

        logger.debug(f"[FIRESTORE] Buscando ID: {doc_id} para URL: {request.url}")

        doc_ref = db.collection("reputacao_urls_v2").document(doc_id)
        doc = await doc_ref.get()

        if doc.exists:
            data = doc.to_dict()
            score = float(data.get("consensus_score", 0))
            is_verified = data.get("verificado_sistema", False)
            status_banco = data.get("status", "safe")

            logger.debug(
                f"[FIRESTORE] Documento encontrado no Cache! Status: {status_banco}, Score: {score}"
            )

            if is_verified:
                logger.info(
                    f"[CACHE HIT] Status: {status_banco} (Autoridade) | Score: {score} | URL: {request.url}"
                )
                return CheckUrlResponse(status=status_banco, score=score)

            if score >= 15:
                logger.info(
                    f"[CACHE HIT] Status: phishing (Comunidade) | Score: {score} | URL: {request.url}"
                )
                return CheckUrlResponse(status="phishing", score=score)

            if score < 0:
                logger.info(
                    f"[CACHE HIT] Status: safe (Comunidade) | Score: {score} | URL: {request.url}"
                )
                return CheckUrlResponse(status="safe", score=score)

            logger.info(
                f"[CACHE NEUTRAL] Score: {score}. Acionando análise profunda para URL: {request.url}"
            )
        else:
            logger.info(
                f"[CACHE MISS] ID: {doc_id} ausente na coleção. URL: {request.url}"
            )

    except Exception as e:
        logger.error(f"Erro na consulta de cache para {request.url}: {e}")

    if not request.dom or request.dom.strip() == "":
        logger.info(
            f"[CONTENT NEEDED] DOM não fornecido. Solicitando à extensão para URL: {request.url}"
        )
        return CheckUrlResponse(status="needs_content", score=0.0)

    logger.info(
        f"[VECTOR ENGINE] Acionando análise de conteúdo para URL: {request.url}"
    )
    try:
        texto_base = request.content if request.content else request.dom

        vetor_query = await asyncio.to_thread(
            search_engine.gerar_vetor_consulta_tfidf, texto_base
        )
        resultados = await asyncio.to_thread(
            search_engine.ranquear_documentos_completo, vetor_query
        )

        if resultados:
            maior_score = resultados[0][1]

            if maior_score > 0.75:
                status_final = "phishing"
            elif maior_score > 0.4:
                status_final = "suspicious"
            else:
                status_final = "safe"

            logger.info(
                f"[VECTOR RESULT] Status Final: {status_final} | Score Máximo: {maior_score:.4f} | URL: {request.url}"
            )

            try:
                if db:
                    doc_ref = db.collection("reputacao_urls_v2").document(doc_id)
                    await doc_ref.set(
                        {
                            "url": request.url,
                            "status": status_final,
                            "consensus_score": 0,
                            "verificado_sistema": True,
                            "score_vetorial": maior_score,
                            "last_updated": firestore.SERVER_TIMESTAMP,
                        },
                        merge=True,
                    )
            except Exception as cache_err:
                logger.error(f"Erro ao salvar cache para {request.url}: {cache_err}")

            return CheckUrlResponse(status=status_final, score=maior_score)

        return CheckUrlResponse(status="safe", score=0.0)

    except Exception as e:
        logger.error(f"Erro crítico no motor vetorial: {e}")
        raise HTTPException(
            status_code=500, detail="Erro interno durante a análise de conteúdo."
        )


class ReportModel(BaseModel):
    url: str
    voto: int


def get_secure_client_ip(request: Request) -> str:
    """Extrai o IP real do cliente validando proxies confiáveis e evita IP Spoofing."""
    remote_addr = request.client.host if request.client else "IP_Desconhecido"

    forwarded_for = request.headers.get("x-forwarded-for")
    real_ip = request.headers.get("x-real-ip")

    if forwarded_for or real_ip:
        if remote_addr in TRUSTED_PROXIES:
            if forwarded_for:
                return forwarded_for.split(",")[0].strip()
            return real_ip.strip()
        else:
            logger.warning(
                f"[AUDITORIA] Tentativa de IP Spoofing bloqueada! Remetente não confiável ({remote_addr}) enviou cabeçalhos de proxy."
            )

    return remote_addr


@app.post("/reportar_url")
async def reportar_url(request: Request, dados: ReportRequest):
    """
    Unifica Indicador 1 (Colaboração) e Indicador 2 (Confiabilidade).
    Captura IP, localiza geograficamente e atualiza o score de consenso.
    """
    if not db:
        raise HTTPException(status_code=503, detail="Banco de dados indisponível.")

    url_id = generate_firestore_id(dados.url)

    client_ip = get_secure_client_ip(request)
    geo_data = get_location_by_ip(client_ip)

    try:
        await db.collection("reports_geolocalizados").add(
            {
                "url": dados.url,
                "ip": client_ip,
                "estado": geo_data.get("estado", "Desconhecido"),
                "cidade": geo_data.get("cidade", "Desconhecido"),
                "pais": geo_data.get("pais", "Desconhecido"),
                "voto": dados.voto,
                "timestamp": datetime.now(ZoneInfo("America/Sao_Paulo")),
            }
        )

        voto_p = 1 if dados.voto == 1 else 0
        voto_s = 1 if dados.voto == -1 else 0

        doc_ref = db.collection("reputacao_urls_v2").document(url_id)
        await doc_ref.set(
            {
                "url": dados.url,
                "total_votos": firestore.Increment(1),
                "votos_phishing": firestore.Increment(voto_p),
                "votos_seguro": firestore.Increment(voto_s),
                "consensus_score": firestore.Increment(dados.voto),
                "last_updated": firestore.SERVER_TIMESTAMP,
            },
            merge=True,
        )

        doc = await doc_ref.get()
        if doc.exists:
            score = doc.to_dict().get("consensus_score", 0)
            status_atual = doc.to_dict().get("status", "safe")
            novo_status = status_atual

            if score >= 15:
                novo_status = "phishing"
                await doc_ref.update({"status": novo_status})
            elif score < 0:
                novo_status = "safe"
                await doc_ref.update({"status": novo_status})

            await log_vote_audit(url_id, dados.voto, novo_status)

        logger.info(
            f"Reporte Completo: {dados.url} | IP: {client_ip} | Voto: {dados.voto}"
        )
        return {
            "success": True,
            "message": "Reporte e geolocalização processados com sucesso.",
        }

    except Exception as e:
        logger.error(f"Erro no processamento unificado: {e}")
        raise HTTPException(
            status_code=500, detail="Erro interno ao processar colaboração."
        )


class ConsentRequest(BaseModel):
    """Payload esperado para registrar o consentimento do usuário."""

    versao_termos: str = Field(..., description="A versão dos termos aceitos.")
    user_agent: Optional[str] = Field(
        default="Desconhecido", description="O User-Agent do navegador."
    )


@app.post("/registrar_consentimento")
async def registrar_consentimento(request: Request, dados: ConsentRequest):
    """
    Registra o aceite dos termos de uso da extensão (LGPD).
    Usa um hash do IP para fins de auditoria anônima.
    """
    if not db:
        raise HTTPException(status_code=503, detail="Banco de dados indisponível.")

    client_ip = get_secure_client_ip(request)

    ip_hash = hashlib.sha256(
        (client_ip + "phishio_salt_lgpd").encode("utf-8")
    ).hexdigest()

    try:
        doc_ref = db.collection("user_consent").document(ip_hash)

        await doc_ref.set(
            {
                "ip_hash": ip_hash,
                "consent": True,
                "versao_termo": dados.versao_termos,
                "user_agent": dados.user_agent,
                "data_aceite": firestore.SERVER_TIMESTAMP,
                "ultimo_ip_mascarado": f"{client_ip.split('.')[0]}.*.*.*",
            },
            merge=True,
        )

        logger.info(f"Consentimento registrado para IP (Hash): {ip_hash[:8]}...")
        return {"success": True, "message": "Consentimento registrado com sucesso."}

    except Exception as e:
        logger.error(f"Erro ao registrar consentimento: {e}")
        raise HTTPException(
            status_code=500, detail="Erro interno ao registrar consentimento."
        )
