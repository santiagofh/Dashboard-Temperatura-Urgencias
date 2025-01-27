#%%
import streamlit as st
import pandas as pd
import plotly.express as px
import datetime

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
path_def = "data_defunciones/defunciones_2024.csv"

#%%

# Cargar datos
data = pd.read_csv(path_def)

# Dividir columnas
columns = [
    'SEXO', 'EDAD_TIPO', 'EDAD_CANT', 'DIA_DEF', 'MES_DEF', 'ANO_DEF',
    'DIAG1', 'REG_RES', 'CARDIOVASCULAR', 'DATE'
]
data = data['SEXO|EDAD_TIPO|EDAD_CANT|DIA_DEF|MES_DEF|ANO_DEF|DIAG1|REG_RES|CARDIOVASCULAR|DATE'].str.split('|', expand=True)
data.columns = columns

# Convertir tipos de datos
data['CARDIOVASCULAR'] = data['CARDIOVASCULAR'].map({'True': True, 'False': False})
data['DATE'] = pd.to_datetime(data['DATE'], errors='coerce')
data['EDAD_CANT'] = pd.to_numeric(data['EDAD_CANT'], errors='coerce')

# Filtrar datos por rango de fechas
filtered_data = data[(data['DATE'] >= pd.to_datetime(rango_fechas[0])) & (data['DATE'] <= pd.to_datetime(rango_fechas[1]))]

#%% Gráfico 1: Cantidad diaria de defunciones cardiovasculares
daily_cardiovascular_deaths = filtered_data[filtered_data['CARDIOVASCULAR']].groupby('DATE').size().reset_index(name='Cantidad')

st.write("## Cantidad diaria de defunciones cardiovasculares")
st.write("Este gráfico muestra el número diario de defunciones relacionadas con causas cardiovasculares dentro del rango de fechas seleccionado.")

fig1 = px.line(
    daily_cardiovascular_deaths, 
    x='DATE', 
    y='Cantidad', 
    title='Cantidad diaria de defunciones cardiovasculares',
    labels={'DATE': 'Fecha', 'Cantidad': 'Cantidad de defunciones'},
    template='plotly_white'
)

st.plotly_chart(fig1)

#%% Gráfico 2: Porcentaje de defunciones cardiovasculares
total_deaths = filtered_data.groupby('DATE').size().reset_index(name='Total')
daily_cardiovascular_deaths = daily_cardiovascular_deaths.rename(columns={'Cantidad': 'CARDIOVASCULAR'})
merged_data = pd.merge(total_deaths, daily_cardiovascular_deaths, on='DATE', how='left').fillna(0)
merged_data['Porcentaje'] = (merged_data['CARDIOVASCULAR'] / merged_data['Total']) * 100

st.write("## Porcentaje de defunciones cardiovasculares")
st.write("Este gráfico muestra el porcentaje de defunciones cardiovasculares respecto al total de defunciones registradas diariamente.")

fig2 = px.line(
    merged_data, 
    x='DATE', 
    y='Porcentaje', 
    title='Porcentaje de defunciones cardiovasculares',
    labels={'DATE': 'Fecha', 'Porcentaje': 'Porcentaje (%)'},
    template='plotly_white'
)

st.plotly_chart(fig2)

#%% Gráfico 3: Cantidad diaria de defunciones cardiovasculares por grupo de edad
grouped_data = filtered_data[filtered_data['CARDIOVASCULAR']].copy()
grouped_data['Grupo_Edad'] = grouped_data['EDAD_CANT'].apply(lambda x: '>= 85' if x >= 85 else ('< 1' if x < 1 else 'Otros'))

daily_cardiovascular_deaths_by_age = grouped_data.groupby(['DATE', 'Grupo_Edad']).size().reset_index(name='Cantidad')

st.write("## Cantidad diaria de defunciones cardiovasculares por grupo de edad")
st.write("Este gráfico muestra la distribución diaria de defunciones cardiovasculares para los grupos de edad: menores de 1 año, mayores de 85 años y otros.")

fig3 = px.line(
    daily_cardiovascular_deaths_by_age, 
    x='DATE', 
    y='Cantidad', 
    color='Grupo_Edad', 
    title='Cantidad diaria de defunciones cardiovasculares por grupo de edad',
    labels={'DATE': 'Fecha', 'Cantidad': 'Cantidad de defunciones', 'Grupo_Edad': 'Grupo de Edad'},
    template='plotly_white'
)

st.plotly_chart(fig3)

#%% Gráfico 4: Porcentaje de defunciones cardiovasculares por grupo de edad
daily_cardiovascular_deaths_by_age = daily_cardiovascular_deaths_by_age.rename(columns={'Cantidad': 'CARDIOVASCULAR'})
merged_data_by_age = pd.merge(total_deaths, daily_cardiovascular_deaths_by_age, on='DATE', how='left').fillna(0)
merged_data_by_age['Porcentaje'] = (merged_data_by_age['CARDIOVASCULAR'] / merged_data_by_age['Total']) * 100

st.write("## Porcentaje de defunciones cardiovasculares por grupo de edad")
st.write("Este gráfico presenta el porcentaje de defunciones cardiovasculares desglosado por grupo de edad, comparando menores de 1 año, mayores de 85 años y otros.")

fig4 = px.line(
    merged_data_by_age, 
    x='DATE', 
    y='Porcentaje', 
    color='Grupo_Edad', 
    title='Porcentaje de defunciones cardiovasculares por grupo de edad',
    labels={'DATE': 'Fecha', 'Porcentaje': 'Porcentaje (%)', 'Grupo_Edad': 'Grupo de Edad'},
    template='plotly_white'
)

st.plotly_chart(fig4)
