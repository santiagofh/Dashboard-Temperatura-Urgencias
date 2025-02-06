# -*- coding: utf-8 -*-
"""
Aplicación Streamlit para el análisis exploratorio de datos de temperaturas extremas en la Región Metropolitana.
Se muestran tres secciones:
    1. Gráfico SENAPRED: Visualiza las temperaturas máximas diarias con rangos de alerta.
    2. Gráfico SEREMI: Presenta las temperaturas máximas diarias con los tipos de alerta asignados.
    3. Gráfico Sobre 35°C: Destaca los días en que la temperatura fue igual o superior a 35°C.
En cada sección se incluye un botón para descargar la información en formato Excel.
"""

# %% 1. Importar librerías y definir funciones auxiliares
import streamlit as st
import pandas as pd
import plotly.express as px
import datetime
import io

# Función auxiliar: Convertir DataFrame a archivo Excel en bytes
def to_excel(df: pd.DataFrame) -> bytes:
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name="Datos")
    return output.getvalue()

# %% 2. Configuración del Sidebar y carga de datos

# Selección del rango de fechas
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
    Se determinan: 'Sin Alerta', 'Alerta temprana preventiva', 'Alerta Amarilla' y 'Alerta Roja'.
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
      - Verde: 30°C ≤ t_max < 34°C
      - Amarillo: 34°C ≤ t_max < 40°C
      - Rojo: t_max ≥ 40°C
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

def grafico_alertas_seremi(df: pd.DataFrame):
    """
    Gráfico SEREMI:
    Visualiza las temperaturas máximas diarias con la clasificación de alertas obtenida.
    Se muestran en diferentes colores:
      - Sin Alerta (Azul)
      - Alerta temprana preventiva (Verde)
      - Alerta Amarilla (Amarillo)
      - Alerta Roja (Rojo)
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
    Resalta los días en que la temperatura máxima alcanzó o superó los 35°C.
    Se utilizan dos colores:
      - Rojo para días con temperatura "Sobre 35"
      - Azul para días "Bajo 35"
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

# --- Sección 1: Gráfico SENAPRED ---
st.header("Días con Alertas **SENAPRED**")
st.markdown(
    """
    **Gráfico SENAPRED:**  
    Este gráfico muestra la evolución de las temperaturas máximas diarias, incluyendo líneas de referencia en 30°C, 34°C y 40°C.
    Se destacan los días en los que la temperatura se encuentra en diferentes rangos:
    - **Verde:** 30°C ≤ t_max < 34°C  
    - **Amarillo:** 34°C ≤ t_max < 40°C  
    - **Rojo:** t_max ≥ 40°C
    """
)
fig_senapred = grafico_alertas_senapred(df)
st.plotly_chart(fig_senapred, use_container_width=True)

# Botón de descarga para los datos usados en el gráfico SENAPRED
excel_senapred = to_excel(df)
st.download_button(
    label="Descargar datos (Excel)",
    data=excel_senapred,
    file_name="datos_senapred.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)

# --- Sección 2: Gráfico y Tabla SEREMI ---
st.header("Días con Alertas **SEREMI**")
st.markdown(
    """
    **Gráfico SEREMI:**  
    En este gráfico se representan las temperaturas máximas diarias junto con el tipo de alerta asignado (según criterios de alerta temprana, amarilla o roja).  
    Los colores utilizados son:
    - **Azul:** Sin Alerta  
    - **Verde:** Alerta temprana preventiva  
    - **Amarillo:** Alerta Amarilla  
    - **Rojo:** Alerta Roja
    """
)
fig_seremi = grafico_alertas_seremi(df)
st.plotly_chart(fig_seremi, use_container_width=True)

# Mostrar tabla de alertas SEREMI
tabla_seremi = tabla_alertas_seremi(df)
st.table(tabla_seremi)

# Botón de descarga para la tabla de alertas SEREMI
excel_seremi = to_excel(tabla_seremi)
st.download_button(
    label="Descargar tabla (Excel)",
    data=excel_seremi,
    file_name="tabla_seremi.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)

# --- Sección 3: Gráfico y Tabla Sobre 35°C ---
st.header("Días con Temperatura **Sobre 35°C**")
st.markdown(
    """
    **Gráfico Sobre 35°C:**  
    Este gráfico destaca los días en que la temperatura máxima fue igual o superior a 35°C.  
    Se utiliza:
    - **Rojo:** Días con temperatura "Sobre 35"  
    - **Azul:** Días con temperatura "Bajo 35"
    """
)
fig_sobre35 = grafico_alertas_sobre35(df)
st.plotly_chart(fig_sobre35, use_container_width=True)

# Mostrar tabla de días con temperatura sobre 35°C
tabla_sobre35 = tabla_alertas_sobre35(df)
st.table(tabla_sobre35)

# Botón de descarga para la tabla Sobre 35°C
excel_sobre35 = to_excel(tabla_sobre35)
st.download_button(
    label="Descargar tabla (Excel)",
    data=excel_sobre35,
    file_name="tabla_sobre35.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)
