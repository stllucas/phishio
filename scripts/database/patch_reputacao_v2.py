import asyncio
import hashlib
import os
import time

from google.cloud import firestore
from google.oauth2 import service_account

# --- Configuração ---
CREDENTIALS_FILENAME = "secrets"
COLLECTION_TARGET = "reputacao_urls_v2"
MAX_CONCURRENT_TASKS = 50  # Processa 50 documentos simultaneamente


def gerar_hash_api(url):
    """Normalização conforme Seção 3.1 do TCC."""
    if not url:
        return None
    u = url.lower().strip().replace(
        "https://", "").replace("http://", "").replace("www.", "")
    u = u.split('?')[0].split('#')[0].rstrip('/')
    return hashlib.sha256(u.encode("utf-8")).hexdigest()


async def process_document(doc, db, semaphore):
    """Função trabalhadora que processa um único documento."""
    async with semaphore:
        data = doc.to_dict()
        url_original = data.get('url')
        if not url_original:
            return False

        new_id = gerar_hash_api(url_original)
        old_id = doc.id

        # Prepara os dados corrigidos
        data['id'] = new_id
        data['status'] = 'phishing'
        data['verificado_sistema'] = True
        data['last_updated'] = firestore.SERVER_TIMESTAMP

        try:
            if new_id != old_id:
                # Operação de migração: Cria novo e deleta antigo
                batch = db.batch()
                batch.set(db.collection(
                    COLLECTION_TARGET).document(new_id), data)
                batch.delete(db.collection(COLLECTION_TARGET).document(old_id))
                await batch.commit()
            else:
                # Apenas atualização
                await db.collection(COLLECTION_TARGET).document(old_id).update({
                    'id': new_id,
                    'status': 'phishing',
                    'verificado_sistema': True,
                    'last_updated': firestore.SERVER_TIMESTAMP
                })
            return True
        except Exception as e:
            print(f"Erro ao processar {url_original}: {e}")
            return False


async def patch_data():
    credentials_path = os.path.join(os.path.dirname(__file__), "secrets")
    gcp_credentials = service_account.Credentials.from_service_account_file(
        credentials_path)
    db = firestore.AsyncClient(credentials=gcp_credentials)

    print(
        f"--- INICIANDO CORREÇÃO PARALELA (Limite: {MAX_CONCURRENT_TASKS}) ---")
    start_time = time.time()

    try:
        # Busca todos os documentos (Stream com timeout longo)
        docs_stream = db.collection(COLLECTION_TARGET).stream(timeout=600)

        semaphore = asyncio.Semaphore(MAX_CONCURRENT_TASKS)
        tasks = []

        async for doc in docs_stream:
            # Cria uma tarefa para cada documento
            task = asyncio.create_task(process_document(doc, db, semaphore))
            tasks.append(task)

        print(f"Total de tarefas agendadas: {len(tasks)}. Executando...")

        # Executa todas as tarefas em paralelo
        results = await asyncio.gather(*tasks)

        success_count = sum(1 for r in results if r)
        duration = time.time() - start_time

        print("\n[FINALIZADO]")
        print(
            f"Documentos processados com sucesso: {success_count}/{len(tasks)}")
        print(
            f"Tempo total: {duration:.2f} segundos ({duration/60:.2f} minutos)")

    except Exception as e:
        print(f"\n[ERRO CRÍTICO] Falha no fluxo principal: {e}")

if __name__ == "__main__":
    asyncio.run(patch_data())
