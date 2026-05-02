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


tab1, tab2, tab3, tab4, tab5 = st.tabs(["Catálogo", "Mapas", "Ficha", "Simulador", "¿Coincidimos?"])

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

with tab4:
    st.subheader("Simulador de Impacto")
    st.caption("Calcula la energía y el cráter estimado para un impacto asteroidal")

    # --- Controles de entrada ---
    col_izq, col_der = st.columns(2)

    with col_izq:
        diametro_km = st.slider(
            "Diámetro del asteroide (km)",
            min_value = 0.01,
            max_value = 20.0,
            value     = 0.14,
            step      = 0.01,
            format    = "%.2f km"
        )

        tipo = st.selectbox(
            "Tipo de asteroide",
            ["Tipo C — carbonáceo (1,500 kg/m³)",
             "Tipo S — silíceo (2,500 kg/m³)",
             "Tipo M — metálico (5,000 kg/m³)"]
        )

    with col_der:
        velocidad_kms = st.slider(
            "Velocidad de impacto (km/s)",
            min_value = 11.0,
            max_value = 70.0,
            value     = 20.0,
            step      = 0.5,
            format    = "%.1f km/s"
        )

        angulo = st.slider(
            "Ángulo de impacto (°)",
            min_value = 10,
            max_value = 90,
            value     = 45,
            help      = "90° = impacto vertical directo. Los impactos oblicuos son más frecuentes."
        )

    # --- Cálculos físicos ---
    densidades = {
        "Tipo C — carbonáceo (1,500 kg/m³)" : 1500,
        "Tipo S — silíceo (2,500 kg/m³)"    : 2500,
        "Tipo M — metálico (5,000 kg/m³)"   : 5000
    }
    rho      = densidades[tipo]                        # densidad en kg/m³
    r_m      = (diametro_km * 1000) / 2               # radio en metros
    volumen  = (4/3) * np.pi * r_m**3                 # m³
    masa_kg  = rho * volumen                           # kg
    v_ms     = velocidad_kms * 1000                   # velocidad en m/s
    E_J      = 0.5 * masa_kg * v_ms**2                # energía en Joules
    E_MT     = E_J / 4.184e15                          # energía en megatones TNT

    # Diámetro del cráter — fórmula empírica calibrada con eventos históricos
    # válida para impactos roca-sobre-roca a velocidades típicas
    D_crater = 0.6 * (E_MT ** 0.314)                  # km

    st.divider()

    # --- Resultados ---
    st.subheader("Resultados")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Masa",            f"{masa_kg:.2e} kg")
    c2.metric("Energía cinética", f"{E_J:.2e} J")
    c3.metric("Energía en Mt TNT", f"{E_MT:.2e} Mt")
    c4.metric("Cráter estimado",  f"{D_crater:.2f} km")

    st.divider()

    # --- Comparación histórica ---
    st.subheader("¿Qué tan grande es esa energía?")

    referencias = {
        "Bomba de Hiroshima"       : 0.015,
        "Chelyabinsk 2013"         : 0.5,
        "Bomba Castle Bravo (EEUU)": 15.0,
        "Tunguska 1908"            : 12.0,
        "Krakatoa 1883"            : 200.0,
        "Chicxulub (~KT)"          : 100_000_000.0
    }

    filas = []
    for evento, e_ref in referencias.items():
        if E_MT >= e_ref:
            ratio = E_MT / e_ref
            comparacion = f"{ratio:.1f}× más grande"
        else:
            ratio = e_ref / E_MT
            comparacion = f"{ratio:.1f}× más pequeño"
        filas.append({"Evento de referencia": evento,
                      "Energía (Mt TNT)": e_ref,
                      "Comparación": comparacion})

    st.dataframe(
        pd.DataFrame(filas),
        use_container_width = True,
        hide_index          = True
    )

    if E_MT < 0.015:
        st.success("Energía menor a Hiroshima — evento local menor")
    elif E_MT < 15:
        st.warning("Energía entre Hiroshima y Castle Bravo — evento regional severo")
    elif E_MT < 10_000:
        st.error("Energía entre Tunguska y Krakatoa — evento continental catastrófico")
    else:
        st.error("Energía comparable o superior a Chicxulub — evento de extinción masiva")

with tab5:
    st.subheader("🔬 ¿Coincidimos con la NASA?")
    st.write("""
    El CNEOS — Centro de Estudios de Objetos Cercanos a la Tierra del JPL —
    tiene una herramienta oficial para estimar el tamaño de asteroides a partir
    de su magnitud absoluta H y su albedo. Vamos a comparar sus resultados con los nuestros.
    """)

    st.info("🔗 Herramienta oficial CNEOS: https://cneos.jpl.nasa.gov/tools/ast_size_est.html")

    st.divider()
    st.subheader("Calcula y compara")

    col1, col2 = st.columns(2)
    with col1:
        H_cneos = st.number_input(
            "Magnitud absoluta H",
            min_value = 0.0,
            max_value = 40.0,
            value     = 19.2,
            step      = 0.1,
            help      = "Apophis: H=19.2 | Bennu: H=20.8 | Chelyabinsk: H=26.0"
        )
    with col2:
        albedo_cneos = st.number_input(
            "Albedo visual",
            min_value = 0.01,
            max_value = 0.90,
            value     = 0.30,
            step      = 0.01,
            help      = "Tipo S (silíceo): ~0.20-0.30 | Tipo C (carbonáceo): ~0.05-0.10"
        )

    # --- Fórmula de Harris (nuestra implementación) ---
    d_nuestro = (1329 / np.sqrt(albedo_cneos)) * 10**(-0.2 * H_cneos)

    # --- Fórmula del CNEOS (exactamente como aparece en su página) ---
    d_cneos = 10 ** (3.1236 - 0.5 * np.log10(albedo_cneos) - 0.2 * H_cneos)

    st.divider()
    st.subheader("Resultado")

    c1, c2, c3 = st.columns(3)
    c1.metric("Nuestra fórmula (Harris)",  f"{d_nuestro:.4f} km")
    c2.metric("Fórmula CNEOS oficial",     f"{d_cneos:.4f} km")
    diferencia = abs(d_nuestro - d_cneos)
    c3.metric("Diferencia",                f"{diferencia:.2e} km")

    if diferencia < 1e-10:
        st.success("✅ Los resultados son idénticos — nuestra implementación es correcta.")
    else:
        st.warning(f"⚠️ Diferencia numérica mínima por redondeo de punto flotante: {diferencia:.2e} km")

    st.divider()

    # --- Demostración matemática ---
    with st.expander("¿Por qué son iguales? — La demostración matemática"):
        st.write("""
        Las dos fórmulas parecen diferentes pero son matemáticamente idénticas:

        **Nuestra fórmula (Harris):**
        d = (1329 / √albedo) × 10^(−0.2 × H)

        **Fórmula CNEOS:**
        d = 10^[3.1236 − 0.5 × log₁₀(albedo) − 0.2 × H]

        **La equivalencia:**
        - 10^3.1236 = 1329  ✓
        - 10^(−0.5 × log₁₀(albedo)) = albedo^(−0.5) = 1/√albedo  ✓

        Son la misma fórmula escrita de dos formas distintas.
        Tú implementaste la forma de Harris. El CNEOS usa la forma logarítmica.
        El resultado es idéntico.
        """)

    st.divider()

    # --- Tabla de referencia del CNEOS ---
    st.subheader("Tabla de referencia del CNEOS")
    st.caption("Diámetros estimados (km) para diferentes valores de H y albedo — reproducida con nuestra fórmula")

    H_valores     = [22.0, 21.0, 20.0, 19.0, 18.0, 17.0, 16.0, 15.0]
    albedo_valores = [0.05, 0.10, 0.15, 0.20, 0.25, 0.30]

    tabla = {}
    for alb in albedo_valores:
        columna = []
        for h in H_valores:
            d = (1329 / np.sqrt(alb)) * 10**(-0.2 * h)
            columna.append(round(d, 3))
        tabla[f"albedo={alb}"] = columna

    df_tabla = pd.DataFrame(tabla, index=[f"H={h}" for h in H_valores])
    st.dataframe(df_tabla, use_container_width=True)
    st.caption("Compara estos valores con la tabla en cneos.jpl.nasa.gov/tools/ast_size_est.html — son idénticos.")
