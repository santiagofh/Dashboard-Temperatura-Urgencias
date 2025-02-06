# -*- coding: utf-8 -*-
"""
Aplicación Streamlit para el análisis exploratorio de datos de temperaturas extremas en la Región Metropolitana.
Se muestran tres secciones:
    1. Gráfico y tabla SENAPRED: Visualiza las temperaturas máximas diarias con rangos de alerta.
    2. Gráfico y tabla SEREMI: Presenta las temperaturas máximas diarias con la clasificación de alertas, junto con una explicación de las reglas.
    3. Gráfico y tabla Sobre 35°C: Destaca los días en que la temperatura fue igual o superior a 35°C.
Debajo de cada gráfico se agrega un botón para descargar los datos utilizados en el mismo.
Al final se agrega una sección para descargar la base completa (el CSV original).
"""

# %% 1. Importar librerías y definir funciones auxiliares
import streamlit as st
import pandas as pd
import plotly.express as px
import datetime
import numpy as np  # Para la función de tabla SENAPRED
import io

# Función auxiliar: Convertir DataFrame a archivo Excel en memoria
def to_excel(df: pd.DataFrame) -> bytes:
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name="Datos")
    return output.getvalue()

# %% 2. Configuración del Sidebar y carga de datos
st.sidebar.write("### Seleccione el rango de fechas")
fecha_inicio = datetime.date(2024, 1, 1)
fecha_fin = datetime.date.today()
fecha_inicio_default = datetime.date(2024, 11, 1)

rango_fechas = st.sidebar.date_input(
    "Rango de Fechas:",
    [fecha_inicio_default, fecha_fin],  # Fechas predeterminadas
    min_value=fecha_inicio,
    max_value=fecha_fin
)

# Cargar y filtrar los datos
df = pd.read_csv("data_temperatura/tmm_historico_2024.csv")
df["date"] = pd.to_datetime(df["date"])

if len(rango_fechas) == 2:
    fecha_inicio_seleccionada, fecha_fin_seleccionada = rango_fechas
    df = df[(df["date"] >= pd.Timestamp(fecha_inicio_seleccionada)) &
            (df["date"] <= pd.Timestamp(fecha_fin_seleccionada))]

# %% 3. Definir funciones para cálculos, gráficos y tablas

def evaluar_alertas(df: pd.DataFrame) -> pd.DataFrame:
    """
    Evalúa y asigna alertas a los datos según la temperatura máxima y el mes.
    Se determinan las siguientes clasificaciones:
      - **Sin Alerta:** Valor por defecto.
      - **Alerta temprana preventiva:** Durante los meses de noviembre, diciembre, enero, febrero y marzo.
      - **Alerta Roja:** Se asigna en dos casos:
            1. Si la temperatura máxima en un día es igual o superior a 40°C.
            2. Si se registran tres días consecutivos (ventana de 3 días) con temperaturas máximas iguales o superiores a 34°C.
      - **Alerta Amarilla:** Se asigna cuando se registran al menos dos días consecutivos (ventana de 2 días) con temperaturas máximas iguales o superiores a 34°C, siempre que no se cumpla la condición de Alerta Roja.
    """
    df = df.copy()
    df["alerta"] = "Sin Alerta"
    df["mes"] = df["date"].dt.month
    df.loc[df["mes"].isin([11, 12, 1, 2, 3]), "alerta"] = "Alerta temprana preventiva"
    df.loc[df["t_max"] >= 40, "alerta"] = "Alerta Roja"
    df["alerta_temporal"] = df["t_max"] >= 34
    df["alerta_consecutiva"] = df["alerta_temporal"].rolling(window=2).sum()
    df.loc[df["alerta_consecutiva"] >= 2, "alerta"] = "Alerta Amarilla"
    df["alerta_consecutiva_3"] = df["alerta_temporal"].rolling(window=3).sum()
    df.loc[df["alerta_consecutiva_3"] >= 3, "alerta"] = "Alerta Roja"
    return df

def grafico_alertas_senapred(df: pd.DataFrame):
    """
    Gráfico SENAPRED:
    Muestra la evolución de las temperaturas máximas diarias y agrega líneas de referencia en 30°C, 34°C y 40°C.
    Se distinguen tres rangos:
      - **Verde:** 30°C ≤ t_max < 34°C
      - **Amarillo:** 34°C ≤ t_max < 40°C
      - **Rojo:** t_max ≥ 40°C
    """
    fig = px.line(
        df,
        x="date",
        y="t_max",
        title="Temperaturas Máximas - SENAPRED",
        markers=True
    )
    # Líneas de referencia
    fig.add_hline(y=34, line_dash="dot", line_color="yellow",
                  annotation_text="34°C", annotation_position="bottom right")
    fig.add_hline(y=40, line_dash="dot", line_color="red",
                  annotation_text="40°C", annotation_position="bottom right")
    fig.add_hline(y=30, line_dash="dot", line_color="green",
                  annotation_text="30°C", annotation_position="bottom right")
    
    # Marcadores según rangos de temperatura
    df_green = df[(df["t_max"] >= 30) & (df["t_max"] < 34)]
    df_yellow = df[(df["t_max"] >= 34) & (df["t_max"] < 40)]
    df_red = df[df["t_max"] >= 40]
    
    fig.add_scatter(x=df_green["date"], y=df_green["t_max"],
                    mode="markers", name="30°C ≤ t_max < 34°C", marker=dict(color="green"))
    fig.add_scatter(x=df_yellow["date"], y=df_yellow["t_max"],
                    mode="markers", name="34°C ≤ t_max < 40°C", marker=dict(color="yellow"))
    fig.add_scatter(x=df_red["date"], y=df_red["t_max"],
                    mode="markers", name="t_max ≥ 40°C", marker=dict(color="red"))
    
    fig.update_layout(
        xaxis_title="Fecha",
        yaxis_title="Temperatura Máxima (°C)",
        legend=dict(orientation="h", yanchor="top", y=-0.2, xanchor="center", x=0.5)
    )
    return fig

def tabla_alertas_senapred(df: pd.DataFrame) -> pd.DataFrame:
    """
    Tabla SENAPRED:
    Lista los días en que la temperatura máxima alcanzó las alertas amarilla o roja, según:
      - **Alerta Amarilla:** 34°C ≤ t_max < 40°C
      - **Alerta Roja:** t_max ≥ 40°C
    """
    df_copy = df.copy()
    # Definir las condiciones usando np.select
    conditions = [
        (df_copy["t_max"] >= 34) & (df_copy["t_max"] < 40),
        (df_copy["t_max"] >= 40)
    ]
    choices = ["Alerta Amarilla", "Alerta Roja"]
    df_copy["alerta_senapred"] = np.select(conditions, choices, default="Sin Alerta")
    # Filtrar solo las filas con alerta amarilla o roja
    df_alertas = df_copy[df_copy["alerta_senapred"].isin(["Alerta Amarilla", "Alerta Roja"])].sort_values(by="date")
    tabla = df_alertas[["date", "alerta_senapred", "t_max"]].reset_index(drop=True)
    tabla.columns = ["Fecha", "Tipo de Alerta", "Temperatura Máxima"]
    return tabla

def grafico_alertas_seremi(df: pd.DataFrame):
    """
    Gráfico SEREMI:
    Visualiza las temperaturas máximas diarias con la clasificación de alertas obtenida.
    Se muestran en diferentes colores:
      - **Azul:** Sin Alerta
      - **Verde:** Alerta temprana preventiva
      - **Amarillo:** Alerta Amarilla
      - **Rojo:** Alerta Roja
    """
    df_alertas = evaluar_alertas(df)
    color_map = {
        "Sin Alerta": "blue",
        "Alerta temprana preventiva": "green",
        "Alerta Amarilla": "yellow",
        "Alerta Roja": "red"
    }
    fig = px.line(df_alertas, x="date", y="t_max",
                  title="Temperaturas Máximas y Alertas - SEREMI",
                  color_discrete_sequence=["grey"])
    fig.add_hline(y=34, line_dash="dot", line_color="yellow",
                  annotation_text="35°C", annotation_position="bottom right")
    fig.add_hline(y=40, line_dash="dot", line_color="red",
                  annotation_text="40°C", annotation_position="bottom right")
    fig.add_hline(y=30, line_dash="dot", line_color="green",
                  annotation_text="30°C", annotation_position="bottom right")
    for alerta, color in color_map.items():
        df_temp = df_alertas[df_alertas["alerta"] == alerta]
        fig.add_scatter(x=df_temp["date"], y=df_temp["t_max"],
                        mode="markers", name=alerta, marker=dict(color=color))
    
    fig.update_layout(
        legend=dict(orientation="h", yanchor="top", y=-0.2, xanchor="center", x=0.5)
    )
    return fig

def tabla_alertas_seremi(df: pd.DataFrame) -> pd.DataFrame:
    """
    Tabla SEREMI:
    Lista los días en que se registraron alertas (Alerta Amarilla o Alerta Roja),
    mostrando la fecha, tipo de alerta y temperatura máxima.
    """
    df_alertas = evaluar_alertas(df)
    df_filtrado = df_alertas[df_alertas["alerta"].isin(["Alerta Amarilla", "Alerta Roja"])].sort_values(by="date")
    tabla = df_filtrado[["date", "alerta", "t_max"]].reset_index(drop=True)
    tabla.columns = ["Fecha", "Tipo de Alerta", "Temperatura Máxima"]
    return tabla

def grafico_alertas_sobre35(df: pd.DataFrame):
    """
    Gráfico Sobre 35°C:
    Resalta los días en que la temperatura máxima fue igual o superior a 35°C.
    Se utilizan dos colores:
      - **Rojo:** Días con temperatura "Sobre 35"
      - **Azul:** Días con temperatura "Bajo 35"
    """
    df_copy = df.copy()
    df_copy["sobre_35"] = df_copy["t_max"].apply(lambda x: "Sobre 35" if x >= 35 else "Bajo 35")
    color_map = {
        "Sobre 35": "red",
        "Bajo 35": "blue"
    }
    fig = px.line(df_copy, x="date", y="t_max",
                  title="Temperaturas Máximas y Días con Temperatura sobre 35°C",
                  color_discrete_sequence=["grey"])
    
    for etiqueta, color in color_map.items():
        df_temp = df_copy[df_copy["sobre_35"] == etiqueta]
        fig.add_scatter(x=df_temp["date"], y=df_temp["t_max"],
                        mode="markers", name=etiqueta, marker=dict(color=color))
    
    fig.update_layout(
        legend=dict(orientation="h", yanchor="top", y=-0.2, xanchor="center", x=0.5)
    )
    return fig

def tabla_alertas_sobre35(df: pd.DataFrame) -> pd.DataFrame:
    """
    Tabla Sobre 35°C:
    Lista los días en que la temperatura máxima fue igual o superior a 35°C,
    mostrando la fecha, etiqueta y temperatura máxima.
    """
    df_copy = df.copy()
    df_copy["sobre_35"] = df_copy["t_max"].apply(lambda x: "Sobre 35" if x >= 35 else "Bajo 35")
    df_filtrado = df_copy[df_copy["sobre_35"] == "Sobre 35"].sort_values(by="date")
    tabla = df_filtrado[["date", "sobre_35", "t_max"]].reset_index(drop=True)
    tabla.columns = ["Fecha", "Alerta", "Temperatura Máxima"]
    return tabla

# %% 4. Construir la aplicación principal

st.title("SEREMI RM - Análisis Exploratorio de Datos de Temperaturas Extremas")
st.write("Esta aplicación permite analizar y visualizar la evolución de las temperaturas máximas diarias en la Región Metropolitana, junto con la clasificación de alertas según criterios definidos.")

# --- Sección 1: Gráfico y Tabla SENAPRED ---
# st.header("Días con Alertas **SENAPRED**")
# st.markdown(
#     """
#     **Gráfico SENAPRED:**  
#     Este gráfico muestra la evolución de las temperaturas máximas diarias, incluyendo líneas de referencia en 30°C, 34°C y 40°C.
#     Se destacan los días en los que la temperatura se encuentra en diferentes rangos:
#     - **Verde:** 30°C ≤ t_max < 34°C  
#     - **Amarillo:** 34°C ≤ t_max < 40°C  
#     - **Rojo:** t_max ≥ 40°C
#     """
# )
# fig_senapred = grafico_alertas_senapred(df)
# st.plotly_chart(fig_senapred, use_container_width=True)

# # Botón para descargar los datos utilizados en el gráfico SENAPRED
# df_senapred = df.copy()  # Datos filtrados según fecha
# excel_senapred_data = to_excel(df_senapred)
# st.download_button(
#     label="Descargar datos del gráfico SENAPRED (Excel)",
#     data=excel_senapred_data,
#     file_name="datos_grafico_senapred.xlsx",
#     mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
# )

# # Tabla de alertas SENAPRED y botón de descarga de la tabla

# with st.expander("Ver tabla"):
#     st.subheader("Tabla de Alertas SENAPRED")
#     tabla_senapred = tabla_alertas_senapred(df)
#     st.table(tabla_senapred)
#     excel_tabla_senapred = to_excel(tabla_senapred)
#     st.download_button(
#         label="Descargar tabla SENAPRED (Excel)",
#         data=excel_tabla_senapred,
#         file_name="tabla_senapred.xlsx",
#         mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
#     )

# --- Sección 2: Gráfico y Tabla SEREMI ---
st.header("Días con Alertas **SENAPRED**")
st.markdown(
    """
    **Gráfico SEREMI:**  
    En este gráfico se representan las temperaturas máximas diarias junto con el tipo de alerta asignado, según las siguientes reglas:
    
    - **Alerta temprana preventiva:**  
      Se asigna durante los meses de **noviembre, diciembre, enero, febrero y marzo** como medida preventiva.
      
    - **Alerta Roja:**  
      Se asigna en dos casos:
        1. Si la temperatura máxima en un día es **igual o superior a 40°C**.
        2. Si se registran **tres días consecutivos** (ventana de 3 días) con temperaturas máximas iguales o superiores a **34°C**.
      
    - **Alerta Amarilla:**  
      Se asigna cuando se registran **al menos dos días consecutivos** (ventana de 2 días) con temperaturas máximas iguales o superiores a **34°C**, siempre que no se cumpla la condición de Alerta Roja.
      
    - **Sin Alerta:**  
      Cuando no se cumplen las condiciones anteriores.
      
    Los colores utilizados son:
      - **Azul:** Sin Alerta  
      - **Verde:** Alerta temprana preventiva  
      - **Amarillo:** Alerta Amarilla  
      - **Rojo:** Alerta Roja
    """
)
# Los datos usados en SEREMI se obtienen aplicando evaluar_alertas()
df_seremi = evaluar_alertas(df)
fig_seremi = grafico_alertas_seremi(df)
st.plotly_chart(fig_seremi, use_container_width=True)

# Botón para descargar los datos utilizados en el gráfico SEREMI
excel_seremi_data = to_excel(df_seremi)
st.download_button(
    label="Descargar datos del gráfico SEREMI (Excel)",
    data=excel_seremi_data,
    file_name="datos_grafico_seremi.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)

# Tabla de alertas SEREMI y botón de descarga de la tabla
with st.expander("Ver tabla"):
    tabla_seremi = tabla_alertas_seremi(df)
    st.table(tabla_seremi)
    excel_tabla_seremi = to_excel(tabla_seremi)
    st.download_button(
        label="Descargar tabla SEREMI (Excel)",
        data=excel_tabla_seremi,
        file_name="tabla_seremi.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

# --- Sección 3: Gráfico y Tabla Sobre 35°C ---
# st.header("Días con Temperatura **Sobre 35°C**")
# st.markdown(
#     """
#     **Gráfico Sobre 35°C:**  
#     Este gráfico destaca los días en que la temperatura máxima fue igual o superior a 35°C.  
#     Se utiliza:
#     - **Rojo:** Días con temperatura "Sobre 35"  
#     - **Azul:** Días con temperatura "Bajo 35"
#     """
# )
# # Preparar los datos para Sobre 35°C
# df_sobre35 = df.copy()
# df_sobre35["sobre_35"] = df_sobre35["t_max"].apply(lambda x: "Sobre 35" if x >= 35 else "Bajo 35")
# fig_sobre35 = grafico_alertas_sobre35(df)
# st.plotly_chart(fig_sobre35, use_container_width=True)

# # Botón para descargar los datos utilizados en el gráfico Sobre 35°C
# excel_sobre35_data = to_excel(df_sobre35)
# st.download_button(
#     label="Descargar datos del gráfico Sobre 35°C (Excel)",
#     data=excel_sobre35_data,
#     file_name="datos_grafico_sobre35.xlsx",
#     mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
# )

# # Tabla de alertas Sobre 35°C y botón de descarga de la tabla
# with st.expander("Ver tabla"):
#     tabla_sobre35 = tabla_alertas_sobre35(df)
#     st.table(tabla_sobre35)
#     excel_tabla_sobre35 = to_excel(tabla_sobre35)
#     st.download_button(
#         label="Descargar tabla Sobre 35°C (Excel)",
#         data=excel_tabla_sobre35,
#         file_name="tabla_sobre35.xlsx",
#         mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
#     )

# --- Sección Final: Descargar Base Completa ---
st.header("Descargar Base Completa")
with open("data_temperatura/tmm_historico_2024.csv", "rb") as f:
    full_data_csv = f.read()
st.download_button(
    label="Descargar base completa (CSV)",
    data=full_data_csv,
    file_name="tmm_historico_2024.csv",
    mime="text/csv"
)
