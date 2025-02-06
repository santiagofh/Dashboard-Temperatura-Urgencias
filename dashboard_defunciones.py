# -*- coding: utf-8 -*-
"""
Página de Defunciones – Análisis de defunciones cardiovasculares con Temperatura y Alertas SEREMI

Esta página muestra distintos gráficos basados en la información de defunciones del año 2024, 
en particular enfocándose en las defunciones cardiovasculares y su distribución por grupo de edad, 
y superpone la serie de temperatura máxima con la clasificación de alertas (según SEREMI).

Cada sección incluye:
  - Un título y una breve explicación.
  - El gráfico interactivo.
  - Una tabla que muestra los datos de los últimos 10 días usados en el gráfico.
  - Un botón para descargar (en Excel) los datos utilizados en el gráfico.
Al final se ofrecen botones para descargar las bases completas en formato CSV.
"""

# %% 1. Importar librerías y definir funciones auxiliares
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import datetime
from io import BytesIO

# Función para convertir un DataFrame a Excel (en bytes)
def to_excel_bytes(df: pd.DataFrame) -> bytes:
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Datos')
    return output.getvalue()

# Función para convertir un DataFrame a CSV (en bytes)
def df_to_csv_bytes(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False, sep=';', decimal=',', encoding='utf-8').encode('utf-8')

# --- Definición de paletas de colores

# Paleta de tonos azules para las series de defunciones
colors_def = {
    'Cardiovascular': '#08306B'  # Azul oscuro
}

# Color distintivo para la temperatura
color_temperatura = '#B22222'  # Firebrick

# Colores para los estados de alerta (manteniendo un estilo profesional)
colors_alerta = {
    'Sin Alerta': '#6c757d',                # Gris muted
    'Alerta temprana preventiva': '#28a745',# Verde Bootstrap
    'Alerta Amarilla': '#ffc107',           # Ámbar
    'Alerta Roja': '#dc3545'                # Rojo Bootstrap
}

# Paleta para grupos de edad (para gráficos desglosados por grupo)
colors_age = {
    '< 1': '#08306B',
    '>= 85': '#2171B5',
    'Otros': '#4292C6'
}

# %% 2. Configuración del Sidebar y carga de datos

# Definir el rango de fechas permitido y predeterminado
fecha_inicio = datetime.date(2024, 1, 1)
fecha_fin = datetime.date.today()
fecha_inicio_default = datetime.date(2024, 11, 1)

st.sidebar.write("### Seleccione el rango de fechas")
rango_fechas = st.sidebar.date_input(
    "Rango de Fechas:",
    [fecha_inicio_default, fecha_fin],
    min_value=fecha_inicio,
    max_value=fecha_fin
)

# Ruta del archivo de defunciones
path_def = "data_defunciones/defunciones_2024.csv"

# Cargar datos de defunciones
data = pd.read_csv(path_def)
columns = [
    'SEXO', 'EDAD_TIPO', 'EDAD_CANT', 'DIA_DEF', 'MES_DEF', 'ANO_DEF',
    'DIAG1', 'REG_RES', 'CARDIOVASCULAR', 'DATE'
]
data = data['SEXO|EDAD_TIPO|EDAD_CANT|DIA_DEF|MES_DEF|ANO_DEF|DIAG1|REG_RES|CARDIOVASCULAR|DATE'].str.split('|', expand=True)
data.columns = columns
data['CARDIOVASCULAR'] = data['CARDIOVASCULAR'].map({'True': True, 'False': False})
data['DATE'] = pd.to_datetime(data['DATE'], errors='coerce')
data['EDAD_CANT'] = pd.to_numeric(data['EDAD_CANT'], errors='coerce')

# Filtrar defunciones según rango de fechas seleccionado
filtered_data = data[(data['DATE'] >= pd.to_datetime(rango_fechas[0])) & 
                     (data['DATE'] <= pd.to_datetime(rango_fechas[1]))]

# Cargar la base de temperaturas (usada para superponer serie de temperatura y alertas)
df_temp = pd.read_csv("data_temperatura/tmm_historico_2024.csv")
df_temp['date'] = pd.to_datetime(df_temp['date'])
df_temp = df_temp[(df_temp['date'] >= pd.to_datetime(rango_fechas[0])) & 
                  (df_temp['date'] <= pd.to_datetime(rango_fechas[1]))]

# Aplicar lógica de alertas SEREMI a la serie de temperatura
df_temp = df_temp.copy()
df_temp['alerta'] = 'Sin Alerta'
df_temp['mes'] = df_temp['date'].dt.month
df_temp.loc[df_temp['mes'].isin([11,12,1,2,3]), 'alerta'] = 'Alerta temprana preventiva'
df_temp.loc[df_temp['t_max'] >= 40, 'alerta'] = 'Alerta Roja'
df_temp['alerta_temporal'] = df_temp['t_max'] >= 34
df_temp['alerta_consecutiva'] = df_temp['alerta_temporal'].rolling(window=2).sum()
df_temp.loc[df_temp['alerta_consecutiva'] >= 2, 'alerta'] = 'Alerta Amarilla'
df_temp['alerta_consecutiva_3'] = df_temp['alerta_temporal'].rolling(window=3).sum()
df_temp.loc[df_temp['alerta_consecutiva_3'] >= 3, 'alerta'] = 'Alerta Roja'

# %% 3. Creación de Gráficos y bases de datos

## Gráfico 1: Cantidad diaria de defunciones cardiovasculares
daily_cardiovascular = filtered_data[filtered_data['CARDIOVASCULAR']].groupby('DATE').size().reset_index(name='CARDIOVASCULAR')

## Gráfico 2: Porcentaje de defunciones cardiovasculares
total_deaths = filtered_data.groupby('DATE').size().reset_index(name='Total')
daily_cardiovascular_perc = daily_cardiovascular.copy()
merged_data = pd.merge(total_deaths, daily_cardiovascular_perc, on='DATE', how='left').fillna(0)
merged_data['Porcentaje'] = (merged_data['CARDIOVASCULAR'] / merged_data['Total']) * 100
merged_data['Temperatura Máxima'] = df_temp.set_index('date').reindex(merged_data['DATE'], method='nearest')['t_max'].values

## Gráfico 3: Cantidad diaria de defunciones cardiovasculares por grupo de edad
grouped_data = filtered_data[filtered_data['CARDIOVASCULAR']].copy()
grouped_data['Grupo_Edad'] = grouped_data['EDAD_CANT'].apply(lambda x: '>= 85' if x >= 85 else ('< 1' if x < 1 else 'Otros'))
daily_by_age = grouped_data.groupby(['DATE', 'Grupo_Edad']).size().reset_index(name='CARDIOVASCULAR')

## Gráfico 4: Porcentaje de defunciones cardiovasculares por grupo de edad
total_by_date = total_deaths.copy()
merged_by_age = pd.merge(total_by_date, daily_by_age, on='DATE', how='left').fillna(0)
merged_by_age['Porcentaje'] = (merged_by_age['CARDIOVASCULAR'] / merged_by_age['Total']) * 100
merged_by_age['Temperatura Máxima'] = df_temp.set_index('date').reindex(merged_by_age['DATE'], method='nearest')['t_max'].values

# %% 4. Renderización de Gráficos, Tablas y Botones de Descarga

### Gráfico 1: Cantidad diaria de defunciones cardiovasculares + Temperatura y Alertas
st.write("## Cantidad diaria de defunciones cardiovasculares")
st.markdown(
    """
    **Descripción:**  
    Este gráfico muestra el número diario de defunciones cardiovasculares dentro del rango de fechas seleccionado, 
    superpuesto a la serie de temperatura máxima (con sus alertas) según criterios SEREMI.
    """
)
fig1 = px.line(
    daily_cardiovascular, 
    x='DATE', 
    y='CARDIOVASCULAR', 
    title='Cantidad diaria de defunciones cardiovasculares',
    labels={'DATE': 'Fecha', 'CARDIOVASCULAR': 'Cantidad de defunciones'},
    template='plotly_white'
)
fig1.update_traces(line_color=colors_def['Cardiovascular'])
fig1.add_trace(go.Scatter(
    x=df_temp['date'], y=df_temp['t_max'],
    mode='lines', name='Temperatura Máxima',
    line=dict(color=color_temperatura), yaxis='y2'
))
for alerta, color in colors_alerta.items():
    df_alerta = df_temp[df_temp['alerta'] == alerta]
    fig1.add_trace(go.Scatter(
        x=df_alerta['date'], y=df_alerta['t_max'],
        mode='markers', name=f'Alerta: {alerta}',
        marker=dict(color=color), yaxis='y2'
    ))
fig1.update_layout(
    yaxis2=dict(title='Temperatura Máxima', overlaying='y', side='right')
)
st.plotly_chart(fig1, use_container_width=True)

with st.expander("Ver tabla: Últimos 10 días (Defunciones Cardiovasculares)"):
    # Tabla 1: Últimos 10 días de defunciones cardiovasculares (Gráfico 1)
    table1 = daily_cardiovascular.sort_values(by='DATE').tail(10)
    st.write("### Tabla: Últimos 10 días (Defunciones Cardiovasculares)")
    st.table(table1)
    st.download_button(
        label="Descargar Tabla (Excel)",
        data=to_excel_bytes(table1),
        file_name="tabla_defunciones_cardiovasculares.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    st.markdown("**Descargar Datos Utilizados en el Gráfico (Excel):**")
    st.download_button(
        label="Descargar Datos (Excel)",
        data=to_excel_bytes(daily_cardiovascular),
        file_name="datos_defunciones_cardiovasculares.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

### Gráfico 2: Porcentaje de defunciones cardiovasculares + Temperatura y Alertas
st.write("## Porcentaje de defunciones cardiovasculares")
st.markdown(
    """
    **Descripción:**  
    Este gráfico muestra el porcentaje diario de defunciones cardiovasculares respecto al total de defunciones, 
    junto con la serie de temperatura máxima (y sus alertas) para complementar el análisis.
    """
)
fig2 = px.line(
    merged_data, 
    x='DATE', 
    y='Porcentaje', 
    title='Porcentaje de defunciones cardiovasculares',
    labels={'DATE': 'Fecha', 'Porcentaje': 'Porcentaje (%)'},
    template='plotly_white'
)
fig2.update_traces(line_color=colors_def['Cardiovascular'])
fig2.add_trace(go.Scatter(
    x=df_temp['date'], y=df_temp['t_max'],
    mode='lines', name='Temperatura Máxima',
    line=dict(color=color_temperatura), yaxis='y2'
))
for alerta, color in colors_alerta.items():
    df_alerta = df_temp[df_temp['alerta'] == alerta]
    fig2.add_trace(go.Scatter(
        x=df_alerta['date'], y=df_alerta['t_max'],
        mode='markers', name=f'Alerta: {alerta}',
        marker=dict(color=color), yaxis='y2'
    ))
fig2.update_layout(
    yaxis2=dict(title='Temperatura Máxima', overlaying='y', side='right')
)
st.plotly_chart(fig2, use_container_width=True)
with st.expander("Ver tabla: Últimos 10 días (Porcentaje de defunciones cardiovasculares)"):
    # Tabla 2: Últimos 10 días (Porcentaje de defunciones cardiovasculares)
    table2 = merged_data.sort_values(by='DATE').tail(10)
    st.write("### Tabla: Últimos 10 días (Porcentaje de Defunciones Cardiovasculares)")
    st.table(table2)
    st.download_button(
        label="Descargar Tabla (Excel)",
        data=to_excel_bytes(table2),
        file_name="tabla_porcentaje_defunciones.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    st.markdown("**Descargar Datos Utilizados en el Gráfico (Excel):**")
    st.download_button(
        label="Descargar Datos (Excel)",
        data=to_excel_bytes(merged_data),
        file_name="datos_porcentaje_defunciones.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

### Gráfico 3: Cantidad diaria de defunciones cardiovasculares por grupo de edad + Temperatura y Alertas
st.write("## Cantidad diaria de defunciones cardiovasculares por grupo de edad")
st.markdown(
    """
    **Descripción:**  
    Este gráfico muestra la distribución diaria de defunciones cardiovasculares para los grupos de edad:  
    - **< 1 año**  
    - **>= 85 años**  
    - **Otros**  
    Se superpone la serie de temperatura máxima (con alertas) en un eje secundario.
    """
)
fig3 = px.line(
    daily_by_age, 
    x='DATE', 
    y='CARDIOVASCULAR', 
    color='Grupo_Edad', 
    title='Cantidad diaria de defunciones cardiovasculares por grupo de edad',
    labels={'DATE': 'Fecha', 'CARDIOVASCULAR': 'Cantidad de defunciones', 'Grupo_Edad': 'Grupo de Edad'},
    template='plotly_white',
    color_discrete_map=colors_age
)
fig3.add_trace(go.Scatter(
    x=df_temp['date'], y=df_temp['t_max'],
    mode='lines', name='Temperatura Máxima',
    line=dict(color=color_temperatura), yaxis='y2'
))
for alerta, color in colors_alerta.items():
    df_alerta = df_temp[df_temp['alerta'] == alerta]
    fig3.add_trace(go.Scatter(
        x=df_alerta['date'], y=df_alerta['t_max'],
        mode='markers', name=f'Alerta: {alerta}',
        marker=dict(color=color), yaxis='y2'
    ))
fig3.update_layout(
    yaxis2=dict(title='Temperatura Máxima', overlaying='y', side='right')
)
st.plotly_chart(fig3, use_container_width=True)

with st.expander("Ver tabla: Últimos 10 días (Defunciones por grupo de edad)"):
    # Tabla 3: Últimos 10 días (Defunciones por grupo de edad)

    daily_by_age = daily_by_age.loc[daily_by_age.Grupo_Edad=='>= 85']
    table3 = daily_by_age.sort_values(by='DATE').tail(10)

    st.write("### Tabla: Últimos 10 días (Defunciones por Grupo de Edad)")
    st.table(table3)
    st.download_button(
        label="Descargar Tabla (Excel)",
        data=to_excel_bytes(table3),
        file_name="tabla_defunciones_por_grupo_edad.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    st.markdown("**Descargar Datos Utilizados en el Gráfico (Excel):**")
    st.download_button(
        label="Descargar Datos (Excel)",
        data=to_excel_bytes(daily_by_age),
        file_name="datos_defunciones_por_grupo_edad.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

### Gráfico 4: Porcentaje de defunciones cardiovasculares por grupo de edad + Temperatura y Alertas
st.write("## Porcentaje de defunciones cardiovasculares por grupo de edad")
st.markdown(
    """
    **Descripción:**  
    Este gráfico presenta el porcentaje diario de defunciones cardiovasculares desglosado por grupo de edad,  
    comparando los grupos **< 1 año**, **>= 85 años** y **Otros**. Se superpone la serie de temperatura máxima  
    (y sus alertas) en un eje secundario.
    """
)
fig4 = px.line(
    merged_by_age, 
    x='DATE', 
    y='Porcentaje', 
    color='Grupo_Edad', 
    title='Porcentaje de defunciones cardiovasculares por grupo de edad',
    labels={'DATE': 'Fecha', 'Porcentaje': 'Porcentaje (%)', 'Grupo_Edad': 'Grupo de Edad'},
    template='plotly_white',
    color_discrete_map=colors_age
)
fig4.add_trace(go.Scatter(
    x=df_temp['date'], y=df_temp['t_max'],
    mode='lines', name='Temperatura Máxima',
    line=dict(color=color_temperatura), yaxis='y2'
))
for alerta, color in colors_alerta.items():
    df_alerta = df_temp[df_temp['alerta'] == alerta]
    fig4.add_trace(go.Scatter(
        x=df_alerta['date'], y=df_alerta['t_max'],
        mode='markers', name=f'Alerta: {alerta}',
        marker=dict(color=color), yaxis='y2'
    ))
fig4.update_layout(
    yaxis2=dict(title='Temperatura Máxima', overlaying='y', side='right')
)
st.plotly_chart(fig4, use_container_width=True)
with st.expander("Ver tabla: Últimos 10 días (Porcentaje de Defunciones por Grupo de Edad)"):
# Tabla 4: Últimos 10 días (Porcentaje de defunciones por grupo de edad)
    merged_by_age = merged_by_age.loc[merged_by_age.Grupo_Edad=='>= 85']
    table4 = merged_by_age.sort_values(by='DATE').tail(10)
    st.write("### Tabla: Últimos 10 días (Porcentaje de Defunciones por Grupo de Edad)")
    st.table(table4)
    st.download_button(
        label="Descargar Tabla (Excel)",
        data=to_excel_bytes(table4),
        file_name="tabla_porcentaje_defunciones_por_grupo.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    st.markdown("**Descargar Datos Utilizados en el Gráfico (Excel):**")
    st.download_button(
        label="Descargar Datos (Excel)",
        data=to_excel_bytes(merged_by_age),
        file_name="datos_porcentaje_defunciones_por_grupo.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

# %% 5. Sección Final: Descargar Bases de Datos Completas (en CSV)
st.write("## Descargar Bases de Datos Completas")
st.markdown(
    """
    **Bases de Datos Completas:**  
    A continuación, puedes descargar los archivos CSV originales que contienen toda la información.
    """
)
with open(path_def, "rb") as f:
    base_defunciones = f.read()
st.download_button(
    label="Descargar Base de Defunciones (CSV)",
    data=base_defunciones,
    file_name="defunciones_2024.csv",
    mime="text/csv"
)
with open("data_temperatura/tmm_historico_2024.csv", "rb") as f_temp:
    base_temp = f_temp.read()
st.download_button(
    label="Descargar Base de Temperaturas (CSV)",
    data=base_temp,
    file_name="tmm_historico_2024.csv",
    mime="text/csv"
)
