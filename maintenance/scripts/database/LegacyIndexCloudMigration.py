"""Script para migração legada do índice invertido para a nuvem Firestore."""
import firebase_admin
from firebase_admin import credentials, firestore
import ijson
import os
import json
import time
import csv
from multiprocessing import Process, Queue, Value, Lock
from tqdm import tqdm

CREDENTIALS_PATH = "tcc-coletor-web-firebase-adminsdk-fbsvc-9a87e2278a.json"
CHECKPOINT_FILE = 'migration_checkpoint.json'
METRICS_FILE = 'metrics_migration.csv'
JSON_SOURCE = 'logs/indice_invertido.json'
LIMITE_TERMOS = 73140
NUM_WORKERS = 8
QUEUE_SIZE = 300
TIMEOUT_HTTP = 120.0

csv_lock = Lock()


def carregar_checkpoint():
    if os.path.exists(CHECKPOINT_FILE):
        with open(CHECKPOINT_FILE, 'r') as f:
            return json.load(f).get('ultimo_indice', 0)
    return 0


def salvar_checkpoint(indice):
    with open(CHECKPOINT_FILE, 'w') as f:
        json.dump({'ultimo_indice': indice}, f)


def inicializar_csv():
    if not os.path.exists(METRICS_FILE):
        with open(METRICS_FILE, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['termo', 'tamanho_postings', 'tempo_proc_ms',
                            'tempo_upload_s', 'tentativa', 'status'])


def worker_upload(queue, checkpoint_val):
    cred = credentials.Certificate(CREDENTIALS_PATH)
    app_name = f"worker-{os.getpid()}"

    try:
        app = firebase_admin.initialize_app(cred, name=app_name)
        db = firestore.client(app=app)
    except Exception as e:
        print(f"Erro ao inicializar worker {app_name}: {e}")
        return

    while True:
        item = queue.get()
        if item is None:
            break

        start_task = time.time()
        idx, termo, dados = item

        termo_limpo = str(termo).replace("/", "_").strip()
        num_postings = len(dados.get('postings', {}))

        if num_postings > 15000:
            status = "PULADO_PESADO"
            proc_time = (time.time() - start_task) * 1000
            with csv_lock:
                with open(METRICS_FILE, 'a', newline='') as f:
                    csv.writer(f).writerow(
                        [termo_limpo, num_postings, proc_time, 0, 0, status])
            continue

        proc_time = (time.time() - start_task) * 1000
        sucesso = False

        for tentativa in range(1, 5):
            try:
                start_upload = time.time()
                batch = db.batch()
                doc_ref = db.collection(
                    'indice_invertido').document(termo_limpo)
                batch.set(doc_ref, dados)
                batch.commit(timeout=TIMEOUT_HTTP)
                upload_time = time.time() - start_upload

                with csv_lock:
                    with open(METRICS_FILE, 'a', newline='') as f:
                        csv.writer(f).writerow(
                            [termo_limpo, num_postings, proc_time, upload_time, tentativa, "OK"])

                sucesso = True
                break
            except Exception:
                time.sleep(2)

        if not sucesso:
            with csv_lock:
                with open(METRICS_FILE, 'a', newline='') as f:
                    csv.writer(f).writerow(
                        [termo_limpo, num_postings, proc_time, 0, 3, "FALHA_TIMEOUT"])

        with checkpoint_val.get_lock():
            if idx > checkpoint_val.value:
                checkpoint_val.value = idx
                if idx % 20 == 0:
                    salvar_checkpoint(idx)


def migrar_paralelo():
    inicializar_csv()
    inicio = carregar_checkpoint()
    print(f"\n[SISTEMA] Iniciando esteira paralela com {NUM_WORKERS} workers.")
    print(f"[INFO] Retomando do índice: {inicio}")

    queue = Queue(maxsize=QUEUE_SIZE)
    checkpoint_val = Value('i', inicio)

    workers = []
    for _ in range(NUM_WORKERS):
        p = Process(target=worker_upload, args=(queue, checkpoint_val))
        p.start()
        workers.append(p)

    barra = tqdm(total=LIMITE_TERMOS, initial=inicio, desc="Migração em Curso")

    try:
        with open(JSON_SOURCE, 'r', encoding='utf-8') as f:
            objetos = ijson.kvitems(f, '')
            contador = 0

            for termo, dados in objetos:
                if contador < inicio:
                    contador += 1
                    continue
                if contador >= LIMITE_TERMOS:
                    break

                queue.put((contador, termo, dados))
                contador += 1

                barra.n = checkpoint_val.value
                barra.refresh()

    except KeyboardInterrupt:
        print("\n[AVISO] Interrupção manual detectada. Finalizando workers...")
    finally:
        for _ in range(NUM_WORKERS):
            queue.put(None)
        for p in workers:
            p.join()
        barra.close()
        print(
            f"\n[FINALIZADO] Checkpoint guardado no índice: {checkpoint_val.value}")


if __name__ == "__main__":
    migrar_paralelo()
