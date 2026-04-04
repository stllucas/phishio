import firebase_admin
from firebase_admin import credentials, firestore
from tqdm import tqdm

# Configuração Inicial
cred = credentials.Certificate('tcc-coletor-web-firebase-adminsdk-fbsvc-9a87e2278a.json')
firebase_admin.initialize_app(cred)
db = firestore.client()

def atualizar_timestamps_processados():
    print("[PHISHIO] Iniciando atualização de timestamps em 'documentos_processados'...")
    
    docs_ref = db.collection('documentos_processados')
    # O stream() é eficiente para grandes volumes de dados
    docs = docs_ref.stream()

    batch = db.batch()
    contador = 0

    for doc in tqdm(docs, desc="Atualizando documentos"):
        # Usamos update para não sobrescrever os dados existentes (URL, conteúdo, etc)
        batch.update(doc.reference, {
            'data_upload': firestore.SERVER_TIMESTAMP
        })
        contador += 1
        
        # Limite de 500 operações por batch do Firestore
        if contador % 500 == 0:
            batch.commit()
            batch = db.batch()

    # Commit final para documentos restantes
    if contador % 500 != 0:
        batch.commit()
        
    print(f"\n[SUCESSO] {contador} documentos atualizados com SERVER_TIMESTAMP.")

if __name__ == "__main__":
    atualizar_timestamps_processados()