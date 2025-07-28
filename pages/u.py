import streamlit as st
import pandas as pd
import numpy as np
from math import pi
from scipy.interpolate import interp1d

# --- Configuración de la página ---
st.set_page_config(page_title="Cálculo Coeficiente Global", layout="wide")
st.title("Cálculo del Coeficiente Global de Transferencia de Calor")

# --- Conversión de unidades ---
def convertir_longitud(valor, unidad):
    factores = {"m": 1, "mm": 0.001, "cm": 0.01, "ft": 0.3048, "in": 0.0254}
    return valor * factores[unidad]

# --- Función para obtener Nu externo ---
def obtener_nu_externo(Di_Do):
    datos = {
        'Di_Do': [0.00, 0.05, 0.10, 0.25, 0.50, 1.00],
        'Nui': [np.nan, 17.46, 11.56, 7.37, 5.74, 4.86]
    }
    f_nui = interp1d(datos['Di_Do'][1:], datos['Nui'][1:], kind='linear', fill_value='extrapolate')
    return float(f_nui(Di_Do)) if Di_Do > 0 else np.nan

# --- Carga de datos con manejo de fases ---
@st.cache_data
def cargar_datos():
    archivos = {
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
    
    data = {}
    for nombre, archivo in archivos.items():
        try:
            df = pd.read_csv(archivo)
            
            # Renombrar columnas para consistencia
            df.columns = df.columns.str.strip()
            data[nombre] = df
            
        except Exception as e:
            st.error(f"Error cargando {archivo}: {str(e)}")
            data[nombre] = None
    return data

# --- Interpolación de propiedades con manejo de fases ---
def interpolar_propiedades(df, T_pelicula, fluido, fase=None):
    try:
        # Fluidos con fases (tablas A9-A12)
        if fluido in ["agua saturada", "refrigerante 134a", "amoniaco", "propano"]:
            if fase == "líquido":
                return {
                    'densidad': np.interp(T_pelicula, df['Temp. (°C)'], df['Densidad líquido (kg/m³)']),
                    'viscosidad': np.interp(T_pelicula, df['Temp. (°C)'], df['Viscosidad dinámica líquido (kg/m·s)']),
                    'k': np.interp(T_pelicula, df['Temp. (°C)'], df['Conductividad térmica líquido (W/m·K)']),
                    'Pr': np.interp(T_pelicula, df['Temp. (°C)'], df['Número de Prandtl líquido'])
                }
            elif fase == "vapor":
                return {
                    'densidad': np.interp(T_pelicula, df['Temp. (°C)'], df['Densidad vapor (kg/m³)']),
                    'viscosidad': np.interp(T_pelicula, df['Temp. (°C)'], df['Viscosidad dinámica vapor (kg/m·s)']),
                    'k': np.interp(T_pelicula, df['Temp. (°C)'], df['Conductividad térmica vapor (W/m·K)']),
                    'Pr': np.interp(T_pelicula, df['Temp. (°C)'], df['Número de Prandtl vapor'])
                }
        
        # Fluidos sin fases (tablas restantes)
        else:
            # Manejar diferentes nombres de columnas en tablas sin fases
            densidad_col = 'Densidad (kg/m³)' if 'Densidad (kg/m³)' in df.columns else 'Densidad'
            viscosidad_col = 'Viscosidad dinámica (kg/m·s)' if 'Viscosidad dinámica (kg/m·s)' in df.columns else 'Viscosidad'
            k_col = 'Conductividad térmica (W/m·K)' if 'Conductividad térmica (W/m·K)' in df.columns else 'Conductividad'
            pr_col = 'Número de Prandtl' if 'Número de Prandtl' in df.columns else 'Prandtl'
            
            return {
                'densidad': np.interp(T_pelicula, df['Temp. (°C)'], df[densidad_col]),
                'viscosidad': np.interp(T_pelicula, df['Temp. (°C)'], df[viscosidad_col]),
                'k': np.interp(T_pelicula, df['Temp. (°C)'], df[k_col]),
                'Pr': np.interp(T_pelicula, df['Temp. (°C)'], df[pr_col])
            }
            
    except Exception as e:
        st.error(f"Error interpolando propiedades: {str(e)}")
        return None

# --- Interfaz principal ---
with st.sidebar:
    st.header("⚙️ Configuración")
    unidad_dia = st.selectbox("Unidad de diámetros", ["m", "mm", "cm", "in"])
    k_pared = st.number_input("Conductividad pared (W/m·K)", value=50.0)
    espesor = st.number_input("Espesor pared (mm)", value=5.0) / 1000
    n_prandtl = st.selectbox("Exponente n para Prandtl (Dittus-Boelter)", [0.4, 0.3], format_func=lambda x: f"{x} (calentamiento)" if x==0.4 else f"{x} (enfriamiento)")

# --- Sección de parámetros geométricos ---
st.header("1. Parámetros Geométricos")
col1, col2 = st.columns(2)
with col1:
    diametro_int = st.number_input(f"Diámetro interno del tubo ({unidad_dia})", value=0.05)
with col2:
    diametro_ext = st.number_input(f"Diámetro de la carcasa ({unidad_dia})", value=0.10)

# Conversión de unidades
diametro_int = convertir_longitud(diametro_int, unidad_dia)
diametro_ext = convertir_longitud(diametro_ext, unidad_dia)
Di_Do_ratio = diametro_int / diametro_ext

# --- Sección de fluidos y propiedades ---
fluidos = cargar_datos()
fluidos_con_fases = ["agua saturada", "refrigerante 134a", "amoniaco", "propano"]

st.header("2. Propiedades de los Fluidos")

# Fluido interno
st.subheader("Fluido Interno (tubo)")
col3, col4 = st.columns(2)
with col3:
    fluido_int = st.selectbox("Fluido interno", list(fluidos.keys()))
    if fluido_int in fluidos_con_fases:
        fase_int = st.radio("Fase fluido interno", ["líquido", "vapor"], horizontal=True)
with col4:
    T_prom_int = st.number_input("Temperatura promedio fluido interno (°C)", value=50.0)
    velocidad = st.number_input("Velocidad fluido interno (m/s)", value=1.0)

# Fluido externo
st.subheader("Fluido Externo (carcasa)")
col5, col6 = st.columns(2)
with col5:
    fluido_ext = st.selectbox("Fluido externo", list(fluidos.keys()))
    if fluido_ext in fluidos_con_fases:
        fase_ext = st.radio("Fase fluido externo", ["líquido", "vapor"], horizontal=True)
with col6:
    T_prom_ext = st.number_input("Temperatura promedio fluido externo (°C)", value=80.0)

# --- Cálculos ---
try:
    # Validación de datos
    if fluidos[fluido_int] is None or fluidos[fluido_ext] is None:
        st.error("No se pueden cargar los datos de los fluidos seleccionados")
        st.stop()

    # Propiedades fluido interno
    props_int = interpolar_propiedades(fluidos[fluido_int], T_prom_int, fluido_int, 
                                     fase_int if fluido_int in fluidos_con_fases else None)
    
    # Propiedades fluido externo
    props_ext = interpolar_propiedades(fluidos[fluido_ext], T_prom_ext, fluido_ext, 
                                     fase_ext if fluido_ext in fluidos_con_fases else None)

    if props_int is None or props_ext is None:
        st.error("Error al obtener propiedades termofísicas")
        st.stop()

    # --- Cálculo de h interno ---
    st.header("3. Coeficiente de Transferencia Interno")
    Re = (velocidad * diametro_int * props_int['densidad']) / props_int['viscosidad']
    st.write(f"Número de Reynolds: {Re:.2f}")
    
    # Determinar régimen de flujo
    if Re < 2300:
        Nu = 3.66  # Flujo laminar completamente desarrollado
        st.write("Régimen: Laminar (Nu = 3.66)")
    else:
        Nu = 0.023 * (Re**0.8) * (props_int['Pr']**n_prandtl)  # Dittus-Boelter con n elegido por usuario
        st.write(f"Régimen: Turbulento (correlación Dittus-Boelter, n={n_prandtl})")
    
    h_int = Nu * props_int['k'] / diametro_int
    st.success(f"**Coeficiente interno (h_int): {h_int:.2f} W/m²K**")

    # --- Cálculo de h externo ---
    st.header("4. Coeficiente de Transferencia Externo")
    Nu_ext = obtener_nu_externo(Di_Do_ratio)
    
    if not np.isnan(Nu_ext):
        h_ext = Nu_ext * props_ext['k'] / (diametro_ext - diametro_int)
        st.success(f"**Coeficiente externo (h_ext): {h_ext:.2f} W/m²K**")
        
        # --- Cálculo del coeficiente global ---
        st.header("5. Coeficiente Global de Transferencia de Calor")
        R_total = (1/h_int) + (1/h_ext)
        U = 1 / R_total
        
        st.latex(r"\frac{1}{U} = \frac{1}{h_{interno}} + \frac{1}{h_{externo}}")
        st.latex(rf"\frac{{1}}{{U}} = \frac{{1}}{{{h_int:.2f}}} + \frac{{1}}{{{h_ext:.2f}}}")
        st.success(f"**Coeficiente global (U): {U:.2f} W/m²K**")
        
    else:
        st.error("No se puede calcular h_externo para la relación Di/Do ingresada")

except Exception as e:
    st.error(f"Error en los cálculos: {str(e)}")