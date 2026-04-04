import firebase_admin
from firebase_admin import credentials, firestore
import json
import os
from tqdm import tqdm

# --- CONFIGURAÇÕES ---
CREDENTIALS_PATH = "tcc-coletor-web-firebase-adminsdk-fbsvc-9a87e2278a.json"
JSON_SOURCE = 'logs/document_map.json'
LIMITE_MIGRACAO = 19000  # Limite para não estourar a cota diaria de escrita no firebase

def migrar_links():
    # 1. Conexão com Firebase
    cred = credentials.Certificate(CREDENTIALS_PATH)
    firebase_admin.initialize_app(cred)
    db = firestore.client()

    # 2. Carregar o Mapa de Documentos
    if not os.path.exists(JSON_SOURCE):
        print(f"[ERRO] Arquivo {JSON_SOURCE} não encontrado.")
        return

    with open(JSON_SOURCE, 'r', encoding='utf-8') as f:
        doc_map = json.load(f)

    print(f"[PHISHIO] Mapeamento carregado. Iniciando upload de {LIMITE_MIGRACAO} links...")

    # 3. Upload em Lote (Batch) para maior eficiência
    count = 0
    batch = db.batch()
    
    for doc_id, url in tqdm(doc_map.items(), total=LIMITE_MIGRACAO):
        if count >= LIMITE_MIGRACAO:
            break
        
        # Referência do documento usando o DocID como ID no Firestore
        doc_ref = db.collection('documentos_processados').document(str(doc_id))
        
        # Estrutura Híbrida: Dados de RI + Campos de Crowdsourcing
        batch.set(doc_ref, {
            'url': url,
            'status': 'suspeito',       # Classificação inicial do seu dataset
            'votos_phishing': 0,        #
            'votos_seguro': 0,          #
            'verificado_sistema': True  # Diferencia da base inicial vs reportes novos
        })
        
        count += 1
        
        # O Firestore permite lotes de no máximo 500 operações por vez
        if count % 500 == 0:
            batch.commit()
            batch = db.batch()

    # Commit final para o que restou
    batch.commit()
    print(f"\n[SUCESSO] {count} links migrados para 'documentos_processados'.")

if __name__ == "__main__":
    migrar_links()