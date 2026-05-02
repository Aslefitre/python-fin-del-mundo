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

st.title("Ibanasca — Defensa Planetaria de Dr.Z Academy")
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


    st.divider()
    st.subheader("Familias de Asteroides")
    st.caption("Distribución orbital por clase — semieje mayor vs excentricidad")

    df_familias = df_filtrado[
        df_filtrado["a"].notna() & df_filtrado["e"].notna()
    ].copy()


    fig_familias = px.scatter(
        df_familias,
        x          = "a",
        y          = "e",
        color      = "class",
        title      = "Familias de Asteroides NEA",
        labels     = {
            "a"    : "Semieje Mayor (UA)",
            "e"    : "Excentricidad",
            "class": "Clase orbital"
        },
        opacity    = 0.5,
        hover_name = "nombre",
        hover_data = {"a": ":.3f", "e": ":.3f", "H": True}
    )
    fig_familias.add_vline(
        x=1.0, line_dash="dash", line_color="cyan",
        annotation_text="Órbita terrestre (1 UA)"
    )
    fig_familias.update_xaxes(range=[0, 4])
    fig_familias.update_yaxes(range=[0, 1])
    fig_familias.update_layout(height=500)
    st.plotly_chart(fig_familias, use_container_width=True)

with tab3:
    st.subheader("Ficha Individual de Asteroide")

    # La misma clase Asteroide del módulo 5
    class Asteroide:
        def __init__(self, nombre, H, albedo, moid, diametro=None):
            self.nombre   = nombre
            self.H        = H
            self.albedo   = albedo
            self.moid     = moid
            self.diametro = diametro if diametro else self.calcular_diametro()

        def calcular_diametro(self):
            if self.H is None or self.albedo is None:
                return None
            return (1329 / np.sqrt(self.albedo)) * 10**(-0.2 * self.H)

        def es_pha(self):
            return self.moid <= 0.05 and self.H <= 22


    nombre_sel = st.selectbox(
        "Selecciona un asteroide",
        df_filtrado["nombre"].dropna().tolist()
    )

    if nombre_sel:
        fila = df_filtrado[
            df_filtrado["nombre"] == nombre_sel
        ].iloc[0]

        ast = Asteroide(
            nombre   = fila["nombre"],
            H        = fila["H"],
            albedo   = fila["albedo"] if pd.notna(fila["albedo"]) else 0.14,
            moid     = fila["moid"],
            diametro = fila["diameter"] if pd.notna(fila["diameter"]) else None
        )

        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"### {ast.nombre}")
            st.metric("Magnitud absoluta H", ast.H)
            st.metric("Albedo", f"{ast.albedo:.3f}")
            st.metric("Diámetro estimado", f"{ast.diametro:.3f} km")
        with col2:
            st.metric("MOID", f"{ast.moid:.4f} UA")
            st.metric("Clase orbital", fila["class"])
            if ast.es_pha():
                st.error("Este asteroide SI es un PHA")
            else:
                st.success("Este asteroide NO es un PHA")
