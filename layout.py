# -----------------------------------------------------------------------------
# Arquivo: layout.py (Versão Final Multi-Ano)
# -----------------------------------------------------------------------------
from dash import dcc, html, dash_table
import dash_bootstrap_components as dbc
import pandas as pd

def create_layout(app_instance):
    return dbc.Container([
        dbc.Row(dbc.Col(html.Div(html.H2("Dashboard de Obras com Planejamento", className="app-title"), className="app-header"), width=12), className="mb-4"),
        dbc.Card(dbc.CardBody([
            dbc.Row([
                dbc.Col([
                    html.H5("Gerenciamento de Dados"),
                    dbc.Button([html.I(className="fas fa-hard-hat me-2"), "Gerenciar Obras"], id="btn-abrir-modal-obras", color="success", className="me-2 mb-2"),
                    dbc.Button([html.I(className="fas fa-plus me-2"), "Adicionar Nova Frente"], id="btn-abrir-modal-nova-frente", color="primary", className="me-2 mb-2"),
                    dbc.Button([html.I(className="fas fa-save me-2"), "Salvar Dados no Servidor"], id="btn-persistir-dados", color="warning", className="me-2 mb-2"),
                    html.Div(id="persistence-feedback-message", className="mt-2 small")
                ], md=5, className="mb-3 mb-md-0 border-end"),
                dbc.Col([
                    html.H5("Filtros de Visualização"),
                    html.Label("Selecionar Obra:", className="form-label fw-bold"),
                    dcc.Dropdown(id='obra-filter', placeholder="Selecione uma Obra", className="dropdown-custom mb-2"),
                    html.Label("Filtrar por Frente de Serviço:", className="form-label fw-bold"),
                    dcc.Dropdown(id='category-filter', placeholder="Selecione uma Frente ou Todas", className="dropdown-custom"),
                ], md=7)
            ], className="align-items-center"),
        ]), className="mb-4 shadow-sm"),
        dbc.Row(id='summary-cards-row', className="mb-4"),
        dbc.Row([
            dbc.Col(html.Div([
                dbc.Button(["Visão Semanal ", html.I(className="fas fa-calendar-week ms-1")], id="btn-semanal", color="info", outline=True, className="me-1 mb-2", n_clicks=0),
                dbc.Button(["Visão Mensal ", html.I(className="fas fa-calendar-alt ms-1")], id="btn-mensal", color="primary", outline=True, className="me-1 mb-2", n_clicks=0),
                dbc.Button(["Visão Geral ", html.I(className="fas fa-globe-americas ms-1")], id="btn-geral", color="success", outline=True, className="mb-2", n_clicks=0),
            ], className="text-center mb-2 button-group-custom"), width=12),
        ]),
        dcc.Loading(id="loading-graphs", type="default", children=[
            dbc.Row([
                dbc.Col(dbc.Card(dbc.CardBody(dcc.Graph(id='graph-progresso-frente', config={'responsive': True})), className="shadow-sm mb-4 h-100"), md=12, lg=4),
                dbc.Col(dbc.Card(dbc.CardBody(dcc.Graph(id='graph-performance-frentes', config={'responsive': True})), className="shadow-sm mb-4 h-100"), md=12, lg=8)
            ]),
            dbc.Row([dbc.Col(dbc.Card(dbc.CardBody(dcc.Graph(id='graph-evolucao-tempo', config={'responsive': True})), className="shadow-sm mb-4"), md=12)]),
            dbc.Row([dbc.Col(dbc.Button([html.I(className="fas fa-table me-2"), "Ver Detalhes e Lançar Andamento"], id="btn-abrir-detalhes-modal", color="secondary", className="w-100 mt-3"), width={"size": 6, "offset": 3})], className="mb-4")
        ]),
        html.Footer(dbc.Container(dbc.Row(dbc.Col(html.P(f"© {pd.Timestamp.now().year} Dashboard de Obras com Planejamento", className="text-center text-muted small"), width=12)), fluid=True, className="footer-custom")),
        dcc.Store(id='data-store'),
        dcc.Store(id='selected-obra-store'),
        dcc.Store(id='category-filter-store', data='Todos'),
        dcc.Store(id='active-timescale-store', data='mensal'),
        dcc.Store(id='selected-row-index-store'),
        dcc.Store(id='edit-mode-store', data={'mode': 'add', 'identifier': None}),
        dbc.Modal([
            dbc.ModalHeader(dbc.ModalTitle("Adicionar Nova Frente de Serviço", id="modal-nova-frente-title")),
            dbc.ModalBody([
                html.Div(id='new-frente-feedback-message', className="mb-3"),
                dbc.Form([
                    dbc.Row([dbc.Label("Nome da Obra", width="auto"), dbc.Col(dcc.Dropdown(id='form-obra-dropdown', placeholder="Selecione a Obra"))], className="align-items-center mb-3"),
                    dbc.Row([dbc.Label("Nome da Frente", width="auto"), dbc.Col(dbc.Input(id='form-frente-nome', type='text', required=True))], className="align-items-center mb-3"),
                    dbc.Row([dbc.Label("Quantidade Total", width="auto"), dbc.Col(dbc.Input(id='form-frente-total', type='number', min=0, required=True))], className="align-items-center mb-3"),
                    html.Hr(),
                    html.P("Informe o período de execução da frente de serviço:", className="small text-muted"),
                    dbc.Row([
                        dbc.Col([dbc.Label("Data de Início:", html_for="form-data-inicio"), dcc.DatePickerSingle(id='form-data-inicio', display_format='DD/MM/YYYY', className="w-100")]),
                        dbc.Col([dbc.Label("Data de Fim:", html_for="form-data-fim"), dcc.DatePickerSingle(id='form-data-fim', display_format='DD/MM/YYYY', className="w-100")])
                    ], className="mb-3"),
                    html.Div(id='weekly-planning-container', className="mt-3")
                ])
            ]),
            dbc.ModalFooter([dbc.Button("Cancelar", id="btn-cancelar-nova-frente", color="secondary"), dbc.Button("Salvar", id="btn-salvar-nova-frente", color="primary")])
        ], id="modal-nova-frente", is_open=False, size="lg", centered=True, scrollable=True),
        dbc.Modal([
            dbc.ModalHeader(dbc.ModalTitle(id="modal-realizado-header")),
            dbc.ModalBody(id="modal-realizado-body"), 
            dbc.ModalFooter([dbc.Button("Cancelar", id="btn-cancelar-realizado", color="secondary"), dbc.Button("Salvar Andamento", id="btn-salvar-realizado", color="success")])
        ], id="modal-preencher-realizado", is_open=False, size="lg", centered=True, scrollable=True),
        dbc.Modal([
            dbc.ModalHeader(dbc.ModalTitle("Detalhes e Andamento das Frentes de Serviço")),
            dbc.ModalBody([
                html.Div(id='table-save-feedback-message', className="mb-2"),
                dash_table.DataTable(id='tabela-detalhes-frentes', columns=[], data=[], editable=False, page_size=10, row_selectable='single', style_header={'backgroundColor': 'rgb(230, 230, 230)', 'fontWeight': 'bold'}, style_cell={'textAlign': 'left', 'padding': '5px'}, sort_action="native", filter_action="native", export_format="xlsx", export_headers="display"),
                html.Div([
                    dbc.Button([html.I(className="fas fa-pencil-alt me-2"), "Lançar Andamento"], id="btn-abrir-realizado-modal", color="success", className="mt-3", style={'display': 'none'}),
                    dbc.Button([html.I(className="fas fa-edit me-2"), "Editar Frente"], id="btn-abrir-editar-modal", color="info", className="mt-3 ms-2", style={'display': 'none'}),
                    dbc.Button([html.I(className="fas fa-trash-alt me-2"), "Excluir Frente"], id="btn-abrir-excluir-modal", color="danger", className="mt-3 ms-2", style={'display': 'none'}),
                ], className="d-flex")
            ]),
            dbc.ModalFooter(dbc.Button("Fechar", id="btn-fechar-detalhes-modal", className="ms-auto"))
        ], id="modal-detalhes-frentes", size="xl", is_open=False, centered=True),
        dbc.Modal([
            dbc.ModalHeader(dbc.ModalTitle("Confirmar Exclusão")),
            dbc.ModalBody(id="delete-confirm-body"),
            dbc.ModalFooter([dbc.Button("Cancelar", id="btn-cancelar-excluir", color="secondary"), dbc.Button("Confirmar Exclusão", id="btn-confirmar-excluir", color="danger")]),
        ], id="modal-confirmar-excluir", is_open=False, centered=True),
        dbc.Modal([
            dbc.ModalHeader(dbc.ModalTitle("Gerenciamento de Obras")),
            dbc.ModalBody([
                html.Div(id="obras-feedback-message", className="mb-3"),
                dbc.Form([
                    dbc.Label("Cadastrar Nova Obra:"),
                    dbc.InputGroup([dbc.Input(id="form-nova-obra-nome", placeholder="Nome da nova obra"), dbc.Button("Adicionar", id="btn-adicionar-obra", color="success")]),
                ]),
                html.Hr(),
                html.H5("Obras Existentes"),
                dcc.Loading(html.Div(id="lista-obras-existentes"))
            ]),
            dbc.ModalFooter(dbc.Button("Fechar", id="btn-fechar-modal-obras", color="secondary")),
        ], id="modal-obras", is_open=False, centered=True, scrollable=True),
        html.Div(id='app-layout-hidden-trigger', style={'display': 'none'})
    ], fluid=True, className="app-container bg-light")