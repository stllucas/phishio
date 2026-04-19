@echo off
REM Altera a pagina de codigos para UTF-8 para exibir acentos corretamente no terminal
chcp 65001 > nul

REM =================================================================
REM Script de Setup, Instalacao e Atualizacao de Dependencias (Windows)
REM PROJETO PHISHIO - ARQUITETURA MONOREPO
REM =================================================================
REM Este script automatiza as seguintes tarefas:
REM 1. Cria um ambiente virtual chamado 'venv' (se nao existir).
REM 2. Ativa o ambiente virtual.
REM 3. Atualiza o 'pip' para a versao mais recente.
REM 4. Instala dependencias via requirements.txt (ou fallback manual).
REM 5. Baixa os dados linguisticos necessarios para o NLTK.
REM 6. Executa a migracao do indice para o formato otimizado, se necessario.
REM =================================================================

REM --- PASSO 1 ---
echo [1/6] Criando Ambiente Virtual (venv)...
if exist venv\ goto :VenvExists
py -m venv venv
if not exist venv\Scripts\activate.bat goto :VenvError
echo [OK] Ambiente virtual 'venv' criado com sucesso.
goto :Step2

:VenvExists
echo [INFO] Ambiente virtual 'venv' ja existe. Pulando criacao.
goto :Step2

:VenvError
echo.
echo ==============================================================
echo [ERRO CRITICO] Falha ao criar o ambiente virtual.
echo Verifique se o Python esta instalado e adicionado ao PATH do Windows.
echo ==============================================================
pause
exit /b 1

REM --- PASSO 2 ---
:Step2
echo.
echo [2/6] Ativando ambiente virtual...
call .\venv\Scripts\activate

REM --- PASSO 3 ---
echo.
echo [3/6] Atualizando o PIP para a versao mais recente...
py.exe -m pip install --upgrade pip

REM --- PASSO 4 ---
echo.
echo [4/6] Instalando e atualizando dependencias do projeto...
REM Verifica se existe o arquivo de requirements na raiz do projeto ou no backend
if exist "requirements.txt" (
    echo [INFO] Encontrado requirements.txt na raiz do projeto. Instalando e atualizando pacotes...
    pip install --upgrade -r requirements.txt
) else if exist "backend\requirements.txt" (
    echo [INFO] Encontrado backend\requirements.txt. Instalando e atualizando pacotes...
    pip install --upgrade -r backend\requirements.txt
) else (
    echo [INFO] requirements.txt nao encontrado. Instalando pacotes principais manualmente...
    pip install --upgrade fastapi uvicorn google-cloud-firestore pandas requests tqdm beautifulsoup4 nltk ijson firebase-admin
)

REM --- PASSO 5 ---
echo.
echo [5/6] Baixando dados linguisticos do NLTK (stopwords, punkt)...
py -m nltk.downloader -q stopwords punkt
echo [OK] Dados linguisticos verificados/baixados.

REM --- PASSO 6 ---
echo.
echo [6/6] Verificando necessidade de migracao de indice (Otimizacao RAM/SSD)...

REM Variaveis de caminho adaptadas para o padrão Monorepo
set "INDICE_JSON=backend\logs\indice_invertido.json"
set "POSTINGS_BIN=backend\logs\postings.bin"
set "MIGRATION_SCRIPT=scripts\data_prep\MigrarIndice.py"

REM Checagem 1: Se o arquivo fonte NAO existe, pula tudo.
if not exist "%INDICE_JSON%" goto :SkipMigrationSourceMissing

REM Checagem 2: Se o arquivo destino JA existe, nao precisa fazer de novo.
if exist "%POSTINGS_BIN%" goto :SkipMigrationAlreadyDone

REM Checagem 3: Verifica se o script de migracao esta na pasta scripts
if not exist "%MIGRATION_SCRIPT%" goto :SkipMigrationScriptMissing

REM Se chegou aqui: Fonte existe E destino nao existe. Executa migracao.
echo [INFO] Arquivo de indice monolitico encontrado.
echo [INFO] Iniciando migracao automatica para formato otimizado (Isso pode demorar)...
echo.
py "%MIGRATION_SCRIPT%"
goto :MigrationEnd

:SkipMigrationAlreadyDone
echo [INFO] O indice ja esta migrado e otimizado para SSD. Pulando etapa.
goto :MigrationEnd

:SkipMigrationSourceMissing
echo [AVISO] '%INDICE_JSON%' nao encontrado.
echo Se esta for uma instalacao limpa, voce precisara rodar os scripts de coleta primeiro.
goto :MigrationEnd

:SkipMigrationScriptMissing
echo [AVISO] Script de migracao '%MIGRATION_SCRIPT%' nao encontrado na pasta scripts.
echo A migracao automatica foi pulada.
goto :MigrationEnd

:MigrationEnd
REM --- FIM ---
echo.
echo ==========================================================
echo AMBIENTE PHISHIO ATUALIZADO E CONFIGURADO COM SUCESSO!
echo ==========================================================
echo.
echo [COMO INICIAR A SUA API / BACK-END]
echo   1. Digite no terminal:  .\venv\Scripts\activate
echo   2. Navegue ate a pasta: cd backend
echo   3. Inicie o servidor:   py -m uvicorn main:app --reload
echo.
echo [COMO TESTAR A EXTENSAO / FRONT-END]
echo   1. Abra o Chrome e acesse a URL: chrome://extensions/
echo   2. Ative o "Modo do desenvolvedor" (canto superior direito).
echo   3. Clique em "Carregar sem compactacao" e selecione a pasta 'extension' deste projeto.
echo.
echo [MANUTENCAO DO PROJETO]
echo   Lembre-se: Caso novos pacotes ou dependencias sejam usados no projeto,
echo   eles devem ser inseridos no arquivo 'requirements.txt'.
echo   Isso garante que o ambiente seja instalado corretamente por todos.
echo.
echo Para mais informacoes, consulte o arquivo README.md
echo.

pause
cls