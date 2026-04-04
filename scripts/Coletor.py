# ==============================================================================
# Coletor.py
# Ponto de entrada principal (Launcher) do Sistema RIWRS.
# Gerencia a execução sequencial das etapas ou via menu interativo.
# ==============================================================================
import sys
import os
import argparse

# --- 1. CONFIGURAÇÃO DE PATHS ---
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.join(PROJECT_ROOT, 'src')
TOOLS_DIR = os.path.join(PROJECT_ROOT, 'tools') # Adiciona pasta tools ao path

sys.path.append(SRC_DIR)
sys.path.append(TOOLS_DIR)

# --- 2. CONFIGURAÇÃO DE LOGGING E MÓDULOS ---
try:
    from src.Logging import setup_logging, get_log_file
    # Inicializa o logger centralizado uma única vez
    logger = setup_logging()

    # Imports dos módulos principais do sistema
    from src.Processor import main as processor_main, run_post_processing
    from src.Indexador import Indexador
    from src.Diagnostico import health_check_sistema
    from src.CalculaIDF import calcula_idf
    from src.Config import OUTPUT_DIR_TEMP, LOG_DIR_OUTPUT
    # O SearchEngine só é importado pelas interfaces (CLI/GUI) quando necessário
    from src.CLI import CLI
    from src.GUI import iniciar_gui as iniciar_gui_app

    # Tenta importar as ferramentas da pasta tools
    try:
        from tools.MigrarIndice import migrar_indice as run_migration_tool
    except ImportError:
        logger.warning("Ferramenta 'tools/MigrarIndice.py' não encontrada. A etapa de migração não estará disponível.")
        run_migration_tool = None

except ImportError as e:
    print("-" * 50)
    print("ERRO CRÍTICO DE IMPORTAÇÃO!")
    print(f"Detalhe do Erro: {e}")
    print("Verifique se o ambiente virtual (venv) está ativado e as dependências instaladas.")
    print("-" * 50)
    sys.exit(1)

# ==============================================================================
# FUNÇÕES DE EXECUÇÃO DAS ETAPAS
# ==============================================================================

def rodar_coleta():
    logger.info("ETAPA 1: Iniciando Coleta e Pós-processamento.")
    collection_successful, attempted_urls = processor_main()
    run_post_processing(collection_successful, attempted_urls)
    logger.info("ETAPA 1: Finalizada.")

def rodar_indexacao():
    logger.info("ETAPA 2: Iniciando Indexação (Geração do Índice Monolítico).")
    log_file_path = get_log_file()
    # A função retorna tupla: (indice, mapa, msg_erro)
    indice_invertido, document_map, msg_erro = Indexador.construir_indice_invertido(log_file_path, OUTPUT_DIR_TEMP)
    if indice_invertido and document_map:
        Indexador.salvar_indice(indice_invertido, document_map, LOG_DIR_OUTPUT)
        logger.info("ETAPA 2: Indexação concluída com sucesso.")
    else:
        logger.error(f"ETAPA 2: Falha na indexação. Motivo: {msg_erro}")

def rodar_calculo_idf():
    logger.info("ETAPA 3: Iniciando cálculo de IDF Global.")
    calcula_idf()
    logger.info("ETAPA 3: Cálculo de IDF finalizado.")

def rodar_migracao():
    logger.info("ETAPA 4: Iniciando Migração e Otimização do Índice (RAM/SSD).")
    if run_migration_tool:
        logger.info("Executando ferramenta 'MigrarIndice.py'...")
        run_migration_tool()
        logger.info("ETAPA 4: Migração finalizada. Índice otimizado criado.")
    else:
        logger.critical("ETAPA 4: Erro. A ferramenta de migração não foi encontrada.")

def rodar_diagnostico():
    logger.info("DIAGNÓSTICO: Iniciando verificação de saúde do sistema.")
    health_check_sistema()
    logger.info("DIAGNÓSTICO: Verificação finalizada.")

def rodar_busca_cli():
    logger.info("MODO DE BUSCA: Iniciando interface de linha de comando (CLI).")
    CLI.modo_interativo()
    logger.info("MODO DE BUSCA (CLI): Finalizado.")

def rodar_busca_gui():
    logger.info("MODO DE BUSCA: Iniciando interface gráfica (GUI).")
    # A GUI gerencia seus próprios erros de Tkinter, não precisamos tratar aqui
    iniciar_gui_app()
    logger.info("MODO DE BUSCA (GUI): Finalizado.")

# ==============================================================================
# MAIN E MENU INTERATIVO
# ==============================================================================

def main():
    parser = argparse.ArgumentParser(description="Coletor e Processador de Páginas Web para RIWRS.")
    parser.add_argument(
        '--etapa',
        type=str,
        choices=['coleta', 'indexacao', 'idf', 'migracao', 'diagnostico', 'busca_cli', 'busca_gui', 'todas'],
        help="Especifica a etapa a ser executada."
    )

    args = parser.parse_args()

    if args.etapa:
        if args.etapa == 'coleta':
            rodar_coleta()
        elif args.etapa == 'indexacao':
            rodar_indexacao()
        elif args.etapa == 'idf':
            rodar_calculo_idf()
        elif args.etapa == 'migracao':
            rodar_migracao()
        elif args.etapa == 'diagnostico':
            rodar_diagnostico()
        elif args.etapa == 'busca_cli':
            rodar_busca_cli()
        elif args.etapa == 'busca_gui':
            rodar_busca_gui()
        elif args.etapa == 'todas':
            logger.info("Executando fluxo completo de indexação (Etapas 1 a 4)...")
            rodar_coleta()
            rodar_indexacao()
            rodar_calculo_idf()
            rodar_migracao()
            logger.info("Fluxo completo finalizado. O sistema está pronto para buscas.")
    else:
        # Se nenhum argumento for fornecido, exibe o menu interativo
        exibir_menu_interativo()

def exibir_menu_interativo():
    menu_opcoes = {
        '1': ("Executar Fluxo Completo (Coleta -> Indexação -> IDF -> Migração)", lambda: (rodar_coleta(), rodar_indexacao(), rodar_calculo_idf(), rodar_migracao())),
        '2': ("Etapa 1: Coleta e Pós-processamento", rodar_coleta),
        '3': ("Etapa 2: Indexação (Geração do JSON gigante)", rodar_indexacao),
        '4': ("Etapa 3: Cálculo de IDF Global", rodar_calculo_idf),
        '5': ("Etapa 4: Migração/Otimização do Índice (Geração RAM/SSD)", rodar_migracao),
        '6': ("BUSCA: Interface de Linha de Comando (CLI)", rodar_busca_cli),
        '7': ("BUSCA: Interface Gráfica (GUI)", rodar_busca_gui),
        '8': ("Ferramentas: Verificar Saúde do Sistema (Diagnóstico)", rodar_diagnostico),
        '0': ("Sair", sys.exit)
    }

    while True:
        print("\n" + "="*60)
        print("SISTEMA DE RECUPERAÇÃO DE INFORMAÇÃO - RIWRS (MENU PRINCIPAL)")
        print("="*60)
        for chave, (descricao, _) in menu_opcoes.items():
            # Formatação para alinhar as opções de dois dígitos (se houver) e o zero
            prefix = f"[{chave}]"
            print(f"{prefix:<4} {descricao}")
        print("-" * 60)
        
        escolha = input(f"Selecione uma opção: ").strip()
        
        if escolha in menu_opcoes:
            descricao, funcao = menu_opcoes[escolha]
            logger.info(f"Opção de menu selecionada: [{escolha}] {descricao}")
            print(f"\n--- Iniciando: {descricao} ---\n")
            try:
                funcao()
            except Exception as e:
                logger.critical(f"Erro crítico durante a execução da opção [{escolha}]: {e}", exc_info=True)
                print(f"\nERRO: Ocorreu uma falha crítica. Verifique os logs.")
            
            if escolha != '0':
                print("\nProcesso concluído. Retornando ao menu principal...")
        else:
            print("\nOpção inválida. Por favor, tente novamente.")
            logger.warning(f"Tentativa de seleção de menu inválida: '{escolha}'")

if __name__ == '__main__':
    logger.info("Ambiente inicializado. Iniciando o Coletor (Launcher).")
    main()