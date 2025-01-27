#%%
import streamlit as st
import pandas as pd
import plotly.express as px
import pydeck as pdk
import plotly.graph_objects as go
from io import BytesIO
import datetime

# Configuración de fechas
fecha_inicio = datetime.date(2024, 1, 1)  # Mínimo permitido
fecha_fin = datetime.date.today()  # Máximo permitido
fecha_inicio_default = datetime.date(2024, 11, 1)

# Selección de rango de fechas
st.sidebar.write("### Seleccione el rango de fechas")
rango_fechas = st.sidebar.date_input(
    "Rango de Fechas:",
    [fecha_inicio_default, fecha_fin],  # Fechas predeterminadas
    min_value=fecha_inicio,
    max_value=fecha_fin
)
fecha_inicio_dt = pd.Timestamp(rango_fechas[0])
fecha_fin_dt = pd.Timestamp(rango_fechas[1])

# Carga de datos
def cargar_datos():
    path_def = "data_defunciones/defunciones_2024.csv"
    df_corredor = pd.read_excel('data_corredor_endemico/corredor_endemico_mayor80.xlsx')
    df_def = pd.read_csv(path_def)
    columns = [
        'SEXO', 'EDAD_TIPO', 'EDAD_CANT', 'DIA_DEF', 'MES_DEF', 'ANO_DEF',
        'DIAG1', 'REG_RES', 'CARDIOVASCULAR', 'DATE'
    ]
    df_def = df_def['SEXO|EDAD_TIPO|EDAD_CANT|DIA_DEF|MES_DEF|ANO_DEF|DIAG1|REG_RES|CARDIOVASCULAR|DATE'].str.split('|', expand=True)
    df_def.columns = columns
    
    return df_corredor, df_def

df_corredor, df_def = cargar_datos()

# Procesamiento de datos del corredor endémico
df_corredor['Éxito'] = df_corredor['Zona de éxito']
df_corredor['Seguridad'] = df_corredor['Zona de éxito'] + df_corredor['Zona de seguridad']
df_corredor['Alerta'] = df_corredor['Zona de éxito'] + df_corredor['Zona de seguridad'] + df_corredor['Zona de alerta']

# Filtrar defunciones para mayores de 80 años y agrupar por fecha
df_def['DATE'] = pd.to_datetime(df_def['DATE'])
df_def_80_mas = df_def[df_def['EDAD_CANT'].astype(float) >= 80]
df_def_80_mas = df_def_80_mas.loc[(df_def_80_mas.DATE >= fecha_inicio_dt) & (df_def_80_mas.DATE <= fecha_fin_dt)]
defunciones_por_dia = df_def_80_mas.groupby('DATE').size().reset_index(name='Defunciones')

#%%
# Carga de datos de temperatura
df_ttm = pd.read_csv("data_temperatura/tmm_historico_2024.csv")
df_ttm['date'] = pd.to_datetime(df_ttm['date'])

if len(rango_fechas) == 2:
    fecha_inicio_seleccionada, fecha_fin_seleccionada = rango_fechas
    df_alertas = df_ttm[(df_ttm['date'] >= pd.Timestamp(fecha_inicio_seleccionada)) &
                     (df_ttm['date'] <= pd.Timestamp(fecha_fin_seleccionada))]
else:
    df_alertas = df_ttm

#%%
# Evaluación de alertas
def evaluar_alertas(df):
    df['alerta'] = 'Sin Alerta' 
    df['mes'] = df['date'].dt.month
    df.loc[df['mes'].isin([11, 12, 1, 2, 3]), 'alerta'] = 'Alerta temprana preventiva'
    df.loc[df['t_max'] >= 40, 'alerta'] = 'Alerta Roja'
    df['alerta_temporal'] = df['t_max'] >= 34
    df['alerta_consecutiva'] = df['alerta_temporal'].rolling(window=2).sum()
    df.loc[df['alerta_consecutiva'] >= 2, 'alerta'] = 'Alerta Amarilla'
    df['alerta_consecutiva_3'] = df['alerta_temporal'].rolling(window=3).sum()
    df.loc[df['alerta_consecutiva_3'] >= 3, 'alerta'] = 'Alerta Roja'
    return df

df_alertas = evaluar_alertas(df_alertas)

#%%
# Funciones para gráficos
def graficar_corredor_endemico_ordenado(df):
    df['Fecha'] = pd.to_datetime(df['Fecha'])
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=df['Fecha'],
        y=df['Éxito'],
        name='Zona de Éxito',
        fill='tozeroy',
        mode='none',
        fillcolor='green'
    ))

    fig.add_trace(go.Scatter(
        x=df['Fecha'],
        y=df['Seguridad'],
        name='Zona de Seguridad',
        fill='tonexty',
        mode='none',
        fillcolor='yellow'
    ))

    fig.add_trace(go.Scatter(
        x=df['Fecha'],
        y=df['Alerta'],
        name='Zona de Alerta',
        fill='tonexty',
        mode='none',
        fillcolor='red'
    ))

    fig.update_layout(
        title='Corredor Endémico',
        xaxis_title='Fecha',
        yaxis_title='Tasa de Defunciones',
        template='plotly_white',
        legend=dict(
            title='Zonas',
            orientation="h",
            yanchor="bottom",
            y=-0.3,
            xanchor="center",
            x=0.5
        ),
        hovermode='x unified'
    )

    return fig

# Generar gráfico ordenado
fig_ordenado = graficar_corredor_endemico_ordenado(df_corredor)

#%%
def graficar_corredor_endemico_con_defunciones(df_corredor, defunciones_por_dia):
    df_corredor['Fecha'] = pd.to_datetime(df_corredor['Fecha'])
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=df_corredor['Fecha'],
        y=df_corredor['Éxito'],
        name='Zona de Éxito',
        fill='tozeroy',
        mode='none',
        fillcolor='green'
    ))

    fig.add_trace(go.Scatter(
        x=df_corredor['Fecha'],
        y=df_corredor['Seguridad'],
        name='Zona de Seguridad',
        fill='tonexty',
        mode='none',
        fillcolor='yellow'
    ))

    fig.add_trace(go.Scatter(
        x=df_corredor['Fecha'],
        y=df_corredor['Alerta'],
        name='Zona de Alerta',
        fill='tonexty',
        mode='none',
        fillcolor='red'
    ))

    fig.add_trace(go.Scatter(
        x=defunciones_por_dia['DATE'],
        y=defunciones_por_dia['Defunciones'],
        name='Defunciones Diarias',
        mode='lines+markers',
        line=dict(color='blue', width=2),
        marker=dict(size=5, symbol='circle')
    ))

    fig.update_layout(
        title='Corredor Endémico con Defunciones Diarias',
        xaxis_title='Fecha',
        yaxis_title='Número de Defunciones',
        template='plotly_white',
        legend=dict(
            title='Zonas y Defunciones',
            orientation="h",
            yanchor="bottom",
            y=-0.3,
            xanchor="center",
            x=0.5
        ),
        hovermode='x unified'
    )

    return fig

# Generar gráfico combinado con defunciones
fig_con_defunciones = graficar_corredor_endemico_con_defunciones(df_corredor, defunciones_por_dia)


#%%
def graficar_corredor_endemico_con_alertas(df_corredor, defunciones_por_dia, df_alertas):
    df_corredor['Fecha'] = pd.to_datetime(df_corredor['Fecha'])
    df_alertas['date'] = pd.to_datetime(df_alertas['date'])
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=df_corredor['Fecha'],
        y=df_corredor['Éxito'],
        name='Zona de Éxito',
        fill='tozeroy',
        mode='none',
        fillcolor='green'
    ))

    fig.add_trace(go.Scatter(
        x=df_corredor['Fecha'],
        y=df_corredor['Seguridad'],
        name='Zona de Seguridad',
        fill='tonexty',
        mode='none',
        fillcolor='yellow'
    ))

    fig.add_trace(go.Scatter(
        x=df_corredor['Fecha'],
        y=df_corredor['Alerta'],
        name='Zona de Alerta',
        fill='tonexty',
        mode='none',
        fillcolor='red'
    ))

    fig.add_trace(go.Scatter(
        x=defunciones_por_dia['DATE'],
        y=defunciones_por_dia['Defunciones'],
        name='Defunciones Diarias',
        mode='lines+markers',
        line=dict(color='blue', width=2),
        marker=dict(size=5, symbol='circle')
    ))

    color_map = {
        'Sin Alerta': 'black',
        'Alerta temprana preventiva': 'green',
        'Alerta Amarilla': 'gold',
        'Alerta Roja': 'red'
    }
    for alerta, color in color_map.items():
        df_alerta = df_alertas[df_alertas['alerta'] == alerta]
        fig.add_trace(go.Scatter(
            x=df_alerta['date'],
            y=df_alerta['t_max'],
            mode='markers',
            name=f'Alerta: {alerta}',
            marker=dict(color=color, size=8, symbol='triangle-up'),
            yaxis='y2'
        ))
        # Agregar la traza para las líneas
        fig.add_trace(go.Scatter(
            x=df_alerta['date'],
            y=df_alerta['t_max'],
            mode='lines',
            line=dict(color='black', width=1),
            name=f'Línea: {alerta}',
            showlegend=False,  # Ocultar la leyenda adicional
            yaxis='y2'
        ))
    fig.update_layout(
            title='Corredor Endémico con Defunciones y Alertas SEREMI',
            xaxis_title='Fecha',
            yaxis_title='Tasa de Defunciones',
            yaxis2=dict(
                title='Temperaturas Máximas',
                overlaying='y',
                side='right',
                showgrid=False
            ),
            template='plotly_white',
            legend=dict(
                title='Zonas, Defunciones y Alertas',
                orientation="h",
                yanchor="bottom",
                y=-0.3,
                xanchor="center",
                x=0.5
            ),
            hovermode='x unified'
        )

    return fig

#%% Generar gráfico combinado
fig_corredor_endemico_con_alertas = graficar_corredor_endemico_con_alertas(df_corredor, defunciones_por_dia, df_alertas)
st.plotly_chart(fig_corredor_endemico_con_alertas)
# %%
