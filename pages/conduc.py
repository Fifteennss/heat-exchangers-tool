import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Wedge

# --- Configuración inicial
st.set_page_config(layout="wide")

# --- Funciones de conversión de unidades
def convertir_longitud(valor, unidad_entrada):
    factores = {"m": 1.0, "cm": 0.01, "mm": 0.001, "in": 0.0254, "ft": 0.3048}
    return valor * factores[unidad_entrada]

def convertir_area(valor, unidad_entrada):
    factores = {"m²": 1.0, "cm²": 0.0001, "mm²": 1e-6, "ft²": 0.092903, "in²": 0.00064516}
    return valor * factores[unidad_entrada]

def convertir_temperatura(valor, unidad_entrada):
    if unidad_entrada == "°F": return (valor - 32) * 5/9
    elif unidad_entrada == "K": return valor - 273.15
    return valor

def convertir_k(valor, unidad_entrada):
    factores = {"W/m·K": 1.0, "W/cm·K": 100, "W/mm·K": 1000, "BTU/(h·ft·°F)": 1.73073}
    return valor * factores[unidad_entrada]

def convertir_h(valor, unidad_entrada):
    factores = {"W/m²·K": 1.0, "W/cm²·K": 10000, "BTU/(h·ft²·°F)": 5.67826}
    return valor * factores[unidad_entrada]

def formatear_resultado(valor, unidad_salida, tipo):
    if tipo == "flujo":
        factores = {"W": 1.0, "BTU/h": 3.41214, "kcal/h": 0.859845}
        return valor * factores[unidad_salida]
    elif tipo == "flujo_area":
        factores = {"W/m²": 1.0, "BTU/(h·ft²)": 0.316998, "kcal/(h·m²)": 0.859845}
        return valor * factores[unidad_salida]

@st.cache_data
def cargar_materiales(csv_path):
    return pd.read_csv(csv_path)

def generar_color(i):
    colores_base = [
        "#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd",
        "#8c564b", "#e377c2", "#7f7f7f", "#bcbd22", "#17becf"
    ]
    return colores_base[i % len(colores_base)]

def dibujar_anillos_radiales(radios):
    fig, ax = plt.subplots()
    for i, (r_i, r_o, mat) in enumerate(radios):
        wedge = Wedge((0, 0), r_o, 0, 360, width=r_o - r_i, facecolor=generar_color(i), edgecolor='k')
        ax.add_patch(wedge)
        ax.text(0, r_i + (r_o - r_i)/2, mat, ha='center', va='center', fontsize=8, color='white')
    ax.set_aspect('equal')
    ax.set_xlim(-radios[-1][1], radios[-1][1])
    ax.set_ylim(-radios[-1][1], radios[-1][1])
    ax.axis('off')
    ax.set_title("Visualización de Sección Circular (Radial)")
    st.pyplot(fig)

def dibujar_capas_rectangulares(capas, unidad_longitud):
    fig, ax = plt.subplots(figsize=(8, 2))
    ancho_total = sum(c['L'] for c in capas)
    inicio = 0
    factor_visual = {"m": 1.0, "cm": 100, "mm": 1000, "in": 39.3701, "ft": 3.28084}[unidad_longitud]

    for i, capa in enumerate(capas):
        ancho_visual = capa['L'] * factor_visual
        ax.barh(0, ancho_visual, left=inicio, height=0.5, label=capa['material'], color=generar_color(i), edgecolor='k')
        ax.text(inicio + ancho_visual / 2, 0, f"{capa['material']}\n{ancho_visual:.2f} {unidad_longitud}", ha='center', va='center', fontsize=9, color='white')
        inicio += ancho_visual

    ax.set_xlim(0, inicio)
    ax.axis('off')
    ax.set_title(f"Visualización de Capas (Unidad: {unidad_longitud})")
    st.pyplot(fig)

# --- Sidebar
st.sidebar.title("Configuración de Unidades")
geometria = st.sidebar.selectbox("Geometría", ["Plana", "Cilíndrica", "Esférica"])
unidad_longitud = st.sidebar.selectbox("Unidad de longitud", ["m", "cm", "mm", "in", "ft"])
unidad_area = st.sidebar.selectbox("Unidad de área", ["m²", "cm²", "mm²", "ft²", "in²"])
unidad_temp = st.sidebar.selectbox("Unidad de temperatura", ["°C", "°F", "K"])
unidad_k = st.sidebar.selectbox("Unidad de conductividad (k)", ["W/m·K", "W/cm·K", "W/mm·K", "BTU/(h·ft·°F)"])
unidad_h = st.sidebar.selectbox("Unidad de coeficiente convección (h)", ["W/m²·K", "W/cm²·K", "BTU/(h·ft²·°F)"])
unidad_flujo = st.sidebar.selectbox("Unidad de flujo de calor", ["W", "BTU/h", "kcal/h"])
unidad_flujo_area = st.sidebar.selectbox("Unidad de flujo por área", ["W/m²", "BTU/(h·ft²)", "kcal/(h·m²)"])

# --- Título
titulo = {
    "Plana": "Pared Compuesta en Serie (Plana)",
    "Cilíndrica": "Cilindro Multicapa en Serie",
    "Esférica": "Esfera Multicapa en Serie"
}[geometria]
st.title(f"Conducción - {titulo}")

# --- Entradas generales
col1, col2 = st.columns(2)
with col1:
    T1 = st.number_input(f"Temperatura interna ({unidad_temp})", value=100.0, step=1.0)
    T2 = st.number_input(f"Temperatura externa ({unidad_temp})", value=25.0, step=1.0)
with col2:
    if geometria == "Plana":
        A_total = st.number_input(f"Área total ({unidad_area})", value=1.0, step=1.0)
    else:
        L_cil = st.number_input("Longitud del cilindro (m)", min_value=0.0001, value=1.0, step=1.0)
    n_capas = st.slider("Número de capas", 1, 5, 2)

usar_conveccion = st.checkbox("¿Aplicar convección en superficie interna y externa?")
if usar_conveccion:
    h_in = st.number_input(f"Coef. convección interior ({unidad_h})", value=10.0, step=1.0)
    h_out = st.number_input(f"Coef. convección exterior ({unidad_h})", value=10.0, step=1.0)
else:
    h_in = h_out = 0

materiales = cargar_materiales("tabla_a3.csv")
tabla_capas = []
radios = []
r_i_actual = None
for i in range(n_capas):
    st.subheader(f"Capa {i + 1}")
    col1, col2, col3 = st.columns(3)
    with col1:
        manual = st.checkbox(f"Ingresar k manualmente capa {i + 1}?", key=f"k_manual_{i}")
        if manual:
            mat = st.text_input("Material", value=f"Capa {i + 1}", key=f"mat_{i}")
            k = st.number_input("k", min_value=0.0001, value=0.5, key=f"k_{i}", step=1.0)
        else:
            mat = st.selectbox("Material", materiales["Material"], key=f"mat_sel_{i}")
            k = materiales[materiales["Material"] == mat]["Conductividad térmica (W/m·K)"].values[0]
        k = convertir_k(k, unidad_k)
    with col2:
        if i == 0 and geometria != "Plana":
            r_i = convertir_longitud(st.number_input("Radio interior", min_value=0.0001, value=0.01, key="r_i", step=1.0), unidad_longitud)
            e = convertir_longitud(st.number_input("Espesor", min_value=0.0001, value=0.005, key=f"e_{i}", step=1.0), unidad_longitud)
            r_o = r_i + e
            r_i_actual = r_o
            radios.append((r_i, r_o, mat))
        else:
            e = convertir_longitud(st.number_input("Espesor", min_value=0.0001, value=0.005, key=f"e_{i}", step=1.0), unidad_longitud)
            if geometria != "Plana":
                r_i = r_i_actual
                r_o = r_i + e
                radios.append((r_i, r_o, mat))
                r_i_actual = r_o
    with col3:
        st.write(" ")
    tabla_capas.append({"material": mat, "L": e, "k": k})

# --- Visualización
st.subheader("Visualización")
if geometria == "Plana":
    dibujar_capas_rectangulares(tabla_capas, unidad_longitud)
else:
    dibujar_anillos_radiales(radios)

# --- Cálculo
if st.button("Calcular transferencia de calor"):
    T1_C = convertir_temperatura(T1, unidad_temp)
    T2_C = convertir_temperatura(T2, unidad_temp)
    if geometria == "Plana":
        A_m2 = convertir_area(A_total, unidad_area)
        R_total = sum(c["L"] / (c["k"] * A_m2) for c in tabla_capas)
        if h_in > 0:
            R_total += 1 / (convertir_h(h_in, unidad_h) * A_m2)
        if h_out > 0:
            R_total += 1 / (convertir_h(h_out, unidad_h) * A_m2)
    elif geometria == "Cilíndrica":
        R_total = 0
        for (r_i, r_o, _), c in zip(radios, tabla_capas):
            R_total += np.log(r_o / r_i) / (2 * np.pi * L_cil * c["k"])
        if h_in > 0:
            R_total += 1 / (convertir_h(h_in, unidad_h) * 2 * np.pi * radios[0][0] * L_cil)
        if h_out > 0:
            R_total += 1 / (convertir_h(h_out, unidad_h) * 2 * np.pi * radios[-1][1] * L_cil)
    elif geometria == "Esférica":
        R_total = 0
        for (r_i, r_o, _), c in zip(radios, tabla_capas):
            R_total += (1 / (4 * np.pi * c["k"])) * (1/r_i - 1/r_o)
        if h_in > 0:
            R_total += 1 / (convertir_h(h_in, unidad_h) * 4 * np.pi * radios[0][0]**2)
        if h_out > 0:
            R_total += 1 / (convertir_h(h_out, unidad_h) * 4 * np.pi * radios[-1][1]**2)

    q = (T1_C - T2_C) / R_total
    A_ref = convertir_area(A_total, unidad_area) if geometria == "Plana" else 1

    st.success(f"""
    **Resultados:**
    - Resistencia total: {R_total:.6f} K/W
    - Flujo de calor: {formatear_resultado(q, unidad_flujo, 'flujo'):.2f} {unidad_flujo}
    """)
    if geometria == "Plana":
        st.success(f"- Flujo por área: {formatear_resultado(q/A_ref, unidad_flujo_area, 'flujo_area'):.2f} {unidad_flujo_area}")
