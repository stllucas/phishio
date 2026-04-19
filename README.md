# Phishio: Detecção Colaborativa de Phishing em Tempo Real

O **Phishio** é um sistema híbrido para detecção de ameaças de *phishing* em tempo real, desenvolvido como um Trabalho de Conclusão de Curso (TCC). 

## Proposta do Projeto

Ameaças de *phishing* estão cada vez mais rápidas e sofisticadas. Defesas tradicionais baseadas em listas de bloqueio (blacklists) estáticas frequentemente falham em detectar ataques de "hora zero" (zero-hour), dado o curto ciclo de vida das páginas maliciosas e o uso de hospedagens legítimas em nuvem. 

Para mitigar esse problema, o Phishio propõe uma abordagem dupla que combina:
1. **Recuperação de Informação:** Utiliza o rigor matemático do Modelo Vetorial (com ponderação TF-IDF e Similaridade do Cosseno) para processar e analisar tecnicamente o conteúdo textual das páginas acessadas em tempo real.
2. **Crowdsourcing:** Estabelece uma camada colaborativa onde o consenso e o feedback dos usuários ajudam a refinar a classificação final das URLs, reduzindo falsos positivos e identificando ameaças que algoritmos puramente matemáticos podem deixar passar.

## Arquitetura

O sistema é estruturado em uma arquitetura Cliente-Servidor distribuída:
*   **Módulo Cliente (Extensão para Google Chrome):** Construída sob o padrão Manifest V3, opera em segundo plano analisando as páginas visitadas. Em caso de ameaça, injeta uma tela de bloqueio (overlay) alertando o usuário, além de coletar votos de reputação (seguro ou *phishing*).
*   **API Backend (Python/FastAPI):** Responsável pela análise de conteúdo através do motor vetorial e pela comunicação com o Google Firestore para gerenciamento dinâmico da reputação das URLs com base no consenso da comunidade.

## Configurando o Ambiente

Para facilitar a configuração do ambiente de desenvolvimento em máquinas Windows, o projeto inclui um script de automação.

**Pré-requisitos:** Python 3.10 ou superior instalado e configurado nas variáveis de ambiente.

### 1. Executando o Setup Automático

Navegue até a pasta `scripts` e execute o arquivo `setup.bat`. Este script irá preparar todo o terreno:
1.  Criar um ambiente virtual Python (`venv`) para isolar as dependências.
2.  Ativar o ambiente virtual.
3.  Atualizar o `pip` e instalar as dependências listadas no `requirements.txt` (FastAPI, Uvicorn, NLTK, Firebase-Admin, etc.).
4.  Baixar os dados linguísticos necessários para o processamento de texto (NLTK).
5.  Verificar e otimizar os índices de dados para a busca vetorial.

### 2. Iniciando a API

Após a conclusão do setup, abra seu terminal na raiz do projeto e execute:
```bash
.\venv\Scripts\activate
cd backend
py -m uvicorn main:app --reload
```
O servidor estará ativo e pronto para receber requisições da extensão.

## Carregando a Extensão (Modo do Desenvolvedor)

Com o backend em execução, o próximo passo é instalar a extensão no seu navegador para atuar como módulo cliente:

1.  Abra o Google Chrome e digite `chrome://extensions/` na barra de endereços.
2.  No canto superior direito, ative a chave **"Modo do desenvolvedor"**.
3.  Clique no botão **"Carregar sem compactação"** que aparecerá no canto superior esquerdo.
4.  Navegue até a pasta deste projeto e selecione o diretório `extension`.
5.  A extensão Phishio agora estará ativa e monitorando sua navegação.

## Agradecimentos

Gostaríamos de registrar nossos profundos agradecimentos à orientadora do projeto, **Prof.ª Dr.ª Sinaide Nunes Bezerra**, pelo suporte, direcionamento e incentivo acadêmico ao longo desta jornada. Além da dedicação da dupla de autores, **Pedro Henrique Gomes Lückeroth** e **Lucas dos Santos Lima**, que colaboraram nas etapas, desde a pesquisa e fundamentação teórica até a concepção arquitetural e desenvolvimento da solução.
