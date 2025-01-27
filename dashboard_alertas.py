#%%
import streamlit as st
import pandas as pd
import plotly.express as px
import pydeck as pdk
import datetime
# Definir el rango inicial y final de fechas
fecha_inicio = datetime.date(2024, 1, 1)
fecha_fin = datetime.date.today()
fecha_inicio_default = datetime.date(2024, 11, 1)

st.sidebar.write("### Seleccione el rango de fechas")
rango_fechas = st.sidebar.date_input(
    "Rango de Fechas:",
    [fecha_inicio_default, fecha_fin],  # Fechas predeterminadas
    min_value=fecha_inicio,
    max_value=fecha_fin
)
#%% Cargar los datos
df = pd.read_csv("data_temperatura/tmm_historico_2024.csv")
df['date'] = pd.to_datetime(df['date'])

if len(rango_fechas) == 2:
    fecha_inicio_seleccionada, fecha_fin_seleccionada = rango_fechas
    df = df[(df['date'] >= pd.Timestamp(fecha_inicio_seleccionada)) &
                     (df['date'] <= pd.Timestamp(fecha_fin_seleccionada))]
else:
    df = df
#%%
# Funciones
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

#%%
# SENAPRED

def grafico_alertas_senapred(df):
    # Crear la figura base con líneas conectando los puntos
    fig = px.line(
        df, 
        x='date', 
        y='t_max', 
        title='Temperaturas Máximas para Región Metropolitana',
        markers=True
    )

    # Agregar líneas de referencia
    fig.add_hline(y=34, line_dash="dot", line_color="yellow", annotation_text="34°C", annotation_position="bottom right")
    fig.add_hline(y=40, line_dash="dot", line_color="red", annotation_text="40°C", annotation_position="bottom right")
    fig.add_hline(y=30, line_dash="dot", line_color="green", annotation_text="30°C", annotation_position="bottom right")

    # Agregar puntos para días que superan las líneas de referencia
    df_green = df[(df['t_max'] >= 30) & (df['t_max'] < 34)]
    df_yellow = df[(df['t_max'] >= 34) & (df['t_max'] < 40)]
    df_red = df[df['t_max'] >= 40]

    fig.add_scatter(
        x=df_green['date'], 
        y=df_green['t_max'], 
        mode='markers', 
        name='30°C <= t_max < 34°C', 
        marker=dict(color="green")
    )

    fig.add_scatter(
        x=df_yellow['date'], 
        y=df_yellow['t_max'], 
        mode='markers', 
        name='34°C <= t_max < 40°C', 
        marker=dict(color="yellow")
    )
    
    fig.add_scatter(
        x=df_red['date'], 
        y=df_red['t_max'], 
        mode='markers', 
        name='t_max >= 40°C', 
        marker=dict(color="red")
    )

    # Ajustar diseño
    fig.update_layout(
        xaxis_title="Fecha",
        yaxis_title="Temperatura Máxima (°C)",
        legend=dict(
            title="",
            orientation="h",  # Horizontal
            yanchor="top",    # Alinear la parte superior de la leyenda
            y=-0.2,           # Posicionar por debajo del gráfico
            xanchor="center", # Centrar horizontalmente
            x=0.5             # Ubicación central
        )
    )
    return fig

# SEREMI

def grafico_alertas_seremi(df):
    df['alerta'] = 'Sin Alerta' 
    df['mes'] = df['date'].dt.month
    df.loc[df['mes'].isin([11, 12, 1, 2, 3]), 'alerta'] = 'Alerta temprana preventiva'
    df.loc[df['t_max'] >= 40, 'alerta'] = 'Alerta Roja'
    df['alerta_temporal'] = df['t_max'] >= 34
    df['alerta_consecutiva'] = df['alerta_temporal'].rolling(window=2).sum()
    df.loc[df['alerta_consecutiva'] >= 2, 'alerta'] = 'Alerta Amarilla'
    df['alerta_consecutiva_3'] = df['alerta_temporal'].rolling(window=3).sum()
    df.loc[df['alerta_consecutiva_3'] >= 3, 'alerta'] = 'Alerta Roja'

    # Mapeo de colores para cada tipo de alerta
    color_map = {
        'Sin Alerta': 'blue',  # Azul para días sin alerta
        'Alerta temprana preventiva': 'green',  # Verde para Alerta Temprana Preventiva
        'Alerta Amarilla': 'yellow',  # Amarillo para Alerta Amarilla
        'Alerta Roja': 'red'  # Rojo para Alerta Roja
    }

    # Crear la figura
    fig = px.line(df, x='date', y='t_max', title=f'Temperaturas Máximas y Alertas para la Región Metropolitana', color_discrete_sequence=['grey'])

    # Agregar marcadores de colores
    for alerta, color in color_map.items():
        df_alerta = df[df['alerta'] == alerta]
        fig.add_scatter(
            x=df_alerta['date'],
            y=df_alerta['t_max'],
            mode='markers',
            name=alerta,
            marker=dict(color=color),
        )

    # Ajustar la posición de la leyenda para que esté debajo del gráfico
    fig.update_layout(
        legend=dict(
            orientation="h",  # Horizontal
            yanchor="top",    # Alinear la parte superior de la leyenda
            y=-0.2,           # Posicionar por debajo del gráfico
            xanchor="center", # Centrar horizontalmente
            x=0.5             # Ubicación central
        )
    )

    return fig

# SOBRE 35

def tabla_alertas_seremi(df):
    # Filtrar solo Alertas Amarillas y Rojas
    df_alertas = df[df['alerta'].isin(['Alerta Amarilla', 'Alerta Roja'])]

    # Ordenar por fecha
    df_alertas = df_alertas.sort_values(by='date')

    # Seleccionar las columnas relevantes, incluyendo la temperatura máxima
    eventos_alerta = df_alertas[['date', 'alerta', 't_max']].reset_index(drop=True)
    eventos_alerta.columns = ['Fecha', 'Tipo de Alerta', 'Temperatura Máxima']

    return eventos_alerta


def grafico_alertas_sobre35(df):
    df['sobre_35'] = 'Bajo 35' 
    df.loc[df['t_max'] >= 35, 'sobre_35'] = 'Sobre 35'

    color_map = {
        'Sobre 35': 'red',  # Azul para días sin alerta
        'Bajo 35': 'blue',  # Azul para días sin alerta
    }
    fig = px.line(df, x='date', y='t_max', title=f'Temperaturas Máximas y Alertas para la Región Metropolitana', color_discrete_sequence=['grey'])

    # Agregar marcadores de colores
    for alerta, color in color_map.items():
        df_alerta = df[df['sobre_35'] == alerta]
        fig.add_scatter(x=df_alerta['date'], y=df_alerta['t_max'], mode='markers', name=alerta, marker=dict(color=color),)
    fig.update_layout(
        legend=dict(
            orientation="h",  # Leyenda horizontal
            yanchor="top",    # Alinear la parte superior de la leyenda
            y=-0.2,           # Posicionar por debajo del gráfico
            xanchor="center", # Centrar horizontalmente
            x=0.5             # Ubicación horizontal central
        )
    )
    return fig

def tabla_alertas_sobre35(df):
    # Filtrar solo Alertas Amarillas y Rojas
    df_alertas = df[df['sobre_35'].isin(['Sobre 35'])]

    # Ordenar por fecha
    df_alertas = df_alertas.sort_values(by='date')

    # Seleccionar las columnas relevantes, incluyendo la temperatura máxima
    eventos_alerta = df_alertas[['date', 'sobre_35', 't_max']].reset_index(drop=True)
    eventos_alerta.columns = ['Fecha', 'Alerta', 'Temperatura Máxima']

    return eventos_alerta

# Pagina Streamlit
st.write("# SEREMI RM - Analisis exploratorio de datos - Temperaturas extremas")
st.write("## Dias con alertas **SENAPRED** para la Región Metropolitana")
st.plotly_chart(grafico_alertas_senapred(df), use_container_width=True)

st.write("## Dias con alertas **SEREMI** para la Región Metropolitana")
fig_con_alertas_con_marcadores = grafico_alertas_seremi(df)
st.plotly_chart(fig_con_alertas_con_marcadores, use_container_width=True)
eventos_alerta_df_con_temp = tabla_alertas_seremi(df)
st.table(eventos_alerta_df_con_temp)
fig_con_alertas35_con_marcadores = grafico_alertas_sobre35(df)
eventos_alerta_df_con_temp35 = tabla_alertas_sobre35(df)

st.write(f"## Dias con temperatura **sobre 35 grados** para la Región Metropolitana")
st.plotly_chart(fig_con_alertas35_con_marcadores, use_container_width=True)
st.table(eventos_alerta_df_con_temp35)
# %%
