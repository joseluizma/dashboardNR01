from pathlib import Path
import pandas as pd
from dash import Dash, dcc, html, dash_table, Input, Output, State, no_update
import plotly.express as px
import sys


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / 'data'
FUNCOES_MAP = BASE_DIR / 'data' / 'normalizacao_funcoes.csv'
SETORES_MAP = BASE_DIR / 'data' / 'normalizacao_setores.csv'
RESPOSTAS_MAP = BASE_DIR / 'data' / 'map_respostas.csv'
PESOS_PATH = BASE_DIR / 'data' / 'pesos_perguntas.csv'


xlsx_files = list(DATA_DIR.glob('*.xlsx'))
if not xlsx_files:
    raise FileNotFoundError(f'Nenhum arquivo .xlsx encontrado em: {DATA_DIR}')
DATA_FILE = xlsx_files[0]


REV_KEYWORDS = [
    'acumula-se por ser mal distribuída', 'não tem tempo para completar', 'trabalhar muito rapidamente',
    'atenção constante', 'decisões difíceis', 'exige emocionalmente de si', 'ficar desempregado',
    'afetar a sua vida privada negativamente', 'emocionalmente cansado', 'irritado(a) com facilidade',
    'comentários desrespeitosos', 'comunicação agressiva', 'falas ofensivas', 'cunho sexual não desejadas',
    'ameaçado(a) ou intimidado(a)'
]


DIMENSOES = {
    'Carga e exigências': [
        'acumula-se por ser mal distribuída', 'não tem tempo para completar', 'trabalhar muito rapidamente',
        'atenção constante', 'decisões difíceis', 'exige emocionalmente de si'
    ],
    'Autonomia e desenvolvimento': ['influência no seu trabalho', 'tenha iniciativa', 'aprender coisas novas'],
    'Informação e clareza': ['informado com antecedência', 'Recebe toda a informação', 'responsabilidades'],
    'Liderança e justiça': [
        'reconhecido e apreciado pelo gestor', 'tratado de forma justa', 'ajuda e apoio do seu superior',
        'ambiente de trabalho', 'boas oportunidades de desenvolvimento', 'planejamento do trabalho',
        'gestor confia', 'Confia na informação', 'conflitos são resolvidos', 'igualmente distribuído'
    ],
    'Sentido e satisfação': [
        'resolver problemas', 'tem algum significado', 'trabalho é importante',
        'problemas do seu local de trabalho são seus', 'satisfeito está com o seu trabalho'
    ],
    'Saúde e bem-estar': [
        'saúde é', 'rotina de sono adequada', 'energia e disposição física',
        'emocionalmente cansado', 'preocupação e a ansiedade', 'irritado(a) com facilidade'
    ],
    'Violência e assédio': [
        'comentários desrespeitosos', 'comunicação agressiva', 'falas ofensivas',
        'cunho sexual não desejadas', 'ameaçado(a) ou intimidado(a)'
    ],
    'Trabalho e vida privada': ['afetar a sua vida privada negativamente']
}


def norm_txt(s):
    if pd.isna(s):
        return None
    s = str(s).replace('\xa0', ' ').strip()
    return s or None


def norm_bool(v, default=True):
    if pd.isna(v):
        return default
    if isinstance(v, bool):
        return v
    if isinstance(v, (int, float)):
        return bool(v)
    s = str(v).strip().lower()
    if s in {'true', '1', 'sim', 'yes', 'y'}:
        return True
    if s in {'false', '0', 'nao', 'não', 'no', 'n'}:
        return False
    return default


def classificar_risco(score):
    if pd.isna(score):
        return None
    if score >= 4.0:
        return 'Baixo risco'
    if score >= 3.0:
        return 'Atenção'
    if score >= 2.0:
        return 'Risco moderado'
    return 'Risco alto'


def prioridade_acao(classificacao):
    mapa = {
        'Baixo risco': 'Monitoramento',
        'Atenção': 'Prevenção',
        'Risco moderado': 'Plano de ação',
        'Risco alto': 'Ação imediata'
    }
    return mapa.get(classificacao)


def cor_risco(classificacao):
    cores = {
        'Baixo risco': '#2e7d32',
        'Atenção': '#f9a825',
        'Risco moderado': '#ef6c00',
        'Risco alto': '#c62828'
    }
    return cores.get(classificacao, '#546e7a')


def pergunta_dimensao(pergunta):
    p = str(pergunta).lower()
    for nome, keys in DIMENSOES.items():
        if any(k.lower() in p for k in keys):
            return nome
    return 'Outros'


def item_reverso(pergunta):
    p = str(pergunta).lower()
    return any(k.lower() in p for k in REV_KEYWORDS)


def detect_columns(df):
    func_col = next(c for c in df.columns if 'Informe sua Função' in c)
    setor_col = next(c for c in df.columns if 'Informe seu Setor' in c)
    return func_col, setor_col


def read_mapping_df(path, values=None):
    if path.exists():
        df = pd.read_csv(path)
    else:
        df = pd.DataFrame(columns=['original', 'grupo'])

    if 'original' not in df.columns:
        df['original'] = None
    if 'grupo' not in df.columns:
        df['grupo'] = None

    df['original'] = df['original'].map(norm_txt)
    df['grupo'] = df['grupo'].map(norm_txt)
    df = df.dropna(subset=['original']).drop_duplicates('original', keep='last')

    if values is not None:
        base = pd.DataFrame({'original': sorted([v for v in values if v])})
        df = base.merge(df[['original', 'grupo']], on='original', how='left')
        df['grupo'] = df['grupo'].fillna(df['original'])

    return df.sort_values(['original']).reset_index(drop=True)


def save_mapping_df(rows, path, values=None):
    df = pd.DataFrame(rows)

    if df.empty:
        df = pd.DataFrame(columns=['original', 'grupo'])
    if 'original' not in df.columns:
        df['original'] = None
    if 'grupo' not in df.columns:
        df['grupo'] = None

    df['original'] = df['original'].map(norm_txt)
    df['grupo'] = df['grupo'].map(norm_txt)
    df = df.dropna(subset=['original']).drop_duplicates('original', keep='last')

    if values is not None:
        base = pd.DataFrame({'original': sorted([v for v in values if v])})
        df = base.merge(df[['original', 'grupo']], on='original', how='left')
        df['grupo'] = df['grupo'].fillna(df['original'])

    df = df.sort_values(['original']).reset_index(drop=True)
    df.to_csv(path, index=False)
    return df


def read_respostas_map(path, values=None):
    if path.exists():
        df = pd.read_csv(path)
    else:
        df = pd.DataFrame(columns=['resposta', 'valor'])

    if 'resposta' not in df.columns:
        df['resposta'] = None
    if 'valor' not in df.columns:
        df['valor'] = None

    df['resposta'] = df['resposta'].map(norm_txt)
    df['valor'] = pd.to_numeric(df['valor'], errors='coerce')
    df = df.dropna(subset=['resposta']).drop_duplicates('resposta', keep='last')

    if values is not None:
        base = pd.DataFrame({'resposta': sorted([v for v in values if v])})
        df = base.merge(df[['resposta', 'valor']], on='resposta', how='left')

    return df.sort_values('resposta').reset_index(drop=True)


def save_respostas_map(rows, path, values=None):
    df = pd.DataFrame(rows)

    if df.empty:
        df = pd.DataFrame(columns=['resposta', 'valor'])
    if 'resposta' not in df.columns:
        df['resposta'] = None
    if 'valor' not in df.columns:
        df['valor'] = None

    df['resposta'] = df['resposta'].map(norm_txt)
    df['valor'] = pd.to_numeric(df['valor'], errors='coerce')
    df = df.dropna(subset=['resposta']).drop_duplicates('resposta', keep='last')

    if values is not None:
        base = pd.DataFrame({'resposta': sorted([v for v in values if v])})
        df = base.merge(df[['resposta', 'valor']], on='resposta', how='left')

    df = df.sort_values('resposta').reset_index(drop=True)
    df.to_csv(path, index=False)
    return df


def read_pesos(perguntas):
    if PESOS_PATH.exists():
        df = pd.read_csv(PESOS_PATH)
    else:
        df = pd.DataFrame(columns=['pergunta', 'peso', 'ativo'])

    if 'pergunta' not in df.columns:
        df['pergunta'] = None
    if 'peso' not in df.columns:
        df['peso'] = 1.0
    if 'ativo' not in df.columns:
        df['ativo'] = True

    df['pergunta'] = df['pergunta'].map(norm_txt)
    df['peso'] = pd.to_numeric(df['peso'], errors='coerce').fillna(1.0)
    df['ativo'] = df['ativo'].map(norm_bool)
    df = df.dropna(subset=['pergunta']).drop_duplicates('pergunta', keep='last')

    base = pd.DataFrame({'pergunta': perguntas})
    base['dimensao'] = base['pergunta'].map(pergunta_dimensao)
    base['invertida'] = base['pergunta'].map(item_reverso)

    out = base.merge(df[['pergunta', 'peso', 'ativo']], on='pergunta', how='left')
    out['peso'] = pd.to_numeric(out['peso'], errors='coerce').fillna(1.0)
    out['ativo'] = out['ativo'].map(lambda x: norm_bool(x, True))

    return out


def save_pesos(rows, perguntas):
    df = pd.DataFrame(rows)

    if df.empty:
        df = pd.DataFrame(columns=['pergunta', 'peso', 'ativo'])
    if 'pergunta' not in df.columns:
        df['pergunta'] = None
    if 'peso' not in df.columns:
        df['peso'] = 1.0
    if 'ativo' not in df.columns:
        df['ativo'] = True

    df['pergunta'] = df['pergunta'].map(norm_txt)
    df['peso'] = pd.to_numeric(df['peso'], errors='coerce').fillna(1.0)
    df['ativo'] = df['ativo'].map(norm_bool)
    df = df[['pergunta', 'peso', 'ativo']].dropna(subset=['pergunta']).drop_duplicates('pergunta', keep='last')

    df.to_csv(PESOS_PATH, index=False)
    return read_pesos(perguntas)


def build_score_map(respostas_df):
    return dict(zip(respostas_df['resposta'], respostas_df['valor']))


def load_data():
    df = pd.read_excel(DATA_FILE)
    df.columns = [str(c).replace('\xa0', ' ').strip() for c in df.columns]

    func_col, setor_col = detect_columns(df)
    meta_cols = ['ID', 'Hora de início', 'Hora de conclusão', 'Email', 'Nome', func_col, setor_col]
    perguntas = [c for c in df.columns if c not in meta_cols]

    for c in [func_col, setor_col] + perguntas:
        df[c] = df[c].map(norm_txt)

    response_values = sorted({
        v
        for p in perguntas
        for v in df[p].dropna().map(norm_txt).tolist()
        if v
    })

    funcoes_df = read_mapping_df(FUNCOES_MAP, df[func_col].dropna().unique().tolist())
    setores_df = read_mapping_df(SETORES_MAP, df[setor_col].dropna().unique().tolist())
    respostas_df = read_respostas_map(RESPOSTAS_MAP, response_values)
    pesos_df = read_pesos(perguntas)

    fun_map = dict(zip(funcoes_df['original'], funcoes_df['grupo']))
    set_map = dict(zip(setores_df['original'], setores_df['grupo']))

    df['funcao_original'] = df[func_col]
    df['setor_original'] = df[setor_col]
    df['funcao_agrupada'] = df[func_col].map(lambda x: fun_map.get(x, x))
    df['setor_agrupado'] = df[setor_col].map(lambda x: set_map.get(x, x))

    return df, perguntas, funcoes_df, setores_df, respostas_df, pesos_df, response_values


def resumo_perguntas(df, perguntas, respostas_df, pesos_df):
    score_map = build_score_map(respostas_df)
    peso_map = pesos_df.set_index('pergunta').to_dict('index') if not pesos_df.empty else {}

    rows = []
    for p in perguntas:
        s = df[p].dropna()
        score = s.map(score_map).dropna()
        media = score.mean()

        if pd.isna(media):
            continue

        ajustada = 6 - media if item_reverso(p) else media
        cfg = peso_map.get(p, {})
        peso = float(cfg.get('peso', 1.0))
        ativo = norm_bool(cfg.get('ativo', True))
        peso_aplicado = peso if ativo else 0.0
        classificacao = classificar_risco(ajustada)

        rows.append({
            'dimensao': pergunta_dimensao(p),
            'pergunta': p,
            'respondidas': int(s.shape[0]),
            'pontuacao_original': round(float(media), 3),
            'pontuacao_ajustada': round(float(ajustada), 3),
            'classificacao_risco': classificacao,
            'prioridade_acao': prioridade_acao(classificacao),
            'invertida': item_reverso(p),
            'peso': peso,
            'ativo': ativo,
            'peso_aplicado': peso_aplicado
        })

    cols = [
        'dimensao',
        'pergunta',
        'respondidas',
        'pontuacao_original',
        'pontuacao_ajustada',
        'classificacao_risco',
        'prioridade_acao',
        'invertida',
        'peso',
        'ativo',
        'peso_aplicado'
    ]
    return pd.DataFrame(rows, columns=cols)


def build_dimensoes(itens):
    if itens is None or itens.empty or 'ativo' not in itens.columns:
        return pd.DataFrame(columns=['dimensao', 'indice_risco', 'classificacao_risco', 'prioridade_acao'])

    ativos = itens[itens['ativo'] == True].copy()
    if ativos.empty:
        return pd.DataFrame(columns=['dimensao', 'indice_risco', 'classificacao_risco', 'prioridade_acao'])

    rows = []
    for dimensao, grp in ativos.groupby('dimensao'):
        peso_total = grp['peso_aplicado'].sum()
        media = (
            (grp['pontuacao_ajustada'] * grp['peso_aplicado']).sum() / peso_total
            if peso_total > 0 else grp['pontuacao_ajustada'].mean()
        )
        classificacao = classificar_risco(media)
        rows.append({
            'dimensao': dimensao,
            'indice_risco': round(float(media), 3),
            'classificacao_risco': classificacao,
            'prioridade_acao': prioridade_acao(classificacao)
        })

    return pd.DataFrame(rows).sort_values('indice_risco')


def make_bar(df_plot, x, y, title, color=None):
    if df_plot.empty:
        return px.bar(pd.DataFrame({x: [], y: []}), x=x, y=y, orientation='h', title=title)
    fig = px.bar(df_plot, x=x, y=y, orientation='h', title=title, color=color)
    return fig


def fig_funcoes():
    counts = (
        df['funcao_agrupada']
        .fillna('Não informado')
        .value_counts()
        .head(20)
        .rename_axis('grupo')
        .reset_index(name='respostas')
        .sort_values('respostas')
    )
    return make_bar(counts, 'respostas', 'grupo', 'Funções')


def fig_setores():
    counts = (
        df['setor_agrupado']
        .fillna('Não informado')
        .value_counts()
        .head(20)
        .rename_axis('grupo')
        .reset_index(name='respostas')
        .sort_values('respostas')
    )
    return make_bar(counts, 'respostas', 'grupo', 'Setores')


df, perguntas, funcoes_df, setores_df, respostas_df, pesos_df, response_values = load_data()
base = resumo_perguntas(df, perguntas, respostas_df, pesos_df)

app = Dash(__name__, suppress_callback_exceptions=True)
server = app.server


app.layout = html.Div([
    dcc.Store(id='reload-flag'),
    html.H2('Clima e Bem-estar'),
    html.P('Análise com classificação de risco psicossocial aderente à NR-01 no contexto do GRO/PGR.'),
    dcc.Tabs(id='tabs', value='tab-dashboard', children=[
        dcc.Tab(label='Dashboard', value='tab-dashboard'),
        dcc.Tab(label='Funções', value='tab-funcoes'),
        dcc.Tab(label='Setores', value='tab-setores'),
        dcc.Tab(label='Respostas', value='tab-respostas'),
        dcc.Tab(label='Pesos', value='tab-pesos'),
    ]),
    html.Div(id='tab-content')
], style={'padding': '24px', 'fontFamily': 'Arial'})


def dashboard_layout():
    base_local = resumo_perguntas(df, perguntas, respostas_df, pesos_df)

    return html.Div([
        html.Div([
            html.Div([
                html.Label('Modo da função'),
                dcc.RadioItems(
                    id='modo-funcao-dashboard',
                    options=[
                        {'label': 'Original', 'value': 'funcao_original'},
                        {'label': 'Agrupada', 'value': 'funcao_agrupada'}
                    ],
                    value='funcao_agrupada',
                    inline=True
                )
            ], style={'minWidth': '260px'}),

            html.Div([
                html.Label('Função'),
                dcc.Dropdown(
                    id='filtro-funcao-dashboard',
                    options=[{'label': 'Todas', 'value': '__all__'}],
                    value='__all__',
                    clearable=False
                )
            ], style={'minWidth': '320px'}),

            html.Div([
                html.Label('Dimensão'),
                dcc.Dropdown(
                    id='filtro-dimensao',
                    options=[{'label': 'Todas', 'value': '__all__'}] + [
                        {'label': d, 'value': d} for d in sorted(base_local['dimensao'].unique())
                    ],
                    value='__all__',
                    clearable=False
                )
            ], style={'minWidth': '320px'})
        ], style={'display': 'flex', 'gap': '24px', 'flexWrap': 'wrap', 'marginBottom': '20px'}),

        dcc.Graph(
            id='graf-dimensoes',
            style={'height': '420px'}
        ),

        html.H3('Itens prioritários'),
        dash_table.DataTable(
            id='tabela-itens',
            page_size=12,
            style_table={'overflowX': 'auto'},
            style_cell={
                'textAlign': 'left',
                'whiteSpace': 'normal',
                'height': 'auto',
                'fontFamily': 'Arial',
                'fontSize': '13px'
            },
            style_header={'fontWeight': 'bold'}
        )
    ])


def funcoes_layout():
    return html.Div([
        html.H3('Funções'),
        html.P('Tabela de agrupamento e gráfico de distribuição das funções na própria aba.'),
        dash_table.DataTable(
            id='tbl-funcoes',
            columns=[
                {'name': 'Original', 'id': 'original', 'editable': False},
                {'name': 'Grupo', 'id': 'grupo', 'editable': True}
            ],
            data=funcoes_df.to_dict('records'),
            editable=True,
            filter_action='native',
            sort_action='native',
            page_size=15,
            style_table={'overflowX': 'auto', 'marginBottom': '16px'},
            style_cell={
                'textAlign': 'left',
                'whiteSpace': 'normal',
                'height': 'auto',
                'fontFamily': 'Arial',
                'fontSize': '13px'
            },
            style_header={'fontWeight': 'bold'}
        ),
        html.Button('Salvar', id='btn-save-funcoes', n_clicks=0, style={'padding': '10px 16px'}),
        html.Div(id='msg-funcoes', style={'marginTop': '10px', 'color': '#0a6', 'marginBottom': '16px'}),
        dcc.Graph(id='graf-funcoes-aba', figure=fig_funcoes(), style={'height': '520px'})
    ])


def setores_layout():
    return html.Div([
        html.H3('Setores'),
        html.P('Tabela de agrupamento e gráfico de distribuição dos setores na própria aba.'),
        dash_table.DataTable(
            id='tbl-setores',
            columns=[
                {'name': 'Original', 'id': 'original', 'editable': False},
                {'name': 'Grupo', 'id': 'grupo', 'editable': True}
            ],
            data=setores_df.to_dict('records'),
            editable=True,
            filter_action='native',
            sort_action='native',
            page_size=15,
            style_table={'overflowX': 'auto', 'marginBottom': '16px'},
            style_cell={
                'textAlign': 'left',
                'whiteSpace': 'normal',
                'height': 'auto',
                'fontFamily': 'Arial',
                'fontSize': '13px'
            },
            style_header={'fontWeight': 'bold'}
        ),
        html.Button('Salvar', id='btn-save-setores', n_clicks=0, style={'padding': '10px 16px'}),
        html.Div(id='msg-setores', style={'marginTop': '10px', 'color': '#0a6', 'marginBottom': '16px'}),
        dcc.Graph(id='graf-setores-aba', figure=fig_setores(), style={'height': '520px'})
    ])


def respostas_layout():
    return html.Div([
        html.H3('Respostas'),
        html.P('Aqui você define diretamente o valor numérico de cada resposta encontrada no formulário.'),
        dash_table.DataTable(
            id='tbl-respostas',
            columns=[
                {'name': 'Resposta', 'id': 'resposta', 'editable': False},
                {'name': 'Valor', 'id': 'valor', 'type': 'numeric', 'editable': True}
            ],
            data=respostas_df.to_dict('records'),
            editable=True,
            filter_action='native',
            sort_action='native',
            page_size=20,
            style_table={'overflowX': 'auto', 'marginBottom': '16px'},
            style_cell={
                'textAlign': 'left',
                'whiteSpace': 'normal',
                'height': 'auto',
                'fontFamily': 'Arial',
                'fontSize': '13px'
            },
            style_header={'fontWeight': 'bold'}
        ),
        html.Button('Salvar valores', id='btn-save-respostas', n_clicks=0, style={'padding': '10px 16px'}),
        html.Div(id='msg-respostas', style={'marginTop': '10px', 'color': '#0a6'})
    ])


def pesos_layout():
    return html.Div([
        html.H3('Pesos por pergunta'),
        dash_table.DataTable(
            id='tbl-pesos',
            columns=[
                {'name': 'Dimensão', 'id': 'dimensao', 'editable': False},
                {'name': 'Pergunta', 'id': 'pergunta', 'editable': False},
                {'name': 'Invertida', 'id': 'invertida', 'editable': False},
                {'name': 'Peso', 'id': 'peso', 'type': 'numeric', 'editable': True},
                {'name': 'Ativo', 'id': 'ativo', 'presentation': 'dropdown', 'editable': True},
            ],
            data=pesos_df.to_dict('records'),
            editable=True,
            page_size=15,
            filter_action='native',
            sort_action='native',
            dropdown={
                'ativo': {
                    'options': [
                        {'label': 'Sim', 'value': True},
                        {'label': 'Não', 'value': False}
                    ]
                }
            },
            style_table={'overflowX': 'auto'},
            style_cell={
                'textAlign': 'left',
                'whiteSpace': 'normal',
                'height': 'auto',
                'fontFamily': 'Arial',
                'fontSize': '13px'
            },
            style_header={'fontWeight': 'bold'}
        ),
        html.Button('Salvar pesos', id='btn-save-pesos', n_clicks=0, style={'padding': '10px 16px', 'marginTop': '12px'}),
        html.Div(id='msg-pesos', style={'marginTop': '10px', 'color': '#0a6'})
    ])


@app.callback(Output('tab-content', 'children'), Input('tabs', 'value'), Input('reload-flag', 'data'))
def render_tab(tab, _):
    global df, perguntas, funcoes_df, setores_df, respostas_df, pesos_df, response_values, base

    df, perguntas, funcoes_df, setores_df, respostas_df, pesos_df, response_values = load_data()
    base = resumo_perguntas(df, perguntas, respostas_df, pesos_df)

    if tab == 'tab-funcoes':
        return funcoes_layout()
    if tab == 'tab-setores':
        return setores_layout()
    if tab == 'tab-respostas':
        return respostas_layout()
    if tab == 'tab-pesos':
        return pesos_layout()
    return dashboard_layout()


@app.callback(
    Output('filtro-funcao-dashboard', 'options'),
    Output('filtro-funcao-dashboard', 'value'),
    Input('modo-funcao-dashboard', 'value')
)
def update_funcoes_dashboard_options(modo_funcao):
    valores = sorted(df[modo_funcao].dropna().astype(str).unique().tolist())
    options = [{'label': 'Todas', 'value': '__all__'}] + [
        {'label': v, 'value': v} for v in valores
    ]
    return options, '__all__'


@app.callback(
    Output('graf-dimensoes', 'figure'),
    Output('tabela-itens', 'data'),
    Output('tabela-itens', 'columns'),
    Input('modo-funcao-dashboard', 'value'),
    Input('filtro-funcao-dashboard', 'value'),
    Input('filtro-dimensao', 'value')
)
def update_dashboard(modo_funcao, filtro_funcao, filtro_dimensao):
    df_filtrado = df.copy()

    if filtro_funcao != '__all__':
        df_filtrado = df_filtrado[df_filtrado[modo_funcao] == filtro_funcao]

    itens = resumo_perguntas(df_filtrado, perguntas, respostas_df, pesos_df)

    if filtro_dimensao != '__all__':
        itens = itens[itens['dimensao'] == filtro_dimensao]

    dim_df = build_dimensoes(itens)

    fig_dim = make_bar(
        dim_df,
        'indice_risco',
        'dimensao',
        'Índice de risco por dimensão',
        color='classificacao_risco'
    )

    tabela = itens.sort_values(['pontuacao_ajustada', 'respondidas'])[
        [
            'dimensao',
            'pergunta',
            'respondidas',
            'pontuacao_ajustada',
            'classificacao_risco',
            'prioridade_acao',
            'peso',
            'ativo'
        ]
    ]
    cols = [{'name': c.replace('_', ' ').title(), 'id': c} for c in tabela.columns]

    return fig_dim, tabela.to_dict('records'), cols


@app.callback(
    Output('msg-funcoes', 'children'),
    Output('reload-flag', 'data', allow_duplicate=True),
    Input('btn-save-funcoes', 'n_clicks'),
    State('tbl-funcoes', 'data'),
    prevent_initial_call=True
)
def save_funcoes(n, rows):
    if not n:
        return no_update, no_update
    save_mapping_df(rows, FUNCOES_MAP, df['funcao_original'].dropna().unique().tolist())
    return 'Funções salvas com sucesso.', {'saved': 'funcoes', 'n': n}


@app.callback(
    Output('msg-setores', 'children'),
    Output('reload-flag', 'data', allow_duplicate=True),
    Input('btn-save-setores', 'n_clicks'),
    State('tbl-setores', 'data'),
    prevent_initial_call=True
)
def save_setores(n, rows):
    if not n:
        return no_update, no_update
    save_mapping_df(rows, SETORES_MAP, df['setor_original'].dropna().unique().tolist())
    return 'Setores salvos com sucesso.', {'saved': 'setores', 'n': n}


@app.callback(
    Output('msg-respostas', 'children'),
    Output('reload-flag', 'data', allow_duplicate=True),
    Input('btn-save-respostas', 'n_clicks'),
    State('tbl-respostas', 'data'),
    prevent_initial_call=True
)
def save_respostas(n, rows):
    if not n:
        return no_update, no_update
    save_respostas_map(rows, RESPOSTAS_MAP, response_values)
    return 'Valores das respostas salvos com sucesso.', {'saved': 'respostas', 'n': n}


@app.callback(
    Output('msg-pesos', 'children'),
    Output('reload-flag', 'data', allow_duplicate=True),
    Input('btn-save-pesos', 'n_clicks'),
    State('tbl-pesos', 'data'),
    prevent_initial_call=True
)
def save_weights(n, rows):
    if not n:
        return no_update, no_update
    save_pesos(rows, perguntas)
    return 'Pesos salvos com sucesso.', {'saved': 'pesos', 'n': n}


if __name__ == '__main__':
    app.run(debug=True)