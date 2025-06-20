# -----------------------------------------------------------------------------
# Arquivo: callbacks.py (Versão Final e Definitiva)
# -----------------------------------------------------------------------------
from dash import dcc, html, Input, Output, State, callback_context, no_update, dash_table, ALL
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import json
import os
from datetime import datetime
from io import StringIO

from utils import recalculate_dataframe

PLOTLY_TEMPLATE = "plotly_white"
DATA_FILE = "project_data.json"

def get_empty_df():
    return pd.DataFrame(columns=['Obra', 'Frente', 'Total', 'Data Início', 'Data Fim', 'Realizado por Semana', 'Planejamento Semanal'])

def get_weeks_in_range(start_date, end_date):
    if pd.isna(start_date) or pd.isna(end_date):
        return []
    weeks = pd.date_range(start=start_date, end=end_date, freq='W-MON').strftime('%G-W%V').tolist()
    start_week = start_date.strftime('%G-W%V')
    if start_week not in weeks:
        weeks.insert(0, start_week)
    return sorted(list(set(weeks)))

def register_callbacks(app):

    @app.callback(
        Output('data-store', 'data', allow_duplicate=True),
        Output('obra-filter', 'options'),
        Output('obra-filter', 'value'),
        Output('persistence-feedback-message', 'children', allow_duplicate=True),
        Input('app-layout-hidden-trigger', 'children'),
        prevent_initial_call='initial_duplicate'
    )
    def load_initial_data(_):
        if os.path.exists(DATA_FILE) and os.path.getsize(DATA_FILE) > 0:
            try:
                df = pd.read_json(DATA_FILE, orient='split')
                for col in ['Realizado por Semana', 'Planejamento Semanal']:
                    if col not in df.columns: df[col] = [{} for _ in range(len(df))]
                df_recalc = recalculate_dataframe(df)
                obras = sorted(df['Obra'].unique()) if 'Obra' in df.columns else []
                return df_recalc.to_json(date_format='iso', orient='split'), [{'label': o, 'value': o} for o in obras], obras[0] if obras else None, dbc.Alert(f"Dados de '{DATA_FILE}' carregados.", color="info", duration=3000, fade=True)
            except Exception as e:
                return get_empty_df().to_json(date_format='iso', orient='split'), [], None, dbc.Alert(f"Erro ao carregar dados: {e}. Verifique o formato do 'project_data.json'.", color="danger")
        else:
            return get_empty_df().to_json(date_format='iso', orient='split'), [], None, dbc.Alert("Nenhum dado salvo encontrado.", color="warning", duration=5000, fade=True)

    @app.callback(
        Output('persistence-feedback-message', 'children', allow_duplicate=True),
        Input('btn-persistir-dados', 'n_clicks'),
        State('data-store', 'data'),
        prevent_initial_call=True
    )
    def persist_data_to_file(n_clicks, data_json):
        if n_clicks and data_json:
            try:
                df_to_save = pd.read_json(StringIO(data_json), orient='split')
                cols_to_save = ['Obra', 'Frente', 'Total', 'Data Início', 'Data Fim', 'Realizado por Semana', 'Planejamento Semanal']
                df_to_save[cols_to_save].to_json(DATA_FILE, orient='split', indent=4)
                return dbc.Alert("Dados salvos com sucesso!", color="success", duration=4000, fade=True)
            except Exception as e:
                return dbc.Alert(f"Falha ao salvar dados: {e}", color="danger")
        return no_update

    @app.callback(
        Output('modal-obras', 'is_open'),
        Output('lista-obras-existentes', 'children'),
        Input('btn-abrir-modal-obras', 'n_clicks'),
        Input('btn-fechar-modal-obras', 'n_clicks'),
        State('modal-obras', 'is_open'),
        State('data-store', 'data')
    )
    def toggle_and_populate_obras_modal(n_open, n_close, is_open, data_json):
        if not callback_context.triggered: return no_update, no_update
        button_id = callback_context.triggered[0]['prop_id'].split('.')[0]
        if button_id == 'btn-abrir-modal-obras':
            df = pd.read_json(StringIO(data_json), orient='split')
            obras = sorted(df['Obra'].unique()) if 'Obra' in df.columns and not df.empty else []
            lista = dbc.ListGroup([dbc.ListGroupItem(o) for o in obras]) if obras else html.P("Nenhuma obra cadastrada.")
            return True, lista
        if button_id == 'btn-fechar-modal-obras':
            return False, no_update
        return is_open, no_update

    @app.callback(
        Output('data-store', 'data', allow_duplicate=True),
        Output('obras-feedback-message', 'children'),
        Output('form-nova-obra-nome', 'value'),
        Output('obra-filter', 'options', allow_duplicate=True),
        Input('btn-adicionar-obra', 'n_clicks'),
        State('form-nova-obra-nome', 'value'),
        State('data-store', 'data'),
        prevent_initial_call=True
    )
    def add_new_obra(n_clicks, nome_obra, data_json):
        if not n_clicks or not nome_obra:
            return no_update, dbc.Alert("O nome da obra não pode estar vazio.", color="warning"), "", no_update
        df = pd.read_json(StringIO(data_json), orient='split')
        if 'Obra' in df.columns and nome_obra.strip() in df['Obra'].unique():
            return no_update, dbc.Alert(f"A obra '{nome_obra}' já existe.", color="danger"), "", no_update
        new_row = {'Obra': nome_obra.strip(), 'Frente': '---', 'Total': 0, 'Data Início': None, 'Data Fim': None, 'Realizado por Semana': {}, 'Planejamento Semanal': {}}
        df_new = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        obras = sorted(df_new['Obra'].unique())
        return df_new.to_json(orient='split', date_format='iso'), dbc.Alert("Obra cadastrada!", color="success"), "", [{'label': o, 'value': o} for o in obras]

    @app.callback(
        Output('modal-nova-frente', 'is_open', allow_duplicate=True),
        Output('modal-nova-frente-title', 'children'),
        Output('edit-mode-store', 'data', allow_duplicate=True),
        Output('new-frente-feedback-message', 'children', allow_duplicate=True),
        Output('form-obra-dropdown', 'options'),
        Output('form-obra-dropdown', 'value'),
        Output('form-obra-dropdown', 'disabled'),
        Output('form-frente-nome', 'value'),
        Output('form-frente-total', 'value'),
        Output('form-data-inicio', 'date'),
        Output('form-data-fim', 'date'),
        Input('btn-abrir-modal-nova-frente', 'n_clicks'),
        State('data-store', 'data'),
        prevent_initial_call=True
    )
    def open_add_frente_modal(n_clicks, data_json):
        if not n_clicks: return (no_update,) * 11
        df = pd.read_json(StringIO(data_json), orient='split')
        obras = sorted(df['Obra'].unique()) if 'Obra' in df.columns else []
        return True, "Adicionar Nova Frente", {'mode': 'add'}, None, [{'label': o, 'value': o} for o in obras], None, False, None, None, None, None

    @app.callback(
        Output('weekly-planning-container', 'children'),
        Input('form-data-inicio', 'date'),
        Input('form-data-fim', 'date'),
        State('edit-mode-store', 'data'),
        State('data-store', 'data'),
    )
    def generate_weekly_planning_inputs(start_date_str, end_date_str, edit_mode, data_json):
        if not start_date_str or not end_date_str: return None
        start_date, end_date = pd.to_datetime(start_date_str), pd.to_datetime(end_date_str)
        weeks_list = get_weeks_in_range(start_date, end_date)
        planning_values = {}
        if edit_mode.get('mode') == 'edit':
            df = pd.read_json(StringIO(data_json), orient='split')
            identifier = edit_mode.get('identifier')
            if identifier:
                frente_data_row = df[(df['Obra'] == identifier['Obra']) & (df['Frente'] == identifier['Frente'])]
                if not frente_data_row.empty:
                    planning_values = frente_data_row.iloc[0].get('Planejamento Semanal', {})
                    if not isinstance(planning_values, dict): planning_values = {}
        form_inputs = [dbc.Row([dbc.Col(dbc.Label(f"Semana {w.split('-W')[-1]} ({w.split('-W')[0]})"), width=6), dbc.Col(dbc.Input(id={'type': 'input-planejamento-semana', 'id': w}, type='number', min=0, value=planning_values.get(w)), width=6)], className="mb-2") for w in weeks_list]
        return [html.Hr(), html.H5("Planejamento Semanal (Opcional)"), html.P("Deixe em branco para um planejamento linear.", className="small text-muted")] + form_inputs

    @app.callback(
        Output('modal-nova-frente', 'is_open', allow_duplicate=True),
        Output('modal-nova-frente-title', 'children', allow_duplicate=True),
        Output('edit-mode-store', 'data', allow_duplicate=True),
        Output('new-frente-feedback-message', 'children', allow_duplicate=True),
        Output('form-obra-dropdown', 'options', allow_duplicate=True),
        Output('form-obra-dropdown', 'value', allow_duplicate=True),
        Output('form-obra-dropdown', 'disabled', allow_duplicate=True),
        Output('form-frente-nome', 'value', allow_duplicate=True),
        Output('form-frente-total', 'value', allow_duplicate=True),
        Output('form-data-inicio', 'date', allow_duplicate=True),
        Output('form-data-fim', 'date', allow_duplicate=True),
        Input('btn-abrir-editar-modal', 'n_clicks'),
        State('selected-row-index-store', 'data'),
        State('data-store', 'data'),
        prevent_initial_call=True
    )
    def open_edit_modal_and_populate(n_clicks, frente_identifier, data_json):
        if not n_clicks or not frente_identifier: return (no_update,) * 11
        df = pd.read_json(StringIO(data_json), orient='split')
        frente_data = df[(df['Obra'] == frente_identifier['Obra']) & (df['Frente'] == frente_identifier['Frente'])].iloc[0]
        obras = sorted(df['Obra'].unique())
        obra_val, frente_val, total_val = frente_data.get('Obra'), frente_data.get('Frente'), frente_data.get('Total')
        data_inicio_ts, data_fim_ts = pd.to_datetime(frente_data.get('Data Início')), pd.to_datetime(frente_data.get('Data Fim'))
        data_inicio_str, data_fim_str = (data_inicio_ts.strftime('%Y-%m-%d') if pd.notna(data_inicio_ts) else None), (data_fim_ts.strftime('%Y-%m-%d') if pd.notna(data_fim_ts) else None)
        return True, f"Editar Frente: {frente_val}", {'mode': 'edit', 'identifier': frente_identifier}, None, [{'label': o, 'value': o} for o in obras], obra_val, True, frente_val, total_val, data_inicio_str, data_fim_str

    @app.callback(
        Output('modal-nova-frente', 'is_open', allow_duplicate=True),
        Input('btn-cancelar-nova-frente', 'n_clicks'),
        prevent_initial_call=True
    )
    def close_add_edit_modal(n_clicks):
        return False if n_clicks else no_update

    @app.callback(
        Output('data-store', 'data', allow_duplicate=True),
        Output('new-frente-feedback-message', 'children', allow_duplicate=True),
        Output('modal-nova-frente', 'is_open', allow_duplicate=True),
        Output('obra-filter', 'options', allow_duplicate=True),
        Output('obra-filter', 'value', allow_duplicate=True),
        Input('btn-salvar-nova-frente', 'n_clicks'),
        State('data-store', 'data'),
        State('edit-mode-store', 'data'),
        State('form-obra-dropdown', 'value'),
        State('form-frente-nome', 'value'),
        State('form-frente-total', 'value'),
        State('form-data-inicio', 'date'),
        State('form-data-fim', 'date'),
        State({'type': 'input-planejamento-semana', 'id': ALL}, 'id'),
        State({'type': 'input-planejamento-semana', 'id': ALL}, 'value'),
        prevent_initial_call=True
    )
    def save_frente_data(n_clicks, data_json, edit_mode, obra, frente, total, data_inicio, data_fim, plan_ids, plan_values):
        if not n_clicks: return (no_update,) * 5
        if not all([obra, frente, total is not None, data_inicio, data_fim]):
            return no_update, dbc.Alert("Todos os campos principais são obrigatórios!", color="danger"), True, no_update, no_update
        if pd.to_datetime(data_fim) < pd.to_datetime(data_inicio):
            return no_update, dbc.Alert("Erro: A Data de Fim não pode ser anterior à Data de Início!", color="danger"), True, no_update, no_update
        total_planejado = sum(pd.to_numeric(v, errors='coerce') or 0 for v in plan_values)
        if total_planejado > float(total):
            return no_update, dbc.Alert(f"Erro: O planejado ({total_planejado}) excede o Total ({total})!", color="danger"), True, no_update, no_update
        df = pd.read_json(StringIO(data_json), orient='split')
        df['Data Início'] = pd.to_datetime(df['Data Início'])
        df['Data Fim'] = pd.to_datetime(df['Data Fim'])
        obra, frente = obra.strip(), frente.strip()
        is_editing = edit_mode.get('mode') == 'edit'
        original_identifier = edit_mode.get('identifier')
        potential_duplicate = df[(df['Obra'] == obra) & (df['Frente'] == frente)]
        if not potential_duplicate.empty and (not is_editing or potential_duplicate.iloc[0]['Frente'] != original_identifier.get('Frente')):
            return no_update, dbc.Alert(f"A frente '{frente}' já existe!", color="danger"), True, no_update, no_update
        planejamento_semanal = {p_id['id']: (float(val) if val is not None else None) for p_id, val in zip(plan_ids, plan_values)}
        new_data = {'Obra': obra, 'Frente': frente, 'Total': float(total), 'Data Início': data_inicio, 'Data Fim': data_fim, 'Planejamento Semanal': planejamento_semanal}
        if is_editing:
            idx = df[(df['Obra'] == original_identifier['Obra']) & (df['Frente'] == original_identifier['Frente'])].index[0]
            new_data['Realizado por Semana'] = df.at[idx, 'Realizado por Semana'] if 'Realizado por Semana' in df.columns and isinstance(df.at[idx, 'Realizado por Semana'], dict) else {}
            for key, value in new_data.items(): df.at[idx, key] = value
            feedback_msg = dbc.Alert("Frente atualizada!", color="success", duration=3000)
        else:
            new_data['Realizado por Semana'] = {}
            new_row_df = pd.DataFrame([new_data])
            new_row_df['Data Início'] = pd.to_datetime(new_row_df['Data Início'])
            new_row_df['Data Fim'] = pd.to_datetime(new_row_df['Data Fim'])
            df = pd.concat([df, new_row_df], ignore_index=True)
            feedback_msg = dbc.Alert("Frente adicionada!", color="success", duration=3000)
        df_recalculated = recalculate_dataframe(df)
        obras = sorted(df_recalculated['Obra'].unique())
        return df_recalculated.to_json(date_format='iso', orient='split'), feedback_msg, False, [{'label': o, 'value': o} for o in obras], obra

    @app.callback(
        Output('modal-detalhes-frentes', 'is_open'),
        Input('btn-abrir-detalhes-modal', 'n_clicks'),
        Input('btn-fechar-detalhes-modal', 'n_clicks'),
        State('modal-detalhes-frentes', 'is_open'),
        prevent_initial_call=True,
    )
    def toggle_detalhes_modal(n_open, n_close, is_open):
        return not is_open if (n_open or n_close) else is_open

    @app.callback(
        Output('btn-abrir-realizado-modal', 'style'),
        Output('btn-abrir-editar-modal', 'style'),
        Output('btn-abrir-excluir-modal', 'style'),
        Output('selected-row-index-store', 'data'),
        Input('tabela-detalhes-frentes', 'selected_rows'),
        State('tabela-detalhes-frentes', 'data'),
        prevent_initial_call=True
    )
    def handle_row_selection(selected_rows, table_data):
        if selected_rows and selected_rows[0] < len(table_data):
            row_data = table_data[selected_rows[0]]
            identifier = {'Obra': row_data.get('Obra'), 'Frente': row_data.get('Frente')}
            return {'display': 'inline-block'}, {'display': 'inline-block'}, {'display': 'inline-block'}, identifier
        return {'display': 'none'}, {'display': 'none'}, {'display': 'none'}, None

    @app.callback(
        Output('modal-confirmar-excluir', 'is_open'),
        Output('delete-confirm-body', 'children'),
        Input('btn-abrir-excluir-modal', 'n_clicks'),
        State('selected-row-index-store', 'data'),
        prevent_initial_call=True
    )
    def open_delete_confirmation_modal(n_clicks, frente_identifier):
        if n_clicks and frente_identifier:
            return True, f"Tem a certeza que deseja excluir a frente '{frente_identifier['Frente']}'?"
        return False, None

    @app.callback(
        Output('modal-confirmar-excluir', 'is_open', allow_duplicate=True),
        Input('btn-cancelar-excluir', 'n_clicks'),
        prevent_initial_call=True
    )
    def cancel_delete(n_clicks):
        return False if n_clicks else no_update

    @app.callback(
        Output('data-store', 'data', allow_duplicate=True),
        Output('table-save-feedback-message', 'children', allow_duplicate=True),
        Output('modal-confirmar-excluir', 'is_open', allow_duplicate=True),
        Output('tabela-detalhes-frentes', 'selected_rows', allow_duplicate=True),
        Input('btn-confirmar-excluir', 'n_clicks'),
        State('selected-row-index-store', 'data'),
        State('data-store', 'data'),
        prevent_initial_call=True
    )
    def execute_delete(n_clicks, frente_identifier, data_json):
        if not n_clicks or not frente_identifier: return no_update, no_update, True, no_update
        df = pd.read_json(StringIO(data_json), orient='split')
        idx_to_delete = df[(df['Obra'] == frente_identifier['Obra']) & (df['Frente'] == frente_identifier['Frente'])].index
        if not idx_to_delete.empty:
            df.drop(idx_to_delete, inplace=True)
            return df.to_json(date_format='iso', orient='split'), dbc.Alert("Frente excluída!", color="success"), False, []
        return no_update, dbc.Alert("Erro ao excluir.", color="danger"), True, []

    @app.callback(
        Output('modal-preencher-realizado', 'is_open'),
        Output('modal-realizado-header', 'children'),
        Output('modal-realizado-body', 'children'),
        Input('btn-abrir-realizado-modal', 'n_clicks'),
        Input('btn-cancelar-realizado', 'n_clicks'),
        State('selected-row-index-store', 'data'),
        State('data-store', 'data'),
        prevent_initial_call=True
    )
    def open_realizado_modal(n_open, n_cancel, frente_identifier, data_json):
        if callback_context.triggered_id == 'btn-abrir-realizado-modal' and frente_identifier:
            df = pd.read_json(StringIO(data_json), orient='split')
            df['Data Início'] = pd.to_datetime(df['Data Início'])
            df['Data Fim'] = pd.to_datetime(df['Data Fim'])
            frente_data = df[(df['Obra'] == frente_identifier['Obra']) & (df['Frente'] == frente_identifier['Frente'])].iloc[0]
            start_date, end_date = frente_data.get('Data Início'), frente_data.get('Data Fim')
            weeks_list = get_weeks_in_range(start_date, end_date)
            realizado_semanal = frente_data.get('Realizado por Semana', {})
            planejado_semanal = frente_data.get('Planejamento Semanal', {})
            form_inputs = [dbc.Row([
                dbc.Col(dbc.Label(f"Semana {w.split('-W')[-1]} ({w.split('-W')[0]})"), width=5),
                dbc.Col(html.Small(f"Planejado: {planejado_semanal.get(w, 0) or 0}", className="text-muted"), width=3),
                dbc.Col(dbc.Input(id={'type': 'input-realizado-semana', 'id': w}, type='number', value=realizado_semanal.get(w)), width=4)
            ], className="mb-2 align-items-center") for w in weeks_list]
            return True, f"Lançar Andamento: {frente_identifier['Frente']}", dbc.Form(form_inputs) if form_inputs else html.P("Período inválido.")
        return False, no_update, no_update

    @app.callback(
        Output('data-store', 'data', allow_duplicate=True),
        Output('table-save-feedback-message', 'children', allow_duplicate=True),
        Output('modal-preencher-realizado', 'is_open', allow_duplicate=True),
        Input('btn-salvar-realizado', 'n_clicks'),
        State({'type': 'input-realizado-semana', 'id': ALL}, 'id'),
        State({'type': 'input-realizado-semana', 'id': ALL}, 'value'),
        State('selected-row-index-store', 'data'),
        State('data-store', 'data'),
        prevent_initial_call=True
    )
    def save_realizado_values(n_clicks, semana_ids, semana_valores, frente_identifier, data_json):
        if not n_clicks or not frente_identifier: return no_update, no_update, True
        df = pd.read_json(StringIO(data_json), orient='split')
        idx = df[(df['Obra'] == frente_identifier['Obra']) & (df['Frente'] == frente_identifier['Frente'])].index[0]
        if 'Realizado por Semana' not in df.columns or not isinstance(df.at[idx, 'Realizado por Semana'], dict):
            df.at[idx, 'Realizado por Semana'] = {}
        for sid, val in zip(semana_ids, semana_valores):
            if val is not None: df.at[idx, 'Realizado por Semana'][sid['id']] = float(val)
        return recalculate_dataframe(df).to_json(date_format='iso', orient='split'), dbc.Alert("Andamento salvo!", color="success"), False

    @app.callback(
        Output('active-timescale-store', 'data'),
        Input('btn-semanal', 'n_clicks'),
        Input('btn-mensal', 'n_clicks'),
        Input('btn-geral', 'n_clicks'),
        prevent_initial_call=True
    )
    def update_active_timescale(n_sem, n_mes, n_geral):
        return callback_context.triggered[0]['prop_id'].split('.')[0].replace('btn-', '')

    @app.callback(
        Output('semana-slider-col', 'style'),
        Input('active-timescale-store', 'data')
    )
    def toggle_slider_visibility(timescale):
        return {'display': 'none'}

    @app.callback(
        Output('category-filter-store', 'data'),
        Input('category-filter', 'value')
    )
    def update_category_filter_store(selected_frente):
        return selected_frente

    @app.callback(
        Output('selected-obra-store', 'data'),
        Input('obra-filter', 'value'),
        prevent_initial_call=True
    )
    def update_selected_obra_store(selected_obra):
        return selected_obra

    @app.callback(
        Output('category-filter', 'options'),
        Output('category-filter', 'value'),
        Input('selected-obra-store', 'data'),
        State('data-store', 'data'),
        prevent_initial_call=True
    )
    def update_frente_options(selected_obra, data_json):
        if not data_json or not selected_obra: return [], 'Todos'
        df = pd.read_json(StringIO(data_json), orient='split')
        if df.empty or 'Obra' not in df.columns: return [], 'Todos'
        frentes = sorted(df[(df['Obra'] == selected_obra) & (df['Frente'] != '---')]['Frente'].unique())
        return [{'label': 'Todos', 'value': 'Todos'}] + [{'label': f, 'value': f} for f in frentes], 'Todos'

    @app.callback(
        Output('graph-progresso-frente', 'figure'),
        Output('graph-performance-frentes', 'figure'),
        Output('graph-evolucao-tempo', 'figure'),
        Output('tabela-detalhes-frentes', 'data'),
        Output('tabela-detalhes-frentes', 'columns'),
        Output('tabela-detalhes-frentes', 'style_data_conditional'),
        Output('summary-cards-row', 'children'),
        Input('data-store', 'data'),
        Input('selected-obra-store', 'data'),
        Input('category-filter-store', 'data'),
        Input('active-timescale-store', 'data'),
        prevent_initial_call=True
    )
    def update_visuals_and_table(jsonified_data, selected_obra, selected_frente, timescale):
        fig_placeholder = go.Figure(layout={'template': PLOTLY_TEMPLATE, 'annotations': [{'text': 'Sem dados', 'showarrow': False}]})
        if not jsonified_data: return (fig_placeholder,) * 3 + ([], [], [], [])

        df = pd.read_json(StringIO(jsonified_data), orient='split')
        if df.empty or 'Frente' not in df.columns: return (fig_placeholder,) * 3 + ([], [], [], [])
        
        df['Data Início'] = pd.to_datetime(df['Data Início'])
        df['Data Fim'] = pd.to_datetime(df['Data Fim'])
        df_vis = df[df['Frente'] != '---'].copy()
        
        if df_vis.empty: return (fig_placeholder,) * 3 + ([], [], [], [])

        df_obra = df_vis[df_vis['Obra'] == selected_obra] if selected_obra else df_vis.copy()
        df_filtered = df_obra[df_obra['Frente'] == selected_frente] if selected_frente and selected_frente != 'Todos' else df_obra.copy()

        df_card = df_filtered if selected_frente != 'Todos' else df_obra
        progresso = (df_card['Ano (Realizado)'].sum() / df_card['Ano (Previsto)'].sum() * 100) if df_card['Ano (Previsto)'].sum() > 0 else 0
        cards = [dbc.Col(dbc.Card([dbc.CardHeader("Progresso"), dbc.CardBody([html.H3(f"{progresso:.1f}%")])]), md=4),
                 dbc.Col(dbc.Card([dbc.CardHeader("Concluídas"), dbc.CardBody([html.H3(f"{df_card[df_card['Total (%)'] >= 99.9].shape[0]} de {df_card['Frente'].nunique()}")])]), md=4),
                 dbc.Col(dbc.Card([dbc.CardHeader("Status"), dbc.CardBody([html.H3("Finalizado" if progresso >= 100 else "Em Andamento")])]), md=4)]

        fig_gauge = go.Figure(go.Indicator(mode="gauge+number", value=(df_filtered.iloc[0]['Total (%)'] if not df_filtered.empty and selected_frente != 'Todos' else progresso), title={'text': f"{selected_frente if selected_frente != 'Todos' else 'Geral'}"}))

        fig_performance = go.Figure(layout={'template': PLOTLY_TEMPLATE})
        if selected_frente and selected_frente != 'Todos' and not df_filtered.empty:
            frente = df_filtered.iloc[0]
            start, end, total = frente.get('Data Início'), frente.get('Data Fim'), frente.get('Total', 0)
            plano_semanal = frente.get('Planejamento Semanal', {})
            realizado = frente.get('Realizado por Semana', {})
            xaxis_format = '%b (%G-W%V)'
            if isinstance(plano_semanal, dict) and any(val for val in plano_semanal.values() if val is not None and val > 0):
                planned_series = pd.Series(plano_semanal).sort_index(); planned_series.index = pd.to_datetime(planned_series.index.str.replace('-W', '') + '-1', format='%G%V-%w')
                planned_cumulative = planned_series.cumsum()
                fig_performance.add_trace(go.Scatter(x=planned_cumulative.index.strftime(xaxis_format), y=planned_cumulative, name='Planejado', line={'dash': 'dash', 'color': 'red'}, marker={'color': 'red'}, mode='lines+markers'))
            elif pd.notna(start) and pd.notna(end) and total > 0:
                planned_series = pd.Series(total / len(pd.date_range(start, end)), index=pd.date_range(start, end)).resample('W-MON').sum()
                planned_cumulative = planned_series.cumsum()
                fig_performance.add_trace(go.Scatter(x=planned_cumulative.index.strftime(xaxis_format), y=planned_cumulative, name='Previsto (Linear)', line={'dash': 'dot', 'color': 'red'}, marker={'color': 'red'}, mode='lines+markers'))
            if isinstance(realizado, dict) and realizado:
                realizado_series = pd.Series(realizado).sort_index(); realizado_series.index = pd.to_datetime(realizado_series.index.str.replace('-W', '') + '-1', format='%G%V-%w')
                realizado_cumulative = realizado_series.cumsum()
                fig_performance.add_trace(go.Scatter(x=realizado_cumulative.index.strftime(xaxis_format), y=realizado_cumulative, name='Realizado', line={'color': 'blue'}, marker={'color': 'blue'}, mode='lines+markers'))
            fig_performance.update_layout(title=f'Curva S: {selected_frente}', xaxis_title='Semana (Mês/Ano-WNumero)')
        else:
            fig_performance = px.bar(df_obra.sort_values('Total (%)'), x='Total (%)', y='Frente', orientation='h', title=f'Performance Geral ({selected_obra})')

        fig_evolucao = go.Figure(layout={'barmode': 'group', 'template': PLOTLY_TEMPLATE, 'title': f'Evolução ({timescale.capitalize()})'})
        series_list_real = [pd.Series({pd.to_datetime(k.replace('-W', '')+'-1', format='%G%V-%w'): v for k,v in r.get('Realizado por Semana',{}).items() if v is not None}) for _, r in df_filtered.iterrows()]
        series_list_plan = []
        for _, r in df_filtered.iterrows():
            plano_semanal, start, end, total = r.get('Planejamento Semanal', {}), r.get('Data Início'), r.get('Data Fim'), r.get('Total', 0)
            if isinstance(plano_semanal, dict) and any(val for val in plano_semanal.values() if val is not None and val > 0):
                series_list_plan.append(pd.Series({pd.to_datetime(k.replace('-W', '')+'-1', format='%G%V-%w'): v for k,v in plano_semanal.items() if v is not None}))
            elif pd.notna(start) and pd.notna(end) and total > 0:
                series_list_plan.append(pd.Series(total / len(pd.date_range(start, end)), index=pd.date_range(start, end)))
        non_empty_series_plan = [s for s in series_list_plan if not s.empty]
        if non_empty_series_plan:
            total_planejado = pd.concat(non_empty_series_plan).groupby(level=0).sum().sort_index()
            if not total_planejado.empty:
                freq = 'ME' if timescale == 'mensal' else 'W-MON'; fmt = '%Y-%m' if timescale == 'mensal' else '%b (%G-W%V)'
                resampled = total_planejado.resample(freq).sum()
                fig_evolucao.add_trace(go.Bar(x=resampled.index.strftime(fmt), y=resampled.values, name='Previsto', marker_color='red'))
        non_empty_series_real = [s for s in series_list_real if not s.empty]
        if non_empty_series_real:
            total_realizado = pd.concat(non_empty_series_real).groupby(level=0).sum().sort_index()
            if not total_realizado.empty:
                freq = 'ME' if timescale == 'mensal' else 'W-MON'; fmt = '%Y-%m' if timescale == 'mensal' else '%b (%G-W%V)'
                resampled = total_realizado.resample(freq).sum()
                fig_evolucao.add_trace(go.Bar(x=resampled.index.strftime(fmt), y=resampled.values, name='Realizado', marker_color='blue'))
        if timescale == 'geral':
            fig_evolucao.add_trace(go.Bar(x=['Visão Geral'], y=[df_filtered['Ano (Previsto)'].sum()], name='Total Previsto', marker_color='red'))
            fig_evolucao.add_trace(go.Bar(x=['Visão Geral'], y=[df_filtered['Ano (Realizado)'].sum()], name='Total Realizado', marker_color='blue'))

        cols_tabela = ['Obra', 'Frente', 'Total', 'Data Início', 'Data Fim', 'Total (%)']
        data_tabela = df_filtered[cols_tabela].copy()
        if not data_tabela.empty:
            data_tabela['Data Início'] = pd.to_datetime(data_tabela['Data Início']).dt.strftime('%d/%m/%Y').replace('NaT', '')
            data_tabela['Data Fim'] = pd.to_datetime(data_tabela['Data Fim']).dt.strftime('%d/%m/%Y').replace('NaT', '')
        
        return (fig_gauge, fig_performance, fig_evolucao, data_tabela.to_dict('records'), [{"name": i, "id": i} for i in cols_tabela], 
                [{'if': {'column_id': 'Total (%)', 'filter_query': '{Total (%)} >= 99.9'}, 'backgroundColor': '#d4edda'}], 
                cards)