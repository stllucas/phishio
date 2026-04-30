"""Módulo principal da API FastAPI para detecção de phishing."""
import hashlib
import logging
from datetime import datetime
from zoneinfo import ZoneInfo
from typing import Optional

from core.Config import SECRETS_FILE
from core.SearchEngine import SearchEngine
from core.GeoLocator import get_location_by_ip

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from google.cloud import firestore
from google.oauth2 import service_account
from pydantic import BaseModel, Field

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# IPs de proxies reversos confiáveis (ex: Nginx, AWS ALB, Cloudflare).
TRUSTED_PROXIES = {"127.0.0.1", "::1", "206.189.204.241"}

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
    "chrome-extension://eobfgpgnhgjfdfoiahbpnegncokaebmo"

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
    gcp_credentials = service_account.Credentials.from_service_account_file(
        SECRETS_FILE
    )
    db = firestore.AsyncClient(credentials=gcp_credentials)
    logger.info(
        "Cliente Firestore inicializado com sucesso a partir do arquivo de credenciais."
    )
except Exception as e:
    logger.critical(f"Falha ao inicializar o cliente Firestore: {e}")
    db = None


class CheckUrlRequest(BaseModel):
    """Payload esperado para a verificação de URL."""

    url: Optional[str] = Field(...,
                               description="A URL completa da página a ser analisada.")
    dom: Optional[str] = Field(
        default="", description="O conteúdo textual (DOM) da página.")
    content: Optional[str] = Field(
        default="", description="O conteúdo de texto extraído da página (innerText).")


class CheckUrlResponse(BaseModel):
    """Resposta da análise da URL."""

    status: str = Field(
        ..., description="O veredito da análise: 'safe', 'suspicious', 'phishing', ou 'needs_content'."
    )
    score: float = Field(..., description="O score de confiança do veredito.")


class ReportRequest(BaseModel):
    """Payload esperado para o reporte de uma URL pelo usuário."""

    url: str = Field(...,
                     description="A URL da página que está sendo reportada.")
    voto: int = Field(
        ...,
        description="O voto do usuário: 1 para phishing, -1 para seguro.",
        ge=-1,
        le=1,
    )


class ReportResponse(BaseModel):
    """Resposta do reporte de URL."""

    message: str = Field(...,
                         description="Mensagem de confirmação do reporte.")
    new_status: str = Field(
        ..., description="O novo status operacional da URL após o reporte."
    )
    new_score: float = Field(...,
                             description="O novo score de consenso da URL.")


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


@app.post("/check_url", response_model=CheckUrlResponse)
async def check_url(request: CheckUrlRequest):
    if not db:
        raise HTTPException(
            status_code=503, detail="Serviço de banco de dados indisponível."
        )

    try:
        doc_id = generate_firestore_id(request.url)

        logger.info(
            f"[DEBUG] Buscando no Firestore ID: {doc_id} para URL: {request.url}"
        )

        doc_ref = db.collection("reputacao_urls_v2").document(doc_id)
        doc = await doc_ref.get()

        if doc.exists:
            data = doc.to_dict()
            score = float(data.get("consensus_score", 0))
            is_verified = data.get("verificado_sistema", False)
            status_banco = data.get("status", "safe")

            logger.info(
                f"[DEBUG] Documento encontrado no Cache! Status: {status_banco}, Score: {score}"
            )

            if is_verified:
                logger.info(
                    f"Cache HIT (Autoridade): {request.url} - Veredito: {status_banco}"
                )
                return CheckUrlResponse(status=status_banco, score=score)

            if score >= 15:
                logger.info(
                    f"Cache HIT (Comunidade - Phishing): {request.url}")
                return CheckUrlResponse(status="phishing", score=score)

            if score < 0:
                logger.info(f"Cache HIT (Comunidade - Safe): {request.url}")
                return CheckUrlResponse(status="safe", score=score)

            logger.info(
                f"URL em Estado Neutro (Score: {score}). Acionando análise profunda..."
            )
        else:
            logger.warning(
                f"[DEBUG] Cache MISS Total: O ID {doc_id} não existe na coleção 'reputacao_urls_v2'."
            )

    except Exception as e:
        logger.error(f"Erro na consulta de cache para {request.url}: {e}")

    if not request.dom or request.dom.strip() == "":
        logger.info(
            f"Cache MISS para {request.url}. DOM não fornecido. Solicitando à extensão...")
        return CheckUrlResponse(status="needs_content", score=0.0)

    logger.info(f"Acionando motor vetorial para {request.url}")
    try:
        texto_base = request.content if request.content else request.dom
        vetor_query = search_engine.gerar_vetor_consulta_tfidf(texto_base)

        resultados = search_engine.ranquear_documentos_completo(vetor_query)

        if resultados:
            maior_score = resultados[0][1]

            if maior_score > 0.75:
                status_final = "phishing"
            elif maior_score > 0.4:
                status_final = "suspicious"
            else:
                status_final = "safe"

            try:
                if db:
                    doc_ref = db.collection(
                        "reputacao_urls_v2").document(doc_id)
                    await doc_ref.set({
                        "url": request.url,
                        "status": status_final,
                        "consensus_score": 0,
                        "verificado_sistema": True,
                        "score_vetorial": maior_score,
                        "last_updated": firestore.SERVER_TIMESTAMP,
                    }, merge=True)
            except Exception as cache_err:
                logger.error(
                    f"Erro ao salvar cache para {request.url}: {cache_err}")

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
        raise HTTPException(
            status_code=503, detail="Banco de dados indisponível.")

    url_id = generate_firestore_id(dados.url)

    client_ip = get_secure_client_ip(request)
    geo_data = get_location_by_ip(client_ip)

    try:
        await db.collection("reports_geolocalizados").add({
            "url": dados.url,
            "ip": client_ip,
            "estado": geo_data.get("estado", "Desconhecido"),
            "cidade": geo_data.get("cidade", "Desconhecido"),
            "pais": geo_data.get("pais", "Desconhecido"), # Novo campo
            "voto": dados.voto,
            "timestamp": datetime.now(ZoneInfo("America/Sao_Paulo"))
        })

        voto_p = 1 if dados.voto == 1 else 0
        voto_s = 1 if dados.voto == -1 else 0

        doc_ref = db.collection("reputacao_urls_v2").document(url_id)
        await doc_ref.set({
            "url": dados.url,
            "total_votos": firestore.Increment(1),
            "votos_phishing": firestore.Increment(voto_p),
            "votos_seguro": firestore.Increment(voto_s),
            "consensus_score": firestore.Increment(dados.voto),
            "last_updated": firestore.SERVER_TIMESTAMP,
        }, merge=True)

        doc = await doc_ref.get()
        if doc.exists:
            score = doc.to_dict().get("consensus_score", 0)
            if score >= 15:
                await doc_ref.update({"status": "phishing"})
            elif score < 0:
                await doc_ref.update({"status": "safe"})

        logger.info(
            f"Reporte Completo: {dados.url} | IP: {client_ip} | Voto: {dados.voto}")
        return {"success": True, "message": "Reporte e geolocalização processados com sucesso."}

    except Exception as e:
        logger.error(f"Erro no processamento unificado: {e}")
        raise HTTPException(
            status_code=500, detail="Erro interno ao processar colaboração.")
