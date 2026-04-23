import hashlib
import logging
from datetime import datetime
from zoneinfo import ZoneInfo

# Imports locais
from core.Config import SECRETS_FILE
from core.SearchEngine import SearchEngine
from core.GeoLocator import get_location_by_ip

# Bibliotecas de terceiros
from fastapi import FastAPI, HTTPException, Request
from google.cloud import firestore
from google.oauth2 import service_account
from pydantic import BaseModel, Field

# --- Configuração de Logging ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Instanciando o motor vetotiral ---
logger.info("Iniciando o carregamento prévio do Motor Vetorial")
search_engine = SearchEngine()

# --- Setup Inicial: FastAPI e Clientes ---

# Inicializa a aplicação FastAPI
app = FastAPI(
    title="Phishio API",
    description="API para detecção híbrida de phishing (Firestore Cache + Motor Vetorial).",
    version="1.0.0",
)

# Inicializa o cliente assíncrono do Firestore.
# As credenciais são obtidas automaticamente do ambiente (GOOGLE_APPLICATION_CREDENTIALS).
try:
    # Para facilitar o desenvolvimento local, as credenciais são carregadas de um arquivo.
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
    # Em um ambiente de produção, isso poderia notificar uma equipe de SRE.
    db = None

# --- Modelos Pydantic (Contrato de Dados) ---


class CheckUrlRequest(BaseModel):
    """Payload esperado para a verificação de URL."""

    url: str = Field(...,
                     description="A URL completa da página a ser analisada.")
    dom: str = Field(..., description="O conteúdo textual (DOM) da página.")


class CheckUrlResponse(BaseModel):
    """Resposta da análise da URL."""

    status: str = Field(
        ..., description="O veredito da análise: 'safe', 'suspicious', ou 'phishing'."
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


# --- Funções Auxiliares ---
def generate_firestore_id(url: str) -> str:
    """
    Normaliza a URL para garantir Cache HIT independente de protocolo ou subdomínio 'www'.
    Seguindo a lógica de desduplicação da Seção 3.1 do TCC.
    """
    # 1. Padronização básica (Minúsculas e remover espaços)
    u = url.lower().strip()

    # 2. Limpeza profunda de protocolo e www (Crucial para o TCC)
    u = u.replace("https://", "").replace("http://", "").replace("www.", "")

    # 3. Remover parâmetros de busca e fragmentos
    u = u.split("?")[0].split("#")[0]

    # 4. Remover barra final para unicidade
    u = u.rstrip("/")

    # 5. SHA-256 (Deve ser igual ao Unify_collections.py)
    return hashlib.sha256(u.encode("utf-8")).hexdigest()


# --- Endpoint Principal de Análise ---


@app.post("/check_url", response_model=CheckUrlResponse)
async def check_url(request: CheckUrlRequest):
    if not db:
        raise HTTPException(
            status_code=503, detail="Serviço de banco de dados indisponível."
        )

    # --- Passo A e B: Consulta ao Cache de Reputação (Firestore) ---
    try:
        # 1. Gera o ID SHA-256
        doc_id = generate_firestore_id(request.url)

        # Log depuração: Crucial para ver no console qual hash a API está gerando
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

            # Prioridade 1: Verificação de Autoridade (Sistema)
            if is_verified:
                logger.info(
                    f"Cache HIT (Autoridade): {request.url} - Veredito: {status_banco}"
                )
                return CheckUrlResponse(status=status_banco, score=score)

            # Prioridade 2: Consenso Comunitário de Perigo
            if score >= 15:
                logger.info(
                    f"Cache HIT (Comunidade - Phishing): {request.url}")
                return CheckUrlResponse(status="phishing", score=score)

            # Prioridade 3: Consenso Comunitário de Segurança Explícita
            if score < 0:
                logger.info(f"Cache HIT (Comunidade - Safe): {request.url}")
                return CheckUrlResponse(status="safe", score=score)

            # ESTADO NEUTRO (0 <= score < 15): O fluxo continua para o Motor Vetorial
            logger.info(
                f"URL em Estado Neutro (Score: {score}). Acionando análise profunda..."
            )
        else:
            # Log de aviso/debug: Confirma se o Google simplesmente NÃO existe no banco
            logger.warning(
                f"[DEBUG] Cache MISS Total: O ID {doc_id} não existe na coleção 'reputacao_urls_v2'."
            )

    except Exception as e:
        logger.error(f"Erro na consulta de cache para {request.url}: {e}")

    # --- Passo C: Análise Vetorial ---
    logger.info(f"Acionando motor vetorial para {request.url}")
    try:
        # 1. Processamento e Vetorização
        vetor_query = search_engine.gerar_vetor_consulta_tfidf(request.dom)

        # 2. Ranking de Similaridade (Ajustado para o nome correto do método)
        resultados = search_engine.ranquear_documentos_completo(vetor_query)

        if resultados:
            # Similaridade do Cosseno
            maior_score = resultados[0][1]

            # Limiares de decisão definidos na metodologia
            if maior_score > 0.75:
                status_final = "phishing"
            elif maior_score > 0.4:
                status_final = "suspicious"
            else:
                status_final = "safe"

            return CheckUrlResponse(status=status_final, score=maior_score)

        return CheckUrlResponse(status="safe", score=0.0)

    except Exception as e:
        logger.error(f"Erro crítico no motor vetorial: {e}")
        raise HTTPException(
            status_code=500, detail="Erro interno durante a análise de conteúdo."
        )


# --- Endpoint de Crowdsourcing (Reporte de URL) ---


# 1. Certifique-se de que o modelo está assim no topo:
class ReportModel(BaseModel):
    url: str
    voto: int  # 1 para phishing, -1 para seguro


@app.post("/reportar_url")
async def reportar_url(request: Request, dados: ReportRequest): # Adicionado Request para pegar o IP
    """
    Unifica Indicador 1 (Colaboração) e Indicador 2 (Confiabilidade).
    Captura IP, localiza geograficamente e atualiza o score de consenso.
    """
    if not db:
        raise HTTPException(status_code=503, detail="Banco de dados indisponível.")

    url_id = generate_firestore_id(dados.url)
    
    # 1. Captura e Geolocalização do IP (Indicador 5 e 1)
    client_ip = request.client.host if request.client else "IP_Desconhecido"
    geo_data = get_location_by_ip(client_ip)

    try:
        # A. Gravação do Rastro Geográfico (Indicador de Distribuição Geográfica)
        await db.collection("reports_geolocalizados").add({
            "url": dados.url,
            "ip": client_ip,
            "estado": geo_data.get("estado", "Desconhecido"),
            "cidade": geo_data.get("cidade", "Desconhecido"),
            "timestamp": datetime.now(ZoneInfo("America/Sao_Paulo"))
        })

        # B. Atualização do Score de Consenso (Indicador de Confiabilidade/Maturidade)
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

        # C. Lógica de Maturidade (Vira o status se houver consenso de 15 votos)
        doc = await doc_ref.get()
        if doc.exists:
            score = doc.to_dict().get("consensus_score", 0)
            if score >= 15:
                await doc_ref.update({"status": "phishing"})
            elif score < 0:
                await doc_ref.update({"status": "safe"})

        logger.info(f"Reporte Completo: {dados.url} | IP: {client_ip} | Voto: {dados.voto}")
        return {"success": True, "message": "Reporte e geolocalização processados com sucesso."}

    except Exception as e:
        logger.error(f"Erro no processamento unificado: {e}")
        raise HTTPException(status_code=500, detail="Erro interno ao processar colaboração.")