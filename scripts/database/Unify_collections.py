import asyncio
import hashlib
import os

from google.cloud import firestore
from google.oauth2 import service_account

# --- Configuração ---
CREDENTIALS_FILENAME = "secrets"
COLLECTION_OLD_DOCS = "documentos_processados"
COLLECTION_OLD_REPUTATION = "reputacao_urls"
COLLECTION_TARGET = "reputacao_urls_v2"


def gerar_hash_padronizado(url):
    """
    Normalização: Garante que a API (FastAPI) e a Migração usem o mesmo ID.
    """
    if not url:
        return None
    # 1. Lowercase e limpeza de espaços
    u = url.lower().strip()
    # 2. Remoção de protocolos e www
    u = u.replace("https://", "").replace("http://", "").replace("www.", "")
    # 3. Remoção de query strings e fragmentos (#)
    u = u.split("?")[0].split("#")[0]
    # 4. Remoção da barra final (trailing slash)
    u = u.rstrip("/")

    return hashlib.sha256(u.encode("utf-8")).hexdigest()


async def unify_data():
    # Setup de credenciais
    credentials_path = os.path.join(
        os.path.dirname(__file__), "..", "..", CREDENTIALS_FILENAME
    )
    gcp_credentials = service_account.Credentials.from_service_account_file(
        credentials_path
    )
    db = firestore.AsyncClient(credentials=gcp_credentials)

    print("--- INICIANDO UNIFICAÇÃO (STATUS: PHISHING) ---")

    # Mapeamento de reputação para merge de votos da comunidade
    reputation_map = {}
    async for doc in db.collection(COLLECTION_OLD_REPUTATION).stream():
        data = doc.to_dict()
        url_raw = data.get("url") or data.get("url_original")
        if url_raw:
            # Normaliza a chave para bater com a URL do documento processado
            norm_key = (
                url_raw.lower()
                .strip()
                .replace("https://", "")
                .replace("http://", "")
                .replace("www.", "")
                .split("?")[0]
                .split("#")[0]
                .rstrip("/")
            )
            reputation_map[norm_key] = data

    batch = db.batch()
    batch_count = 0
    total_migrated = 0

    async for doc in db.collection(COLLECTION_OLD_DOCS).stream():
        doc_data = doc.to_dict()
        url_original = doc_data.get("url")
        if not url_original:
            continue

        # Gera o ID SHA-256 normalizado (ex: b6b1dbf7...)
        url_hash = gerar_hash_padronizado(url_original)

        # Localiza votos prévios no mapa de reputação
        url_norm_para_busca = (
            url_original.lower()
            .strip()
            .replace("https://", "")
            .replace("http://", "")
            .replace("www.", "")
            .split("?")[0]
            .split("#")[0]
            .rstrip("/")
        )
        old_reputation = reputation_map.get(url_norm_para_busca, {})

        # --- ESTRUTURA FINAL ATUALIZADA ---
        final_data = {
            "id": url_hash,  # Campo ID explícito solicitado
            "url": url_original,
            # FORÇADO PARA PHISHING (DANGER)
            "status": "phishing",
            "consensus_score": old_reputation.get("consensus_score", 0),
            "total_votos": old_reputation.get("total_votos", 0),
            "votos_phishing": doc_data.get("votos_phishing", 0),
            "votos_seguro": doc_data.get("votos_seguro", 0),
            "verificado_sistema": True,
            "last_updated": firestore.SERVER_TIMESTAMP,
        }

        target_ref = db.collection(COLLECTION_TARGET).document(url_hash)
        batch.set(target_ref, final_data)

        batch_count += 1
        total_migrated += 1

        if batch_count >= 450:
            await batch.commit()
            batch = db.batch()
            batch_count = 0

    if batch_count > 0:
        await batch.commit()

    print(f"\n[SUCESSO] {total_migrated} documentos migrados.")
    print("Status global definido como 'phishing' e campo 'id' incluído.")


if __name__ == "__main__":
    asyncio.run(unify_data())
