```markdown
# Relatório Final Integrado - Etapa 3: Motor de Busca e Recuperação de Informação
**Projeto:** Sistema de Recuperação de Informação para URLs de Phishing (RIWRS)
**Data da Última Atualização:** 21/11/2025

---

## 1. Introdução

Este relatório consolida as implementações realizadas na Etapa 3 do projeto RIWRS, cujo objetivo foi desenvolver um motor de busca funcional capaz de recuperar e ranquear páginas de *phishing* a partir de consultas em linguagem natural. O sistema utiliza o Modelo Vetorial, empregando o esquema de ponderação TF-IDF e a métrica de Similaridade do Cosseno para o ranqueamento.

O trabalho foi dividido em módulos interdependentes, culminando na integração centralizada no `SearchEngine.py` e na disponibilização de duas interfaces de usuário: uma via linha de comando (CLI) e uma gráfica (GUI). Um desafio crítico enfrentado foi o volume do índice invertido (4.6 GB), que exigiu soluções de arquitetura híbrida RAM/SSD para viabilizar a busca em tempo hábil além do aumento significativo de memória ao executar o programa.

---

## 2. Arquitetura do Sistema e Componentes

A arquitetura do sistema de recuperação é composta por módulos especializados que interagem para processar consultas, calcular pesos, recuperar documentos e gerar o ranking final.



### 2.1. Cálculo de Frequências Globais (IDF) - `src/CalculaIDF.py`

**Responsável:** Osvaldo Neto

Como pré-requisito para o modelo TF-IDF, foi desenvolvido um módulo para calcular o *Inverse Document Frequency* (IDF) de cada termo do vocabulário. O IDF mensura a raridade e o poder discriminante de um termo na coleção.

* **Entrada:** `logs/document_map.json` (total de documentos $N$) e `logs/indice_invertido.json` (frequência de documentos $df_t$).
* **Fórmula:** $\text{IDF}(t) = \log\left(\frac{N}{df_t}\right)$
* **Desafio de Escalabilidade:** O carregamento do índice invertido gigante (4.6 GB) na RAM era inviável.
* **Solução:** Utilização da biblioteca `ijson` para leitura e processamento incremental (streaming) do arquivo JSON, calculando o IDF termo a termo sem estourar a memória.
* **Saída:** O resultado é persistido em `logs/idf.json`, um mapa `{ "termo": valor_idf }`.

### 2.2. Processamento e Vetorização da Consulta - `SearchEngine.gerar_vetor_consulta_tfidf`

**Responsável:** Camille Irias

Este componente é a porta de entrada do motor, convertendo a consulta do usuário em um vetor de pesos TF-IDF. Para garantir a eficácia da busca, o processamento da consulta replica exatamente o pipeline utilizado na indexação.

1.  **Processamento Léxico (`_processar_texto_query`):**
    * **Normalização:** Conversão para minúsculas e remoção de pontuação/números via Regex.
    * **Tokenização:** Divisão da string em termos.
    * **Stopwords:** Remoção de palavras comuns usando o corpus do NLTK.
    * **Stemming:** Redução das palavras aos seus radicais usando o *SnowballStemmer* (Portuguese).
2.  **Geração do Vetor:** Calcula o peso de cada termo na consulta usando a fórmula $w_{t,q} = tf_{t,q} \times idf_t$, onde $tf_{t,q}$ é a frequência na consulta e $idf_t$ é recuperado do `idf.json`.

### 2.3. Orquestrador Central - `src/SearchEngine.py`

**Responsáveis:** Luana Mateus (Busca no Índice) e Lucas Lima (Mapeamento)

A classe `SearchEngine` é o núcleo do sistema, integrando todos os componentes e gerenciando o fluxo da busca. Devido ao tamanho do índice, sua arquitetura evoluiu para um modelo híbrido.

**Evolução Arquitetural (RAM/SSD):**
* **Camada Quente (RAM):** Carrega na inicialização apenas metadados leves: `vocabulario.json` (mapeia termos para offsets no disco), `idf.json` e `document_map.json`.
* **Camada Fria (SSD):** Mantém o índice invertido volumoso em um arquivo binário denso (`postings.bin`).
* **Recuperação Otimizada (`buscar_postings_por_termo`):** Para cada termo da consulta, o motor usa o vocabulário na RAM para encontrar a posição exata no SSD e realiza uma leitura cirúrgica (`seek` + `read`), recuperando apenas a lista de postings necessária com latência mínima.
* **Mapeamento de Resultados (`mapear_resultados_para_urls`):** Converte os DocIDs ranqueados (inteiros) de volta para as URLs originais utilizando o `document_map.json` carregado em memória.

### 2.4. Ranking e Similaridade - `SearchEngine.ranquear_documentos_completo`

**Responsável:** Ana Paula

Este módulo implementa o Modelo Vetorial para ordenar os documentos recuperados por relevância.

* **Métrica:** Similaridade do Cosseno, que mede o ângulo entre o vetor da consulta ($Q$) e o vetor do documento ($D$).
* **Fórmula:** $\text{sim}(Q, D) = \frac{Q \cdot D}{\|Q\| \|D\|}$
* **Processo:**
    1.  Recupera as listas de postings do SSD para os termos da consulta.
    2.  Constrói dinamicamente os vetores TF-IDF dos documentos candidatos na RAM.
    3.  Calcula a similaridade do cosseno entre o vetor da consulta e cada vetor de documento.
    4.  Ordena todos os documentos por score decrescente, permitindo a paginação posterior.

---

## 3. Fluxo Integrado de Execução da Busca

O diagrama abaixo ilustra o pipeline completo de uma operação de busca, demonstrando a integração entre os diferentes módulos do sistema, desde a entrada do usuário até a exibição dos resultados.

```

┌─────────────────────────────────────────────────────────────────┐
│ 1. PROCESSAMENTO DA CONSULTA (Camille Irias)                    │
│    - Aplicar pipeline de limpeza, stemming e remoção de         │
│      stopwords na query do usuário                              │
│    - Resultado: vetor de termos processados                     │
└──────────────────────────┬──────────────────────────────────────┘
│
┌──────────────────────────▼──────────────────────────────────────┐
│ 2. CARREGAMENTO DO ÍNDICE (Luana Mateus)                        │
│    - Buscar os termos processados no índice invertido (SSD)     │
│    - Recuperar lista de DocIDs e Term Frequencies (TF)          │
│    - Resultado: postings para cada termo da query               │
└──────────────────────────┬──────────────────────────────────────┘
│
┌──────────────────────────▼──────────────────────────────────────┐
│ 3. CÁLCULO DE PESOS IDF (Osvaldo Neto)                          │
│    - Carregar mapa IDF pré-calculado (RAM)                      │
│    - Aplicar pesos IDF aos termos da consulta                   │
│    - Calcular vetor TF-IDF da consulta                          │
│    - Resultado: consulta ponderada por raridade dos termos      │
└──────────────────────────┬──────────────────────────────────────┘
│
┌──────────────────────────▼──────────────────────────────────────┐
│ 4. RANKING VIA SIMILARIDADE DO COSSENO (Ana Paula)              │
│    - Para cada documento encontrado, calcular seu vetor TF-IDF  │
│    - Aplicar Similaridade do Cosseno entre consulta e documento │
│    - Ranquear documentos por score de similaridade (descendente)│
│    - Resultado: lista completa de documentos ordenados          │
└──────────────────────────┬──────────────────────────────────────┘
│
┌──────────────────────────▼──────────────────────────────────────┐
│ 5. MAPEAMENTO E EXIBIÇÃO (Lucas Lima + Ana Clara/GUI)           │
│    - Aplicar paginação (fatiar resultados)                      │
│    - Converter DocIDs ranqueados para URLs originais (RAM)      │
│    - Formatar resultado para exibição amigável na CLI ou GUI    │
│    - Resultado: interface clara e intuitiva para o usuário      │
└─────────────────────────────────────────────────────────────────┘

````

---

## 4. Interfaces de Usuário e Funcionalidades

O sistema oferece duas interfaces para interação, ambas consumindo o mesmo backend `SearchEngine`.

### 4.1. Interface de Linha de Comando (CLI) - `src/CLI.py`

**Responsável:** Ana Clara

Uma interface de terminal robusta e eficiente para buscas rápidas.

* **Modos:** Interativo (loop de busca) e busca única (para scripts).
* **Recursos:** Validação de pré-requisitos, tratamento de erros e exibição formatada dos resultados (Rank, Score, URL).
* **Acesso:** Via `python Coletor.py --etapa busca` ou menu principal.

### 4.2. Interface Gráfica (GUI) - `src/GUI.py`

Uma interface visual desenvolvida com Tkinter, proporcionando uma experiência similar a mecanismos de busca comerciais.

* **Design:** Layout limpo com barra de busca central e resultados formatados.
* **Paginação:** Permite navegar por todo o conjunto de resultados através de botões "Anterior" e "Próximo" no rodapé.
* **Interatividade:** As URLs nos resultados são clicáveis e abrem no navegador padrão.
* **Feedback:** Exibe o número total de resultados e o tempo de execução da busca.
* **Gestão de Memória:** Implementa um protocolo de fechamento seguro que força a liberação da memória RAM ocupada pelos mapas gigantes ao fechar a aplicação, prevenindo vazamentos de memória.

---

## 5. Estrutura de Arquivos do Projeto

A seguir, a estrutura de diretórios atualizada do projeto após a conclusão da Etapa 3, refletindo a adição de novos módulos, ferramentas e a organização dos logs e artefatos de dados.

```bash
RIWRS_2/
│
├── .gitignore                  # Arquivos ignorados pelo Git
├── Coletor.py                  # Launcher principal (Menu e CLI)
├── README.md                   # Documentação geral do projeto
├── requirements.txt            # Dependências Python do projeto
├── setup.bat                   # Script de instalação e configuração (Windows)
│
├── logs/                       # Diretório de dados e logs
│   ├── collection_log.csv      # Log mestre da coleta de URLs
│   ├── coletor_run_*.log       # Logs de execução do sistema
│   ├── diagnostico.txt         # Relatório de diagnóstico
│   ├── document_map.json       # Mapa (DocID -> URL) - RAM
│   ├── idf.json                # Pesos IDF dos termos - RAM
│   ├── indice_invertido.json   # Índice original (backup/fonte)
│   ├── postings.bin            # Índice binário otimizado - SSD
│   ├── vocabulario.json        # Metadados do índice binário - RAM
│   └── temp_html/              # Páginas HTML brutas coletadas
│
├── src/                        # Código-fonte principal
│   ├── __init__.py
│   ├── CalculaIDF.py           # Módulo de cálculo de IDF
│   ├── CLI.py                  # Interface de Linha de Comando
│   ├── Config.py               # Configurações globais
│   ├── Diagnostico.py          # Ferramentas de verificação
│   ├── GUI.py                  # Interface Gráfica (Tkinter)
│   ├── Indexador.py            # Módulo de indexação e processamento
│   ├── Logging.py              # Configuração central de logs
│   ├── Processor.py            # Processamento da coleta (threads)
│   ├── Relatorio.py            # Geração de estatísticas da coleta
│   ├── SearchEngine.py         # Motor de busca (Backend)
│   └── Verificador.py          # Validação de URLs
│
└── tools/                      # Ferramentas utilitárias
    └── MigrarIndice.py         # Script de migração (JSON -> Binário)
````

-----

## 6\. Conclusão

A Etapa 3 foi concluída com sucesso diante das entregas propostas, entregando um sistema de recuperação de informação funcional e integrado. O principal desafio técnico, a escala do índice invertido, foi superado através da implementação de uma arquitetura híbrida RAM/SSD e de técnicas de leitura incremental. O sistema final combina a precisão teórica do Modelo Vetorial com uma implementação de software e interfaces de usuário práticas, cumprindo os objetivos estabelecidos para o projeto.

```
```