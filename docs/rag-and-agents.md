# Recuperação, assistência e orquestração

O corpus contém cinco documentos fictícios sobre reposição, picos, capacidade,
cancelamentos e governança. A ingestão normaliza quebras de linha; parágrafos com
comprimento mínimo formam chunks limitados a 1.600 caracteres. O índice local usa
TF-IDF word/bigram; alternativas avaliadas são LSA e mistura word/character TF-IDF.
Cada chunk carrega documento, título, URL e o documento tem SHA-256.

A API retorna os trechos usados. O botão de referência consulta o texto integral
com autenticação, em vez de mandar o navegador a um link inexistente. Há abstenção
quando a recuperação não tem score lexical suficiente; o coordinator também
rejeita intenções fora do escopo operacional.

A primeira avaliação devolveu referências para todas as perguntas negativas, por
peso de palavras funcionais. O relatório original foi preservado em
`reports/rag_initial.json`. A mudança remove palavras funcionais frequentes e exige
suporte lexical, inclusive para LSA/híbrido. O conjunto atual é **de desenvolvimento**;
foi usado ao diagnosticar o problema e não é uma estimativa imparcial de generalização.

Em 19 perguntas respondíveis e quatro negativas, o default lexical encontrou o
documento esperado em 18/19 e absteve-se nas quatro negativas. Precisão das
referências pelo documento ouro: 77,8%. Há uma referência correta por pergunta;
Hit Rate@3 e Recall@3 coincidem nesse protocolo. Não confundir precisão de documento
com entailment semântico de toda frase gerada. As respostas offline citam trechos
literais; as tentativas externas não foram avaliadas sem credenciais.

O broker disponibiliza sete ferramentas tipadas: previsão, riscos, capacidade,
simulação, busca, proposta pendente e status. Ele valida argumentos e restaurante
em cada execução. `Question.architecture` compara modo simple/roles, mas ambos
compartilham a mesma execução determinística. A medição alterna a ordem, aquece
caches e usa 12 consultas por modo. Fatos foram idênticos; pequenas diferenças de
latência não demonstram vantagem de agentes. A UI usa `simple`.

O modo externo recebe evidências depois das ferramentas, não dirige o plano de
execução. Seu JSON precisa ter explicação e IDs de citações permitidos; introduzir
dígitos na prosa causa fallback. Esse controle restringe afirmações numéricas,
mas não prova ausência de alucinação qualitativa. O modo offline é rotulado como
template e usa números calculados pelos módulos Python.
