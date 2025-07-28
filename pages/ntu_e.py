import streamlit as st
import numpy as np
from scipy.optimize import root_scalar
import matplotlib.pyplot as plt

# Configuración de la página
st.set_page_config(page_title="Calculadora NTU-ε", layout="wide")
st.title("Calculadora NTU-ε para Intercambiadores de Calor")

# --- Funciones para calcular ε dado NTU ---
def efectividad_paralelo(NTU, C):
    return (1 - np.exp(-NTU * (1 + C))) / (1 + C)

def efectividad_contraflujo(NTU, C):
    if C == 1:
        return NTU / (1 + NTU)
    return (1 - np.exp(-NTU * (1 - C))) / (1 - C * np.exp(-NTU * (1 - C)))

def efectividad_coraza_tubos(NTU, C):
    gamma = NTU * np.sqrt(1 + C**2)
    return 2 / (1 + C + np.sqrt(1 + C**2) * (1 + np.exp(-gamma)) / (1 - np.exp(-gamma)))

def efectividad_cruzado_Cmax_mezclado(NTU, C):
    return (1 / C) * (1 - np.exp(-C * (1 - np.exp(-NTU))))

def efectividad_cruzado_Cmin_mezclado(NTU, C):
    return 1 - np.exp(-(1 / C) * (1 - np.exp(-C * NTU)))

def efectividad_cruzado_no_mezclado(NTU, C):
    # CORRECCIÓN: Paréntesis agregados
    return 1 - np.exp((1/C) * (NTU**0.22) * (np.exp(-C * NTU**0.78) - 1))

def efectividad_C_cero(NTU, _):
    return 1 - np.exp(-NTU)

# --- Funciones para calcular NTU dado ε (usando root_scalar) ---
def resolver_NTU(ecuacion, epsilon, C):
    try:
        sol = root_scalar(
            lambda NTU: ecuacion(NTU, C) - epsilon,
            bracket=[0.001, 100],  # Rango de búsqueda
            method='brentq'
        )
        return sol.root
    except Exception as e:
        st.error(f"Error en cálculo: {str(e)}")
        return None

# Mapeo de funciones
funciones_efectividad = {
    "Flujo paralelo (doble tubo)": efectividad_paralelo,
    "Flujo en contraflujo (doble tubo)": efectividad_contraflujo,
    "Coraza y tubos (1-2, 1-4, ...)": efectividad_coraza_tubos,
    "Flujo cruzado: Cmax mezclado, Cmin no mezclado": efectividad_cruzado_Cmax_mezclado,
    "Flujo cruzado: Cmax no mezclado, Cmin mezclado": efectividad_cruzado_Cmin_mezclado,
    "Flujo cruzado: Ambos no mezclados": efectividad_cruzado_no_mezclado,
    "Caso especial (C=0): Evaporación/Condensación": efectividad_C_cero
}

# --- Interfaz de usuario ---
tipo_intercambiador = st.selectbox(
    "Tipo de intercambiador:",
    options=[
        "Flujo paralelo (doble tubo)",
        "Flujo en contraflujo (doble tubo)",
        "Coraza y tubos (1-2, 1-4, ...)",
        "Flujo cruzado: Cmax mezclado, Cmin no mezclado",
        "Flujo cruzado: Cmax no mezclado, Cmin mezclado",
        "Flujo cruzado: Ambos no mezclados",
        "Caso especial (C=0): Evaporación/Condensación"
    ]
)

calculo = st.radio(
    "Cálculo deseado:",
    options=["Calcular ε (efectividad) dado NTU", "Calcular NTU dado ε (efectividad)"]
)

# Determinar si necesitamos C
necesita_C = tipo_intercambiador != "Caso especial (C=0): Evaporación/Condensación"

if calculo == "Calcular ε (efectividad) dado NTU":
    NTU = st.number_input("NTU", min_value=0.001, max_value=100.0, value=1.0, step=0.1)
    if necesita_C:
        C = st.number_input("C (Cmin/Cmax)", min_value=0.001, max_value=1.0, value=0.5, step=0.01)
    else:
        C = 0.0
    
    if st.button("Calcular ε"):
        funcion = funciones_efectividad[tipo_intercambiador]
        epsilon = funcion(NTU, C)
        st.success(f"## Resultado: ε = {epsilon:.6f}")
        st.metric("Efectividad", f"{epsilon:.4f}")

else:
    epsilon = st.number_input("ε (efectividad)", min_value=0.001, max_value=0.999, value=0.7, step=0.01)
    if necesita_C:
        C = st.number_input("C (Cmin/Cmax)", min_value=0.001, max_value=1.0, value=0.5, step=0.01)
    else:
        C = 0.0
    
    if st.button("Calcular NTU"):
        funcion_efectividad = funciones_efectividad[tipo_intercambiador]
        NTU = resolver_NTU(funcion_efectividad, epsilon, C)
        
        if NTU is not None:
            st.success(f"## Resultado: NTU = {NTU:.6f}")
            st.metric("Número de Unidades de Transferencia", f"{NTU:.4f}")

# --- Gráfico interactivo ---
if st.checkbox("Mostrar curva ε vs NTU"):
    st.subheader(f"Comportamiento para {tipo_intercambiador}")
    
    if necesita_C:
        C_plot = C
    else:
        C_plot = 0.0
    
    funcion_efectividad = funciones_efectividad[tipo_intercambiador]
    
    NTU_values = np.linspace(0.01, 5, 200)
    epsilon_values = [funcion_efectividad(NTU, C_plot) for NTU in NTU_values]
    
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(NTU_values, epsilon_values, 'b-', linewidth=2.5)
    
    # Punto actual si está calculado
    if 'NTU' in locals() and 'epsilon' in locals():
        ax.plot(NTU, epsilon, 'ro', markersize=8)
    
    ax.set_xlabel('NTU', fontsize=12)
    ax.set_ylabel('ε (Efectividad)', fontsize=12)
    ax.set_title(f'Curva ε vs NTU (C = {C_plot:.3f})', fontsize=14)
    ax.grid(True, alpha=0.3)
    ax.set_xlim([0, 5])
    ax.set_ylim([0, 1])
    
    st.pyplot(fig)

# --- Explicación de parámetros ---
st.divider()
with st.expander("📖 Explicación de parámetros"):
    st.markdown("""
    - **NTU (Número de Unidades de Transferencia):**  
      \( NTU = \frac{UA}{C_{\text{min}}} \)  
      *Indica el tamaño del intercambiador*
    
    - **C (Relación de capacidades):**  
      \( C = \frac{C_{\text{min}}}{C_{\text{max}}} \)  
      *Siempre 0 ≤ C ≤ 1*
    
    - **ε (Efectividad):**  
      \( \varepsilon = \frac{Q_{\text{real}}}{Q_{\text{máximo}}} \)  
      *0 ≤ ε ≤ 1 (Eficiencia térmica)*
    """)