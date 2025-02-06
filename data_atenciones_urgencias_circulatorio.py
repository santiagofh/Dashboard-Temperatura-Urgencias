#%%
import pandas as pd

#%%
# Leer el archivo CSV
df_2024 = pd.read_csv(r'C:\Users\fariass\OneDrive - SUBSECRETARIA DE SALUD PUBLICA\Escritorio\DATA\ATENCIONES_URGENCIA\au_2024\AtencionesUrgencia2024.csv', sep=';', encoding='LATIN')
df_2025 = pd.read_csv(r'C:\Users\fariass\OneDrive - SUBSECRETARIA DE SALUD PUBLICA\Escritorio\DATA\ATENCIONES_URGENCIA\au_2025\AtencionesUrgencia2025.csv', sep=';', encoding='LATIN')
#%%
diccionario_causas = {
    # Trastornos mentales y comportamentales
    # 'Trastornos neuróticos, trastornos relacionados con el estrés y trastornos somatomorfos (F40-F48) Incluído el trastorno de pánico (F41.0)': 40,
    # 'Trastornos del Humor (Afectivos) (F30-F39)': 39,
    # 'Lesiones autoinfligidas intencionalmente (X60-X84)': 35,
    # 'TOTAL CAUSAS DE TRASTORNOS MENTALES (F00-F99)': 36,
    # 'Ideación Suicida (R45.8)': 37,
    # 'Trastornos mentales y del comportamiento debidos al uso de sustancias psicoactivas (F10-F19)': 38,
    # 'Otros trastornos mentales no contenidos en las categorías anteriores': 41,
    # '- CAUSAS POR TRASTORNOS MENTALES (F00-F99)': 42,
    # Sistema circulatorio
    'TOTAL CAUSAS SISTEMA CIRCULATORIO': 12,
    'Infarto agudo miocardio': 13,
    'Accidente vascular encefálico': 14,
    'Crisis hipertensiva': 15,
    'Arritmia grave': 16,
    'Otras causas circulatorias': 17,
    '-CAUSAS SISTEMA CIRCULATORIO': 22,
    # Sistema respiratorio
    # 'TOTAL CAUSAS SISTEMA RESPIRATORIO': 2,
    # '- COVID-19, VIRUS IDENTIFICADO U07.1': 32,
    # 'Otra causa respiratoria (J22, J30-J39, J47, J60-J98)': 6,
    # '- COVID-19, VIRUS NO IDENTIFICADO U07.2': 33,
    # 'Neumonía (J12-J18)': 5,
    # 'Influenza (J09-J11)': 4,
    # 'CAUSAS SISTEMA RESPIRATORIO': 7,
    # 'IRA Alta (J00-J06)': 10,
    # 'Bronquitis/bronquiolitis aguda (J20-J21)': 3,
    # 'Crisis obstructiva bronquial (J40-J46)': 11,
    # Traumatismos y envenenamientos
    # 'TOTAL TRAUMATISMOS Y ENVENENAMIENTO': 18,
    # 'Accidentes del tránsito': 19,
    # '- TRAUMATISMOS Y ENVENENAMIENTOS': 23,
    # Otras causas
    # 'TOTAL DEMÁS CAUSAS': 21,
    # 'Otras causas externas': 20,
    # '- LAS DEMÁS CAUSAS': 8,
    # 'DIARREA AGUDA (A00-A09)': 29,
    # 'CIRUGÍAS DE URGENCIA': 24,
    # 'TOTAL DEMANDA': 34,
    # 'SECCIÓN 2. TOTAL DE HOSPITALIZACIONES': 25,
    # 'Pacientes en espera de hospitalización que esperan menos de 12 horas para ser trasladados a cama hospitalaria': 28,
    # 'Pacientes en espera de hospitalización': 27,
    'SECCIÓN 1. TOTAL ATENCIONES DE URGENCIA': 1,
    # 'Covid-19, Virus no identificado U07.2': 31,
    # 'Covid-19, Virus identificado U07.1': 30,
}

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
# Filtrar datos para la Región Metropolitana de Santiago
# 2024
columnas=['Total', 'Menores_1', 'De_1_a_4', 'De_5_a_14', 'De_15_a_64','De_65_y_mas']
def filter_rm_circ(df):
    columnas = ['Total', 'Menores_1', 'De_1_a_4', 'De_5_a_14', 'De_15_a_64', 'De_65_y_mas']
    df_rm = df.loc[df.CodigoRegion == 13]
    df_rm_circ = df_rm.loc[df_rm.IdCausa.isin(diccionario_causas_au.keys())]
    df_rm_circ['Causa'] = df_rm_circ.IdCausa.map(diccionario_causas_au)
    df_rm_circ = df_rm_circ.groupby(by=['GLOSATIPOESTABLECIMIENTO', 'fecha', 'IdCausa', 'Causa'])[columnas].sum().reset_index()
    df_rm_circ['fecha'] = pd.to_datetime(df_rm_circ['fecha'], format='%d/%m/%Y')
    return df_rm_circ

# %%
df_2024_rm_resp = filter_rm_circ(df_2024)
df_2025_rm_resp = filter_rm_circ(df_2025)

df_rm_circ_combined = pd.concat([df_2024_rm_resp, df_2025_rm_resp])

# Guardar el archivo combinado en un solo CSV
output_path = 'data_atenciones_urgencia/df_rm_circ_2024.csv'
df_rm_circ_combined.to_csv(output_path, index=False)


# %%
