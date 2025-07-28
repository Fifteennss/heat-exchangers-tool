import streamlit as st
import numpy as np
import pandas as pd
from scipy.interpolate import interp1d

# Configuración de página
st.set_page_config(page_title="Intercambiadores de Calor - Propiedades Termodinámicas", layout="wide")
st.title("Intercambiadores de Calor - Calculadora Dinámica")

# Diccionario de archivos (debes tener estos CSV en tu directorio)
ARCHIVOS_PROPIEDADES = {
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

def cargar_propiedades(fluido, fase, temp_promedio):
    """Carga propiedades del fluido desde CSV y aplica interpolación"""
    try:
        df = pd.read_csv(ARCHIVOS_PROPIEDADES[fluido])
        
        if fluido in ["agua saturada", "refrigerante 134a", "amoniaco", "propano"]:
            if fase == "líquido":
                col_cp = "Calor específico líquido (J/kg·K)"
            else:
                col_cp = "Calor específico vapor (J/kg·K)"
        else:  # Para fluidos con una sola fase
            col_cp = "Calor específico (J/kg·K)"
        
        # Interpolación lineal
        interpolador = interp1d(df["Temp. (°C)"], df[col_cp], bounds_error=False, fill_value="extrapolate")
        cp = float(interpolador(temp_promedio))
        
        return cp
    except Exception as e:
        st.error(f"Error al cargar propiedades: {str(e)}")
        return None

def propiedades_fluido(fluido_nombre, fase, T_in, T_out, key_suffix):
    """Interfaz para selección de propiedades de fluido"""
    temp_promedio = (T_in + T_out) / 2
    
    col1, col2 = st.columns(2)
    with col1:
        opcion_cp = st.radio(
            f"Calor específico para {fluido_nombre}",
            ["Introducir manualmente", "Calcular automáticamente"],
            key=f"cp_opcion_{key_suffix}"
        )
    
    with col2:
        if opcion_cp == "Introducir manualmente":
            cp = st.number_input(
                f"Calor específico {fluido_nombre} (J/kg·K)",
                min_value=100.0,
                value=4186.0,
                key=f"cp_manual_{key_suffix}"
            )
        else:
            fluido = st.selectbox(
                f"Seleccionar fluido {fluido_nombre}",
                options=list(ARCHIVOS_PROPIEDADES.keys()),
                key=f"fluido_select_{key_suffix}"
            )
            
            if fluido in ["agua saturada", "refrigerante 134a", "amoniaco", "propano"]:
                fase = st.radio(
                    f"Fase para {fluido_nombre}",
                    ["líquido", "vapor"],
                    key=f"fase_{key_suffix}"
                )
            
            cp = cargar_propiedades(fluido, fase, temp_promedio)
            if cp is not None:
                st.info(f"Calor específico calculado: {cp:.2f} J/kg·K a {temp_promedio:.1f}°C")
    
    return cp

# Selección del parámetro a calcular
parametro = st.selectbox(
    "¿Qué desea calcular?",
    [
        "Carga térmica (Q)",
        "LMTD",
        "Temperatura de salida",
        "Eficacia (ε)",
        "Razón de capacidades (c)",
        "R y P"
    ]
)

# Entradas y cálculos según el parámetro seleccionado
if parametro == "Carga térmica (Q)":
    st.header("Datos necesarios para Q")
    m = st.number_input("Flujo másico (kg/s)", min_value=0.01, value=1.0)
    cp = st.number_input("Calor específico (J/kg·K)", min_value=100.0, value=4186.0)
    T_in = st.number_input("Temperatura de entrada (°C)", value=90.0)
    T_out = st.number_input("Temperatura de salida (°C)", value=60.0)
    if st.button("Calcular Q"):
        Q = m * cp * (T_in - T_out)
        st.success(f"Carga térmica (Q): {Q/1000:.2f} kW")

elif parametro == "LMTD":
    st.header("Datos necesarios para LMTD")
    T_hot_in = st.number_input("Temperatura entrada fluido caliente (°C)", value=90.0)
    T_hot_out = st.number_input("Temperatura salida fluido caliente (°C)", value=60.0)
    T_cold_in = st.number_input("Temperatura entrada fluido frío (°C)", value=20.0)
    T_cold_out = st.number_input("Temperatura salida fluido frío (°C)", value=50.0)
    if st.button("Calcular LMTD"):
        delta_T1 = T_hot_in - T_cold_out
        delta_T2 = T_hot_out - T_cold_in
        LMTD = (delta_T1 - delta_T2) / np.log(delta_T1 / delta_T2) if delta_T1 != delta_T2 else delta_T1
        st.success(f"LMTD: {LMTD:.2f} °C")

elif parametro == "Temperatura de salida":
    st.header("Datos necesarios para temperatura de salida")
    tipo = st.radio("¿Qué temperatura de salida desea calcular?", ["Fluido caliente", "Fluido frío"])
    m_hot = st.number_input("Flujo másico caliente (kg/s)", min_value=0.01, value=1.0)
    cp_hot = st.number_input("Calor específico caliente (J/kg·K)", min_value=100.0, value=4186.0)
    m_cold = st.number_input("Flujo másico frío (kg/s)", min_value=0.01, value=1.0)
    cp_cold = st.number_input("Calor específico frío (J/kg·K)", min_value=100.0, value=4186.0)
    T_hot_in = st.number_input("Temperatura entrada caliente (°C)", value=90.0)
    T_cold_in = st.number_input("Temperatura entrada fría (°C)", value=20.0)
    # El usuario ingresa la temperatura de salida del otro fluido
    if tipo == "Fluido caliente":
        T_cold_out = st.number_input("Temperatura salida fluido frío (°C)", value=50.0)
        if st.button("Calcular T_hot_out"):
            # Igualar Q_hot = Q_cold
            # m_hot * cp_hot * (T_hot_in - T_hot_out) = m_cold * cp_cold * (T_cold_out - T_cold_in)
            T_hot_out = T_hot_in - (m_cold * cp_cold * (T_cold_out - T_cold_in)) / (m_hot * cp_hot)
            st.success(f"Temperatura de salida fluido caliente: {T_hot_out:.2f} °C")
    else:
        T_hot_out = st.number_input("Temperatura salida fluido caliente (°C)", value=60.0)
        if st.button("Calcular T_cold_out"):
            # Igualar Q_hot = Q_cold
            # m_hot * cp_hot * (T_hot_in - T_hot_out) = m_cold * cp_cold * (T_cold_out - T_cold_in)
            T_cold_out = T_cold_in + (m_hot * cp_hot * (T_hot_in - T_hot_out)) / (m_cold * cp_cold)
            st.success(f"Temperatura de salida fluido frío: {T_cold_out:.2f} °C")

elif parametro == "Eficacia (ε)":
    st.header("Datos necesarios para eficacia")
    Q = st.number_input("Carga térmica real (Q) [W]", value=100000.0)
    m_hot = st.number_input("Flujo másico caliente (kg/s)", min_value=0.01, value=1.0)
    cp_hot = st.number_input("Calor específico caliente (J/kg·K)", min_value=100.0, value=4186.0)
    m_cold = st.number_input("Flujo másico frío (kg/s)", min_value=0.01, value=1.0)
    cp_cold = st.number_input("Calor específico frío (J/kg·K)", min_value=100.0, value=4186.0)
    T_hot_in = st.number_input("Temperatura entrada caliente (°C)", value=90.0)
    T_cold_in = st.number_input("Temperatura entrada fría (°C)", value=20.0)
    if st.button("Calcular eficacia"):
        c_hot = m_hot * cp_hot
        c_cold = m_cold * cp_cold
        cmin = min(c_hot, c_cold)
        qmax = cmin * (T_hot_in - T_cold_in)
        e = Q / qmax if qmax != 0 else np.nan
        st.success(f"Eficacia (ε): {e:.3f}")

elif parametro == "Razón de capacidades (c)":
    st.header("Datos necesarios para razón de capacidades")
    m_hot = st.number_input("Flujo másico caliente (kg/s)", min_value=0.01, value=1.0)
    cp_hot = st.number_input("Calor específico caliente (J/kg·K)", min_value=100.0, value=4186.0)
    m_cold = st.number_input("Flujo másico frío (kg/s)", min_value=0.01, value=1.0)
    cp_cold = st.number_input("Calor específico frío (J/kg·K)", min_value=100.0, value=4186.0)
    if st.button("Calcular razón de capacidades"):
        c_hot = m_hot * cp_hot
        c_cold = m_cold * cp_cold
        cmin = min(c_hot, c_cold)
        cmax = max(c_hot, c_cold)
        c = cmin / cmax if cmax != 0 else np.nan
        st.success(f"Razón de capacidades (c): {c:.3f}")

elif parametro == "R y P":
    st.header("Datos necesarios para R y P")
    T_hot_in = st.number_input("Temperatura entrada caliente (°C)", value=90.0)
    T_hot_out = st.number_input("Temperatura salida caliente (°C)", value=60.0)
    T_cold_in = st.number_input("Temperatura entrada fría (°C)", value=20.0)
    T_cold_out = st.number_input("Temperatura salida fría (°C)", value=50.0)
    if st.button("Calcular R y P"):
        R = (T_hot_in - T_hot_out) / (T_cold_out - T_cold_in) if (T_cold_out - T_cold_in) != 0 else np.nan
        P = (T_cold_out - T_cold_in) / (T_hot_in - T_cold_in) if (T_hot_in - T_cold_in) != 0 else np.nan
        st.success(f"R: {R:.3f}")
        st.success(f"P: {P:.3f}")