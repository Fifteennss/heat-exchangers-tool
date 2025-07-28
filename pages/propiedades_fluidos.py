import streamlit as st
import pandas as pd
import numpy as np

# Configuración de la página
st.set_page_config(
    page_title="Propiedades de Fluidos",
    page_icon="💧",
    layout="wide"
)

# Diccionario de fluidos disponibles
FLUIDOS = {
    "agua saturada": "tabla_a9.csv",
    "refrigerante 134a": "tabla_a10.csv",
    "amoniaco": "tabla_a11.csv",
    "propano": "tabla_a12.csv",
    "aire": "tabla_a15.csv",
    "glicerina": "tabla_glicerina.csv",
    "isobutano": "tabla_isobutano.csv",
    "metano": "tabla_metano.csv",
    "metanol": "tabla_metanol.csv",
    "aceite para motor": "tabla_aceitemotor.csv"
}

FLUIDOS_CON_FASES = ["agua saturada", "refrigerante 134a", "amoniaco", "propano"]

# Función de interpolación
def interpolar(x, y, valor):
    return np.interp(valor, x, y)

def mostrar_propiedades_fluido():
    st.title("📊 Consulta de Propiedades de Fluidos")
    st.markdown("""
    Esta herramienta permite consultar las propiedades termofísicas de diversos fluidos 
    a diferentes temperaturas y condiciones.
    """)
    
    with st.sidebar:
        st.header("Parámetros de Entrada")
        
        # Selección de fluido
        fluido = st.selectbox(
            "Seleccione el fluido:",
            options=list(FLUIDOS.keys()),
            index=0
        )
        
        # Selección de estado si aplica
        estado = None
        if fluido in FLUIDOS_CON_FASES:
            estado = st.radio(
                "Estado del fluido:",
                ["líquido", "vapor"],
                horizontal=True
            )
        
        # Ingreso de temperatura
        col1, col2 = st.columns(2)
        with col1:
            temp = st.number_input(
                "Temperatura:",
                min_value=-273.15,
                max_value=2000.0,
                value=25.0,
                step=0.1
            )
        with col2:
            unidad_temp = st.selectbox(
                "Unidad:",
                ["°C", "°F", "K", "R"],
                index=0
            )
        
        # Para aire, preguntar por presión
        presion_kpa = 101.325  # Valor por defecto (1 atm)
        if fluido == "aire":
            if st.checkbox("Especificar presión diferente a 1 atm"):
                presion_kpa = st.number_input(
                    "Presión del aire (kPa):",
                    min_value=0.01,
                    value=101.325,
                    step=1.0
                )
    
    # Convertir temperatura a °C
    if unidad_temp == "°F":
        temp_c = (temp - 32) * 5/9
    elif unidad_temp == "K":
        temp_c = temp - 273.15
    elif unidad_temp == "R":
        temp_c = (temp - 491.67) * 5/9
    else:
        temp_c = temp
    
    # Cargar la tabla del fluido
    try:
        tabla = pd.read_csv(FLUIDOS[fluido])
    except FileNotFoundError:
        st.error(f"Error: No se encontró el archivo {FLUIDOS[fluido]}")
        st.info("Asegúrese de que el archivo CSV esté en el mismo directorio que este script.")
        return
    
    # Obtener propiedades
    T_col = "Temp. (°C)"
    
    if fluido in FLUIDOS_CON_FASES:
        if estado == "líquido":
            props = {
                "Temperatura (°C)": temp_c,
                "Viscosidad dinámica (kg/m·s)": interpolar(tabla[T_col], tabla["Viscosidad dinámica líquido (kg/m·s)"], temp_c),
                "Conductividad térmica (W/m·K)": interpolar(tabla[T_col], tabla["Conductividad térmica líquido (W/m·K)"], temp_c),
                "Densidad (kg/m³)": interpolar(tabla[T_col], tabla["Densidad líquido (kg/m³)"], temp_c),
                "Calor específico (J/kg·K)": interpolar(tabla[T_col], tabla["Calor específico líquido (J/kg·K)"], temp_c),
                "Número de Prandtl": interpolar(tabla[T_col], tabla["Número de Prandtl líquido"], temp_c)
            }
        else:
            props = {
                "Temperatura (°C)": temp_c,
                "Viscosidad dinámica (kg/m·s)": interpolar(tabla[T_col], tabla["Viscosidad dinámica vapor (kg/m·s)"], temp_c),
                "Conductividad térmica (W/m·K)": interpolar(tabla[T_col], tabla["Conductividad térmica vapor (W/m·K)"], temp_c),
                "Densidad (kg/m³)": interpolar(tabla[T_col], tabla["Densidad vapor (kg/m³)"], temp_c),
                "Calor específico (J/kg·K)": interpolar(tabla[T_col], tabla["Calor específico vapor (J/kg·K)"], temp_c),
                "Número de Prandtl": interpolar(tabla[T_col], tabla["Número de Prandtl vapor"], temp_c)
            }
    else:
        props = {
            "Temperatura (°C)": temp_c,
            "Viscosidad dinámica (kg/m·s)": interpolar(tabla[T_col], tabla["Viscosidad dinámica (kg/m·s)"], temp_c),
            "Conductividad térmica (W/m·K)": interpolar(tabla[T_col], tabla["Conductividad térmica (W/m·K)"], temp_c),
            "Densidad (kg/m³)": interpolar(tabla[T_col], tabla["Densidad (kg/m³)"], temp_c),
            "Calor específico (J/kg·K)": interpolar(tabla[T_col], tabla["Calor específico (J/kg·K)"], temp_c),
            "Número de Prandtl": interpolar(tabla[T_col], tabla["Número de Prandtl"], temp_c)
        }
        
        # Ajuste para aire a diferente presión
        if fluido == "aire" and presion_kpa != 101.325:
            props["Viscosidad cinemática (m²/s)"] = interpolar(tabla[T_col], tabla["Viscosidad cinemática (m²/s)"], temp_c)
            props["Viscosidad cinemática (m²/s)"] = props["Viscosidad cinemática (m²/s)"] * 101.325 / presion_kpa
            props["Densidad (kg/m³)"] = props["Densidad (kg/m³)"] * presion_kpa / 101.325
    
    # Mostrar resultados
    st.subheader(f"Propiedades del {fluido}{f' ({estado})' if estado else ''}")
    st.caption(f"Temperatura: {temp_c:.2f} °C | {temp:.2f} {unidad_temp}")
    if fluido == "aire" and presion_kpa != 101.325:
        st.caption(f"Presión: {presion_kpa:.2f} kPa ({presion_kpa/101.325:.2f} atm)")
    
    # Mostrar propiedades en columnas
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Temperatura", f"{temp_c:.2f} °C")
        st.metric("Densidad", f"{props['Densidad (kg/m³)']:.4f} kg/m³")
        st.metric("Calor específico", f"{props['Calor específico (J/kg·K)']:.2f} J/kg·K")
    
    with col2:
        st.metric("Viscosidad dinámica", f"{props['Viscosidad dinámica (kg/m·s)']:.4g} kg/m·s")
        st.metric("Conductividad térmica", f"{props['Conductividad térmica (W/m·K)']:.4f} W/m·K")
        st.metric("Número de Prandtl", f"{props['Número de Prandtl']:.4f}")
    
    if fluido == "aire" and presion_kpa != 101.325:
        st.metric("Viscosidad cinemática", f"{props['Viscosidad cinemática (m²/s)']:.4g} m²/s")
    
    # Mostrar tabla completa de propiedades
    with st.expander("Ver datos completos"):
        st.dataframe(
            pd.DataFrame.from_dict(props, orient='index', columns=['Valor']),
            use_container_width=True
        )

# Ejecutar la aplicación
if __name__ == "__main__":
    mostrar_propiedades_fluido()