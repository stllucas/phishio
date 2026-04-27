#!/bin/bash
# Script de inicialização e configuração do ambiente Phishio para Linux.

echo "----------------------------------------------------------"
echo "PHISHIO - AMBIENTE DE PRODUCAO/MANUTENCAO"
echo "----------------------------------------------------------"

echo "[1/6] Preparando Ambiente Virtual (venv)..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "[OK] Ambiente virtual 'venv' criado."
else
    echo "[INFO] Ambiente virtual 'venv' ja existe."
fi

echo -e "\n[2/6] Ativando ambiente virtual..."
source ./venv/bin/activate

echo -e "\n[3/6] Atualizando o PIP..."
pip install --upgrade pip

echo -e "\n[4/6] Instalando dependências do projeto..."
if [ -f "requirements.txt" ]; then
    pip install --upgrade -r requirements.txt
else
    echo -e "[ERRO] requirements.txt não encontrado. Abortando para evitar ambiente inconsistente."
    exit 1
fi

echo -e "\n[5/6] Baixando dados linguísticos do NLTK..."
python3 -m nltk.downloader -q stopwords punkt
echo "[OK] Dados linguísticos verificados."

echo -e "\n[6/6] Verificando integridade dos dados (Camada Warm)..."
INDICE_FONTE="maintenance/data-raw/indice_invertido.json"
POSTINGS_BIN="data/postings.bin"
MIGRATION_SCRIPT="maintenance/scripts/database/MigrarIndice.py"

if [ ! -f "$INDICE_FONTE" ]; then
    echo "[INFO] Indice fonte (4.6GB) nao detectado localmente. Pulando migracao."
elif [ -f "$POSTINGS_BIN" ]; then
    echo "[INFO] Artefato binario ja existe em data/. Pronto para uso."
elif [ ! -f "$MIGRATION_SCRIPT" ]; then
    echo "[ERRO] Script de migracao nao encontrado em maintenance/."
else
    echo "[ALERTA] Indice binario faltando. Iniciando conversao..."
    python3 "$MIGRATION_SCRIPT"
fi

echo -e "\n=========================================================="
echo "      AMBIENTE CONFIGURADO COM SUCESSO (LINUX VM)         "
echo "=========================================================="
echo -e "\n[COMO INICIAR O BACKEND]"
echo "  1. Ative o venv:    source venv/bin/activate"
echo "  2. Entre na pasta:  cd runtime"
echo "  3. Rode a API:      python3 -m uvicorn main:app --host 0.0.0.0 --port 8000"
echo -e "\n[DICA DE PRODUCAO]"
echo "  Para manter a API rodando apos fechar o SSH, use:"
echo "  nohup python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 > api.log 2>&1 &"
echo -e "\n[COMO TESTAR A API]"
echo "  Na raiz do projeto (com venv ativado), rode: pytest"
echo "----------------------------------------------------------"