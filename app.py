"""
app.py
------
Aplicación principal: Learning Analytics + Criptografía + Blockchain
Interfaz Streamlit con diseño minimalista estilo iOS 26.

Uso:
    streamlit run app.py
"""

import streamlit as st
import pandas as pd
import json
import time
import io

from data_module import generar_dataset, calcular_riesgo, cargar_csv
from crypto_module import AESCipher, RSASigner, cifrar_columnas_df, descifrar_registro
from blockchain_module import BlockchainEducativa
from analytics_module import (
    estadisticas_generales,
    recomendaciones,
    ModeloRiesgo,
    fig_distribucion_notas,
    fig_asistencia_vs_nota,
    fig_importancia_features,
    fig_radar_estudiante,
    fig_riesgo_gauge,
)

# ---------------------------------------------------------------------------
# Configuración de página e inyección CSS iOS 26
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="EduAnalytics · LA Platform",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

IOS_CSS = """
<style>
/* ---- Fuentes ---- */
@import url('https://fonts.googleapis.com/css2?family=SF+Pro+Display:wght@300;400;500;600;700&display=swap');
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

/* ---- Reset & Variables ---- */
:root {
    --bg: #F2F2F7;
    --card: #FFFFFF;
    --blue: #007AFF;
    --green: #34C759;
    --orange: #FF9500;
    --red: #FF3B30;
    --gray: #8E8E93;
    --dark: #1C1C1E;
    --secondary: #6C6C70;
    --separator: #E5E5EA;
    --radius: 16px;
    --radius-sm: 10px;
    --shadow: 0 2px 20px rgba(0,0,0,0.06);
    --font: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
}

html, body, [class*="css"] {
    font-family: var(--font) !important;
    background-color: var(--bg) !important;
    color: var(--dark) !important;
}

/* ---- Sidebar ---- */
section[data-testid="stSidebar"] {
    background-color: rgba(255,255,255,0.85) !important;
    backdrop-filter: blur(20px);
    border-right: 1px solid var(--separator) !important;
}
section[data-testid="stSidebar"] .stRadio label {
    font-size: 14px !important;
    color: var(--dark) !important;
    font-weight: 500;
}

/* ---- Main container ---- */
.main .block-container {
    padding: 2rem 2.5rem !important;
    max-width: 1200px;
}

/* ---- Encabezado principal ---- */
.ios-header {
    display: flex;
    align-items: center;
    gap: 14px;
    margin-bottom: 28px;
}
.ios-header-icon {
    width: 52px; height: 52px;
    background: linear-gradient(135deg, #007AFF, #5AC8FA);
    border-radius: 14px;
    display: flex; align-items: center; justify-content: center;
    font-size: 26px;
    box-shadow: 0 4px 16px rgba(0,122,255,0.25);
}
.ios-header-title { margin: 0; }
.ios-header-title h1 {
    font-size: 28px; font-weight: 700;
    color: var(--dark); margin: 0; letter-spacing: -0.5px;
}
.ios-header-title p {
    font-size: 13px; color: var(--secondary); margin: 2px 0 0;
}

/* ---- Cards ---- */
.ios-card {
    background: var(--card);
    border-radius: var(--radius);
    padding: 20px 24px;
    box-shadow: var(--shadow);
    margin-bottom: 16px;
    border: 1px solid var(--separator);
}
.ios-card-title {
    font-size: 13px; font-weight: 600; text-transform: uppercase;
    letter-spacing: 0.5px; color: var(--secondary); margin-bottom: 14px;
}

/* ---- KPI Pills ---- */
.kpi-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
    gap: 12px;
    margin-bottom: 20px;
}
.kpi-pill {
    background: var(--card);
    border-radius: var(--radius-sm);
    padding: 16px 18px;
    border: 1px solid var(--separator);
    box-shadow: var(--shadow);
}
.kpi-pill .label {
    font-size: 11px; color: var(--secondary); font-weight: 500;
    text-transform: uppercase; letter-spacing: 0.4px;
}
.kpi-pill .value {
    font-size: 26px; font-weight: 700; letter-spacing: -0.5px; margin-top: 4px;
}
.kpi-pill .value.blue   { color: var(--blue); }
.kpi-pill .value.green  { color: var(--green); }
.kpi-pill .value.orange { color: var(--orange); }
.kpi-pill .value.red    { color: var(--red); }

/* ---- Tabla ---- */
.dataframe { border-radius: var(--radius-sm) !important; }

/* ---- Badges ---- */
.badge {
    display: inline-block;
    padding: 3px 10px;
    border-radius: 20px;
    font-size: 11px; font-weight: 600;
}
.badge-red    { background: #FFF2F1; color: var(--red); }
.badge-green  { background: #F0FFF4; color: var(--green); }
.badge-orange { background: #FFF8EE; color: var(--orange); }
.badge-blue   { background: #EBF5FF; color: var(--blue); }

/* ---- Alert boxes ---- */
.ios-alert {
    border-radius: var(--radius-sm);
    padding: 14px 18px;
    font-size: 13px;
    margin: 10px 0;
    border-left: 4px solid;
}
.ios-alert-info  { background:#EBF5FF; border-color:var(--blue);   color:#0051a8; }
.ios-alert-ok    { background:#F0FFF4; border-color:var(--green);  color:#1a7a3a; }
.ios-alert-warn  { background:#FFF8EE; border-color:var(--orange); color:#995800; }
.ios-alert-error { background:#FFF2F1; border-color:var(--red);    color:#b00000; }

/* ---- Streamlit overrides ---- */
div[data-testid="stMetric"] {
    background: var(--card);
    border-radius: var(--radius-sm);
    padding: 16px !important;
    border: 1px solid var(--separator);
}
div[data-testid="stMetricValue"] > div { font-size: 26px !important; font-weight: 700 !important; }

.stButton > button {
    background: var(--blue) !important;
    color: white !important;
    border: none !important;
    border-radius: var(--radius-sm) !important;
    font-weight: 600 !important;
    font-size: 14px !important;
    padding: 10px 20px !important;
    transition: all 0.15s ease !important;
}
.stButton > button:hover {
    background: #0066DD !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 12px rgba(0,122,255,0.3) !important;
}

div[data-testid="stSelectbox"] > div > div {
    border-radius: var(--radius-sm) !important;
    border-color: var(--separator) !important;
}

.stTabs [data-baseweb="tab"] {
    font-weight: 500 !important;
    font-size: 13px !important;
}
.stTabs [aria-selected="true"] {
    color: var(--blue) !important;
}
.stTabs [data-baseweb="tab-highlight"] {
    background-color: var(--blue) !important;
}

div[data-testid="stExpander"] {
    border: 1px solid var(--separator) !important;
    border-radius: var(--radius-sm) !important;
}

/* ---- Blockchain chain viz ---- */
.chain-block {
    background: var(--card);
    border: 1px solid var(--separator);
    border-radius: var(--radius-sm);
    padding: 12px 16px;
    margin: 6px 0;
    font-size: 12px;
    font-family: 'SF Mono', 'Fira Code', monospace;
}
.chain-block .block-index {
    font-size: 11px; font-weight: 700; color: var(--blue); margin-bottom: 4px;
}
.chain-hash { color: var(--secondary); font-size: 10px; }
.chain-arrow { text-align: center; color: var(--gray); font-size: 18px; line-height: 1; }

/* ---- Scrollbar ---- */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: #C7C7CC; border-radius: 3px; }
</style>
"""

st.markdown(IOS_CSS, unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Estado de sesión
# ---------------------------------------------------------------------------

@st.cache_resource
def init_crypto():
    return AESCipher(), RSASigner()


@st.cache_resource
def init_blockchain():
    return BlockchainEducativa()


def init_state():
    if "df" not in st.session_state:
        df_raw = generar_dataset(n_estudiantes=20)
        st.session_state.df = calcular_riesgo(df_raw)
    if "modelo" not in st.session_state:
        st.session_state.modelo = None
    if "metricas_ml" not in st.session_state:
        st.session_state.metricas_ml = None
    if "registros_cifrados" not in st.session_state:
        st.session_state.registros_cifrados = {}
    if "blockchain_log" not in st.session_state:
        st.session_state.blockchain_log = []


init_state()
cipher, signer = init_crypto()
blockchain = init_blockchain()

# ---------------------------------------------------------------------------
# Sidebar — Navegación
# ---------------------------------------------------------------------------

with st.sidebar:
    st.markdown("""
    <div style="padding: 8px 0 20px;">
        <div style="display:flex;align-items:center;gap:10px;margin-bottom:6px;">
            <div style="width:36px;height:36px;background:linear-gradient(135deg,#007AFF,#5AC8FA);
                        border-radius:10px;display:flex;align-items:center;justify-content:center;
                        font-size:18px;">🎓</div>
            <div>
                <div style="font-weight:700;font-size:16px;color:#1C1C1E;">EduAnalytics</div>
                <div style="font-size:11px;color:#8E8E93;">Learning Analytics Platform</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    pagina = st.radio(
        "Navegación",
        ["📊  Panel General", "🔍  Análisis Individual", "🔐  Criptografía",
         "⛓️  Blockchain", "🤖  Predicción ML"],
        label_visibility="collapsed",
    )

    st.markdown("---")
    st.markdown("""
    <div style="font-size:11px;color:#8E8E93;padding:4px 0;">
        <div style="font-weight:600;color:#6C6C70;margin-bottom:6px;">DATOS</div>
    </div>
    """, unsafe_allow_html=True)

    fuente = st.radio("Fuente de datos", ["Dataset sintético", "Cargar CSV"],
                      label_visibility="collapsed")
    if fuente == "Cargar CSV":
        uploaded = st.file_uploader("CSV educativo", type=["csv"])
        if uploaded:
            try:
                df_up = cargar_csv(uploaded)
                st.session_state.df = calcular_riesgo(df_up)
                st.success("✅ CSV cargado")
            except Exception as e:
                st.error(f"Error: {e}")
    else:
        n = st.slider("Nº de estudiantes", 10, 50, 20)
        if st.button("🔄 Regenerar"):
            st.session_state.df = calcular_riesgo(generar_dataset(n_estudiantes=n))
            st.session_state.modelo = None
            st.rerun()

    st.markdown("---")
    st.markdown("""
    <div style="font-size:10px;color:#C7C7CC;text-align:center;padding-top:8px;">
        Proyecto académico · Análisis de Datos II<br>
        Criptografía · Blockchain · Learning Analytics
    </div>
    """, unsafe_allow_html=True)

df = st.session_state.df
stats = estadisticas_generales(df)

# ---------------------------------------------------------------------------
# Header común
# ---------------------------------------------------------------------------

st.markdown("""
<div class="ios-header">
    <div class="ios-header-icon">🎓</div>
    <div class="ios-header-title">
        <h1>EduAnalytics Platform</h1>
        <p>Análisis de Datos · Criptografía · Blockchain</p>
    </div>
</div>
""", unsafe_allow_html=True)


# ===========================================================================
# PÁGINA 1: PANEL GENERAL
# ===========================================================================

if pagina == "📊  Panel General":

    # KPIs
    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.metric("Estudiantes", stats["total_estudiantes"])
    with col2:
        st.metric("Nota Media", f"{stats['nota_media_grupo']:.1f}")
    with col3:
        color_asist = "normal" if stats["asistencia_media"] >= 80 else "inverse"
        st.metric("Asistencia Media", f"{stats['asistencia_media']}%")
    with col4:
        st.metric("En Riesgo", stats["en_riesgo"],
                  delta=f"{stats['pct_riesgo']}%", delta_color="inverse")
    with col5:
        st.metric("Entrega Tareas", f"{stats['tasa_entrega_media']}%")

    st.markdown("<br>", unsafe_allow_html=True)

    # Gráficos
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown('<div class="ios-card"><div class="ios-card-title">Distribución de Notas</div>', unsafe_allow_html=True)
        st.pyplot(fig_distribucion_notas(df), use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with col_b:
        st.markdown('<div class="ios-card"><div class="ios-card-title">Asistencia vs Rendimiento</div>', unsafe_allow_html=True)
        st.pyplot(fig_asistencia_vs_nota(df), use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # Tabla de estudiantes
    st.markdown('<div class="ios-card"><div class="ios-card-title">Listado de Estudiantes</div>', unsafe_allow_html=True)

    def color_riesgo(val):
        if val == 1:
            return "color: #FF3B30; font-weight:600;"
        return "color: #34C759; font-weight:600;"

    cols_mostrar = ["id_estudiante", "nota_media", "asistencia_pct",
                    "participacion_foro", "tareas_entregadas", "indice_riesgo", "en_riesgo"]
    df_display = df[cols_mostrar].rename(columns={
        "id_estudiante": "ID", "nota_media": "Nota", "asistencia_pct": "Asistencia %",
        "participacion_foro": "Foro", "tareas_entregadas": "Tareas",
        "indice_riesgo": "Índice Riesgo", "en_riesgo": "⚠️ Riesgo",
    })

    st.dataframe(
        df_display.style
        .format({"Nota": "{:.1f}", "Asistencia %": "{:.1f}%", "Índice Riesgo": "{:.3f}"})
        .map(color_riesgo, subset=["⚠️ Riesgo"])
        .set_properties(**{"font-size": "12px"}),
        use_container_width=True, height=400,
    )
    st.markdown('</div>', unsafe_allow_html=True)


# ===========================================================================
# PÁGINA 2: ANÁLISIS INDIVIDUAL
# ===========================================================================

elif pagina == "🔍  Análisis Individual":

    st.markdown('<div class="ios-card-title">PERFIL DE ESTUDIANTE</div>', unsafe_allow_html=True)
    sid = st.selectbox("Seleccionar estudiante", df["id_estudiante"].tolist())
    row = df[df["id_estudiante"] == sid].iloc[0]

    col_left, col_right = st.columns([1.2, 1])

    with col_left:
        # Métricas
        m1, m2, m3 = st.columns(3)
        m1.metric("Nota Media", f"{row['nota_media']:.1f}")
        m2.metric("Asistencia", f"{row['asistencia_pct']:.1f}%")
        m3.metric("Tareas", f"{row['tareas_entregadas']}/{row['total_tareas']}")

        m4, m5, _ = st.columns(3)
        m4.metric("Participación", row['participacion_foro'])
        m5.metric("Tiempo Online", f"{row['tiempo_plataforma_h']:.0f}h")

        st.markdown("<br>", unsafe_allow_html=True)

        # Índice de riesgo (gauge)
        st.markdown("**Indicador de Riesgo**")
        st.pyplot(fig_riesgo_gauge(float(row["indice_riesgo"])), use_container_width=False)

    with col_right:
        st.markdown("**Perfil Multidimensional**")
        st.pyplot(fig_radar_estudiante(row), use_container_width=True)

    # Recomendaciones
    st.markdown('<div class="ios-card"><div class="ios-card-title">RECOMENDACIONES PERSONALIZADAS</div>', unsafe_allow_html=True)
    recs = recomendaciones(row)
    for r in recs:
        st.markdown(f"- {r}")
    st.markdown('</div>', unsafe_allow_html=True)

    # Notas por asignatura
    with st.expander("📚 Desglose por asignatura"):
        nota_cols = [c for c in df.columns if c.startswith("nota_") and c != "nota_media"]
        notas_df = pd.DataFrame({
            "Asignatura": [c.replace("nota_", "").replace("_", " ").title() for c in nota_cols],
            "Nota": [row[c] for c in nota_cols],
        }).sort_values("Nota", ascending=False)
        st.dataframe(notas_df.style.format({"Nota": "{:.2f}"}), use_container_width=True)


# ===========================================================================
# PÁGINA 3: CRIPTOGRAFÍA
# ===========================================================================

elif pagina == "🔐  Criptografía":

    tab1, tab2, tab3 = st.tabs(["🔑 AES-256-GCM", "✍️  Firma RSA", "📋 Registro Cifrado"])

    # --- AES
    with tab1:
        st.markdown('<div class="ios-card"><div class="ios-card-title">ENCRIPTACIÓN AES-256-GCM</div>', unsafe_allow_html=True)
        st.markdown("""
        <div class="ios-alert ios-alert-info">
        <strong>AES-256-GCM</strong> es un esquema de cifrado autenticado (AEAD).
        Proporciona confidencialidad e integridad en una sola operación.
        El nonce de 96 bits es único por cada operación, evitando reutilización.
        </div>
        """, unsafe_allow_html=True)

        texto_input = st.text_area("Texto a cifrar (dato educativo sensible)", 
                                   value="Nombre: Ana García | Nota final: 8.7 | DNI: 12345678A",
                                   height=80)

        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔒 Cifrar"):
                payload = cipher.encrypt(texto_input)
                st.session_state["ultimo_payload"] = payload
                st.markdown("**Resultado cifrado:**")
                st.code(json.dumps(payload, indent=2), language="json")
                st.markdown(f"""
                <div class="ios-alert ios-alert-ok">
                ✅ Texto cifrado correctamente · Nonce único generado · {len(payload['ciphertext'])} chars en Base64
                </div>""", unsafe_allow_html=True)

        with col2:
            if st.button("🔓 Descifrar último") and "ultimo_payload" in st.session_state:
                try:
                    resultado = cipher.decrypt(st.session_state["ultimo_payload"])
                    st.success(f"Texto descifrado: **{resultado}**")
                except Exception as e:
                    st.error(str(e))

        st.markdown('</div>', unsafe_allow_html=True)

        # Demo integridad
        st.markdown('<div class="ios-card"><div class="ios-card-title">DEMO MANIPULACIÓN DE DATOS</div>', unsafe_allow_html=True)
        st.markdown("""
        <div class="ios-alert ios-alert-warn">
        Si un atacante modifica el ciphertext, GCM detecta la manipulación y rechaza el descifrado.
        </div>""", unsafe_allow_html=True)
        if st.button("🧪 Simular ataque (modificar ciphertext)") and "ultimo_payload" in st.session_state:
            payload_corrupto = dict(st.session_state["ultimo_payload"])
            payload_corrupto["ciphertext"] = payload_corrupto["ciphertext"][:-4] + "XXXX"
            try:
                cipher.decrypt(payload_corrupto)
            except ValueError as e:
                st.markdown(f"""
                <div class="ios-alert ios-alert-error">
                {str(e)}
                </div>""", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # --- RSA
    with tab2:
        st.markdown('<div class="ios-card"><div class="ios-card-title">FIRMA DIGITAL RSA-2048</div>', unsafe_allow_html=True)
        st.markdown("""
        <div class="ios-alert ios-alert-info">
        <strong>RSA-2048 + SHA-256</strong> con esquema PKCS#1v15.
        Las firmas digitales garantizan autenticidad (el mensaje proviene del emisor) 
        e integridad (el mensaje no fue alterado).
        </div>
        """, unsafe_allow_html=True)

        mensaje = st.text_input("Mensaje a firmar", 
                                value=f"Registro académico · Estudiante EST-A1B2C3D4 · Nota: 8.5")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("✍️  Firmar mensaje"):
                firma = signer.sign(mensaje)
                st.session_state["firma_demo"] = firma
                st.session_state["mensaje_demo"] = mensaje
                st.code(f"Firma (Base64, primeros 80 chars):\n{firma[:80]}…", language="text")

        with col2:
            if st.button("✅ Verificar firma") and "firma_demo" in st.session_state:
                valida = signer.verify(st.session_state["mensaje_demo"],
                                       st.session_state["firma_demo"])
                if valida:
                    st.markdown('<div class="ios-alert ios-alert-ok">✅ Firma válida — autenticidad confirmada</div>',
                                unsafe_allow_html=True)
                else:
                    st.markdown('<div class="ios-alert ios-alert-error">❌ Firma inválida</div>',
                                unsafe_allow_html=True)

        if st.button("🧪 Verificar firma con mensaje alterado") and "firma_demo" in st.session_state:
            valida = signer.verify("Mensaje alterado por atacante",
                                   st.session_state["firma_demo"])
            st.markdown('<div class="ios-alert ios-alert-error">❌ Firma inválida — el mensaje fue modificado</div>',
                        unsafe_allow_html=True)

        with st.expander("🔑 Clave pública RSA (PEM)"):
            st.code(signer.export_public_key_pem(), language="text")

        st.markdown('</div>', unsafe_allow_html=True)

    # --- Registro cifrado masivo
    with tab3:
        st.markdown('<div class="ios-card"><div class="ios-card-title">CIFRADO MASIVO DE DATOS SENSIBLES</div>', unsafe_allow_html=True)
        st.markdown("""
        <div class="ios-alert ios-alert-info">
        Simulación de cifrado GDPR: los datos sensibles de los estudiantes se cifran con AES-256-GCM
        antes de almacenarse. Solo usuarios autorizados con la clave pueden descifrarlos.
        </div>""", unsafe_allow_html=True)

        columnas_sensibles = st.multiselect(
            "Columnas a cifrar",
            ["nombre_real", "nota_media", "asistencia_pct", "indice_riesgo"],
            default=["nombre_real", "nota_media"],
        )

        if st.button("🔒 Cifrar dataset completo") and columnas_sensibles:
            with st.spinner("Cifrando registros…"):
                cifrado = cifrar_columnas_df(df, columnas_sensibles, cipher)
                st.session_state["registros_cifrados"] = cifrado

            st.success(f"✅ {len(cifrado)} registros cifrados")

            # Mostrar uno de ejemplo
            ejemplo_id = list(cifrado.keys())[0]
            st.markdown(f"**Ejemplo — Registro {ejemplo_id}:**")
            st.code(json.dumps(cifrado[ejemplo_id], indent=2), language="json")

        # Descifrar uno
        if st.session_state.get("registros_cifrados"):
            ids_cifrados = list(st.session_state["registros_cifrados"].keys())
            id_sel = st.selectbox("Descifrar registro:", ids_cifrados)
            if st.button("🔓 Descifrar"):
                desc = descifrar_registro(
                    st.session_state["registros_cifrados"][id_sel], cipher
                )
                st.json(desc)

        st.markdown('</div>', unsafe_allow_html=True)


# ===========================================================================
# PÁGINA 4: BLOCKCHAIN
# ===========================================================================

elif pagina == "⛓️  Blockchain":

    col1, col2 = st.columns([1.5, 1])

    with col1:
        st.markdown('<div class="ios-card"><div class="ios-card-title">REGISTRAR EVENTO EDUCATIVO</div>', unsafe_allow_html=True)

        sid_bc = st.selectbox("Estudiante", df["id_estudiante"].tolist())
        evento = st.selectbox("Tipo de evento", [
            "CALIFICACIÓN_REGISTRADA", "ASISTENCIA", "TAREA_ENTREGADA",
            "ACCESO_PLATAFORMA", "EXAMEN_COMPLETADO", "FEEDBACK_DOCENTE",
        ])
        detalle_val = st.text_input("Detalle / valor", placeholder="p. ej. 8.5 · Matemáticas")
        firmar = st.checkbox("✍️  Firmar bloque con RSA", value=True)

        if st.button("⛓️  Añadir bloque"):
            with st.spinner("Minando bloque…"):
                bloque = blockchain.agregar_registro_estudiante(
                    id_estudiante=sid_bc,
                    evento=evento,
                    detalles={"valor": detalle_val},
                    signer=signer if firmar else None,
                )
            st.markdown(f"""
            <div class="ios-alert ios-alert-ok">
            ✅ Bloque #{bloque.index} añadido · Hash: <code>{bloque.hash_propio[:24]}…</code> · Nonce: {bloque.nonce}
            </div>""", unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="ios-card"><div class="ios-card-title">VERIFICACIÓN DE INTEGRIDAD</div>', unsafe_allow_html=True)

        if st.button("🔍 Verificar cadena completa"):
            resultado = blockchain.verificar_integridad()
            if resultado["integra"]:
                st.markdown(f"""
                <div class="ios-alert ios-alert-ok">
                ✅ Cadena íntegra · {resultado['total_bloques']} bloques verificados
                </div>""", unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="ios-alert ios-alert-error">
                ❌ Integridad comprometida:<br>{'<br>'.join(resultado['errores'])}
                </div>""", unsafe_allow_html=True)

        if st.button("🧪 Simular manipulación (demo)"):
            if len(blockchain.cadena) > 1:
                blockchain.manipular_bloque_demo(1, "DATOS_ALTERADOS")
                st.markdown("""
                <div class="ios-alert ios-alert-warn">
                ⚠️  Bloque 1 manipulado. Ejecuta 'Verificar cadena' para detectarlo.
                </div>""", unsafe_allow_html=True)

        st.markdown(f"**Total bloques:** {len(blockchain)}", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # Visualización de la cadena
    st.markdown('<div class="ios-card"><div class="ios-card-title">VISUALIZACIÓN DE LA CADENA</div>', unsafe_allow_html=True)

    chain_data = blockchain.get_resumen_cadena()
    for i, bloque_res in enumerate(chain_data[-8:]):  # últimos 8
        is_genesis = bloque_res["Bloque"] == 0
        bg = "#EBF5FF" if is_genesis else "#FFFFFF"
        border = "#007AFF" if is_genesis else "#E5E5EA"
        st.markdown(f"""
        <div class="chain-block" style="background:{bg};border-color:{border}">
            <div class="block-index">BLOQUE #{bloque_res['Bloque']} {'· GÉNESIS' if is_genesis else ''}</div>
            <div>🕐 {bloque_res['Timestamp']} &nbsp;·&nbsp; Nonce: {bloque_res['Nonce']}</div>
            <div class="chain-hash">↑ prev: {bloque_res['Hash anterior']}</div>
            <div class="chain-hash">🔑 hash: {bloque_res['Hash propio']}</div>
            {'<div class="chain-hash">✍️  firma: ' + bloque_res['Firma'] + '</div>' if bloque_res['Firma'] != '—' else ''}
        </div>
        {'<div class="chain-arrow">↕</div>' if i < len(chain_data[-8:]) - 1 else ''}
        """, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

    # Tabla exportable
    with st.expander("📥 Ver cadena completa como tabla"):
        st.dataframe(pd.DataFrame(chain_data), use_container_width=True)


# ===========================================================================
# PÁGINA 5: PREDICCIÓN ML
# ===========================================================================

elif pagina == "🤖  Predicción ML":

    st.markdown('<div class="ios-card"><div class="ios-card-title">MODELO DE PREDICCIÓN DE RIESGO — RANDOM FOREST</div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="ios-alert ios-alert-info">
    El modelo predice la probabilidad de que un estudiante esté en riesgo de abandono,
    basándose en nota media, asistencia, participación, tareas y tiempo en plataforma.
    Entrenado con los datos actuales del dataset.
    </div>""", unsafe_allow_html=True)

    if st.button("🚀 Entrenar modelo"):
        with st.spinner("Entrenando Random Forest…"):
            modelo = ModeloRiesgo()
            metricas = modelo.entrenar(df)
            st.session_state["modelo"] = modelo
            st.session_state["metricas_ml"] = metricas
            time.sleep(0.5)
        st.markdown(f"""
        <div class="ios-alert ios-alert-ok">
        ✅ Modelo entrenado · Accuracy: <strong>{metricas['accuracy']:.1%}</strong>
        </div>""", unsafe_allow_html=True)

    if st.session_state.get("modelo"):
        modelo = st.session_state["modelo"]
        metricas = st.session_state["metricas_ml"]

        col1, col2, col3 = st.columns(3)
        col1.metric("Accuracy", f"{metricas['accuracy']:.1%}")

        report = metricas["report"]
        if "1" in report:
            col2.metric("Precision (riesgo)", f"{report['1']['precision']:.1%}")
            col3.metric("Recall (riesgo)", f"{report['1']['recall']:.1%}")

        # Importancia de features
        st.markdown("<br>", unsafe_allow_html=True)
        st.pyplot(fig_importancia_features(metricas["importancias"]), use_container_width=False)

        # Predicciones sobre dataset
        st.markdown("---")
        st.markdown("**Predicciones sobre el dataset completo**")
        probs = modelo.predecir(df)
        df_pred = df[["id_estudiante", "nota_media", "asistencia_pct", "en_riesgo"]].copy()
        df_pred["prob_riesgo_ML"] = probs.round(3)
        df_pred["prediccion_ML"] = (probs > 0.5).astype(int)
        df_pred["coincide"] = (df_pred["en_riesgo"] == df_pred["prediccion_ML"]).map(
            {True: "✅", False: "❌"}
        )

        st.dataframe(
            df_pred.rename(columns={
                "id_estudiante": "ID", "nota_media": "Nota",
                "asistencia_pct": "Asistencia %", "en_riesgo": "Riesgo Real",
                "prob_riesgo_ML": "Prob. Riesgo", "prediccion_ML": "Pred. ML",
            }).style.format({"Prob. Riesgo": "{:.1%}", "Nota": "{:.1f}"}),
            use_container_width=True, height=360,
        )

        # Predicción interactiva
        st.markdown("---")
        st.markdown("**Predicción sobre nuevo estudiante**")
        with st.expander("🔬 Ingresar datos manualmente"):
            c1, c2, c3 = st.columns(3)
            nota_n = c1.slider("Nota media", 0.0, 10.0, 6.0, 0.1)
            asist_n = c2.slider("Asistencia %", 0, 100, 80)
            parti_n = c3.slider("Participación foro", 0, 30, 10)
            c4, c5 = st.columns(2)
            tareas_n = c4.slider("Tareas entregadas", 0, 20, 15)
            tiempo_n = c5.slider("Tiempo plataforma (h)", 0, 120, 40)

            nuevo = pd.DataFrame([{
                "nota_media": nota_n, "asistencia_pct": asist_n,
                "participacion_foro": parti_n, "tareas_entregadas": tareas_n,
                "tiempo_plataforma_h": tiempo_n,
            }])
            prob_nuevo = float(modelo.predecir(nuevo)[0])
            st.markdown("**Resultado:**")
            st.pyplot(fig_riesgo_gauge(prob_nuevo), use_container_width=False)

    st.markdown('</div>', unsafe_allow_html=True)
