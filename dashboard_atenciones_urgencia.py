#%%
import streamlit as st
import pandas as pd
import plotly.express as px
import pydeck as pdk
import plotly.graph_objects as go
from io import BytesIO
import datetime
#%%
fecha_inicio = datetime.date(2024, 1, 1)  # Mínimo permitido
fecha_fin = datetime.date.today()  # Máximo permitido
fecha_inicio_default = datetime.date(2024, 11, 1)

st.sidebar.write("### Seleccione el rango de fechas")
rango_fechas = st.sidebar.date_input(
    "Rango de Fechas:",
    [fecha_inicio_default, fecha_fin],  # Fechas predeterminadas
    min_value=fecha_inicio,
    max_value=fecha_fin
)
#%%
df_au = pd.read_csv("data_atenciones_urgencia/df_rm_circ_2024.csv")
df_au['fecha'] = pd.to_datetime(df_au['fecha'])

if len(rango_fechas) == 2:
    fecha_inicio_seleccionada, fecha_fin_seleccionada = rango_fechas
    df_au = df_au[(df_au['fecha'] >= pd.Timestamp(fecha_inicio_seleccionada)) &
                     (df_au['fecha'] <= pd.Timestamp(fecha_fin_seleccionada))]
else:
    df_au = df_au

df_tmm = pd.read_csv("data_temperatura/tmm_historico_2024.csv")
df_tmm['date'] = pd.to_datetime(df_tmm['date'])

if len(rango_fechas) == 2:
    fecha_inicio_seleccionada, fecha_fin_seleccionada = rango_fechas
    df_tmm = df_tmm[(df_tmm['date'] >= pd.Timestamp(fecha_inicio_seleccionada)) &
                     (df_tmm['date'] <= pd.Timestamp(fecha_fin_seleccionada))]
else:
    df_tmm = df_tmm
#%%
diccionario_causas_au={
    1   :'Atenciones de urgencia - Total',
    12   :'Atenciones de urgencia - Total Sistema Circulatorio',
    13  :'Atenciones de urgencia - Infarto agudo miocardio',
    14  :'Atenciones de urgencia - Accidente vascular encefálico',
    15   :'Atenciones de urgencia - Crisis hipertensiva',
    16   :'Atenciones de urgencia - Arritmia grave',
    17   :'Atenciones de urgencia - Otras causas circulatorias',
    25  :'Hospitalizaciones - Total',
    22   :'Hospitalizaciones - CAUSAS SISTEMA CIRCULATORIO',
}

#%%

def grafico_area_atenciones_respiratorias(df_au, df_temp, col, title):
    # Filtrar y agrupar los datos según las causas indicadas
    df_tota_sc = df_au[df_au['Causa'] == diccionario_causas_au[12]].groupby('fecha')[col].sum().reset_index()
    df_infarto = df_au[df_au['Causa'] == diccionario_causas_au[13]].groupby('fecha')[col].sum().reset_index()
    df_accidente = df_au[df_au['Causa'] == diccionario_causas_au[14]].groupby('fecha')[col].sum().reset_index()
    df_crisis = df_au[df_au['Causa'] == diccionario_causas_au[15]].groupby('fecha')[col].sum().reset_index()
    df_arritmia = df_au[df_au['Causa'] == diccionario_causas_au[16]].groupby('fecha')[col].sum().reset_index()
    df_otras = df_au[df_au['Causa'] == diccionario_causas_au[17]].groupby('fecha')[col].sum().reset_index()

    # Configurar las alertas de temperatura
    df_temp['alerta'] = 'Sin Alerta'
    df_temp['mes'] = df_temp['date'].dt.month
    df_temp.loc[df_temp['mes'].isin([11, 12, 1, 2, 3]), 'alerta'] = 'Alerta temprana preventiva'
    df_temp.loc[df_temp['t_max'] >= 40, 'alerta'] = 'Alerta Roja'
    df_temp['alerta_temporal'] = df_temp['t_max'] >= 34
    df_temp['alerta_consecutiva'] = df_temp['alerta_temporal'].rolling(window=2).sum()
    df_temp.loc[df_temp['alerta_consecutiva'] >= 2, 'alerta'] = 'Alerta Amarilla'
    df_temp['alerta_consecutiva_3'] = df_temp['alerta_temporal'].rolling(window=3).sum()
    df_temp.loc[df_temp['alerta_consecutiva_3'] >= 3, 'alerta'] = 'Alerta Roja'

    # Crear la figura del gráfico
    fig = go.Figure()

    # Agregar las trazas de atenciones de urgencia (eje Y1)
    fig.add_trace(go.Scatter(
        x=df_tota_sc['fecha'], y=df_tota_sc[col],
        mode='lines', name='Atenciones de urgencia - Total Sistema Circulatorio'
    ))
    fig.add_trace(go.Scatter(
        x=df_infarto['fecha'], y=df_infarto[col],
        mode='lines', name='Atenciones de urgencia - Infarto agudo miocardio'
    ))
    fig.add_trace(go.Scatter(
        x=df_accidente['fecha'], y=df_accidente[col],
        mode='lines', name='Atenciones de urgencia - Accidente vascular encefálico'
    ))
    fig.add_trace(go.Scatter(
        x=df_crisis['fecha'], y=df_crisis[col],
        mode='lines', name='Atenciones de urgencia - Crisis hipertensiva'
    ))
    fig.add_trace(go.Scatter(
        x=df_arritmia['fecha'], y=df_arritmia[col],
        mode='lines', name='Atenciones de urgencia - Arritmia grave'
    ))
    fig.add_trace(go.Scatter(
        x=df_otras['fecha'], y=df_otras[col],
        mode='lines', name='Atenciones de urgencia - Otras causas circulatorias'
    ))

    # Agregar las trazas de temperatura máxima (eje Y2)
    fig.add_trace(go.Scatter(
        x=df_temp['date'], y=df_temp['t_max'],
        mode='lines',
        name='Temperatura Máxima',
        line=dict(color='red'),
        yaxis='y2'  # Especificar el eje secundario
    ))

    # Agregar los marcadores de alertas (eje Y2)
    color_map = {
        'Sin Alerta': 'blue',
        'Alerta temprana preventiva': 'green',
        'Alerta Amarilla': 'yellow',
        'Alerta Roja': 'red'
    }
    for alerta, color in color_map.items():
        df_alerta = df_temp[df_temp['alerta'] == alerta]
        fig.add_trace(go.Scatter(
            x=df_alerta['date'],
            y=df_alerta['t_max'],
            mode='markers',
            name=f'Alerta: {alerta}',
            marker=dict(color=color),
            yaxis='y2'  # Eje secundario
        ))

    # Configurar el diseño del gráfico
    fig.update_layout(
        title=title,
        xaxis_title='Fecha',
        yaxis=dict(
            title=col,                # Título del eje principal
        ),
        yaxis2=dict(
            title='Temperatura Máxima',  # Título del eje secundario
            overlaying='y',             # Superponer al eje principal
            side='right'                # Mostrar en el lado derecho
        ),
        template='plotly_white',
        legend=dict(
            orientation="h",           # Leyenda horizontal
            yanchor="top",             # Alinear parte superior
            y=-0.2,                    # Posicionar debajo del gráfico
            xanchor="auto",          # Centrar horizontalmente
            x=0.5                      # Ubicación horizontal central
        )
    )

    return fig
def grafico_atenciones_urgencia_pie(df, df_temp, col, title):
    diccionario_causas_au = {
        1: 'Atenciones de urgencia - Total',
        12: 'Atenciones de urgencia - Total Sistema Circulatorio',
        13: 'Atenciones de urgencia - Infarto agudo miocardio',
        14: 'Atenciones de urgencia - Accidente vascular encefálico',
        15: 'Atenciones de urgencia - Crisis hipertensiva',
        16: 'Atenciones de urgencia - Arritmia grave',
        17: 'Atenciones de urgencia - Otras causas circulatorias'
    }

    data = []
    labels = []
    for key, value in diccionario_causas_au.items():
        suma = df[df['Causa'] == value][col].sum()
        data.append(suma)
        labels.append(value)

    fig = go.Figure(data=[go.Pie(labels=labels, values=data, hole=0.3)])

    # Configurar alertas de temperatura
    df_temp['alerta'] = 'Sin Alerta'
    df_temp['mes'] = df_temp['date'].dt.month
    df_temp.loc[df_temp['mes'].isin([11, 12, 1, 2, 3]), 'alerta'] = 'Alerta temprana preventiva'
    df_temp.loc[df_temp['t_max'] >= 40, 'alerta'] = 'Alerta Roja'
    df_temp['alerta_temporal'] = df_temp['t_max'] >= 34
    df_temp['alerta_consecutiva'] = df_temp['alerta_temporal'].rolling(window=2).sum()
    df_temp.loc[df_temp['alerta_consecutiva'] >= 2, 'alerta'] = 'Alerta Amarilla'
    df_temp['alerta_consecutiva_3'] = df_temp['alerta_temporal'].rolling(window=3).sum()
    df_temp.loc[df_temp['alerta_consecutiva_3'] >= 3, 'alerta'] = 'Alerta Roja'

    # Configuración del diseño
    fig.update_layout(
        title=title,
        template='plotly_white'
    )

    return fig
def grafico_porcentaje_atenciones(df, df_temp, col, title):
    diccionario_causas_au = {
        1: 'Atenciones de urgencia - Total',
        12: 'Atenciones de urgencia - Total Sistema Circulatorio',
        13: 'Atenciones de urgencia - Infarto agudo miocardio',
        14: 'Atenciones de urgencia - Accidente vascular encefálico',
        15: 'Atenciones de urgencia - Crisis hipertensiva',
        16: 'Atenciones de urgencia - Arritmia grave',
        17: 'Atenciones de urgencia - Otras causas circulatorias'
    }

    # Filtrar los datos por causa y fecha
    df_total_sc = df[df['Causa'] == diccionario_causas_au[12]].groupby('fecha')[col].sum().reset_index()
    df_infarto = df[df['Causa'] == diccionario_causas_au[13]].groupby('fecha')[col].sum().reset_index()
    df_accidente = df[df['Causa'] == diccionario_causas_au[14]].groupby('fecha')[col].sum().reset_index()
    df_crisis = df[df['Causa'] == diccionario_causas_au[15]].groupby('fecha')[col].sum().reset_index()
    df_arritmia = df[df['Causa'] == diccionario_causas_au[16]].groupby('fecha')[col].sum().reset_index()
    df_otras = df[df['Causa'] == diccionario_causas_au[17]].groupby('fecha')[col].sum().reset_index()

    # Calcular los porcentajes por día
    porcentajes = pd.DataFrame()
    porcentajes['fecha'] = df_total_sc['fecha']
    porcentajes['Infarto agudo miocardio (%)'] = (df_infarto[col] / df_total_sc[col]) * 100
    porcentajes['Accidente vascular encefálico (%)'] = (df_accidente[col] / df_total_sc[col]) * 100
    porcentajes['Crisis hipertensiva (%)'] = (df_crisis[col] / df_total_sc[col]) * 100
    porcentajes['Arritmia grave (%)'] = (df_arritmia[col] / df_total_sc[col]) * 100
    porcentajes['Otras causas circulatorias (%)'] = (df_otras[col] / df_total_sc[col]) * 100

    # Crear la figura del gráfico
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=porcentajes['fecha'], y=porcentajes['Infarto agudo miocardio (%)'],
        mode='lines', name='Infarto agudo miocardio (%)'
    ))
    fig.add_trace(go.Scatter(
        x=porcentajes['fecha'], y=porcentajes['Accidente vascular encefálico (%)'],
        mode='lines', name='Accidente vascular encefálico (%)'
    ))
    fig.add_trace(go.Scatter(
        x=porcentajes['fecha'], y=porcentajes['Crisis hipertensiva (%)'],
        mode='lines', name='Crisis hipertensiva (%)'
    ))
    fig.add_trace(go.Scatter(
        x=porcentajes['fecha'], y=porcentajes['Arritmia grave (%)'],
        mode='lines', name='Arritmia grave (%)'
    ))
    fig.add_trace(go.Scatter(
        x=porcentajes['fecha'], y=porcentajes['Otras causas circulatorias (%)'],
        mode='lines', name='Otras causas circulatorias (%)'
    ))

    # Configurar alertas de temperatura
    df_temp['alerta'] = 'Sin Alerta'
    df_temp['mes'] = df_temp['date'].dt.month
    df_temp.loc[df_temp['mes'].isin([11, 12, 1, 2, 3]), 'alerta'] = 'Alerta temprana preventiva'
    df_temp.loc[df_temp['t_max'] >= 40, 'alerta'] = 'Alerta Roja'
    df_temp['alerta_temporal'] = df_temp['t_max'] >= 34
    df_temp['alerta_consecutiva'] = df_temp['alerta_temporal'].rolling(window=2).sum()
    df_temp.loc[df_temp['alerta_consecutiva'] >= 2, 'alerta'] = 'Alerta Amarilla'
    df_temp['alerta_consecutiva_3'] = df_temp['alerta_temporal'].rolling(window=3).sum()
    df_temp.loc[df_temp['alerta_consecutiva_3'] >= 3, 'alerta'] = 'Alerta Roja'

    # Agregar las trazas de temperatura máxima (eje Y2)
    fig.add_trace(go.Scatter(
        x=df_temp['date'], y=df_temp['t_max'],
        mode='lines',
        name='Temperatura Máxima',
        line=dict(color='red'),
        yaxis='y2'
    ))

    # Agregar los marcadores de alertas (eje Y2)
    color_map = {
        'Sin Alerta': 'blue',
        'Alerta temprana preventiva': 'green',
        'Alerta Amarilla': 'yellow',
        'Alerta Roja': 'red'
    }

    for alerta, color in color_map.items():
        df_alerta = df_temp[df_temp['alerta'] == alerta]
        fig.add_trace(go.Scatter(
            x=df_alerta['date'],
            y=df_alerta['t_max'],
            mode='markers',
            name=f'Alerta: {alerta}',
            marker=dict(color=color),
            yaxis='y2'
        ))

    # Configurar el diseño del gráfico
    fig.update_layout(
        title=title,
        xaxis_title='Fecha',
        yaxis=dict(
            title=col
        ),
        yaxis2=dict(
            title='Temperatura Máxima',
            overlaying='y',
            side='right'
        ),
        template='plotly_white',
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.2,
            xanchor="center",
            x=0.5
        )
    )

    return fig

def grafico_total_grupo_etario(df, title):
    df_filtrado = df[df['Causa'] == diccionario_causas_au[12]]

    # Agrupar los datos por fecha para cada grupo etario
    df_total = df_filtrado.groupby('fecha')['Total'].sum().reset_index()
    df_menores_1 = df_filtrado.groupby('fecha')['Menores_1'].sum().reset_index()
    df_1_a_4 = df_filtrado.groupby('fecha')['De_1_a_4'].sum().reset_index()
    df_5_a_14 = df_filtrado.groupby('fecha')['De_5_a_14'].sum().reset_index()
    df_15_a_64 = df_filtrado.groupby('fecha')['De_15_a_64'].sum().reset_index()
    df_65_y_mas = df_filtrado.groupby('fecha')['De_65_y_mas'].sum().reset_index()

    # Crear la figura del gráfico
    fig = go.Figure()

    # Agregar la línea para el total
    fig.add_trace(go.Scatter(
        x=df_total['fecha'], y=df_total['Total'],
        mode='lines', name='Total',
        line=dict(color='blue')
    ))

    # Agregar las barras para cada grupo etario
    fig.add_trace(go.Bar(
        x=df_menores_1['fecha'], y=df_menores_1['Menores_1'],
        name='Menores_1',
        marker=dict(color='cyan')
    ))

    fig.add_trace(go.Bar(
        x=df_1_a_4['fecha'], y=df_1_a_4['De_1_a_4'],
        name='De_1_a_4',
        marker=dict(color='magenta')
    ))

    fig.add_trace(go.Bar(
        x=df_5_a_14['fecha'], y=df_5_a_14['De_5_a_14'],
        name='De_5_a_14',
        marker=dict(color='orange')
    ))

    fig.add_trace(go.Bar(
        x=df_15_a_64['fecha'], y=df_15_a_64['De_15_a_64'],
        name='De_15_a_64',
        marker=dict(color='yellow')
    ))

    fig.add_trace(go.Bar(
        x=df_65_y_mas['fecha'], y=df_65_y_mas['De_65_y_mas'],
        name='De_65_y_mas',
        marker=dict(color='green')
    ))

    # Configurar el diseño del gráfico
    fig.update_layout(
        title=title,
        xaxis_title='Fecha',
        yaxis_title='Cantidad de Consultas',
        barmode='stack',
        template='plotly_white',
        legend=dict(
            title='Grupos Etarios',
            orientation="h",  # Leyenda horizontal
            yanchor="top",    # Alinear la parte superior de la leyenda
            y=-0.2,           # Posicionar debajo del gráfico
            xanchor="center", # Centrar horizontalmente
            x=0.5             # Ubicación horizontal central
        )

    )


    
    return fig
def grafico_total_grupo_etario(df, df_temp, title):
    df_filtrado = df[df['Causa'] == diccionario_causas_au[12]]

    # Agrupar los datos por fecha para cada grupo etario
    df_total = df_filtrado.groupby('fecha')['Total'].sum().reset_index()
    df_menores_1 = df_filtrado.groupby('fecha')['Menores_1'].sum().reset_index()
    df_1_a_4 = df_filtrado.groupby('fecha')['De_1_a_4'].sum().reset_index()
    df_5_a_14 = df_filtrado.groupby('fecha')['De_5_a_14'].sum().reset_index()
    df_15_a_64 = df_filtrado.groupby('fecha')['De_15_a_64'].sum().reset_index()
    df_65_y_mas = df_filtrado.groupby('fecha')['De_65_y_mas'].sum().reset_index()

    # Crear la figura del gráfico
    fig = go.Figure()

    # Agregar la línea para el total
    fig.add_trace(go.Scatter(
        x=df_total['fecha'], y=df_total['Total'],
        mode='lines', name='Total',
        line=dict(color='blue')
    ))

    # Agregar las barras para cada grupo etario
    fig.add_trace(go.Bar(
        x=df_menores_1['fecha'], y=df_menores_1['Menores_1'],
        name='Menores_1',
        marker=dict(color='cyan')
    ))

    fig.add_trace(go.Bar(
        x=df_1_a_4['fecha'], y=df_1_a_4['De_1_a_4'],
        name='De_1_a_4',
        marker=dict(color='magenta')
    ))

    fig.add_trace(go.Bar(
        x=df_5_a_14['fecha'], y=df_5_a_14['De_5_a_14'],
        name='De_5_a_14',
        marker=dict(color='orange')
    ))

    fig.add_trace(go.Bar(
        x=df_15_a_64['fecha'], y=df_15_a_64['De_15_a_64'],
        name='De_15_a_64',
        marker=dict(color='yellow')
    ))

    fig.add_trace(go.Bar(
        x=df_65_y_mas['fecha'], y=df_65_y_mas['De_65_y_mas'],
        name='De_65_y_mas',
        marker=dict(color='green')
    ))

    # Configurar alertas de temperatura
    df_temp['alerta'] = 'Sin Alerta'
    df_temp['mes'] = df_temp['date'].dt.month
    df_temp.loc[df_temp['mes'].isin([11, 12, 1, 2, 3]), 'alerta'] = 'Alerta temprana preventiva'
    df_temp.loc[df_temp['t_max'] >= 40, 'alerta'] = 'Alerta Roja'
    df_temp['alerta_temporal'] = df_temp['t_max'] >= 34
    df_temp['alerta_consecutiva'] = df_temp['alerta_temporal'].rolling(window=2).sum()
    df_temp.loc[df_temp['alerta_consecutiva'] >= 2, 'alerta'] = 'Alerta Amarilla'
    df_temp['alerta_consecutiva_3'] = df_temp['alerta_temporal'].rolling(window=3).sum()
    df_temp.loc[df_temp['alerta_consecutiva_3'] >= 3, 'alerta'] = 'Alerta Roja'

    # Agregar las trazas de temperatura máxima (eje Y2)
    fig.add_trace(go.Scatter(
        x=df_temp['date'], y=df_temp['t_max'],
        mode='lines',
        name='Temperatura Máxima',
        line=dict(color='red'),
        yaxis='y2'
    ))

    # Agregar los marcadores de alertas (eje Y2)
    color_map = {
        'Sin Alerta': 'blue',
        'Alerta temprana preventiva': 'green',
        'Alerta Amarilla': 'yellow',
        'Alerta Roja': 'red'
    }

    for alerta, color in color_map.items():
        df_alerta = df_temp[df_temp['alerta'] == alerta]
        fig.add_trace(go.Scatter(
            x=df_alerta['date'],
            y=df_alerta['t_max'],
            mode='markers',
            name=f'Alerta: {alerta}',
            marker=dict(color=color),
            yaxis='y2'
        ))

    # Configurar el diseño del gráfico
    fig.update_layout(
        title=title,
        xaxis_title='Fecha',
        yaxis_title='Cantidad de Consultas',
        barmode='stack',
        template='plotly_white',
        yaxis2=dict(
            title='Temperatura Máxima',
            overlaying='y',
            side='right'
        ),
        legend=dict(
            title='Grupos Etarios',
            orientation="h",  # Leyenda horizontal
            yanchor="top",    # Alinear la parte superior de la leyenda
            y=-0.2,           # Posicionar debajo del gráfico
            xanchor="center", # Centrar horizontalmente
            x=0.5             # Ubicación horizontal central
        )

    )

    return fig

def grafico_grupos_interes_epidemiologico(df, title):
    # Filtrar el DataFrame para 'Atenciones de urgencia - Total Sistema Circulatorio'
    df_filtrado = df[df['Causa'] == diccionario_causas_au[12]]

    # Agrupar los datos por fecha para cada grupo de interés epidemiológico
    df_menores_1 = df_filtrado.groupby('fecha')['Menores_1'].sum().reset_index()
    df_1_a_4 = df_filtrado.groupby('fecha')['De_1_a_4'].sum().reset_index()
    df_65_y_mas = df_filtrado.groupby('fecha')['De_65_y_mas'].sum().reset_index()

    # Crear la figura del gráfico
    fig = go.Figure()



    # Agregar las barras para cada grupo de interés epidemiológico
    fig.add_trace(go.Bar(
        x=df_menores_1['fecha'], y=df_menores_1['Menores_1'],
        name='Menores_1',
        marker=dict(color='cyan')
    ))

    fig.add_trace(go.Bar(
        x=df_65_y_mas['fecha'], y=df_65_y_mas['De_65_y_mas'],
        name='De_65_y_mas',
        marker=dict(color='green')
    ))

    # Configurar el diseño del gráfico
    fig.update_layout(
        title=title,
        xaxis_title='Fecha',
        yaxis_title='Cantidad de Consultas',
        barmode='stack',
        template='plotly_white',
        legend=dict(
            title='Grupos Etario de interes',
            orientation="h",  # Leyenda horizontal
            yanchor="top",    # Alinear la parte superior de la leyenda
            y=-0.2,           # Posicionar debajo del gráfico
            xanchor="center", # Centrar horizontalmente
            x=0.5             # Ubicación horizontal central
        )
        
    )

    return fig
def grafico_grupos_interes_epidemiologico(df, df_temp, title):
    # Filtrar el DataFrame para 'Atenciones de urgencia - Total Sistema Circulatorio'
    df_filtrado = df[df['Causa'] == diccionario_causas_au[12]]

    # Agrupar los datos por fecha para cada grupo de interés epidemiológico
    df_menores_1 = df_filtrado.groupby('fecha')['Menores_1'].sum().reset_index()
    df_65_y_mas = df_filtrado.groupby('fecha')['De_65_y_mas'].sum().reset_index()

    # Crear la figura del gráfico
    fig = go.Figure()

    # Agregar las barras para cada grupo de interés epidemiológico
    fig.add_trace(go.Bar(
        x=df_menores_1['fecha'], y=df_menores_1['Menores_1'],
        name='Menores_1',
        marker=dict(color='cyan')
    ))

    fig.add_trace(go.Bar(
        x=df_65_y_mas['fecha'], y=df_65_y_mas['De_65_y_mas'],
        name='De_65_y_mas',
        marker=dict(color='green')
    ))

    # Configurar alertas de temperatura
    df_temp['alerta'] = 'Sin Alerta'
    df_temp['mes'] = df_temp['date'].dt.month
    df_temp.loc[df_temp['mes'].isin([11, 12, 1, 2, 3]), 'alerta'] = 'Alerta temprana preventiva'
    df_temp.loc[df_temp['t_max'] >= 40, 'alerta'] = 'Alerta Roja'
    df_temp['alerta_temporal'] = df_temp['t_max'] >= 34
    df_temp['alerta_consecutiva'] = df_temp['alerta_temporal'].rolling(window=2).sum()
    df_temp.loc[df_temp['alerta_consecutiva'] >= 2, 'alerta'] = 'Alerta Amarilla'
    df_temp['alerta_consecutiva_3'] = df_temp['alerta_temporal'].rolling(window=3).sum()
    df_temp.loc[df_temp['alerta_consecutiva_3'] >= 3, 'alerta'] = 'Alerta Roja'

    # Agregar las trazas de temperatura máxima (eje Y2)
    fig.add_trace(go.Scatter(
        x=df_temp['date'], y=df_temp['t_max'],
        mode='lines',
        name='Temperatura Máxima',
        line=dict(color='red'),
        yaxis='y2'
    ))

    # Agregar los marcadores de alertas (eje Y2)
    color_map = {
        'Sin Alerta': 'blue',
        'Alerta temprana preventiva': 'green',
        'Alerta Amarilla': 'yellow',
        'Alerta Roja': 'red'
    }

    for alerta, color in color_map.items():
        df_alerta = df_temp[df_temp['alerta'] == alerta]
        fig.add_trace(go.Scatter(
            x=df_alerta['date'],
            y=df_alerta['t_max'],
            mode='markers',
            name=f'Alerta: {alerta}',
            marker=dict(color=color),
            yaxis='y2'
        ))

    # Configurar el diseño del gráfico
    fig.update_layout(
        title=title,
        xaxis_title='Fecha',
        yaxis_title='Cantidad de Consultas',
        barmode='stack',
        template='plotly_white',
        yaxis2=dict(
            title='Temperatura Máxima',
            overlaying='y',
            side='right'
        ),
        legend=dict(
            title='Grupos Etario de interés',
            orientation="h",  # Leyenda horizontal
            yanchor="top",    # Alinear la parte superior de la leyenda
            y=-0.2,           # Posicionar debajo del gráfico
            xanchor="center", # Centrar horizontalmente
            x=0.5             # Ubicación horizontal central
        )
    )

    return fig

def grafico_porcentaje_total(df, df_temp, col, title):
    # Filtrar datos por causas específicas y calcular el total general de atenciones de urgencia
    df_total_urgencias = df[df['Causa'] == 'Atenciones de urgencia - Total'].groupby('fecha')[col].sum().reset_index()
    df_total_sc = df[df['Causa'] == 'Atenciones de urgencia - Total Sistema Circulatorio'].groupby('fecha')[col].sum().reset_index()
    df_infarto = df[df['Causa'] == 'Atenciones de urgencia - Infarto agudo miocardio'].groupby('fecha')[col].sum().reset_index()
    df_accidente = df[df['Causa'] == 'Atenciones de urgencia - Accidente vascular encefálico'].groupby('fecha')[col].sum().reset_index()
    df_crisis = df[df['Causa'] == 'Atenciones de urgencia - Crisis hipertensiva'].groupby('fecha')[col].sum().reset_index()
    df_arritmia = df[df['Causa'] == 'Atenciones de urgencia - Arritmia grave'].groupby('fecha')[col].sum().reset_index()
    df_otras = df[df['Causa'] == 'Atenciones de urgencia - Otras causas circulatorias'].groupby('fecha')[col].sum().reset_index()

    # Calcular los porcentajes por día
    porcentajes = pd.DataFrame()
    porcentajes['fecha'] = df_total_urgencias['fecha']
    porcentajes['Sistema Circulatorio (%)'] = (df_total_sc[col] / df_total_urgencias[col]) * 100
    porcentajes['Infarto agudo miocardio (%)'] = (df_infarto[col] / df_total_urgencias[col]) * 100
    porcentajes['Accidente vascular encefálico (%)'] = (df_accidente[col] / df_total_urgencias[col]) * 100
    porcentajes['Crisis hipertensiva (%)'] = (df_crisis[col] / df_total_urgencias[col]) * 100
    porcentajes['Arritmia grave (%)'] = (df_arritmia[col] / df_total_urgencias[col]) * 100
    porcentajes['Otras causas circulatorias (%)'] = (df_otras[col] / df_total_urgencias[col]) * 100

    # Crear la figura del gráfico
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=porcentajes['fecha'], y=porcentajes['Sistema Circulatorio (%)'],
        mode='lines', name='Sistema Circulatorio (%)'
    ))
    fig.add_trace(go.Scatter(
        x=porcentajes['fecha'], y=porcentajes['Infarto agudo miocardio (%)'],
        mode='lines', name='Infarto agudo miocardio (%)'
    ))
    fig.add_trace(go.Scatter(
        x=porcentajes['fecha'], y=porcentajes['Accidente vascular encefálico (%)'],
        mode='lines', name='Accidente vascular encefálico (%)'
    ))
    fig.add_trace(go.Scatter(
        x=porcentajes['fecha'], y=porcentajes['Crisis hipertensiva (%)'],
        mode='lines', name='Crisis hipertensiva (%)'
    ))
    fig.add_trace(go.Scatter(
        x=porcentajes['fecha'], y=porcentajes['Arritmia grave (%)'],
        mode='lines', name='Arritmia grave (%)'
    ))
    fig.add_trace(go.Scatter(
        x=porcentajes['fecha'], y=porcentajes['Otras causas circulatorias (%)'],
        mode='lines', name='Otras causas circulatorias (%)'
    ))

    # Configurar alertas de temperatura
    df_temp['alerta'] = 'Sin Alerta'
    df_temp['mes'] = df_temp['date'].dt.month
    df_temp.loc[df_temp['mes'].isin([11, 12, 1, 2, 3]), 'alerta'] = 'Alerta temprana preventiva'
    df_temp.loc[df_temp['t_max'] >= 40, 'alerta'] = 'Alerta Roja'
    df_temp['alerta_temporal'] = df_temp['t_max'] >= 34
    df_temp['alerta_consecutiva'] = df_temp['alerta_temporal'].rolling(window=2).sum()
    df_temp.loc[df_temp['alerta_consecutiva'] >= 2, 'alerta'] = 'Alerta Amarilla'
    df_temp['alerta_consecutiva_3'] = df_temp['alerta_temporal'].rolling(window=3).sum()
    df_temp.loc[df_temp['alerta_consecutiva_3'] >= 3, 'alerta'] = 'Alerta Roja'

    # Agregar las trazas de temperatura máxima (eje Y2)
    fig.add_trace(go.Scatter(
        x=df_temp['date'], y=df_temp['t_max'],
        mode='lines',
        name='Temperatura Máxima',
        line=dict(color='red'),
        yaxis='y2'
    ))

    # Agregar los marcadores de alertas (eje Y2)
    color_map = {
        'Sin Alerta': 'blue',
        'Alerta temprana preventiva': 'green',
        'Alerta Amarilla': 'yellow',
        'Alerta Roja': 'red'
    }

    for alerta, color in color_map.items():
        df_alerta = df_temp[df_temp['alerta'] == alerta]
        fig.add_trace(go.Scatter(
            x=df_alerta['date'],
            y=df_alerta['t_max'],
            mode='markers',
            name=f'Alerta: {alerta}',
            marker=dict(color=color),
            yaxis='y2'
        ))

    # Configurar el diseño del gráfico
    fig.update_layout(
        title=title,
        xaxis_title='Fecha',
        yaxis=dict(
            title='Porcentaje (%)'
        ),
        yaxis2=dict(
            title='Temperatura Máxima',
            overlaying='y',
            side='right'
        ),
        template='plotly_white',
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.2,
            xanchor="center",
            x=0.5
        )
    )

    return fig

#%%
# Llamar a la función con el DataFrame y columna correspondiente
fig_area_atenciones_respiratorias = grafico_area_atenciones_respiratorias(
    df_au, df_tmm, 'Total', 'Evolución de Atenciones de Urgencia en el Sistema Circulatorio'
)

fig_porcentaje_atenciones = grafico_porcentaje_atenciones(
    df_au,df_tmm ,'Total', 'Porcentaje de Atenciones de Urgencia por Causa en el Sistema Circulatorio'
)

fig_porcentaje_atenciones_total = grafico_porcentaje_total(
    df_au,df_tmm, 'Total', 'Porcentaje de Atenciones de Urgencia por Causa en Relación al Total General'
)

fig_total_grupo_etario = grafico_total_grupo_etario(
    df_au,df_tmm, 'Consultas de Urgencia por Grupos Etarios del Sistema Circulatorio'
)

fig_grupos_interes_epidemiologico = grafico_grupos_interes_epidemiologico(
    df_au,df_tmm, 'Consultas de Urgencia en Grupos de Interés Epidemiológico'
)
# Renderizar los gráficos en la aplicación
st.write("## Evolución de cantidad Atenciones de Urgencia por Sistema Circulatorio")
st.write("Este gráfico muestra la evolución temporal de las atenciones de urgencia relacionadas con diferentes causas del sistema circulatorio.")
st.plotly_chart(fig_area_atenciones_respiratorias)

st.write("## Porcentaje de Atenciones de Urgencia por Causas por Sistema Circulatorio")
st.write("Se presenta la proporción diaria de las distintas causas de urgencia dentro del total de atenciones del sistema circulatorio.")
st.plotly_chart(fig_porcentaje_atenciones, use_container_width=True)

st.write("## Porcentaje de Atenciones de Urgencia por Causa de Sistema Circulatorio en Relación al Total General de Atenciones de Urgencia")
st.write("Este gráfico muestra el porcentaje de atenciones de urgencia de causas circulatorias específicas respecto al total de consultas de urgencia.")
st.plotly_chart(fig_porcentaje_atenciones_total, use_container_width=True)

st.write("## Consultas de Urgencia por Grupos Etarios en el Sistema Circulatorio")
st.write("Representación de la distribución total de atenciones de urgencia del sistema circulatorio según grupos etarios.")
st.plotly_chart(fig_total_grupo_etario, use_container_width=True)

st.write("## Consultas de Urgencia en Grupos de Interés Epidemiológico")
st.write("Este gráfico ilustra la cantidad de consultas de urgencia de grupos clave: menores de 1 año, y adultos mayores de 65 años.")
st.plotly_chart(fig_grupos_interes_epidemiologico, use_container_width=True)
# %%
