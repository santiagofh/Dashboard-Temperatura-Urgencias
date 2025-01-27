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
path_eh = "data_egresos/eh_2024.csv"

#%%

# Cargar datos
data_eh = pd.read_csv(path_eh, encoding='LATIN1')

# Convertir tipos de datos
data_eh['CARDIOVASCULAR'] = data_eh['CARDIOVASCULAR']
data_eh['date_ingreso'] = pd.to_datetime(data_eh['date_ingreso'], errors='coerce')
data_eh['EDAD_CANT'] = pd.to_numeric(data_eh['EDAD_CANT'], errors='coerce')

# Filtrar datos por rango de fechas
data_eh = data_eh[(data_eh['date_ingreso'] >= pd.to_datetime(rango_fechas[0])) & (data_eh['date_ingreso'] <= pd.to_datetime(rango_fechas[1]))]

#%% Gráfico 1: Cantidad diaria de defunciones cardiovasculares
daily_cardiovascular_eh = data_eh[data_eh['CARDIOVASCULAR']].groupby('date_ingreso').size().reset_index(name='Cantidad')

st.write("## Cantidad diaria de egresos hospitalarios")

st.write("Este gráfico muestra el número diario de ingresos hospitalarios relacionadas con causas cardiovasculares dentro del rango de fechas seleccionado.")

fig1 = px.line(
    daily_cardiovascular_eh, 
    x='date_ingreso', 
    y='Cantidad', 
    title='Cantidad diaria de egresos por causas cardiovasculares',
    labels={'date_ingreso': 'Fecha ingreso', 'Cantidad': 'Cantidad de egresos'},
    template='plotly_white'
)

st.plotly_chart(fig1)

# %%
