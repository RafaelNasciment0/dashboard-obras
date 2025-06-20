# -----------------------------------------------------------------------------
# Arquivo: utils.py (Versão Final Multi-Ano)
# -----------------------------------------------------------------------------
import pandas as pd
import numpy as np

def recalculate_dataframe(df):
    if df.empty:
        return df
    df_recalc = df.copy()
    if 'Data Início' in df_recalc.columns:
        df_recalc['Data Início'] = pd.to_datetime(df_recalc['Data Início'], errors='coerce')
    if 'Data Fim' in df_recalc.columns:
        df_recalc['Data Fim'] = pd.to_datetime(df_recalc['Data Fim'], errors='coerce')
    if 'Total' in df_recalc.columns:
        df_recalc['Total'] = pd.to_numeric(df_recalc['Total'], errors='coerce').fillna(0)
    df_recalc['Ano (Previsto)'] = df_recalc['Total']
    def somar_realizado_semanal(d):
        if isinstance(d, dict):
            return sum(pd.to_numeric(v, errors='coerce') or 0 for v in d.values())
        return 0
    if 'Realizado por Semana' in df_recalc.columns:
        df_recalc['Ano (Realizado)'] = df_recalc['Realizado por Semana'].apply(somar_realizado_semanal)
    else:
        df_recalc['Ano (Realizado)'] = 0
    df_recalc['Total (%)'] = (df_recalc['Ano (Realizado)'] / df_recalc['Ano (Previsto)'].replace(0, np.nan) * 100).fillna(0).round(2)
    return df_recalc