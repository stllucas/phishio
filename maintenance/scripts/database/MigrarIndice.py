# ==============================================================================
# tools/migrar_indice.py
# Script de utilidade única para converter o índice invertido monolítico (JSON gigante)
# em uma estrutura híbrida otimizada (Mapa JSON leve + Arquivo Binário denso).
# ==============================================================================
import json
import os
import sys

# Adiciona o diretório pai (raiz do projeto) ao path para importar Config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import ijson
    from tqdm import tqdm

    from runtime.core.Config import LOG_DIR_OUTPUT
except ImportError as e:
    print(f"Erro de importação: {e}")
    print("Verifique se está rodando do ambiente virtual e se 'ijson' e 'tqdm' estão instalados.")
    sys.exit(1)

# --- Configuração dos Caminhos ---
# Arquivo de entrada (Gigante)
INPUT_INDICE_JSON = os.path.join(LOG_DIR_OUTPUT, 'indice_invertido.json')

# Arquivos de saída (Otimizados)
OUTPUT_VOCAB_JSON = os.path.join(
    LOG_DIR_OUTPUT, 'vocabulario.json')  # Vai para a RAM
OUTPUT_POSTINGS_BIN = os.path.join(
    LOG_DIR_OUTPUT, 'postings.bin')   # Fica no SSD


def migrar_indice():
    print("-" * 60)
    print("INICIANDO MIGRAÇÃO DE ÍNDICE (Otimização RAM/SSD)")
    print(f"Entrada: {INPUT_INDICE_JSON}")
    print("-" * 60)

    if not os.path.exists(INPUT_INDICE_JSON):
        print(f"ERRO: Arquivo de entrada não encontrado: {INPUT_INDICE_JSON}")
        return

    vocabulario_map = {}
    termo_count = 0

    print("Lendo índice gigante e gerando arquivos otimizados...")
    print("Isso pode levar vários minutos. Por favor, aguarde.")

    # Abre o arquivo binário de saída para escrita ('wb')
    # Abre o JSON gigante de entrada para leitura ('rb')
    try:
        with open(OUTPUT_POSTINGS_BIN, 'wb') as f_bin, open(INPUT_INDICE_JSON, 'rb') as f_in:
            # Usa ijson para iterar sobre o arquivo gigante sem carregar tudo na RAM
            # kvitems itera sobre pares chave/valor do objeto raiz
            iterable = ijson.kvitems(f_in, '')

            for termo, dados in tqdm(iterable, desc="Processando termos"):
                # 1. Extrai dados relevantes
                df = dados.get('df', 0)
                postings_dict = dados.get('postings', {})

                if not postings_dict:
                    continue

                # 2. Serializa a lista de postings para uma string JSON compacta
                # e converte para bytes (utf-8)
                postings_bytes = json.dumps(
                    postings_dict, ensure_ascii=False, separators=(',', ':')).encode('utf-8')

                # 3. Obtém a posição atual do cursor no arquivo binário (Offset)
                start_offset = f_bin.tell()

                # 4. Escreve os bytes no arquivo binário
                f_bin.write(postings_bytes)

                # 5. Calcula o tamanho dos dados escritos
                length = len(postings_bytes)

                # 6. Salva os metadados no mapa do vocabulário (RAM)
                vocabulario_map[termo] = {
                    'df': df,
                    'offset': start_offset,  # Onde começa no SSD
                    'length': length        # Quanto ler do SSD
                }
                termo_count += 1

        print("\nGerando arquivo de vocabulário (JSON leve)...")
        with open(OUTPUT_VOCAB_JSON, 'w', encoding='utf-8') as f_vocab:
            json.dump(vocabulario_map, f_vocab, ensure_ascii=False, indent=2)

        print("-" * 60)
        print("MIGRAÇÃO CONCLUÍDA COM SUCESSO!")
        print(f"Termos processados: {termo_count}")
        print(f"Vocabulário (RAM) salvo em: {OUTPUT_VOCAB_JSON}")
        print(f"Postings (SSD) salvos em:    {OUTPUT_POSTINGS_BIN}")
        print("-" * 60)

        # Mostra estatísticas de tamanho
        size_vocab_mb = os.path.getsize(OUTPUT_VOCAB_JSON) / (1024 * 1024)
        size_bin_gb = os.path.getsize(
            OUTPUT_POSTINGS_BIN) / (1024 * 1024 * 1024)
        print(f"Tamanho estimado na RAM (Vocabulário): {size_vocab_mb:.2f} MB")
        print(f"Tamanho no SSD (Postings Binário):     {size_bin_gb:.2f} GB")

    except Exception as e:
        print(f"\nERRO CRÍTICO DURANTE A MIGRAÇÃO: {e}")
        # Apagar arquivos parciais em caso de erro


if __name__ == '__main__':
    migrar_indice()
