#%%
import pandas as pd
#%%
# Cargar los datos (Asumiendo que ya has cargado y preparado 'df' y 'df_est' como antes)
df = pd.read_csv(r"C:\Users\fariass\OneDrive - SUBSECRETARIA DE SALUD PUBLICA\Escritorio\DATA\TEMPERATURA\tmm_historico_2024.csv")
#%%
df['date'] = pd.to_datetime(df['date'])

# %%
## FUNCIONES DE EVALUACION DE ALERTAS 
def evaluar_alertas_senapred(df):
    # Inicializar columnas de alerta y mes
    df['senapred_alerta'] = 'Sin Alerta'
    df['mes'] = df['date'].dt.month

    # Alerta Temprana Preventiva
    df.loc[df['mes'].isin([11, 12, 1, 2, 3]), 'senapred_alerta'] = 'Alerta Temprana Preventiva'

    # Alerta Roja por temperatura >= 40°C en cualquier día
    df.loc[df['t_max'] >= 40, 'senapred_alerta'] = 'Alerta Roja'

    # Alerta Amarilla y Roja por temperatura >= 34°C en 2 o 3 días consecutivos
    df['senapred_alerta_temporal'] = df['t_max'] >= 34
    df['senapred_alerta_consecutiva'] = df['senapred_alerta_temporal'].rolling(window=2).sum()
    df.loc[df['senapred_alerta_consecutiva'] >= 2, 'senapred_alerta'] = 'Alerta Amarilla'
    df['senapred_alerta_consecutiva_3'] = df['senapred_alerta_temporal'].rolling(window=3).sum()
    df.loc[df['senapred_alerta_consecutiva_3'] >= 3, 'senapred_alerta'] = 'Alerta Roja'

    return df

def evaluar_alertas_sobre35(df):
    # Indicador para temperaturas sobre 35°C
    df['sobre_35_alerta'] = 'Bajo 35'
    df.loc[df['t_max'] >= 35, 'sobre_35_alerta'] = 'Sobre 35'
    return df

def evaluar_alertas_seremi(df):
    # Inicializar columna de alerta con valor por defecto
    df['seremi_alerta'] = 'Sin Alerta'

    # Verde Temprana Preventiva para temperaturas >= 30°C
    df.loc[df['t_max'] >= 30, 'seremi_alerta'] = 'Verde Temprana Preventiva'

    # Preparar indicadores temporales para Alerta Amarilla y Roja
    df['seremi_alerta_temporal_34'] = df['t_max'] >= 34
    df['seremi_alerta_consecutiva_34_2dias'] = df['seremi_alerta_temporal_34'].rolling(window=2).sum()
    df['seremi_alerta_consecutiva_34_3dias'] = df['seremi_alerta_temporal_34'].rolling(window=3).sum()

    # Alerta Amarilla: Temperaturas >= 34°C por al menos 2 días consecutivos
    df.loc[df['seremi_alerta_consecutiva_34_2dias'] >= 2, 'seremi_alerta'] = 'Alerta Amarilla'

    # Alerta Roja por temperatura >= 40°C en cualquier día
    df.loc[df['t_max'] >= 40, 'seremi_alerta'] = 'Alerta Roja'

    # Alerta Roja: Temperaturas >= 34°C por al menos 3 días consecutivos
    df.loc[df['seremi_alerta_consecutiva_34_3dias'] >= 3, 'seremi_alerta'] = 'Alerta Roja'

    return df

#%%
df = evaluar_alertas_seremi(df)
df = evaluar_alertas_sobre35(df)
df = evaluar_alertas_senapred(df)

# %%
df.to_csv("data_temperatura/datos_meteo.csv")
# %%
