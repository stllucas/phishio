"""Script para geração de gráficos de dispersão referentes à densidade do índice invertido."""
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os


def gerar_grafico_tcc():
    arquivo_csv = 'metrics_migration.csv'

    if not os.path.exists(arquivo_csv):
        print(f"Erro: O arquivo {arquivo_csv} não foi encontrado.")
        return

    try:
        df = pd.read_csv(arquivo_csv, encoding='utf-8', on_bad_lines='skip')
    except UnicodeDecodeError:
        df = pd.read_csv(arquivo_csv, encoding='latin-1', on_bad_lines='skip')

    df_ok = df[df['status'] == 'OK'].copy()
    df_ok['tamanho_postings'] = pd.to_numeric(df_ok['tamanho_postings'])
    df_ok['tempo_upload_s'] = pd.to_numeric(df_ok['tempo_upload_s'])

    if df_ok.empty:
        print("Nenhum dado válido para plotagem.")
        return

    plt.figure(figsize=(10, 6))
    sns.set_style("whitegrid")

    plot = sns.regplot(
        data=df_ok,
        x='tamanho_postings',
        y='tempo_upload_s',
        scatter_kws={'alpha': 0.4, 'color': '#34495e'},
        line_kws={'color': 'red', 'label': 'Tendência de Escala'}
    )

    plt.title('Análise de Densidade de Termos no Índice Invertido', fontsize=14)
    plt.xlabel('Quantidade de Documentos (Postings)', fontsize=12)
    plt.ylabel('Tempo de Resposta Firestore (Segundos)', fontsize=12)
    plt.legend()

    plt.tight_layout()
    plt.savefig('grafico_latencia_tcc.png', dpi=300)
    print(f"Sucesso! Gráfico gerado a partir de {len(df_ok)} termos.")


if __name__ == "__main__":
    gerar_grafico_tcc()
