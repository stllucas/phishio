import os
import sys
import asyncio
from google.cloud import firestore
from google.oauth2 import service_account

# --- Configuração ---
# Altere para o nome da sua coleção, se for diferente
COLLECTION_NAME = 'documentos_processados'
# Caminho para o arquivo de credenciais na raiz do projeto
CREDENTIALS_FILENAME = 'secrets'

# Mapeamento para tradução dos valores de status
STATUS_VALUE_MAP = {
    'suspeito': 'suspicious',
    'seguro': 'safe',
    'perigoso': 'phishing'
    # Adicione outros mapeamentos se necessário
}

async def migrate_data():
    """
    Executa a migração dos nomes de campos e valores de status no Firestore.
    """
    print("Iniciando script de migração do Firestore...")

    try:
        # O script está em 'scripts', então subimos um nível para achar 'secrets'
        credentials_path = os.path.join(os.path.dirname(__file__), '..', CREDENTIALS_FILENAME)
        if not os.path.exists(credentials_path):
            raise FileNotFoundError(f"Arquivo de credenciais '{CREDENTIALS_FILENAME}' não encontrado na pasta raiz do projeto.")

        gcp_credentials = service_account.Credentials.from_service_account_file(credentials_path)
        db = firestore.AsyncClient(credentials=gcp_credentials)
        print("Cliente Firestore inicializado com sucesso.")
    except Exception as e:
        print(f"[ERRO] Falha ao inicializar o cliente Firestore: {e}")
        sys.exit(1)

    # Pega todos os documentos da coleção
    docs_stream = db.collection(COLLECTION_NAME).stream()
    
    # Usa um batch para realizar as operações em lote
    batch = db.batch()
    docs_processed = 0
    batch_count = 0

    print(f"Buscando documentos na coleção '{COLLECTION_NAME}' para padronização...")

    async for doc in docs_stream:
        try:
            doc_data = doc.to_dict()
            updated_data = doc_data.copy() # Trabalha em uma cópia para segurança
            needs_update = False

            # 1. Renomeia os campos que existem no documento
            if 'verificado_sistema' in updated_data:
                updated_data['system_verified'] = updated_data.pop('verificado_sistema')
                needs_update = True
            
            if 'votos_phishing' in updated_data:
                updated_data['phishing_votes'] = updated_data.pop('votos_phishing')
                needs_update = True

            if 'votos_seguro' in updated_data:
                updated_data['safe_votes'] = updated_data.pop('votos_seguro')
                needs_update = True

            # 2. Traduz o valor do status, se necessário
            if 'status' in updated_data and updated_data['status'] in STATUS_VALUE_MAP:
                updated_data['status'] = STATUS_VALUE_MAP[updated_data['status']]
                needs_update = True

            # Se o documento precisou de alguma atualização, adiciona ao lote
            if needs_update:
                batch.set(doc.reference, updated_data)
                docs_processed += 1
                batch_count += 1
                print(f"  - Documento {doc.id} marcado para atualização.")

            # O Firestore tem um limite de 500 operações por batch
            if batch_count >= 499:
                print("\nEnviando lote de atualizações para o Firestore...\n")
                await batch.commit()
                # Reinicia o batch
                batch = db.batch()
                batch_count = 0

        except Exception as e:
            print(f"[AVISO] Erro ao processar o documento {doc.id}: {e}. Pulando.")

    # Commita o último lote, se houver algo nele
    if batch_count > 0:
        print(f"\nEnviando o lote final de {batch_count} atualizações para o Firestore...\n")
        await batch.commit()

    if docs_processed > 0:
        print(f"Migração concluída! {docs_processed} documentos foram atualizados na coleção '{COLLECTION_NAME}'.")
    else:
        print("Nenhum documento precisou de atualização. O banco de dados já parece estar padronizado.")

async def main():
    print("======================================================================")
    print("AVISO: Este script fará alterações DESTRUTIVAS no seu banco de dados.")
    print("É ALTAMENTE RECOMENDADO que você faça um BACKUP da sua coleção")
    print(f"'{COLLECTION_NAME}' antes de continuar.")
    print("======================================================================")
    
    answer = input("Você fez um backup e deseja continuar? (s/n): ").lower().strip()
    
    if answer == 's':
        await migrate_data()
    else:
        print("Migração cancelada pelo usuário.")

if __name__ == '__main__':
    # Altera a pagina de codigos para UTF-8 no Windows para exibir acentos
    if sys.platform == "win32":
        os.system("chcp 65001 > nul")
    asyncio.run(main())