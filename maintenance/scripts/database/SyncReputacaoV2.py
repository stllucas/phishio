import hashlib
import json
import os
from google.cloud import firestore
from google.oauth2 import service_account
from tqdm import tqdm

# --- CONFIGURAÇÕES ---
CREDENTIALS_PATH = "secrets" # Padronizado com o seu main.py
JSON_SOURCE = 'logs/document_map.json'
COLLECTION_TARGET = 'reputacao_urls_v2'
LIMITE_MIGRACAO = 19000 

def gerar_hash_padronizado(url):
    """Normalização idêntica ao main.py para garantir integridade do Cache"""
    if not url: return None
    u = url.lower().strip()
    u = u.replace("https://", "").replace("http://", "").replace("www.", "")
    u = u.split('?')[0].split('#')[0].rstrip('/')
    return hashlib.sha256(u.encode("utf-8")).hexdigest()

async def migrar_para_v2():
    # 1. Conexão Firestore
    if not os.path.exists(CREDENTIALS_PATH):
        print(f"[ERRO] Ficheiro '{CREDENTIALS_PATH}' não encontrado.")
        return

    gcp_credentials = service_account.Credentials.from_service_account_file(CREDENTIALS_PATH)
    db = firestore.AsyncClient(credentials=gcp_credentials)

    # 2. Carregar Document Map
    if not os.path.exists(JSON_SOURCE):
        print(f"[ERRO] Fonte {JSON_SOURCE} não encontrada.")
        return

    with open(JSON_SOURCE, 'r', encoding='utf-8') as f:
        doc_map = json.load(f)

    print(f"[PHISHIO] Iniciando migração para {COLLECTION_TARGET}...")
    
    batch = db.batch()
    count = 0

    # 3. Processamento em Lote
    for _, url in tqdm(list(doc_map.items())[:LIMITE_MIGRACAO], desc="Migrando"):
        url_hash = gerar_hash_padronizado(url)
        
        doc_ref = db.collection(COLLECTION_TARGET).document(url_hash)
        
        # Estrutura exata conforme a sua imagem
        doc_data = {
            "consensus_score": 0,
            "id": url_hash,
            "last_updated": firestore.SERVER_TIMESTAMP,
            "status": "phishing", # Classificação inicial do dataset
            "total_votos": 0,
            "url": url,
            "verificado_sistema": True,
            "votos_phishing": 0,
            "votos_seguro": 0
        }
        
        batch.set(doc_ref, doc_data)
        count += 1

        if count % 500 == 0:
            await batch.commit()
            batch = db.batch()

    if count % 500 != 0:
        await batch.commit()

    print(f"\n[SUCESSO] {count} documentos migrados com IDs em SHA-256.")

if __name__ == "__main__":
    import asyncio
    asyncio.run(migrar_para_v2())