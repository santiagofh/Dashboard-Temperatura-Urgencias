#%%
import streamlit as st
import pandas as pd
import plotly.express as px
import pydeck as pdk
import plotly.graph_objects as go
from io import BytesIO
import datetime

fecha_inicio = datetime.date(2024, 1, 1)  # Mínimo permitido
fecha_fin = datetime.date.today()  # Máximo permitido
fecha_inicio_default = datetime.date(2025, 1, 1)

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

def grafico_area_atenciones_respiratorias(df, col, title):
    # Filtrar y agrupar los datos según las causas indicadas
    # df_total = df[df['Causa'] == diccionario_causas_au[1]].groupby('fecha')[col].sum().reset_index()
    df_tota_sc = df[df['Causa'] == diccionario_causas_au[22]].groupby('fecha')[col].sum().reset_index()

    # Crear la figura del gráfico
    fig = go.Figure()

    # Añadir trazas para cada grupo de causas
    # fig.add_trace(go.Scatter(
    #     x=df_total['fecha'], y=df_total[col],
    #     mode='lines', name='Atenciones de urgencia - Total'
    # ))
    fig.add_trace(go.Scatter(
        x=df_tota_sc['fecha'], y=df_tota_sc[col],
        mode='lines', name='Hospitalizaciones - Total Sistema Circulatorio'
    ))

    # Configurar el diseño del gráfico
    fig.update_layout(
        title=title,
        xaxis_title='Fecha',
        yaxis_title=col,
        template='plotly_white',
        legend=dict(
            orientation="h",  # Leyenda horizontal
            yanchor="top",    # Alinear la parte superior de la leyenda
            y=-0.2,           # Posicionar debajo del gráfico
            xanchor="center", # Centrar horizontalmente
            x=0.5             # Ubicación horizontal central
        )
    )
    return fig
def grafico_atenciones_urgencia_pie(df, col, title):
    data = []
    labels = []
    for key, value in diccionario_causas_au.items():
        suma = df[df['Causa'] == value][col].sum()
        data.append(suma)
        labels.append(value)
    fig = go.Figure(data=[go.Pie(labels=labels, values=data, hole=0.3)])
    fig.update_layout(
        title=title,
        template='plotly_white'
    )
def grafico_porcentaje_atenciones(df, col, title):

    # Filtrar los datos por causa y fecha
    df_total_sc = df[df['Causa'] == diccionario_causas_au[12]].groupby('fecha')[col].sum().reset_index()
    df_infarto = df[df['Causa'] == diccionario_causas_au[13]].groupby('fecha')[col].sum().reset_index()

    # Calcular los porcentajes por día
    porcentajes = pd.DataFrame()
    porcentajes['fecha'] = df_total_sc['fecha']
    porcentajes['Infarto agudo miocardio (%)'] = (df_infarto[col] / df_total_sc[col]) * 100

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

    # Configurar el diseño del gráfico
    fig.update_layout(
        title=title,
        xaxis_title='fecha',
        yaxis_title='Porcentaje (%)',
        template='plotly_white',
        legend=dict(
            orientation="h",  # Leyenda horizontal
            yanchor="top",    # Alinear la parte superior de la leyenda
            y=-0.2,           # Posicionar debajo del gráfico
            xanchor="center", # Centrar horizontalmente
            x=0.5             # Ubicación horizontal central
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
        x=df_1_a_4['fecha'], y=df_1_a_4['De_1_a_4'],
        name='De_1_a_4',
        marker=dict(color='magenta')
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
def grafico_porcentaje_total(df, col, title):
    # Filtrar datos por causas específicas y calcular el total general de atenciones de urgencia
    df_total_urgencias = df[df['Causa'] == 'Atenciones de urgencia - Total'].groupby('fecha')[col].sum().reset_index()
    df_total_sc = df[df['Causa'] == 'Atenciones de urgencia - Total Sistema Circulatorio'].groupby('fecha')[col].sum().reset_index()

    # Calcular los porcentajes por día
    porcentajes = pd.DataFrame()
    porcentajes['fecha'] = df_total_urgencias['fecha']
    porcentajes['Sistema Circulatorio (%)'] = (df_total_sc[col] / df_total_urgencias[col]) * 100

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
    # Configurar el diseño del gráfico
    fig.update_layout(
        title=title,
        xaxis_title='Fecha',
        yaxis_title='Porcentaje (%)',
        template='plotly_white',
        legend=dict(
            orientation="h",  # Leyenda horizontal
            yanchor="top",    # Alinear la parte superior de la leyenda
            y=-0.2,           # Posicionar debajo del gráfico
            xanchor="center", # Centrar horizontalmente
            x=0.5             # Ubicación horizontal central
        )
    )
    return fig
#%%
# Llamar a la función con el DataFrame y columna correspondiente
fig_area_atenciones_respiratorias=(grafico_area_atenciones_respiratorias(df_au,'Total','Total sistema circulatorio'))
fig_porcentaje_atenciones=(grafico_porcentaje_atenciones(df_au, 'Total', 'Porcentaje en relación a Total Sistema Circulatorio'))
fig_porcentaje_atenciones_total=(grafico_porcentaje_total(df_au, 'Total', 'Porcentaje en relación a Total de atenciones'))
fig_total_grupo_etario=(grafico_total_grupo_etario(df_au, 'Total Consultas de Urgencia por Grupo Etario'))
fig_grupos_interes_epidemiologico=(grafico_grupos_interes_epidemiologico(df_au, 'Consultas de Urgencia por Grupos de Interés Epidemiológico'))

st.plotly_chart(fig_area_atenciones_respiratorias, use_container_width=True)
st.plotly_chart(fig_porcentaje_atenciones, use_container_width=True)
st.plotly_chart(fig_porcentaje_atenciones_total, use_container_width=True)
st.plotly_chart(fig_total_grupo_etario, use_container_width=True)
st.plotly_chart(fig_grupos_interes_epidemiologico, use_container_width=True)