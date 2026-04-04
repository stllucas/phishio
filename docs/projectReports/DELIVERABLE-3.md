# Funcionalidade de Cálculo de IDF (Inverse Document Frequency)

## Introdução

Como parte fundamental da Etapa 3 (Recuperação), foi implementado o módulo `CalculaIDF.py`, responsável por computar o **Inverse Document Frequency (IDF)** para cada termo do vocabulário. O IDF é uma métrica estatística que mensura a raridade e, consequentemente, a importância de um termo em toda a coleção de documentos. Este cálculo é um pré-requisito para a implementação de modelos de ranking avançados, como o TF-IDF.

## Mudanças Realizadas

1.  **Criação do Módulo `src/CalculaIDF.py`**: Um novo script dedicado exclusivamente ao cálculo dos pesos IDF.
2.  **Leitura de Artefatos**: O script consome dois arquivos gerados na etapa de indexação:
    *   `logs/indice_invertido.json`: Para obter a frequência de documentos (`df`) de cada termo.
    *   `logs/document_map.json`: Para obter o número total de documentos (`N`) na coleção.
3.  **Geração de Saída**: O resultado é persistido no arquivo `logs/idf.json`, que armazena um mapa `{ "termo": idf_value }`.
4.  **Robustez para Escalabilidade**: Implementado um mecanismo de *fallback* que utiliza a biblioteca `ijson` para processamento incremental. Essa abordagem garante que o cálculo possa ser executado mesmo com índices invertidos de grande volume (múltiplos gigabytes), que não caberiam inteiramente na memória RAM.

## Funcionamento e Fórmula

O processo segue uma lógica bem definida:

1.  **Obtenção de N**: O número total de documentos (`N`) é determinado pela contagem de entradas no `document_map.json`.
2.  **Processamento do Índice**: O script tenta carregar o `indice_invertido.json` em memória. Em caso de `MemoryError`, ativa o modo de leitura incremental com `ijson`.
3.  **Cálculo do IDF**: Para cada termo no índice, o script extrai sua frequência nos documentos (`df`) e aplica a fórmula padrão do Inverse Document Frequency:
   
   $$
   \text{IDF}(t) = \log\left(\frac{N}{df_t}\right)
   $$
   Onde `t` é o termo, `N` é o número total de documentos e `df_t` é o número de documentos que contêm o termo `t`. O uso do logaritmo suaviza a escala dos valores.

4.  **Persistência**: Os resultados são salvos em `logs/idf.json`.

## Como Interpretar o Resultado (`idf.json`)

O arquivo `idf.json` é um dicionário que mapeia cada termo ao seu valor de IDF. A interpretação é a seguinte:

### Interpretação dos valores de IDF
- **IDF Alto**: Indica que o termo é raro na coleção de documentos. Termos com IDF alto são excelentes para discriminar o conteúdo e possuem maior peso no cálculo de relevância.
- **IDF Baixo (próximo de 0)**: Indica que o termo é muito comum, aparecendo em uma grande fração dos documentos. Sua capacidade de distinção é baixa.
- **IDF igual a 0**: Ocorre quando um termo está presente em todos os documentos da coleção, tornando-o inútil para o ranking.

### Exemplo de uso
Se o termo "bradesco" possui um IDF alto, uma consulta contendo essa palavra retornará com maior prioridade os documentos que também a contenham. Em contrapartida, um termo como "login" (após stemming), que provavelmente aparece em muitas páginas, terá um IDF baixo e menor influência no score final.

---

**Autor:**
Osvaldo Neto @osvaldoferreiraf
Data da atualização: 08/11/2025

# Implementação do `SearchEngine.py` (Entrega 3)

### Objetivo

Esta tarefa adiciona o módulo de recuperação (Etapa 3) responsável por mapear resultados de DocIDs gerados pelo ranking para as URLs originais dos documentos, além de preparar a base para cálculos de ranking e uso do índice invertido.


### O que foi implementado

- Criação da classe `SearchEngine` em `src/SearchEngine.py`.
- Função de carregamento do mapa de documentos (`document_map.json`) para memória, com conversão das chaves para inteiros.
- Cache interno (`_document_map`) para evitar leituras repetidas do arquivo em disco.
- Método `mapear_resultados_para_urls(doc_ids)` que recebe uma lista de DocIDs (inteiros) e retorna as URLs correspondentes, ignorando DocIDs inexistentes.
- **Busca direta por termo no índice invertido:** método `buscar_postings_por_termo(termo)` que retorna todos os DocIDs e frequências para um termo processado, usando leitura incremental eficiente com `ijson`.
- Logs informativos e tratamento de erro quando o arquivo `document_map.json` ou `indice_invertido.json` não é encontrado ou não pode ser lido.
- Estrutura preparada para extensão com ranking, cálculo de IDF/TF-IDF e outras funcionalidades de recuperação.


### Contrato (entrada / saída / erros)

- **mapear_resultados_para_urls**
    - Entrada: lista de inteiros (DocIDs) — ex: [12, 45, 2]
    - Saída: lista de strings (URLs) correspondentes na mesma ordem dos DocIDs válidos — ex: ["http://...", "https://..."]. DocIDs inválidos são simplesmente ignorados.
    - Modos de erro: se o `document_map.json` não existir ou ocorrer exceção ao carregar, o módulo retorna uma lista vazia e registra mensagem crítica no logger.
- **buscar_postings_por_termo**
    - Entrada: termo processado (string, após stemming/stopwords)
    - Saída: dicionário `{doc_id: tf, ...}` com todos os DocIDs e frequências para o termo, ou `None` se não encontrado.
    - Modos de erro: se o `indice_invertido.json` não existir ou ocorrer exceção ao carregar, retorna `None` e registra mensagem crítica no logger.

### Fluxo interno

1. Ao chamar `mapear_resultados_para_urls`, o método tenta garantir que `_document_map` esteja carregado chamando `carregar_document_map()`.
2. `carregar_document_map()` verifica se o arquivo existe; em caso afirmativo, carrega o JSON em memória e converte as chaves (strings) para inteiros, costruindo um dicionário {DocID: URL}.
3. Com o mapa em memória, `mapear_resultados_para_urls` itera sobre os DocIDs solicitados, faz lookups usando `.get()` (evita KeyError) e agrega apenas URLs encontradas.

### Complexidade e desempenho

- Leitura do `document_map.json`: O(n) em relação ao número de documentos (n = |document_map|) no momento da carga.
- Acesso/lookup por DocID: O(1) por consulta (dicionário em memória).
- Uso de cache (`_document_map`) elimina custo de I/O em chamadas subsequentes.

Observação de escalabilidade: o mapa de documentos é mantido inteiro em memória. Para coleções enormes (milhões de documentos) pode ser necessário um mecanismo alternativo (ex.: banco de chaves, mmap, ou leitura por lote). A versão atual é adequada para coleções de porte moderado (até algumas centenas de milhares de entradas dependendo da memória disponível).

### Casos de borda e decisões de projeto

- DocIDs inexistentes: simplesmente ignorados (sem lançar exceção). Isso facilita pipelines que possam pedir mapeamentos incompletos.
- Arquivo faltando/corrompido: o método registra uma mensagem crítica e retorna lista vazia — cabe ao chamador tratar a situação (p.ex. acionar indexação ou abortar a query).
- Conversão das chaves para inteiros: adotada para consistência com o resto do código que trata DocIDs como inteiros.

### Integração com o restante do sistema

- `Processor` / `Relatorio` / `Indexador` devem garantir que `logs/document_map.json` esteja presente (gerado durante a indexação) antes de utilizar o `SearchEngine`.
- O `SearchEngine` foi escrito como um componente independente e testável (métodos de classe). Futuramente pode-se adicionar instância para manter estado adicional (ex.: índices auxiliares, caches de ranking).


### Como usar / testar

#### Busca direta por termo (menu interativo)

1. Certifique-se de que `logs/indice_invertido.json` existe e foi gerado pela indexação.
2. Execute o launcher principal:

```bash
python Coletor.py
```

3. No menu interativo, escolha a opção:

```
[5] Etapa 3: Busca Direta por Termo no Índice Invertido
```

4. Digite o termo processado (após stemming/stopwords, ex: "log") quando solicitado. O sistema exibirá até 20 resultados de DocIDs e suas frequências para o termo.

#### Mapeamento de DocIDs para URLs (uso programático)

```python
from src.SearchEngine import SearchEngine
urls = SearchEngine.mapear_resultados_para_urls([12, 45, 2])
print(urls)
```

#### Testes unitários recomendados
- Chamar `mapear_resultados_para_urls` e `buscar_postings_por_termo` com entradas válidas, inválidas e mistura.
- Mockar a leitura dos arquivos (ou gerar arquivos temporários) para verificar comportamento de carga, cache e busca incremental.

### Execução das Etapas via Linha de Comando

O `Coletor.py` foi atualizado para permitir a execução de cada etapa do processo de forma independente através de argumentos de linha de comando.

| Comando | Descrição |
| :--- | :--- |

| Comando | Descrição |
| :--- | :--- |
| `python Coletor.py --etapa coleta` | **Etapa 1:** Inicia o processo de download e salvamento das páginas HTML. |
| `python Coletor.py --etapa indexacao` | **Etapa 2:** Constrói o índice invertido e o mapa de documentos a partir dos HTMLs coletados. |
| `python Coletor.py --etapa idf` | **Etapa 3:** Calcula os pesos IDF para cada termo do vocabulário. |
| `python Coletor.py --etapa diagnostico`| Roda um script de verificação para contar os arquivos coletados. |
| `python Coletor.py --etapa todas` | Executa todas as etapas acima em sequência. |
| `python Coletor.py` | Exibe o menu interativo, incluindo a opção de busca direta por termo no índice invertido. |


Se nenhum argumento for fornecido, o programa exibirá um menu interativo, incluindo a opção de busca direta por termo no índice invertido (Etapa 3).

---

**Autor:**
Luana Almeida @Luana-Almeid
Data da atualização: 13/11/2025

# Implementação da Métrica de Similaridade (Entrega 3)

### Objetivo

A métrica de Similaridade do Cosseno tem como objetivo ranquear os documentos coletados e indexados de acordo com a relevância em relação a uma consulta do usuário. Ela é parte central da Etapa 3, sendo responsável por transformar o índice invertido em resultados ordenados por importância semântica. Essa métrica é baseada em vetores de pesos TF-IDF, medindo o “ângulo” entre o vetor da consulta e o vetor de cada documento.

### Implementação

A implementação foi feita no arquivo:
src/SearchEngine.py

Foram criados três novos métodos dentro da classe SearchEngine:
- similaridade_cosseno():	Calcula a similaridade entre dois vetores TF-IDF (consulta × documento).
- calcular_pesos_tf_idf(): Aplica o IDF sobre as frequências de termos (TF) para gerar o vetor ponderado.
- ranquear_documentos(): Gera o ranking completo, ordenando os documentos por relevância decrescente.

Esses métodos trabalham em conjunto com os módulos:
- CalculaIDF.py: Responsável por gerar os valores de IDF (Etapa 3.1).
- Indexador.py: Responsável por gerar o índice invertido (Etapa 2).
- Coletor.py: Integra o menu interativo e exibe o resultado ranqueado.

### Integração

O método ranquear_documentos() é chamado a partir da função:
busca_com_ranking_menu() no arquivo Coletor.py.

Fluxo integrado:
- Usuário → Coletor.py → SearchEngine.ranquear_documentos() → TF-IDF + Cosine → URLs ranqueadas

Além disso, o método mapear_resultados_para_urls() é usado para traduzir os doc_ids ranqueados em URLs originais, com base no arquivo document_map.json.

### Como usar / testar

- Pré-requisitos: Antes de executar o ranking TF-IDF, as etapas anteriores precisam estar completas, pois o método ranquear_documentos() depende de arquivos gerados nas fases de coleta, indexação e cálculo de IDF.

Esses arquivos devem existir na pasta logs/:
- indice_invertido.json: Contém os termos e suas ocorrências (TF) em cada documento.
- idf.json: Contém o peso IDF de cada termo, usado para ponderar os vetores TF-IDF.
- document_map.json: Mapeia o DocID interno para a URL original.

Se qualquer um desses arquivos estiver ausente, o ranking não será executado e o sistema exibirá uma mensagem de erro, como:
- Erro ao executar a busca ranqueada: [Errno 2] No such file or directory: 'logs/idf.json'

Nesse caso, basta rodar as etapas anteriores para gerar os arquivos necessários.

- Execute o sistema interativo: python Coletor.py

- Escolha no menu: [6] Etapa 5: Busca com Ranking TF-IDF (Similaridade do Cosseno)

- Digite uma consulta, por exemplo: phishing banco login

O sistema exibirá algo como, Top 10 Resultados Ranqueados (TF-IDF + Similaridade do Cosseno):
- [1] DocID: 123 | Score: 0.8421 → http://exemplo.com/phishing123
- [2] DocID: 98  | Score: 0.7654 → http://exemplo.com/banco_fake

- Logs de execução são gravados em: logs/riwrs.log

---
**Autor:**
Ana Paula de Oliveira
Data da atualização: 19/11/2025

# Implementação da Interface de Linha de Comando (CLI) - Entrega 3

### Objetivo

A Interface de Linha de Comando (CLI) constitui o front-end interativo do sistema de Recuperação de Informação. Seu objetivo é fornecer uma interface amigável e intuitiva para que os usuários possam realizar consultas no corpus de páginas phishing coletadas, recebendo resultados ranqueados de forma clara e estruturada.

A CLI orquestra todas as funcionalidades implementadas pelas equipes anteriores (Processamento de Consulta, Busca, Ranking TF-IDF e Mapeamento de URLs), oferecendo uma experiência integrada ao usuário final.

### Implementação

O módulo foi implementado em: `src/CLI.py`

A classe `CLI` encapsula toda a lógica de interface e contém os seguintes métodos estáticos:

#### Métodos Principais

| Método | Responsabilidade |
| :--- | :--- |
| `verificar_prerequisitos()` | Valida se todos os arquivos necessários (indice_invertido.json, idf.json, document_map.json) existem antes de iniciar a busca. |
| `carregar_indice_invertido_parcial(termos)` | Carrega apenas os termos solicitados do índice invertido, economizando memória (usa ijson para leitura incremental). |
| `carregar_document_map()` | Carrega o mapa de documentos (DocID → URL) em memória para resolução de resultados. |
| `exibir_cabecalho()` | Exibe o cabeçalho de boas-vindas com instruções de uso. |
| `exibir_resultado_busca(query, resultados, document_map, limit)` | Formata e exibe os resultados de forma estruturada (rank, relevância percentual, URL). |
| `executar_busca(query, document_map, limite_resultados)` | Orquestra todo o pipeline de busca em 4 etapas principais. |
| `modo_interativo()` | Loop interativo que permite múltiplas consultas consecutivas com tratamento de exceções e interrupção por Ctrl+C. |
| `busca_unica(query, limite_resultados)` | Executa uma busca única sem modo interativo, útil para integração com scripts. |

### Pipeline de Busca (4 Etapas Integradas)

A CLI implementa um pipeline completo que integra o trabalho de todos os membros da equipe:

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
│    - Buscar os termos processados no índice invertido           │
│    - Recuperar lista de DocIDs e Term Frequencies (TF)          │
│    - Resultado: postings para cada termo da query               │
└──────────────────────────┬──────────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────────┐
│ 3. CÁLCULO DE PESOS IDF (Osvaldo Neto)                          │
│    - Carregar mapa IDF pré-calculado (idf.json)                 │
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
│    - Resultado: top-10 documentos ordenados por relevância      │
└──────────────────────────┬──────────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────────┐
│ 5. MAPEAMENTO E EXIBIÇÃO (Lucas Lima + Ana Clara)               │
│    - Converter DocIDs ranqueados para URLs originais            │
│    - Formatar resultado para exibição amigável                  │
│    - Exibir rank, percentual de relevância e URL                │
│    - Resultado: interface clara e intuitiva para o usuário      │
└─────────────────────────────────────────────────────────────────┘
```

### Características Principais

#### 1. **Validação Robusta**
- Verifica pré-requisitos antes de iniciar qualquer busca
- Mensagens de erro claras indicando quais arquivos estão faltando
- Instruções sobre quais etapas executar para gerar os arquivos necessários

#### 2. **Carregamento Eficiente de Memória**
- Usa `ijson` para leitura incremental do índice invertido
- Carrega apenas os termos necessários, não o arquivo inteiro (4.6 GB)
- Cache do document_map em memória para rápido acesso aos DocIDs

#### 3. **Modo Interativo**
- Loop contínuo que permite múltiplas buscas
- Suporta comandos para sair: 'sair', 'exit', 'quit', 'q'
- Tratamento de Ctrl+C sem causar erro
- Retorno automático ao prompt após cada busca

#### 4. **Modo Não-Interativo**
- Função `busca_unica()` para integração com scripts
- Útil para testes automatizados ou pipelines

#### 5. **Exibição Formatada**
```
--------------------------------------------------------------------------------
RESULTADOS PARA: 'phishing banco'
--------------------------------------------------------------------------------
  [OK] Encontrados 1523 documentos relevantes

  1. [Relevância: 95%]
     URL: http://exemplo.com/phishing123

  2. [Relevância: 87%]
     URL: http://exemplo2.com/banco_fake

  3. [Relevância: 82%]
     URL: http://exemplo3.com/login_falso
     
  ...
```

#### 6. **Compatibilidade com Windows**
- Substituição de caracteres Unicode por versões ASCII
- Uso de `[OK]`, `[ERRO]`, `>>` em vez de `✓`, `✗`, `→`
- Testado em PowerShell 5.1 (Windows)

### Integração com Coletor.py

A CLI foi integrada ao launcher principal com as seguintes modificações:

**1. Importação do módulo:**
```python
from CLI import CLI
```

**2. Função wrapper:**
```python
def rodar_busca_interativa():
    """Executa a CLI interativa de busca (Etapa 3 - Ana Clara)."""
    logger.info("MODO INTERATIVO DE BUSCA: Iniciando interface CLI.")
    CLI.modo_interativo()
    logger.info("MODO INTERATIVO DE BUSCA: Finalizado.")
```

**3. Opção de linha de comando:**
```bash
python Coletor.py --etapa busca
```

**4. Opção no menu interativo:**
```
[7] Etapa 6: Modo Interativo de Busca (CLI) - Ana Clara
```

### Como Usar

#### Via Linha de Comando
```bash
# Ativar ambiente virtual
.\venv\Scripts\activate

# Executar CLI interativa
python Coletor.py --etapa busca
```

#### Via Menu Interativo
```bash
python Coletor.py
# Selecionar opção [7] no menu
```

#### Programaticamente
```python
from src.CLI import CLI

# Busca única
CLI.busca_unica("phishing login", limite_resultados=10)

# Ou modo interativo
CLI.modo_interativo()
```

### Estrutura de Erros e Validação

A CLI implementa validação em múltiplos níveis:

| Cenário | Comportamento |
| :--- | :--- |
| Arquivo indice_invertido.json não encontrado | Mensagem de erro clara, instrução para executar indexação |
| Arquivo idf.json não encontrado | Mensagem de erro clara, instrução para calcular IDF |
| Arquivo document_map.json não encontrado | Mensagem de erro clara, impossível mapear DocIDs para URLs |
| Consulta vazia | Mensagem pedindo ao usuário digitar algo |
| Consulta com apenas stopwords | Mensagem indicando que nenhum termo relevante foi encontrado |
| Nenhum documento encontrado para a consulta | Mensagem sugerindo termos alternativos |
| Erro durante a busca (exceção) | Log detalhado no arquivo de log, mensagem amigável ao usuário |

### Fluxo de Execução Detalhado

```
CLI.executar_busca("phishing")
    │
    ├─→ Etapa 1: Processar Consulta
    │   └─→ SearchEngine.gerar_vetor_consulta_tfidf()
    │       • Remover stopwords
    │       • Aplicar stemming
    │       • Calcular TF da consulta
    │       • Aplicar pesos IDF
    │       └─→ Resultado: {'phish': 2.14, 'ing': 0.0, ...}
    │
    ├─→ Etapa 2: Carregar Índice
    │   └─→ CLI.carregar_indice_invertido_parcial(['phish'])
    │       • Ler ijson do indice_invertido.json
    │       • Filtrar apenas termos solicitados
    │       └─→ Resultado: {'phish': {'123': 5, '456': 3, ...}}
    │
    ├─→ Etapa 3: Carregar IDF
    │   └─→ JSON.load(idf.json)
    │       └─→ Resultado: {'phish': 2.14, 'bank': 1.87, ...}
    │
    ├─→ Etapa 4: Ranquear
    │   └─→ SearchEngine.ranquear_documentos()
    │       • Para cada DocID encontrado:
    │         - Calcular TF-IDF do documento
    │         - Aplicar Similaridade do Cosseno
    │       • Ordenar por score descendente
    │       └─→ Resultado: [(123, 0.95), (456, 0.87), ...]
    │
    └─→ Etapa 5: Exibir
        └─→ CLI.exibir_resultado_busca()
            • Mapear DocIDs para URLs
            • Formatar resultado
            • Imprimir para o usuário
            └─→ Resultado: Interface amigável com top-10
```

### Testes Realizados

A CLI foi testada com sucesso usando o script `test_cli.py`:

```
[OK] Logging carregado com sucesso
[OK] Modulos carregados com sucesso
[OK] Todos os arquivos necessarios foram encontrados
[OK] Document map carregado com 296628 URLs
[OK] Consulta processada com 1 termos unicos
[OK] Indice carregado para 1 termos
[OK] Mapa IDF carregado
[OK] Encontrados 5 documentos relevantes

Busca por "login" retornou:
  1. http://www.remisereduc.com/test/ssi/webscr.php?cmd=_login-run
  2. http://shabdasnehalibrary.com/xmlrpc/secure-code9/security/login.php
  3. http://www.austinrc.org//cl1/remax/
  4. http://steamstorepowered.chez.com/
  5. http://steamcommunitylog.chez.com/

[OK] TESTE CONCLUIDO COM SUCESSO!
```

### Considerações de Performance

- **Carregamento do Índice:** ~1-2 minutos para ler termos específicos do índice de 4.6 GB
- **Cálculo de Ranking:** ~30-60 segundos para ranquear ~27.000 documentos
- **Memória:** Mantém apenas os termos necessários em memória, não o arquivo inteiro
- **Escalabilidade:** Preparado para corpus de até centenas de milhões de documentos

### Próximos Passos (Opcional)

Possíveis melhorias futuras:

1. Cache de resultados recentes para consultas repetidas
2. Paginação de resultados (exibir 10 por página, com navegação)
3. Sugestão de termos alternativos (spell correction)
4. Exportação de resultados em formatos adicionais (JSON, CSV)
5. Interface gráfica (GUI) como alternativa ao CLI

---
**Autor:**
Ana Clara Contarini @anacontarini
Data da atualização: 20/11/2025


**Autor:**
Camille Irias Gonçalves @CamilleIrias
Data da atualização: 19/11/2025

# Implementação da Métrica de Similaridade (Entrega 3)

### Objetivo

Método responsável por ser a porta de entrada do Motor de Busca, recebendo a string de consulta em linguagem natural inserida pelo usuário e convertendo-a em uma representação matemática (vetor de pesos TF-IDF). 
### Implementação

### 2.1. Consistência do Pipeline de Processamento
Para evitar problemas com "descasamento de vocabulário", onde termos relevantes na busca não são encontrados porque sofreram processamentos diferentes durante a indexação, foi implementado o método `gerar_vetor_consulta_tfidf` na classe `SearchEngine` que reutiliza estritamente os mesmos recursos linguísticos definidos na classe `Indexador`:

* **Normalização:** Aplicação de *lowercase* e remoção de caracteres especiais (pontuação e números) via Regex, preservando a acentuação padrão da língua portuguesa.
* **Stopwords:** Utilização do mesmo conjunto de *stopwords* (NLTK) importado diretamente do módulo de indexação.
* **Stemming:** Aplicação do algoritmo *SnowballStemmer* (Portuguese) para a redução de palavras aos seus radicais (ex: "recuperação" $\rightarrow$ "recuper"), garantindo que variações morfológicas sejam tratadas como o mesmo termo.

### 2.2. Integração com o Modelo Vetorial (TF-IDF)
O sistema adota o Modelo Vetorial para a ponderação dos termos. Para a consulta ($q$), o peso de cada termo ($t$) é calculado conforme a fórmula:

$$w_{t,q} = tf_{t,q} \times idf_t$$

Onde:
* **$tf_{t,q}$ (Term Frequency):** Representa a frequência bruta do termo na consulta do usuário.
* **$idf_t$ (Inverse Document Frequency):** Representa o valor de raridade do termo no corpus completo. Este valor é recuperado do arquivo `idf.json` (gerado na Etapa 2), assegurando que termos raros e discriminantes recebam maior peso no ranking final.

### 3. Métodos Principais Desenvolvidos

Foram criados de três métodos interconectados:

* **`gerar_vetor_consulta_tfidf(query_string)`**: Método público principal. Orquestra todo o fluxo: solicita o carregamento do IDF, chama o processamento de texto, calcula a frequência dos termos (TF) na consulta e retorna o dicionário final com os pesos $TF \times IDF$.
* **`_processar_texto_query(texto_query)`**: Método auxiliar privado. Replica a lógica de limpeza de dados da Etapa 2 (Indexação), aplicando normalização, remoção de *stopwords* e *stemming* na string de busca. Garante que a consulta "fale a mesma língua" do índice.
* **`_carregar_idf_map()`**: Método auxiliar de gerenciamento de recursos. Verifica a existência do arquivo `idf.json`, carrega seu conteúdo para a memória RAM e implementa um *cache* simples para evitar leituras de disco repetitivas em buscas subsequentes.

### 5. Como Usar e Testar

Para validar a implementação isoladamente (Teste Unitário), foi criado um script de verificação na raiz do projeto local.

**Exemplo de uso do módulo:**
```python
from SearchEngine import SearchEngine

# 1. Entrada do usuário
consulta = "recuperação de informação"

# 2. Geração do Vetor (Chamada do método desenvolvido)
vetor = SearchEngine.gerar_vetor_consulta_tfidf(consulta)

# 3. Saída Esperada (Dicionário de pesos)
# Ex: {'recuper': 1.45, 'inform': 2.10}
print(vetor)
```
---

**Autor:** 
Lucas Lima @Lucas-San99
Data da atualização: 21/11/2025

# Implementação da Lógica de Paginação, Mapeamento e Gerenciamento de Memória (Backend)

### Objetivo

O motor de ranking bruto retorna uma lista extensa de identificadores numéricos (DocIDs) e seus scores. O objetivo desta implementação foi refinar essa saída bruta no backend (`SearchEngine.py`) para torná-la consumível pelos frontends (CLI e GUI). Isso envolveu três tarefas críticas: traduzir DocIDs de volta para URLs, implementar a lógica de paginação (fatiamento de resultados) no servidor e criar mecanismos explícitos de gerenciamento de memória para evitar vazamentos de recursos durante o ciclo de vida da aplicação.

### Implementação

As implementações foram realizadas na classe central `SearchEngine` em `src/SearchEngine.py`.

#### 1\. Mapeamento Eficiente (DocID $\rightarrow$ URL)

Foi desenvolvido o método `mapear_resultados_para_urls(doc_ids)`.

  * **Funcionamento:** O método recebe uma lista de inteiros (DocIDs) retornados pelo processo de ranking. Ele utiliza o dicionário `self.doc_map` (carregado em RAM na inicialização a partir do `document_map.json`) para realizar a tradução.
  * **Desempenho:** Como o mapa está inteiramente na memória RAM como uma tabela hash, a busca por cada URL tem complexidade de tempo O(1), garantindo que esta etapa não adicione latência perceptível ao processo de busca, mesmo para milhares de resultados.

#### 2\. Lógica Central de Paginação (`buscar`)

O método principal de fachada `buscar` foi refatorado para suportar paginação no backend.

  * **Assinatura Anterior:** `buscar(query_string)` retornando os top-10 fixos.
  * **Nova Assinatura:** `buscar(query_string, pagina=1, resultados_por_pagina=10)`
  * **Fluxo:**
    1.  Recebe a consulta e os parâmetros de página.
    2.  Chama o método de ranking completo (implementado por Ana Paula) para obter *todos* os resultados possíveis ordenados.
    3.  Calcula os índices de fatiamento (slice) com base na página solicitada:
          * `inicio = (pagina - 1) * resultados_por_pagina`
          * `fim = inicio + resultados_por_pagina`
    4.  Aplica o fatiamento à lista completa de resultados.
    5.  Chama o método de mapeamento apenas para os DocIDs da página atual.
    6.  **Retorno:** Retorna uma tupla contendo a lista paginada e o total geral de resultados: `(resultados_da_pagina, total_encontrado)`.

#### 3\. Gerenciamento Explícito de Memória

Devido à arquitetura híbrida que mantém grandes estruturas na RAM (vocabulário e mapas), foi identificado um problema de vazamento de memória (*memory leak*) quando a interface gráfica era aberta e fechada múltiplas vezes.

  * **Solução:** Implementação do método `liberar_memoria_explicitamente()`.
  * **Funcionamento:** Este método é chamado pelos frontends (especificamente a GUI) no momento do fechamento da aplicação. Ele realiza duas ações críticas:
    1.  Fecha explicitamente o descritor de arquivo (`file handle`) do índice binário no SSD (`self.postings_handle.close()`).
    2.  Define as referências dos grandes dicionários em RAM (`self.doc_map`, `self.vocabulario`, etc.) como `None` e invoca manualmente o Garbage Collector do Python (`gc.collect()`) para forçar a liberação imediata da memória alocada.

### Fluxo da Nova Metodologia `buscar`

```
┌───────────────────────────┐
│ Entrada: Query, Pág, Limit│
└─────────────┬─────────────┘
              │
              ▼
┌───────────────────────────┐
│ 1. Gerar Vetor TF-IDF     │
└─────────────┬─────────────┘
              │
              ▼
┌───────────────────────────┐
│ 2. Ranking Completo (RAM) │
│ - Retorna lista gigante   │
│   de [(DocID, Score),...] │
└─────────────┬─────────────┘
              │
              ▼
┌───────────────────────────┐
│ 3. Lógica de Paginação    │
│ - Calcular slices         │
│ - Fatiar a lista gigante  │
└─────────────┬─────────────┘
              │
              ▼
┌───────────────────────────┐
│ 4. Mapeamento (RAM)       │
│ - Traduzir DocIDs da fatia│
│   para URLs usando doc_map│
└─────────────┬─────────────┘
              │
              ▼
┌───────────────────────────┐
│ Saída: (Resultados        |
| Paginados, Total Geral)   |
└───────────────────────────┘
```

### Como Usar (Exemplo Programático)

O uso principal se dá através das interfaces CLI e GUI, mas o método pode ser invocado diretamente:

```python
from src.SearchEngine import SearchEngine

# Inicializa o motor (carrega mapas na RAM)
engine = SearchEngine()

# Busca a segunda página, com 20 resultados por página
query = "recuperar senha nubank"
resultados_pag_2, total_geral = engine.buscar(query, pagina=2, resultados_por_pagina=20)

print(f"Total de documentos encontrados para a query: {total_geral}")
print(f"Exibindo {len(resultados_pag_2)} resultados da página 2:")

for doc_id, score, url in resultados_pag_2:
    print(f" - [{score:.4f}] {url}")

# Ao finalizar, liberar recursos
engine.liberar_memoria_explicitamente()
```