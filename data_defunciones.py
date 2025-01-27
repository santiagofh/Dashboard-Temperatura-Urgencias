#%%
import pandas as pd

#%%
# Leer el archivo CSV
col=["SEXO",
 "DIAG1",
 "REG_RES",
 "DIA_DEF",
 "MES_DEF",
 "ANO_DEF",
 "EDAD_TIPO",
 "EDAD_CANT"
]

df_2024 = pd.read_csv(r'C:\Users\fariass\OneDrive - SUBSECRETARIA DE SALUD PUBLICA\Escritorio\DATA\DEFUNCIONES\DEF2024.csv', sep='|', encoding='LATIN',usecols=col,low_memory=False)
df_2025 = pd.read_csv(r'C:\Users\fariass\OneDrive - SUBSECRETARIA DE SALUD PUBLICA\Escritorio\DATA\DEFUNCIONES\DEF2025.csv', sep='|', encoding='LATIN',usecols=col,low_memory=False)
#%%
# Filtrar los datos para la región 13
filtered_df_2024 = df_2024[df_2024['REG_RES'] == 13]
filtered_df_2025 = df_2025[df_2025['REG_RES'] == 13]
filtered_df = pd.concat([filtered_df_2024, filtered_df_2025])
filtered_df.loc[filtered_df['EDAD_TIPO'].isin([2, 3, 4]), 'EDAD_CANT'] = 0
edad_cant_out_of_range = filtered_df[(filtered_df['EDAD_CANT'] >= 80) | (filtered_df['EDAD_CANT'] <= 0)]
filtered_df['CARDIOVASCULAR'] = filtered_df['DIAG1'].str.startswith('I', na=False)
filtered_df['DATE'] = pd.to_datetime(filtered_df[['ANO_DEF', 'MES_DEF', 'DIA_DEF']].astype(str).agg('-'.join, axis=1), errors='coerce')
filtered_df.to_csv(r'data_defunciones/defunciones_2024.csv', index=False, sep='|', encoding='LATIN')
print("Los datos filtrados y agrupados se han guardado correctamente.")

# %%
