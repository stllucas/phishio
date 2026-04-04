import logging
from fastapi import FastAPI, HTTPException
import hashlib
import os
import sys
from pydantic import BaseModel, Field
from google.cloud import firestore
from google.oauth2 import service_account

# --- Configuração de Logging ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Setup Inicial: FastAPI e Clientes ---

# Inicializa a aplicação FastAPI
app = FastAPI(
    title="Phishio API",
    description="API para detecção híbrida de phishing (Firestore Cache + Motor Vetorial).",
    version="1.0.0"
)

# Inicializa o cliente assíncrono do Firestore.
# As credenciais são obtidas automaticamente do ambiente (GOOGLE_APPLICATION_CREDENTIALS).
try:
    # Para facilitar o desenvolvimento local, as credenciais são carregadas de um arquivo.
    # O servidor é executado a partir da pasta 'backend', então o caminho relativo sobe um nível para a raiz do projeto.
    CREDENTIALS_FILENAME = 'secrets'
    credentials_path = os.path.join(os.path.dirname(__file__), '..', CREDENTIALS_FILENAME)

    if not os.path.exists(credentials_path):
        raise FileNotFoundError(f"Arquivo de credenciais não encontrado em: {os.path.abspath(credentials_path)}. Verifique se o arquivo '{CREDENTIALS_FILENAME}' está na pasta raiz do projeto.")

    gcp_credentials = service_account.Credentials.from_service_account_file(credentials_path)
    db = firestore.AsyncClient(credentials=gcp_credentials)
    logger.info("Cliente Firestore inicializado com sucesso a partir do arquivo de credenciais.")
except Exception as e:
    logger.critical(f"Falha ao inicializar o cliente Firestore: {e}")
    # Em um ambiente de produção, isso poderia notificar uma equipe de SRE.
    db = None

# --- Modelos Pydantic (Contrato de Dados) ---

class CheckUrlRequest(BaseModel):
    """Payload esperado para a verificação de URL."""
    url: str = Field(..., description="A URL completa da página a ser analisada.")
    dom: str = Field(..., description="O conteúdo textual (DOM) da página.")

class CheckUrlResponse(BaseModel):
    """Resposta da análise da URL."""
    status: str = Field(..., description="O veredito da análise: 'safe', 'suspicious', ou 'phishing'.")
    score: float = Field(..., description="O score de confiança do veredito.")

class ReportRequest(BaseModel):
    """Payload esperado para o reporte de uma URL pelo usuário."""
    url: str = Field(..., description="A URL da página que está sendo reportada.")
    voto: int = Field(..., description="O voto do usuário: 1 para phishing, -1 para seguro.", ge=-1, le=1)

class ReportResponse(BaseModel):
    """Resposta do reporte de URL."""
    message: str = Field(..., description="Mensagem de confirmação do reporte.")
    new_status: str = Field(..., description="O novo status operacional da URL após o reporte.")
    new_score: float = Field(..., description="O novo score de consenso da URL.")

# --- Funções Auxiliares ---
def gerar_id_firestore(url: str) -> str:
    """
    Gera um ID MD5 para o Firestore a partir de uma URL.
    Isso previne erros com URLs muito longas ou com caracteres especiais
    que não são permitidos como IDs de documentos no Firestore.
    """
    return hashlib.md5(url.encode('utf-8')).hexdigest()


# --- Endpoint Principal de Análise ---

@app.post("/check_url", response_model=CheckUrlResponse)
async def check_url(request: CheckUrlRequest):
    """
    Implementa o fluxo de validação híbrida para detectar phishing.
    """
    if not db:
        raise HTTPException(status_code=503, detail="Serviço indisponível: Conexão com o banco de dados falhou.")

    # --- Passo A e B: Consulta ao Cache de Reputação (Firestore) ---
    # Decisão arquitetural: Priorizamos uma consulta rápida ao Firestore (cache de
    # reputação) para obter um veredito baseado em consenso comunitário. Isso
    # economiza recursos computacionais significativos, evitando acionar o motor
    # vetorial, que é mais custoso, para URLs já conhecidas.
    try:
        # O hash da URL é usado como ID do documento para acesso rápido.
        # Em produção, um hash da URL (ex: SHA-256) seria mais robusto.
        doc_ref = db.collection('reputacao_urls').document(gerar_id_firestore(request.url))
        doc = await doc_ref.get()

        if doc.exists:
            data = doc.to_dict()
            consensus_score = data.get('consensus_score', 0)
            
            # Veredito baseado no consenso (Seção 5.3.2 do TCC)
            if consensus_score >= 15: # Perigoso
                logger.info(f"Cache HIT (Perigoso): {request.url}")
                return CheckUrlResponse(status="phishing", score=consensus_score)
            if consensus_score <= 0: # Confiável
                logger.info(f"Cache HIT (Seguro): {request.url}")
                return CheckUrlResponse(status="safe", score=consensus_score)
            # Se for 'Suspeito' (0 < score < 15), o fluxo continua para a análise vetorial.

    except Exception as e:
        logger.error(f"Erro ao acessar o Firestore para a URL {request.url}: {e}")
        raise HTTPException(status_code=500, detail="Erro interno ao consultar o cache de reputação.")

    # --- Passo C: Análise Vetorial (Ataque Zero-Hora) ---
    # Se a URL é desconhecida ou apenas 'suspeita', acionamos o motor de busca
    # vetorial para uma análise profunda baseada em conteúdo (TF-IDF + Cosseno).
    logger.info(f"Cache MISS: Acionando motor vetorial para {request.url}")
    try:
        from backend.core.SearchEngine import SearchEngine # Importação sob demanda
        search_engine = SearchEngine() # Instancia o motor de busca
        
        # 1. Obtenha o vetor TF-IDF da consulta (DOM da página)
        vetor_query = search_engine.gerar_vetor_consulta_tfidf(request.dom)
        
        # 2. Obtenha o ranking completo dos documentos
        resultados = search_engine.ranquear_documentos(vetor_query)
        
        # 3. Lógica de decisão baseada no maior score de similaridade
        if resultados: # Se houver resultados ranqueados
            maior_score = resultados[0][1] # O primeiro resultado é o de maior score
            status = "phishing" if maior_score > 0.8 else "safe" # Limiar de decisão
            return CheckUrlResponse(status=status, score=maior_score)
        else: # Se não houver resultados relevantes
            logger.info(f"Nenhum resultado relevante encontrado pelo motor vetorial para {request.url}")
            return CheckUrlResponse(status="safe", score=0.0)

    except ImportError:
        logger.error("Falha crítica: Módulo 'src.SearchEngine' não encontrado.")
        raise HTTPException(status_code=500, detail="Erro interno: Componente de análise indisponível.")
    except Exception as e:
        logger.error(f"Erro no motor vetorial para a URL {request.url}: {e}")
        raise HTTPException(status_code=500, detail="Erro interno durante a análise de conteúdo.")

# --- Mock de Usuário (Temporário) ---
def get_mock_user_reputation() -> float:
    """
    Função auxiliar temporária para simular o peso de reputação de um usuário.
    Retorna 1.0, simulando um usuário 'Colaborador' (Reputação 3 a 8 do TCC).
    """
    return 1.0

# --- Endpoint de Crowdsourcing (Reporte de URL) ---

@app.post("/reportar_url", response_model=ReportResponse)
async def reportar_url(request: ReportRequest):
    """
    Permite que usuários reportem o status de uma URL, contribuindo para o consenso.
    Aplica a lógica de consenso ponderado descrita na Seção 5.3 do TCC.
    """
    if not db:
        raise HTTPException(status_code=503, detail="Serviço indisponível: Conexão com o banco de dados falhou.")

    # Obtém o peso de reputação do usuário (mock temporário)
    user_reputation_weight = get_mock_user_reputation()

    # Inicia uma transação assíncrona no Firestore para garantir atomicidade
    # Isso é crucial para evitar condições de corrida ao atualizar o score de consenso.
    transaction = db.transaction()
    doc_ref = db.collection('reputacao_urls').document(gerar_id_firestore(request.url))

    @firestore.transactional
    async def update_consensus_score(transaction, doc_ref, voto, weight):
        """
        Atualiza o score de consenso e o total de votos para uma URL.
        """
        snapshot = await doc_ref.get(transaction=transaction)
        
        current_score = 0
        total_votes = 0

        if snapshot.exists:
            data = snapshot.to_dict()
            current_score = data.get('consensus_score', 0)
            total_votes = data.get('total_votos', 0)

        # Aplica a fórmula do TCC: S = S_atual + (V_i * W_i)
        new_score = current_score + (voto * weight)
        new_total_votes = total_votes + 1

        transaction.set(doc_ref, {
            'consensus_score': new_score,
            'total_votos': new_total_votes,
            'last_updated': firestore.SERVER_TIMESTAMP
        })
        return new_score

    try:
        final_score = await update_consensus_score(transaction, doc_ref, request.voto, user_reputation_weight)

        # Determina o novo status operacional da URL com base nas regras do TCC (Seção 5.3.2)
        new_status = ""
        if final_score <= 0:
            new_status = "safe" # Confiável
        elif 0 < final_score < 15:
            new_status = "suspicious" # Suspeito
        else: # final_score >= 15
            new_status = "phishing" # Perigoso
        
        logger.info(f"URL {request.url} reportada. Novo score: {final_score}, Status: {new_status}")
        return ReportResponse(
            message="Reporte recebido com sucesso. A reputação da URL foi atualizada.",
            new_status=new_status,
            new_score=final_score
        )

    except Exception as e:
        logger.error(f"Erro ao processar o reporte para a URL {request.url}: {e}")
        raise HTTPException(status_code=500, detail="Erro interno ao processar o reporte.")
