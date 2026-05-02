import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import requests

# set_page_config debe ser SIEMPRE el primer comando de Streamlit
# layout="wide" aprovecha todo el ancho de la pantalla
st.set_page_config(
    page_title = "Ibanasca — Defensa Planetaria de Dr. Z Academy",
    page_icon  = "🪨",
    layout     = "wide"
)

# @st.cache_data guarda el resultado en memoria
# sin esto la app descargaría 41,000 asteroides
# cada vez que el usuario toca cualquier control
@st.cache_data
def cargar_datos():
    url    = "https://ssd-api.jpl.nasa.gov/sbdb_query.api"
    campos = "full_name,H,albedo,diameter,moid,e,a,i,class,neo,pha"
    params = {
        "fields"   : campos,
        "sb-kind"  : "a",
        "sb-group" : "neo",
    }
    r  = requests.get(url, params=params, timeout=60)
    df = pd.DataFrame(r.json()["data"], columns=r.json()["fields"])

    for col in ["H", "albedo", "diameter", "moid", "e", "a", "i"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    
    df["nombre"] = df["full_name"].str.strip()
    return df

# st.spinner muestra un mensaje mientras espera la descarga
with st.spinner("Descargando catálogo del JPL..."):
    df = cargar_datos()

st.title("Ibanasca — Defensa Planetaria de Dr. Academy")
st.caption(f"Catálogo JPL — {len(df):,} asteroides NEA")

st.sidebar.header("Filtros")

clases = ["Todas"] + sorted(df["class"].dropna().unique().tolist())
clase_sel = st.sidebar.selectbox("Clase orbital", clases)

solo_pha = st.sidebar.checkbox("Solo PHAs")

h_min, h_max = st.sidebar.slider(
    "Rango de magnitud H",
    min_value = float(df["H"].min()),
    max_value = float(df["H"].max()),
    value     = (float(df["H"].min()), 25.0)
)

df_filtrado = df.copy()
if clase_sel != "Todas":
    df_filtrado = df_filtrado[df_filtrado["class"] == clase_sel]
if solo_pha:
    df_filtrado = df_filtrado[df_filtrado["pha"] == "Y"]
df_filtrado = df_filtrado[
    (df_filtrado["H"] >= h_min) & (df_filtrado["H"] <= h_max)
]

st.sidebar.markdown(f"**{len(df_filtrado):,} asteroides** con estos filtros")


tab1, tab2, tab3 = st.tabs(["📋 Catálogo", "🗺️ Mapas", "🔍 Ficha"])

with tab1:
    st.subheader("Catálogo de Asteroides NEA")
    columnas = ["nombre", "H", "albedo", "diameter", "moid", "class", "pha"]
    st.dataframe(
        df_filtrado[columnas].rename(columns={
            "nombre"   : "Nombre",
            "H"        : "Mag. H",
            "albedo"   : "Albedo",
            "diameter" : "Diámetro (km)",
            "moid"     : "MOID (UA)",
            "class"    : "Clase",
            "pha"      : "PHA"
        }),
        use_container_width = True,
        height              = 500
    )


    

with tab2:
    st.subheader("Mapa de Peligrosidad")
    st.caption("Los más peligrosos tienen MOID pequeño y H pequeño")

    df_mapa = df_filtrado[
        df_filtrado["moid"].notna() & df_filtrado["H"].notna()
    ].copy()


    fig_peligro = px.scatter(
        df_mapa,
        x          = "moid",
        y          = "H",
        color      = "H",
        color_continuous_scale = "viridis_r",
        title      = "Mapa de Peligrosidad — Catálogo JPL",
        labels     = {
            "moid" : "MOID — distancia mínima a la Tierra (UA)",
            "H"    : "Magnitud Absoluta H"
        },
        opacity    = 0.6,
        hover_name = "nombre",
        hover_data = {"moid": ":.4f", "H": True, "class": True}
    )

    fig_peligro.add_hline(
        y=22, line_dash="dash", line_color="orange",
        annotation_text="Límite H PHA (H=22)"
    )
    fig_peligro.add_vline(
        x=0.05, line_dash="dash", line_color="red",
        annotation_text="Límite MOID PHA (0.05 UA)"
    )
    fig_peligro.update_layout(height=500)
    st.plotly_chart(fig_peligro, use_container_width=True)

    
