import streamlit as st

# Configuración básica de la página
st.set_page_config(
    page_title="Mausquerramienta",
    page_icon="🔥",
    layout="wide"
)

# Título principal
st.title("Mausquerramienta")
st.markdown("""
    **Seleccione un módulo de la barra lateral** para acceder a las herramientas especializadas.
""")

# Mensaje instructivo (solo visible en main.py)
st.sidebar.markdown("""
# Módulos Disponibles
Navegue a las herramientas desde esta barra:
""")

# Redirección automática a la primera página (opcional)
if st.sidebar.button("🏠 Página Principal"):
    st.switch_page("main.py")

# Footer
st.divider()
st.markdown("""
🔧 *Desarrollado por [15] - v1.0*  
📚 *Herramientas para análisis térmico*
""")