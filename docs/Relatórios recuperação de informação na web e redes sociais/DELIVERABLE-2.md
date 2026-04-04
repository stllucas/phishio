Etapa 2 - Representação e Indexação

Este documento é a continuação do Relatório da Etapa 1 e detalha a implementação da fase de Representação e Indexação (Parte 2 do projeto).

## 1\. Status e Contexto da Etapa 2

A **Etapa 1 (Coleta)** foi concluída com sucesso, resultando na aquisição de **297.068 documentos HTML** únicos, prontos para serem processados. A Etapa 2 foca em transformar este vasto *corpus* de texto em uma estrutura de dados eficiente para a fase de Recuperação (Entrega 3).

| Métrica da Coleta (Base para Indexação) | Valor |
| :--- | :--- |
| **Total de Documentos de Origem (SUCCESS)** | 297.159 |
| **Documentos Encontrados em Disco (Prontos para Indexar)** | 297.068 |
| **Status da Base** | Consistente e robusta para indexação adequada à regra estabelecida de no mínimo 50.001 arquivos lidos. |

-----

## 2\. Decisão da Arquitetura de Representação

O objetivo principal desta etapa é criar uma estrutura que permita buscas rápidas e o cálculo de relevância (ranking).

### 2.1. Escolha da Estrutura de Dados (Alternativa a BDM)

| Critério | Escolha | Justificativa e Conformidade |
| :--- | :--- | :--- |
| **Estrutura de Representação** | **Índice Invertido** | É o modelo canônico e mais eficiente para Sistemas de Recuperação da Informação (RI), permitindo acesso instantâneo a documentos por termo. |
| **Persistência em Disco** | **Arquivos JSON** (`indice_invertido.json`) | **Conformidade:** Satisfaz a proibição de uso de Bancos de Dados ACID (MySQL, etc.) e evita a complexidade desnecessária de um BD NoSQL para esta fase. A persistência em JSON é simples e nativa. |
| **Informação Armazenada** | **DocID e Term Frequency (TF)** | Permite o futuro cálculo do *ranking* por similaridade (como o TF-IDF) que poderá ser implementado na Etapa 3. |

### 2.2. Estrutura do Índice Invertido Implementado

O índice é um dicionário mapeado da seguinte forma:

```json
{
  "termo_processado": {
    "df": 125, // Document Frequency: Contagem de documentos que contêm o termo
    "postings": {
      "doc_id_1": 5, // Term Frequency (TF): 5 ocorrências neste documento
      "doc_id_42": 1, 
      // ...
    }
  },
  // ...
}
```

O Índice Invertido é a estrutura de dados escolhida para a Representação, funcionando como um mapa lógico que inverte o problema da busca: em vez de procurar por termos em documentos, ele permite ir diretamente do **termo** para a **lista de documentos** que o contêm.

A estrutura implementada em JSON é aninhada em três níveis:

#### 1. Nível Superior: O Vocabulário (Termo)

* **Representação:** A chave principal do objeto JSON é o **termo único** (ou *token*). Este termo já passou por todo o processamento léxico: remoção de *stopwords* e *stemming* (Ex: 'log').
* **Função no RI:** O vocabulário define o universo de *features* que o sistema conhece e permite a pesquisa por termos exatos de forma instantânea.

#### 2. Nível Intermediário: A Frequência do Documento (DF)

* **Campo:** **`"df"` (Document Frequency)**
* **Valor:** Um número inteiro que representa a **quantidade total de documentos** em que o `termo` aparece.
* **Função no RI:** O `DF` é essencial para calcular o **Peso IDF (Inverse Document Frequency)**, que mede a raridade de um termo.
    * *Exemplo:* Um termo como "o" ou "a" (se as *stopwords* falhassem) teria um `DF` muito alto. Um termo raro, como um nome específico de ataque de *phishing*, teria um `DF` baixo.
    * **Termos Raros (baixo DF) são mais relevantes** para classificar documentos do que termos comuns.

#### 3. Nível Interno: A Lista de Postagens

* **Campo:** **`"postings"`** (Lista de Postagens)
* **Valor:** Um objeto aninhado que mapeia o ID do Documento para sua frequência.
* **Função no RI:** É o coração do índice. Ele resolve o problema da busca e fornece o peso local do termo:

    * **`"doc_id_X"`:** É o identificador único do documento (um índice numérico incremental que mapeia para a URL original no arquivo `document_map.json`). Permite a recuperação final do documento.
    * **`valor` (Ex: `5`)**: É a **Frequência do Termo (`TF` - Term Frequency)**. Representa o **número de vezes** que o termo apareceu naquele documento específico.

### Exemplo do Funcionamento:

Se um usuário buscar pela palavra "login", o sistema fará o *stemming* para 'log' e:

1.  Acessará a chave `'log'`.
2.  Obterá o **DF** (por exemplo, 10.000 documentos).
3.  Acessará a lista de **`postings`**.
4.  Para cada documento nessa lista, ele saberá **quantas vezes** ('TF') a palavra 'log' apareceu.

Este mecanismo permite ao sistema ranquear os documentos: uma página onde 'log' aparece 10 vezes (TF alto) será considerada **mais relevante** para a consulta do que uma página onde 'log' aparece apenas uma vez.

-----

## 3\. Implementação e Processamento da Representação

A indexação é realizada pelo módulo **`src/Indexador.py`**, que aplica uma série de transformações nos documentos HTML.

### 3.1. Pipeline de Análise Léxica

Para garantir que a indexação seja linguística e não apenas literal, foi aplicado um *pipeline* robusto para a língua portuguesa:

| Fase | Método no `Indexador.py` | Justificativa |
| :--- | :--- | :--- |
| **1. Limpeza de HTML** | `_remover_tags_e_obter_texto` (BeautifulSoup) | Extrai apenas o conteúdo visível, removendo ruído (CSS, JavaScript e *tags* estruturais). |
| **2. Normalização** | `lower()` e RegEx | Converte tudo para minúsculas e remove pontuação/números, mantendo a acentuação e o cedilha para o português. |
| **3. Remoção de Stopwords** | NLTK (Lista do Português) | Elimina termos de alta frequência e baixa relevância para a busca (e.g., "o", "de", "que"). |
| **4. Stemming** | NLTK (`SnowballStemmer('portuguese')`) | Reduz as palavras à sua raiz comum (e.g., "coletar," "coletando" $\rightarrow$ "colet"). Essencial para aumentar o *recall* do sistema. |

### 3.2. Robustez e Consistência

Foi implementado um mecanismo de filtro para lidar com a inconsistência entre o log e o disco, causada pela natureza volátil das páginas e ações do *antivírus* (que deleta arquivos suspeitos mesmo quando ele é desativado).

  * **Mecanismo:** Antes do *loop* de indexação, o `Indexador` compara o campo `saved_filename` do log com o conteúdo da pasta `html_pages_temp` (`os.listdir`).
  * **Ação:** O sistema **ignora** os arquivos faltantes (logging o total de *91 documentos faltantes*), mas continua a indexar os documentos **disponíveis**. Isso garante que a indexação não seja interrompida por erros de I/O (`[Errno 2]`) e utilize o máximo de dados possível. Isso foi necessário porque a planilha csv mestre **collection_loc.csv** (em `.\logs`) armazena todos os resultados da coleta, sendo ele `error` ou `success`. Porém quando cruzamos os dados da planilha com os arquivos html gerados conseguimos reduzir o tempo de análise e a ocorrencia de erros I/O do `Indexador`. 

## 3.3. Análise Empírica da Escala e Eficiência

O teste de indexação do *corpus* completo confirmou a robustez da solução e forneceu métricas cruciais de escala e eficiência:

| Métrica de Saída | Valor | Análise |
| :--- | :--- | :--- |
| **Duração da Coleta (Multithreading)** | **78 Horas (Aproximadamente)** | Etapa 1 |
| **Tempo Total de Indexação** | **15 Horas (Aproximadamente)** | Reforça a necessidade da solução modular: uma tarefa que durou 15 horas *deve* ser isolada do processo de coleta volátil. |
| **Tamanho do Índice Invertido** | 4.606.014 KB (**~4.6 GB**) | Confirma a complexidade léxica do *corpus* e o volume de *postings* (entradas DocID:TF). |
| **Tamanho do Mapa de Documentos** | 20.436 KB (**~20 MB**) | Demonstra que o *overhead* para mapear URLs originais é insignificante em comparação com o índice de termos. |
| **Total de Documentos Processados** | 297.068 | Atingido o requisito de volume de dados. |

> O teste de indexação confirmou a robustez da solução, mas a métrica de tempo de coleta validou a importância da arquitetura paralela:
>
> 1.  **Duração da Coleta:** O processo de de analise das URL e coleta das **297.068 URLs ativas levou aproximadamente 78 horas** (3 dias e 6 horas) utilizando 15 *workers* paralelos. Este tempo extenso, mesmo com concorrência, é um reflexo direto da alta latência e da inatividade de 77% dos *links* de *phishing* no *corpus*.
> 2.  **Duração da Indexação:** O processamento léxico e a construção do índice levaram **15 horas** (como uma tarefa *CPU/I/O-bound*).
>
> O tempo gasto representa o massivo uso do **`ThreadPoolExecutor`** recomendado pelo professor Pedro Felipe. Em um processo sequencial, a coleta teria levado centenas de horas. Além disso, a longa duração reforça a decisão de usar *logging* persistente e a estrutura modular, garantindo que nenhum *state* fosse perdido durante um ciclo de execução tão longo e possibilitasse que errors fossem visualizados em realtime possibilitando uma parada no processo para eventuais correções no código.
>
> O **tamanho massivo do `indice_invertido.json` (aproximadamente 4.6 GB)** é um resultado final que confirma a complexidade e a profundidade do *corpus* que será utilizado na fase de Recuperação (Entrega 3).

-----

## 4\. Próximos Passos

A próxima fase se concentrará em utilizar o índice gerado para implementar a funcionalidade de recuperação.

| Tarefa Distribuível | Responsável | Detalhamento da Tarefa Simples | Cronograma (Sugerido) |
| :--- | :--- | :--- | :--- |
| **Cálculo de Frequências Globais** | Osvaldo Neto | Desenvolver a função que percorre o Índice Invertido para calcular e persistir o valor **IDF (Inverse Document Frequency)** para cada termo. | 3 dias |
| **Implementação da Métrica de Similaridade** | Ana Paula | Implementar a função para calcular a **Similaridade do Cosseno** entre dois vetores de termos (com pesos TF-IDF), fundamental para o *ranking*. | 4 dias |
| **Geração de Vetor de Consulta** | Camille Irias | Criar o módulo que recebe a *string* de consulta do usuário, aplica o mesmo *pipeline* de **Limpeza/Stemming/Stopwords** e gera o vetor de *features* TF-IDF para a busca. | 3 dias |
| **Função de Busca Direta** | Luana Mateus | Desenvolver a função que, dado o termo processado, **recupera do JSON** (`indice_invertido.json`) a lista de `DocIDs` (a *Postings List*). | 2 dias |
| **Mapeamento de Resultados** | Lucas Lima | Criar a função que, dado um `DocID`, utiliza o arquivo **`document_map.json`** para retornar a **URL original** correspondente para exibição ao usuário. | 2 dias |
| **Interface CLI Básica (Frontend)** | Ana Clara | Estruturar a interface de linha de comando (CLI) simples que recebe a *query* do usuário e chama a função de busca. | 3 dias |

## Diagrama de Fluxo: Sistema de Recuperação (Esperado Etapa 3)

Este diagrama representa o caminho da informação (fluxo de dados) quando um usuário insere uma consulta no sistema.

![Diagrama de fluxo do sistema de Recuperação de Informação (Etapa 3). O fluxo começa com 'Usuário: Insere Consulta' e entra no 'Módulo de Análise Léxica', onde a consulta é processada (tokenização, stemming) para gerar o 'Cálculo de Vetor de Consulta'. O vetor é passado para o 'Motor de Busca (Ranking)', onde é feita a 'Busca no Índice Invertido.json'. Em seguida, são realizados o 'Cálculo do Peso IDF - Global' e o 'Cálculo da Similaridade do Cosseno' para ranquear os documentos. O processo finaliza com o 'Mapeamento de DocID para URL' e a exibição dos 'RESULTADOS: 10 URLs Ranqueadas'.](/images/Diagrama_esperado_para_etapa_3.png)

### Explicação do Fluxo:

1.  **Entrada (`A`):** O usuário insere a *query* (ex: "site banco falso").
2.  **Análise Léxica (`C`):** O sistema aplica o mesmo tratamento que fez na indexação (limpeza, *stemming* de "site", "banco", "falso").
3.  **Vetorização (`D`):** A *query* é transformada em um **vetor numérico** com pesos (TF-IDF).
4.  **Busca (`F`):** O sistema usa o `indice_invertido.json` para encontrar todos os documentos que contêm os termos da consulta.
5.  **Ranking (`G`, `H`, `I`):** Para os documentos encontrados, o sistema calcula o peso **IDF** e aplica a **Similaridade do Cosseno** para gerar um *score* de relevância.
6.  **Mapeamento (`J`, `K`):** Os `DocID`s ranqueados são convertidos de volta para as URLs originais usando o `document_map.json` para exibição final.

----

### Conclusões sobre a Implementação

A implementação da estrutura de Representação se mostrou bastante escalável, mas intensiva em uso de CPU e I/O:

1.  O tamanho massivo do **`indice_invertido.json` (aproximadamente 4.6 GB)** é um resultado direto da alta complexidade léxica dos *websites* de *phishing* e do grande volume de documentos. Isso confirma que a indexação está densa e detalhada, pronta para gerar *features* robustas. Quanto à **Eficiência (I/O e Processamento)**, a longa duração de **15 horas** (principalmente devido à leitura e processamento de I/O e aos algoritmos de *stemming* e tokenização) justifica plenamente:
    * **Otimização:** A necessidade da otimização que implementamos para **filtrar arquivos faltantes em memória**, evitando que 15 horas de processamento fossem perdidas por falhas de I/O em apenas 91 documentos.
    * **Arquitetura:** A separação do Indexador como uma etapa **manual/separada** no *launcher* (`Coletor.py`) foi essencial para que o processo pudesse ser executado em um bloco de tempo dedicado e monitorado.