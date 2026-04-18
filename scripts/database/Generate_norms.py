import json
import math
import os
from collections import defaultdict

from tqdm import tqdm

# --- LÓGICA DE CAMINHOS DINÂMICOS (Igual ao Config.py) ---
# Se o script estiver em phishio/scripts/database/generate_norms.py, subimos 3 níveis
BASE_PATH = os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))))
LOG_DIR = os.path.join(BASE_PATH, 'data', 'logs')

# Definição dos arquivos baseada no LOG_DIR dinâmico
VOCAB_FILE = os.path.join(LOG_DIR, 'vocabulario.json')
IDF_FILE = os.path.join(LOG_DIR, 'idf.json')
POSTINGS_FILE = os.path.join(LOG_DIR, 'postings.bin')
OUTPUT_FILE = os.path.join(LOG_DIR, 'norms.json')


def generate_norms():
    print(f"DEBUG: Buscando artefatos em: {LOG_DIR}")

    if not os.path.exists(VOCAB_FILE):
        print(f"ERRO: Arquivo não encontrado: {VOCAB_FILE}")
        return

    print("Iniciando pré-cálculo de normas dos documentos...")

    with open(VOCAB_FILE, 'r') as f:
        vocab = json.load(f)
    with open(IDF_FILE, 'r') as f:
        idf_map = json.load(f)

    # Acumulador para a soma dos quadrados (tf * idf)^2
    norm_accumulators = defaultdict(float)

    with open(POSTINGS_FILE, 'rb') as bin_file:
        for termo, meta in tqdm(vocab.items(), desc="Processando termos"):
            idf = idf_map.get(termo, 0)
            if idf == 0:
                continue

            # Leitura profunda no SSD
            bin_file.seek(meta['offset'])
            bin_data = bin_file.read(meta['length'])
            postings = json.loads(bin_data.decode('utf-8'))

            for doc_id, tf in postings.items():
                # Acumula o peso ao quadrado: (tf * idf)^2
                weight = tf * idf
                norm_accumulators[str(doc_id)] += weight ** 2

    # Finaliza calculando a raiz quadrada (Norma Euclidiana)
    final_norms = {doc_id: math.sqrt(val)
                   for doc_id, val in norm_accumulators.items()}

    with open(OUTPUT_FILE, 'w') as f:
        json.dump(final_norms, f)

    print(f"\nSUCESSO! Normas geradas para {len(final_norms)} documentos.")
    print(f"Arquivo salvo em: {OUTPUT_FILE}")


if __name__ == "__main__":
    generate_norms()
