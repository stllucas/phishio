# ==============================================================================
# Classe responsável por analisar o log e gerar relatórios de sucesso/erro.
# ==============================================================================
import pandas as pd
import os

class GeradorRelatorio:
    """
    Analisa um arquivo de log CSV e gera dois novos arquivos CSV
    separando os resultados de sucesso e erro.
    """

    @staticmethod
    def gerar_relatorios_consolidados(log_file_path, base_path):
        """
        Gera dois novos CSVs (Sucesso e Erro) a partir do log principal.

        :param log_file_path: Caminho completo para o arquivo de log principal (collection_log.csv).
        :param base_path: Diretório base onde os novos arquivos serão salvos.
        :return: Um dicionário com os caminhos dos relatórios gerados e as contagens.
        """
        try:
            if not os.path.exists(log_file_path):
                print(f"Aviso: Arquivo de log principal não encontrado em {log_file_path}.")
                return {"success_path": None, "error_path": None, "total": 0, "success_count": 0, "error_count": 0}

            # Lê o log geral
            log_df = pd.read_csv(log_file_path, on_bad_lines='skip')
            
            # Remove linhas duplicadas, mantendo a mais recente (opcional, mas bom)
            log_df = log_df.sort_values(by='original_url', ascending=False).drop_duplicates(subset=['original_url'], keep='last')

            # Filtra Sucesso
            success_df = log_df[log_df['status'].str.startswith('SUCCESS', na=False)]
            success_output_path = os.path.join(base_path, 'relatorio_sucesso.csv')
            
            # Filtra Erro
            # Inclui ERROR_ e FATAL_ERROR_
            error_df = log_df[log_df['status'].str.startswith(('ERROR_', 'FATAL_ERROR_'), na=False)]
            error_output_path = os.path.join(base_path, 'relatorio_erros.csv')

            # Salva os arquivos
            success_df.to_csv(success_output_path, index=False)
            error_df.to_csv(error_output_path, index=False)

            return {
                "success_path": success_output_path, 
                "error_path": error_output_path,
                "total": len(log_df),
                "success_count": len(success_df),
                "error_count": len(error_df)
            }

        except Exception as e:
            print(f"Erro ao gerar relatórios consolidados: {e}")
            return {"success_path": None, "error_path": None, "total": 0, "success_count": 0, "error_count": 0}