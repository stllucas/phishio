import json
import math
import os
from tqdm import tqdm
from Config import LOG_DIR

# Caminhos dos arquivos dentro da pasta `logs` (definida em src/config.py)
INDICE_PATH = os.path.join(LOG_DIR, 'indice_invertido.json')
DOC_MAP_PATH = os.path.join(LOG_DIR, 'document_map.json')
IDF_OUTPUT_PATH = os.path.join(LOG_DIR, 'idf.json')

def calcula_idf():
    # Carrega o mapa de documentos para obter N
    with open(DOC_MAP_PATH, 'r', encoding='utf-8') as f:
        doc_map = json.load(f)
    N = len(doc_map)

    # Tenta carregar o índice inteiro em memória (pode falhar se o arquivo for muito grande)

    try:
        try:
            with open(INDICE_PATH, 'r', encoding='utf-8') as f:
                indice = json.load(f)

            print('Calculando IDF para todos os termos...')
            idf_dict = {}
            for termo, dados in tqdm(indice.items(), total=len(indice), desc='Calculando IDF'):
                df = dados.get('df', 0)
                idf = math.log(N / df) if df > 0 else 0.0
                idf_dict[termo] = idf

            # Salva o resultado
            with open(IDF_OUTPUT_PATH, 'w', encoding='utf-8') as f:
                json.dump(idf_dict, f, ensure_ascii=False, indent=2)

            print(f'IDF calculado para {len(idf_dict)} termos. Resultado salvo em {IDF_OUTPUT_PATH}')

        except MemoryError:
            # Fallback: parsing incremental com ijson para índices muito grandes
            try:
                import ijson
            except Exception:
                raise RuntimeError("Arquivo muito grande para carregar em memória e o pacote 'ijson' não está disponível. Instale com: pip install ijson")

            print('Índice muito grande: usando parser incremental (ijson).')
            # Abre o arquivo de saída e escreve objetos incrementalmente
            with open(INDICE_PATH, 'r', encoding='utf-8') as fin, open(IDF_OUTPUT_PATH, 'w', encoding='utf-8') as fout:
                fout.write('{\n')
                first = True
                # ijson.kvitems itera sobre pares (key, value) do objeto JSON no topo
                for termo, dados in ijson.kvitems(fin, ''):
                    df = dados.get('df', 0)
                    idf = math.log(N / df) if df > 0 else 0.0
                    if not first:
                        fout.write(',\n')
                    else:
                        first = False
                    json.dump(termo, fout, ensure_ascii=False)
                    fout.write(': ')
                    json.dump(idf, fout, ensure_ascii=False)
                fout.write('\n}')
            print(f'IDF calculado com parser incremental e salvo em {IDF_OUTPUT_PATH}')
    except Exception as e:
        print(f'ERRO ao calcular IDF: {e.__class__.__name__}: {e}')
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    calcula_idf()
