# Trabalho de Recuperação de Informação na Web e Redes Sociais
## Etapa 1: Coletor Web para Dataset de Phishing

**Alunos:**

* Ana Clara Contarini Barbosa (@anacontarini)
* Ana Paula de Oliveira (@)
* Camille Irias Goncalves (@CamilleIrias)
* Luana Mateus de Almeida (@Luana-Almeid)
* Lucas dos Santos Lima (@Lucas-San99)
* Osvaldo Ferreira de Freitas Neto (@osvaldoferreiraf)

**Disciplina:** Recuperação de Dados na Web e Redes Sociais

***

## 1. Proposta do Sistema de Recuperação de Informação (RI)

### 1.1. O Problema

O *phishing* representa uma das ameaças cibernéticas mais críticas e difundidas, resultando em perdas financeiras significativas e no comprometimento de dados sensíveis de indivíduos e corporações. A agilidade dos atacantes, que criam e desativam páginas maliciosas em questão de horas, impõe um desafio constante aos métodos tradicionais de detecção baseados em listas de bloqueio (*blacklists*), que frequentemente se mostram reativos e insuficientes. Existe, portanto, uma necessidade contínua de analisar as características de páginas de *phishing* em larga escala para desenvolver sistemas de detecção mais proativos, automatizados e resilientes.

### 1.2. A Solução Proposta

Este projeto visa o desenvolvimento de um **Sistema de Recuperação de Informação do tipo vertical**, focado na coleta, representação e análise de páginas web utilizadas em ataques de *phishing*. O objetivo é criar um sistema capaz de, futuramente, auxiliar na identificação de novas ameaças com base nos padrões aprendidos a partir de um *dataset*, coletado especificamente para este fim.

O projeto está dividido em três etapas:

1.  **Coleta (Etapa Atual):** Construir um coletor web para baixar o conteúdo completo (HTML) de uma lista pré-definida de URLs de *phishing*, criando um *dataset* original para análise.
2.  **Representação:** Processar e indexar o conteúdo coletado para extrair e estruturar características (*features*) relevantes, como a presença de formulários, termos suspeitos, *links* externos, e ofuscação de código.
3.  **Recuperação:** Implementar um modelo de recuperação que, ao receber uma nova URL, possa classificá-la como suspeita com base em sua similaridade com os documentos do nosso *dataset*.

---

## 2. Descrição e Metodologia do Coletor

Para a construção do nosso *dataset*, foi desenvolvido um coletor web focado cujas características e políticas são detalhadas a seguir.

### 2.1. Arquitetura e Políticas

O sistema foi projetado com base nas seguintes decisões:

| Política / Característica | Detalhamento |
| :--- | :--- |
| **Tipo de Coletor** | **Vertical**, pois o escopo da coleta é restrito a um tópico específico (*phishing*) a partir de uma lista de URLs pré-definida. |
| **Política de Seleção** | A fronteira de coleta é **estática**, limitada exclusivamente às URLs fornecidas no arquivo CSV inicial. O coletor **não extrai novos *links*** das páginas baixadas, garantindo a pureza do *dataset*. |
| **Política de Re-visita** | Adotou-se uma política de **não re-visita**. Cada URL foi processada uma única vez para capturar um "snapshot" do seu estado. |
| **Política de "Boa Vizinhança"** | Foi implementado um atraso deliberado (pool de *workers*) e um cabeçalho **User-Agent** para simular um navegador real. O arquivo `robots.txt` foi deliberadamente ignorado, pois os alvos são páginas maliciosas sem expectativa de cooperação. |
| **Tolerância a Falhas** | O coletor foi programado para lidar com uma vasta gama de erros de rede (*timeouts*, falhas de DNS) e de *status* HTTP (4xx, 5xx), registrando cada resultado em um arquivo de *log* detalhado. |
| **Critério de Parada** | O processo é encerrado de forma determinística após a tentativa de coleta da **última URL** da lista de entrada. |

### 2.2. Implementação e Escala

A implementação foi realizada em Python, utilizando bibliotecas como `pandas` para manipulação de dados, `requests` para as requisições HTTP e `concurrent.futures` para paralelização.

* Para atingir a escala necessária, foi adotada uma estratégia de **multithreading** com um *pool* de **30 *workers***, o que permitiu processar mais de 50.000 URLs em um tempo de execução de aproximadamente 30 minutos, uma tarefa que levaria dezenas de horas em uma abordagem sequencial.

---

## 3. Conclusão da Etapa 1

A primeira etapa do projeto foi concluída. Foi desenvolvido um coletor web capaz de processar um grande volume de URLs e lidar com as instabilidades da infraestrutura de sites maliciosos.

### Resultados Quantitativos:

| Métrica | Valor | Percentual |
| :--- | :--- | :--- |
| **Universo Total de URLs** | 457.265 | 100% |
| **Páginas Ativas Coletadas** | 105.548 | 23.08% |
| **Páginas Inativas/Erros** | 351.717 | 76.92% |

### Análise Qualitativa

Embora o *log* detalhado com a categorização de cada erro individual tenha sido sobrescrito durante as coletas incrementais, as execuções de teste e as análises parciais (documentadas no histórico de desenvolvimento) indicaram que a grande maioria das falhas se concentrou em:

* 'Erros de Resolução de DNS' (domínios que não existem mais).
* 'Páginas Não Encontradas (Erro 404)'.

Esta observação qualitativa, alinhada à alta taxa de inatividade geral de **~77%**, reforça a conclusão sobre o ciclo de vida extremamente curto das páginas de *phishing*.

Esta constatação reforça a relevância do projeto, pois evidencia a necessidade de sistemas que possam analisar e aprender com as características de ameaças ativas para, futuramente, identificar novas campanhas. O *dataset* e o coletor desenvolvidos nesta etapa constituem a fundação sobre a qual as fases de representação, indexação e recuperação serão construídas.