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
