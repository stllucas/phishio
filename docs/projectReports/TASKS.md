# Project Charter: Sistema de Recuperação de Informação (RI)

Este documento descreve as etapas, requisitos e critérios de avaliação para o desenvolvimento de um **Sistema de Recuperação da Informação (RI)** completo, desde a aquisição dos dados até a entrega de uma interface de busca funcional.

O projeto será dividido em 3 grandes etapas:

| Etapa | Foco Principal |
| :--- | :--- |
| **1. Coleta** | Aquisição e armazenamento de um corpus de documentos da web. |
| **2. Representação e Indexação** | Processamento do corpus e construção de um índice invertido. |
| **3. Recuperação e Ranking** | Implementação de um motor de busca para consultar o índice. |

Os relatórios serão entregues incrementalmente, ou seja, o segundo será uma extensão/atualização do primeiro.

---

## Etapa 1: Coleta

Nesta fase, o grupo deve desenvolver um coletor web para adquirir os dados que formarão a base do sistema de RI. O processo de coleta deve ser documentado, detalhando as decisões de arquitetura e as políticas adotadas.

### Critérios de Avaliação

| Critério | Descrição |
| :--- | :--- |
| **1.1. Proposta do Sistema de RI** | Apresentar formalmente o problema a ser resolvido e a solução de RI proposta. |
| **1.2. Arquitetura do Coletor** | Descrever o tipo de coletor (vertical, focado), suas políticas (seleção, re-visita, "boa vizinhança"), tolerância a falhas e critério de parada. Justificar as decisões de projeto. |
| **1.3. Escala e Volume** | Atingir a meta de coleta de dados. A pontuação máxima requer uma **coleta superior a 50.001 documentos**. |
| **1.4. Apresentação** | Apresentar os resultados e a arquitetura do coletor para a turma. |

---

## Etapa 2: Representação e Indexação

Nesta fase, o grupo irá processar os dados coletados na Etapa 1, transformando o corpus bruto em uma estrutura de dados otimizada para busca: o **índice invertido**.

**ATENÇÃO:** Está **expressamente proibido** o uso de tecnologias de Banco de Dados ACID (MySQL, PostgreSQL, Oracle, MS SQL Server, etc.). O uso de Banco de Dados NoSQL está liberado desde que a sua utilização seja devidamente justificada ao professor previamente (Exemplo: usar o Neo4J para representar e recuperar *nodes* em uma estrutura de grafo).

----
### Critérios de Avaliação

| Critério | Descrição |
| :--- | :--- |
| **2.1. Implementação do Pipeline de Indexação** | Desenvolver e documentar o processo de indexação, que deve incluir: <br> • Limpeza e extração de texto (e.g., remoção de HTML, scripts). <br> • Análise Léxica (tokenização, normalização). <br> • Remoção de *stopwords*. <br> • Aplicação de *stemming* ou lematização. |
| **2.2. Construção do Índice Invertido** | Implementar a lógica para gerar e persistir o índice invertido, contendo, no mínimo, a frequência do termo no documento (TF) e a frequência do documento (DF). |
| **2.3. Análise de Complexidade e Desempenho** | Medir e relatar métricas importantes, como: <br> • Tempo total de indexação. <br> • Tamanho final do índice em disco (KB/MB/GB). <br> • Análise de complexidade de tempo e espaço do algoritmo. |
| **2.4. Relatório e Planejamento** | Entregar um relatório parcial detalhando a arquitetura de representação, as implementações e um **cronograma de conclusão** para a Etapa 3, com divisão explícita de tarefas entre os membros do grupo. |

---

## Etapa 3: Recuperação e Ranking

Nesta etapa final, o grupo implementará o motor de busca, utilizando o índice invertido para processar consultas, ranquear os resultados e apresentá-los ao usuário. O sistema completo deverá ser apresentado à turma.

### Critérios de Avaliação

| Critério | Descrição |
| :--- | :--- |
| **3.1. Implementação do Modelo de Ranking** | Implementar um modelo vetorial para ranquear documentos, que deve incluir: <br> • Cálculo do peso **TF-IDF** para termos na consulta e nos documentos. <br> • Cálculo de similaridade (e.g., **Similaridade de Cossenos**) para gerar um score de relevância. |
| **3.2. Motor de Busca** | Desenvolver a lógica que recebe uma consulta do usuário, processa-a (aplicando o mesmo pipeline da indexação), recupera as listas de postagem do índice e aplica o modelo de ranking para ordenar os documentos. |
| **3.3. Interface com o Usuário** | Criar uma interface (CLI ou gráfica simples) que permita ao usuário inserir uma consulta e receber uma lista ordenada de resultados (e.g., as 10 URLs mais relevantes). |
| **3.4. Relatório Final e Código-Fonte** | Entregar o relatório final consolidado, descrevendo todas as etapas, decisões de projeto, desafios e soluções. O código-fonte completo e funcional deve ser entregue. |
| **3.5. Apresentação Final** | Apresentar e demonstrar o sistema de recuperação de informação finalizado para a turma. |

---

# Diretrizes para Relatórios e Apresentação

**Relatórios**: Os relatórios devem ser documentos técnicos claros e bem estruturados. Devem abordar:
- **Desafios e Soluções:** Quais foram os principais obstáculos técnicos (e.g., memória, performance, qualidade dos dados) e como foram superados?
- **Justificativa de Decisões:** Qual é a vantagem/desvantagem das suas soluções em relação às alternativas? (e.g., Por que usar *stemming* em vez de lematização? Por que JSON em vez de outro formato?).
- **Bibliotecas Externas:** Listar e explicar o papel de todas as bibliotecas externas utilizadas (e.g., NLTK, BeautifulSoup, ijson).
- **Fundamentação Teórica:** Explicar o funcionamento das técnicas e fórmulas adotadas (e.g., apresentar e justificar a fórmula do TF-IDF e da Similaridade de Cossenos).

**Apresentação**: A apresentação final deve ser uma demonstração clara e concisa do sistema. O objetivo é "vender" a solução para a turma, destacando sua funcionalidade, eficiência e os desafios superados durante o desenvolvimento.