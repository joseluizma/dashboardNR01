# dashboardNR01

Esta atualização consolida o projeto em um único `app.py`, preservando a ideia original do dashboard e adicionando:

- aba de Funções com de/para dinâmico salvo em `normalizacao_funcoes.csv`;
- aba de Setores com de/para dinâmico salvo em `normalizacao_setores.csv`;
- aba de Respostas com de/para dinâmico `original -> grupo` em `normalizacao_respostas.csv`;
- tabela `grupo -> valor` em `valores_grupos_respostas.csv`;
- aba de Pesos por pergunta em `pesos_perguntas.csv`;
- dashboard recalculado usando mapeamento dinâmico das respostas e pesos.

Arquivos esperados na raiz do projeto:
- `data/*.xlsx`
- `normalizacao_funcoes.csv`
- `normalizacao_setores.csv`
- `normalizacao_respostas.csv`
- `valores_grupos_respostas.csv`
- `pesos_perguntas.csv`

Se os CSVs não existirem, o app os cria implicitamente quando você salvar pela interface.
