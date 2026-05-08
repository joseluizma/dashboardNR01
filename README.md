# dashboardNR01

Esta atualização consolida o projeto em um único `app.py`, preservando a ideia original do dashboard e adicionando:

- aba de Funções com de/para dinâmico salvo em `normalizacao_funcoes.csv`;
- aba de Setores com de/para dinâmico salvo em `normalizacao_setores.csv`;
- aba de Respostas com mapeamento dinâmico de respostas para valor numérico;
- aba de Pesos por pergunta em `pesos_perguntas.csv`;
- dashboard recalculado usando mapeamento dinâmico das respostas e pesos;
- classificação de risco em linha com a lógica operacional adotada para a NR-01 no contexto de GRO/PGR.[web:101][page:0]

## Estrutura esperada

Arquivos e pastas esperados no projeto:

```text
.
├── app.py
├── requirements.txt
├── data/
│   ├── arquivo_formulario.xlsx
│   ├── normalizacao_funcoes.csv
│   ├── normalizacao_setores.csv
│   ├── map_respostas.csv
│   └── pesos_perguntas.csv
```

Se os CSVs não existirem, o aplicativo pode criá-los ao salvar pela interface, desde que a pasta `data/` exista e contenha ao menos um arquivo `.xlsx` para leitura.

## Requisitos

- Python 3.10 ou superior.
- `pip` instalado.
- Um arquivo Excel exportado do Google Forms dentro da pasta `data/`.

## Instalação

Clone o projeto e entre na pasta:

```bash
git clone <URL_DO_REPOSITORIO>
cd dashboardNR01
```

Crie e ative um ambiente virtual.

### Linux / macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### Windows PowerShell

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

Instale as dependências:

```bash
pip install -r requirements.txt
```

## requirements.txt sugerido

```txt
dash>=2.17.0
pandas>=2.2.0
plotly>=5.22.0
openpyxl>=3.1.2
```

Se quiser versões fixas para ambiente mais previsível:

```txt
dash==2.18.2
pandas==2.2.3
plotly==5.24.1
openpyxl==3.1.5
```

## Como rodar o projeto

Com o ambiente virtual ativo e as dependências instaladas, execute:

```bash
python app.py
```

O Dash iniciará localmente e normalmente exibirá algo como:

```text
Dash is running on http://127.0.0.1:8050/
```

Abra esse endereço no navegador.

## Rodar em modo de desenvolvimento

Para desenvolvimento local, basta usar:

```bash
python app.py
```

O código já usa:

```python
if __name__ == '__main__':
    app.run(debug=True)
```

Isso habilita recarregamento automático e mensagens de debug.

## Gerar ambiente do zero

Exemplo completo no Linux/macOS:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
mkdir -p data
python app.py
```

## Como “compilar” o projeto

Como este projeto é um app Dash em Python, ele não possui compilação tradicional como um binário nativo. O fluxo normal é instalar dependências e executar o `app.py`.[file:50]

As formas mais comuns de preparar entrega são:

### 1. Empacotar dependências

Gerar o arquivo de dependências usado no deploy:

```bash
pip freeze > requirements.txt
```

### 2. Executar em servidor local/redeploy

```bash
python app.py
```

### 3. Produção com Gunicorn

Para ambiente Linux, você pode instalar Gunicorn:

```bash
pip install gunicorn
```

E rodar com:

```bash
gunicorn app:server --bind 0.0.0.0:8050
```

Nesse caso, o objeto `server = app.server` já está pronto no projeto para publicação WSGI.[file:50]

## Exemplo de Procfile

Para serviços como Render ou plataformas compatíveis:

```text
web: gunicorn app:server --bind 0.0.0.0:$PORT
```

## Build para executável

Se a necessidade for gerar um executável local, é possível usar PyInstaller:

Instalação:

```bash
pip install pyinstaller
```

Geração:

```bash
pyinstaller --onefile app.py
```

Observação: para Dash, esse formato nem sempre é o melhor para distribuição, porque o projeto continua sendo uma aplicação web local e pode exigir ajustes adicionais de arquivos, caminhos e pasta `data/`.

## Dados usados pelo app

O app procura automaticamente o primeiro arquivo `.xlsx` dentro de `data/`.[file:50]

Também utiliza estes arquivos auxiliares:

- `data/normalizacao_funcoes.csv`
- `data/normalizacao_setores.csv`
- `data/map_respostas.csv`
- `data/pesos_perguntas.csv`

## Lógica do dashboard

O painel transforma respostas textuais em escala numérica, aplica inversão para itens negativos, calcula médias por pergunta e médias ponderadas por dimensão, e depois classifica o resultado em faixas de risco para operação do dashboard no contexto da NR-01.[web:101][page:0]

Faixas adotadas no sistema:

- `>= 4.0`: Baixo risco
- `>= 3.0 e < 4.0`: Atenção
- `>= 2.0 e < 3.0`: Risco moderado
- `< 2.0`: Risco alto

Essas faixas funcionam como regra operacional do painel para priorização de ação no GRO/PGR, enquanto a exigência normativa é a inclusão e gestão dos fatores de risco psicossociais no processo de gerenciamento de riscos ocupacionais.[web:101][page:0]

## Problemas comuns

### 1. Nenhum arquivo `.xlsx` encontrado

Erro típico:

```text
FileNotFoundError: Nenhum arquivo .xlsx encontrado em: ...
```

Solução: coloque o arquivo exportado do Google Forms dentro da pasta `data/`.

### 2. Dependências ausentes

Se aparecer erro de importação, reinstale:

```bash
pip install -r requirements.txt
```

### 3. Porta ocupada

Se a porta `8050` já estiver em uso, finalize o processo anterior ou ajuste a porta no `app.run(...)`.

## Sugestão de arquivos auxiliares

### requirements.txt

```txt
dash>=2.17.0
pandas>=2.2.0
plotly>=5.22.0
openpyxl>=3.1.2
```

### runtime.txt

```txt
python-3.11.9
```

### Procfile

```txt
web: gunicorn app:server --bind 0.0.0.0:$PORT
```