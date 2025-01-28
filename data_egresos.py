#%%
import pandas as pd
#%%
col_list=[
'Seremi',
'NUM_EGR',
'EDAD_CANT',
'TIPO_EDAD',
'COMUNA',
'REGION',
'DIA_ING',
'MES_ING',
'ANO_ING',
'T_DIAG1',
'DIAG1',
]
df_eh = pd.read_csv(r"C:\Users\fariass\OneDrive - SUBSECRETARIA DE SALUD PUBLICA\Escritorio\DATA\EGRESOS_HOSPITALARIOS\EH_2024_preliminar13012025.csv", usecols=col_list,sep=';', encoding='LATIN',low_memory=False)
#%%
df_eh = df_eh.dropna(subset=["DIA_ING", "MES_ING", "ANO_ING"])
df_eh["DIA_ING"] = pd.to_numeric(df_eh["DIA_ING"], errors="coerce").astype("Int64")
df_eh["MES_ING"] = pd.to_numeric(df_eh["MES_ING"], errors="coerce").astype("Int64")
df_eh["ANO_ING"] = pd.to_numeric(df_eh["ANO_ING"], errors="coerce").astype("Int64")
df_eh["date_ingreso"] = pd.to_datetime(
    df_eh[["ANO_ING", "MES_ING", "DIA_ING"]].rename(columns={"ANO_ING": "year", "MES_ING": "month", "DIA_ING": "day"}),
    errors="coerce"
)
df_eh_rm = df_eh[df_eh["COMUNA"].astype(str).str.startswith("13", na=False)]
df_eh_rm['CARDIOVASCULAR'] = df_eh_rm['DIAG1'].str.startswith('I', na=False)
df_eh_rm.loc[df_eh_rm['TIPO_EDAD'].isin([2, 3, 4]), 'EDAD_CANT'] = 0
df_eh_rm['MAYOR_80'] = df_eh_rm['EDAD_CANT'] >= 80
df_eh_rm['MENOR_1'] = df_eh_rm['EDAD_CANT'] < 1
df_eh_rm_2024 = df_eh_rm[df_eh_rm['date_ingreso'] < '2025-01-01']
# %%
df_eh_rm_2024.to_csv(r'data_egresos/eh_2024.csv', index=False, encoding='LATIN')
# %%
