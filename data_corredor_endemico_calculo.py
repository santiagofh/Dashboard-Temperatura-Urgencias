# %% Cargar y procesar datos
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

df_historico = pd.read_csv("data_corredor_endemico/defunciones_historicas_2018_2023.csv")
df_2024 = pd.read_csv("data_defunciones/defunciones_2024.csv", sep="|")

# Asegurarse de que las fechas estén en formato datetime
df_historico['Fechadef'] = pd.to_datetime(df_historico['Fechadef'], errors='coerce')
df_2024['DATE'] = pd.to_datetime(df_2024['DATE'], errors='coerce')

# Crear rangos de edad
bins = [-1, 0, 79, float('inf')]
labels = ['Menor 1 año', '1 a 79', '80 y mas']
df_2024['Edad_Rango'] = pd.cut(df_2024['EDAD_CANT'], bins=bins, labels=labels)

# Agrupar defunciones por fecha y rango de edad
conteo_por_fecha = df_2024.groupby(['DATE', 'Edad_Rango']).size().unstack(fill_value=0)

# Asegurarse de que las fechas coincidan
conteo_por_fecha.reset_index(inplace=True)
conteo_por_fecha.rename(columns={'DATE': 'Fechadef'}, inplace=True)

# Guardar el DataFrame actualizado
conteo_por_fecha.to_csv("data_corredor_endemico/defunciones_historicas_2024.csv", index=False)

col = ['Fechadef', 'Menor 1 año', '1 a 79', '80 y mas']
df_historico_hoy = pd.concat([df_historico[col], conteo_por_fecha[col]])
df_historico_hoy.to_csv("data_corredor_endemico/defunciones_historicas_hoy.csv", index=False)

# %% Funciones para cálculo del corredor endémico
def load_and_process_data(file_path):
    data = pd.read_csv(file_path)
    data['Fechadef'] = pd.to_datetime(data['Fechadef'])
    data = data[((data['Fechadef'].dt.month >= 11) | (data['Fechadef'].dt.month <= 3))]
    return data

def calculate_daily_rates(data, population_mapping):
    def get_population(date):
        year = date.year
        if date.month >= 11:
            start_year = year
            end_year = year + 1
        else:
            start_year = year - 1
            end_year = year
        return population_mapping.get((start_year, end_year), None)

    data['Poblacion'] = data['Fechadef'].apply(get_population)
    data['Tasa'] = (data['80 y mas'] / data['Poblacion']) * 100000 + 1
    return data

def create_graph(data):
    plt.figure(figsize=(12, 6))
    plt.plot(data['Fechadef'], data['IC_Inf_Casos'], label='Zona de Éxito', linestyle='--', color='green')
    plt.plot(data['Fechadef'], data['Media_Casos'], label='Zona de Seguridad', linestyle='-', color='blue')
    plt.plot(data['Fechadef'], data['IC_Sup_Casos'], label='Zona de Alerta', linestyle='--', color='red')
    plt.fill_between(data['Fechadef'], data['IC_Inf_Casos'], data['Media_Casos'], color='green', alpha=0.1)
    plt.fill_between(data['Fechadef'], data['Media_Casos'], data['IC_Sup_Casos'], color='red', alpha=0.1)
    plt.xlabel('Fecha')
    plt.ylabel('Casos')
    plt.title('Corredor Endémico: Personas de 80 años y más')
    plt.legend()
    plt.grid(True)
    plt.show()

# %% Calcular corredor endémico hasta 2023-2024
population_mapping = {
    (2017, 2018): 194610,
    (2018, 2019): 200661,
    (2019, 2021): 213649,
    (2021, 2022): 220388,
    (2022, 2023): 227450,
    (2023, 2024): 234985,
    (2024, 2025): 243337,
}

processed_data = calculate_daily_rates(df_historico_hoy, population_mapping)
#%%

fecha_inicio = pd.Timestamp('2018-01-01')
fecha_fin = pd.Timestamp('2024-03-31')
filtered_data = processed_data[
    (processed_data['Fechadef'] >= fecha_inicio) &
    (processed_data['Fechadef'] <= fecha_fin) &
    (processed_data['Fechadef'].dt.year != 2020)
]
filtered_data['Dia_Mes'] = filtered_data['Fechadef'].dt.strftime('%d-%b')
filtered_data['Mes'] = filtered_data['Fechadef'].dt.month
filtered_data['Dia'] = filtered_data['Fechadef'].dt.day

# Aplicar logaritmo a las defunciones
filtered_data['Ln_80ymas'] = np.log(filtered_data['80 y mas'].replace(0, np.nan))

# Agrupar por día-mes y calcular estadísticas
stats = filtered_data.groupby(['Dia','Mes'])['Ln_80ymas'].agg(
    Ln_Media='mean',
    Ln_DE='std'
).reset_index()
stats=stats.loc[(stats.Mes>=11) & (stats.Mes>=3)]
# %%
