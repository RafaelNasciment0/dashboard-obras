# -----------------------------------------------------------------------------
# Arquivo: app.py (Versão Final Limpa)
# -----------------------------------------------------------------------------
from dash import Dash, html
import dash_bootstrap_components as dbc
import os

try:
    from layout import create_layout
    from callbacks import register_callbacks
    print("Importações de 'layout.py' e 'callbacks.py' concluídas com sucesso.")
except ImportError as e:
    print("\n--- ERRO CRÍTICO na importação ---")
    print(f"Não foi possível importar 'layout.py' ou 'callbacks.py'. Detalhes: {e}")
    print("----------------------------------\n")
    raise

# 1. Inicializa a aplicação Dash
app = Dash(__name__,
           suppress_callback_exceptions=True,
           external_stylesheets=[dbc.themes.FLATLY, dbc.icons.FONT_AWESOME])

# 2. Define o título do aplicativo
app.title = 'Dashboard de Obras Interativo'

# 3. Expõe a variável do servidor Flask para o Gunicorn
server = app.server

# 4. Define o layout da aplicação a partir do arquivo layout.py
try:
    app.layout = create_layout(app)
except Exception as e:
    print(f"\n--- ERRO CRÍTICO no layout.py: {e} ---")
    app.layout = html.Div([
        html.H1("Erro ao Carregar o Layout do Aplicativo"),
        html.P("Verifique o console/terminal para os detalhes completos do erro.")
    ])

# 5. Registra todos os callbacks a partir do arquivo callbacks.py
try:
    register_callbacks(app)
except Exception as e:
    print(f"\n--- ERRO CRÍTICO no callbacks.py: {e} ---")

# 6. Bloco para execução em modo de desenvolvimento local
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8050))
    app.run(debug=True, host='0.0.0.0', port=port)