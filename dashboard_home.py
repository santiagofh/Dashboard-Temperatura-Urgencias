import streamlit as st
from datetime import datetime

# Cargar imágenes y logotipos
st.image('img/seremi-100-años.png', width=300)
logo_horizontal = 'img/horizontal_SEREMIRM_blue.png'
logo_icono = 'img/icon_SEREMIRM.png'
st.logo(logo_horizontal, icon_image=logo_icono)

# Función de la página de inicio
def home():
    st.markdown('# Bienvenido a la Plataforma de Monitoreo de temperatura extrema')
    st.write(
        """
        Este dashboar/visor está diseñada para brindar información actualizada sobre **temperaturas extremas** y sus posibles impactos en la salud de la Región Metropolitana.
        
        ### ¿Cómo utilizar?
        
        - **Inicio**: Aquí encuentras una visión general del proyecto.
        - **Temperatura extrema**: Accede a dashboards específicos relacionados con:
            - Alertas de temperatura
            - Atenciones de urgencias
            - Defunciones
            - Egresos hospitalarios
            - Un enlace externo para la sección de Vigilancia
        - **Corredores endemicos**: Visualiza datos combinados para análisis en:
            - Corredor endémico en menores de 1 año
            - Corredor endémico en mayores de 80 años
        
        Utiliza el menú de navegación (ubicado en la parte lateral) para desplazarte entre las diferentes secciones. Cada sección contiene visualizaciones y datos interactivos que permitirán explorar en detalle la información.
        """
    )

# Función para la página del enlace externo
def external_link():
    st.markdown("### Alertas y Atenciones de Urgencias")
    st.write("Haga clic en el siguiente enlace para acceder al dashboard:")
    url = "https://lookerstudio.google.com/u/0/reporting/0307c04c-870f-4a62-83e3-bb015ed63136/page/SSDdE"
    st.markdown(f"[Ir al Dashboard Looker Studio]({url})", unsafe_allow_html=True)

# Definir las páginas
pages = {
    "Inicio": [
        st.Page(home, default=True, title="Página de inicio", icon=":material/home:")
    ],
    "Temperatura extrema": [
        st.Page("dashboard_alertas.py", title="Alertas de temperatura", icon=":material/public:"),
        st.Page("dashboard_atenciones_urgencia.py", title="Atenciones de urgencias", icon=":material/public:"),
        st.Page("dashboard_defunciones.py", title="Defunciones", icon=":material/public:"),
        st.Page("dashboard_egresos.py", title="Egresos Hospitalarios", icon=":material/public:"),
        st.Page(external_link, title="Enlace externo: Vigilancia", icon=":material/link:")
    ],
    "Graficos combinados":[
        st.Page("dashboard_corredor_endemico_menor01.py", title="Corredor endemico menores de 1", icon=":material/public:"),
        st.Page("dashboard_corredor_endemico_mayor80.py", title="Corredor endemico mayores de 80", icon=":material/public:")
    ]
}

# Navegación entre páginas
pg = st.navigation(pages)
pg.run()
