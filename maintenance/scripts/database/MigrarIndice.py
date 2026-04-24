"""Script para converter o índice invertido monolítico (JSON) em formato híbrido (Mapa JSON + Binário)."""
import json
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import ijson
    from tqdm import tqdm

    from runtime.core.Config import LOG_DIR_OUTPUT
except ImportError as e:
    print(f"Erro de importação: {e}")
    print("Verifique se está rodando do ambiente virtual e se 'ijson' e 'tqdm' estão instalados.")
    sys.exit(1)

INPUT_INDICE_JSON = os.path.join(LOG_DIR_OUTPUT, 'indice_invertido.json')

OUTPUT_VOCAB_JSON = os.path.join(
    LOG_DIR_OUTPUT, 'vocabulario.json')
OUTPUT_POSTINGS_BIN = os.path.join(
    LOG_DIR_OUTPUT, 'postings.bin')


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

    try:
        with open(OUTPUT_POSTINGS_BIN, 'wb') as f_bin, open(INPUT_INDICE_JSON, 'rb') as f_in:
            iterable = ijson.kvitems(f_in, '')

            for termo, dados in tqdm(iterable, desc="Processando termos"):
                df = dados.get('df', 0)
                postings_dict = dados.get('postings', {})

                if not postings_dict:
                    continue

                postings_bytes = json.dumps(
                    postings_dict, ensure_ascii=False, separators=(',', ':')).encode('utf-8')

                start_offset = f_bin.tell()

                f_bin.write(postings_bytes)

                length = len(postings_bytes)

                vocabulario_map[termo] = {
                    'df': df,
                    'offset': start_offset,
                    'length': length
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

        size_vocab_mb = os.path.getsize(OUTPUT_VOCAB_JSON) / (1024 * 1024)
        size_bin_gb = os.path.getsize(
            OUTPUT_POSTINGS_BIN) / (1024 * 1024 * 1024)
        print(f"Tamanho estimado na RAM (Vocabulário): {size_vocab_mb:.2f} MB")
        print(f"Tamanho no SSD (Postings Binário):     {size_bin_gb:.2f} GB")

    except Exception as e:
        print(f"\nERRO CRÍTICO DURANTE A MIGRAÇÃO: {e}")


if __name__ == '__main__':
    migrar_indice()
