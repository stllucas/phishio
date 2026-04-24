"""Script para ingestão de métricas e dados no Firestore."""
import asyncio
import csv
import time

from google.cloud import firestore

db = firestore.AsyncClient()

METRICS_FILE = "ingestion_metrics.csv"
MAX_POSTINGS_LIMIT = 15000
MAX_TERMS_LIMIT = 19500

async def process_term(termo, num_postings, data, start_task):
    """
    Filtro heurístico de segurança para evitar documentos > 1MB no Firestore
    e focar em termos com alto poder discriminatório.
    """
    if num_postings > MAX_POSTINGS_LIMIT:
        status = "PULADO_PESADO"
        proc_time = (time.time() - start_task) * 1000
        
        with open(METRICS_FILE, 'a', newline='') as f:
            csv.writer(f).writerow([termo, num_postings, proc_time, 0, 0, status])
        return None

    doc_ref = db.collection('reputacao_urls_v2').document(termo)
    await doc_ref.set(data)
    
    status = "SUCESSO"
    proc_time = (time.time() - start_task) * 1000
    
    with open(METRICS_FILE, 'a', newline='') as f:
        csv.writer(f).writerow([termo, num_postings, proc_time, 1, 1, status])
    return termo

async def batch_upload_index(index_data):
    tasks = []
    for i, (termo, postings) in enumerate(index_data.items()):
        if i >= MAX_TERMS_LIMIT:
            break
            
        start_task = time.time()
        tasks.append(process_term(termo, len(postings), {"postings": postings}, start_task))
    await asyncio.gather(*tasks)