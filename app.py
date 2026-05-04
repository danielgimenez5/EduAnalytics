"""
app.py — EduAnalytics Platform
Arquitectura: Streamlit para lógica Python + HTML/CSS nativo para toda la UI.
Los componentes nativos de Streamlit (st.metric, st.pyplot, tabs…) son
sustituidos por HTML puro renderizado en st.components.v1.html(), que corre
en su propio iframe sin las restricciones de estilo de Streamlit.
"""

import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import json, io, base64, time

from data_module import generar_dataset, calcular_riesgo, cargar_csv
from crypto_module import AESCipher, RSASigner, cifrar_columnas_df, descifrar_registro
from blockchain_module import BlockchainEducativa
from analytics_module import (
    estadisticas_generales, recomendaciones, ModeloRiesgo,
    fig_distribucion_notas, fig_asistencia_vs_nota,
    fig_importancia_features, fig_radar_estudiante, fig_riesgo_gauge,
)

# ── Configuración mínima de Streamlit ────────────────────────────────────────
st.set_page_config(
    page_title="EduAnalytics · iOS 26",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Ocultar absolutamente todo el chrome de Streamlit
st.markdown("""
<style>
#MainMenu, header, footer, [data-testid="stToolbar"],
[data-testid="stDecoration"], [data-testid="stStatusWidget"],
[data-testid="stSidebarCollapsedControl"] { display: none !important; }
.stApp { background: #F2F2F7 !important; }
.main .block-container { padding: 0 !important; max-width: 100% !important; }
</style>
""", unsafe_allow_html=True)


# ── Helper: matplotlib fig → data URI base64 ─────────────────────────────────
def fig_to_b64(fig, dpi=144):
    import matplotlib.pyplot as plt
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=dpi, bbox_inches="tight",
                facecolor=fig.get_facecolor())
    plt.close(fig)
    buf.seek(0)
    return "data:image/png;base64," + base64.b64encode(buf.read()).decode()


# ── Estado de sesión ──────────────────────────────────────────────────────────
@st.cache_resource
def init_crypto():
    return AESCipher(), RSASigner()

@st.cache_resource
def init_blockchain():
    return BlockchainEducativa()

def init_state():
    if "df"                 not in st.session_state:
        st.session_state.df = calcular_riesgo(generar_dataset(20))
    if "pagina"             not in st.session_state:
        st.session_state.pagina = "dashboard"
    if "modelo"             not in st.session_state:
        st.session_state.modelo = None
    if "metricas_ml"        not in st.session_state:
        st.session_state.metricas_ml = None
    if "registros_cifrados" not in st.session_state:
        st.session_state.registros_cifrados = {}
    if "aes_payload"        not in st.session_state:
        st.session_state.aes_payload = None
    if "aes_result"         not in st.session_state:
        st.session_state.aes_result = None
    if "rsa_firma"          not in st.session_state:
        st.session_state.rsa_firma = None
    if "rsa_msg"            not in st.session_state:
        st.session_state.rsa_msg = None
    if "rsa_result"         not in st.session_state:
        st.session_state.rsa_result = None
    if "bc_msg"             not in st.session_state:
        st.session_state.bc_msg = ""
    if "integ_msg"          not in st.session_state:
        st.session_state.integ_msg = ""

init_state()
cipher, signer = init_crypto()
blockchain     = init_blockchain()
df             = st.session_state.df
stats          = estadisticas_generales(df)

# ── iOS 26 Design System CSS (vive dentro de iframes — sin restricciones) ────
IOS_CSS = """
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
<style>
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
:root {
    --blue:       #007AFF;  --blue-dk:  #0051C3;  --blue-lt:   rgba(0,122,255,.10);
    --green:      #34C759;  --green-lt: rgba(52,199,89,.10);
    --orange:     #FF9500;  --orange-lt:rgba(255,149,0,.10);
    --red:        #FF3B30;  --red-lt:   rgba(255,59,48,.10);
    --purple:     #AF52DE;  --teal:     #5AC8FA;
    --dark:       #1C1C1E;  --sec:      #3C3C43;   --ter:  #6C6C70;  --qua: #8E8E93;
    --g3: #C7C7CC;  --g5: #E5E5EA;  --g6: #F2F2F7;  --white: #FFFFFF;
    --glass:      rgba(255,255,255,.75);
    --glass-hvy:  rgba(255,255,255,.92);
    --glass-brd:  rgba(255,255,255,.60);
    --shd:  0 2px 24px rgba(0,0,0,.07), 0 1px 2px rgba(0,0,0,.04);
    --shd2: 0 8px 40px rgba(0,0,0,.10), 0 2px 8px rgba(0,0,0,.06);
    --r-sm:12px; --r-md:18px; --r-lg:22px; --r-pill:999px;
    --font:'Inter',-apple-system,BlinkMacSystemFont,sans-serif;
    --mono:'SF Mono','Fira Code',monospace;
    --spring:cubic-bezier(.34,1.56,.64,1);
    --ease:  cubic-bezier(.16,1,.3,1);
}
html,body { font-family:var(--font); background:transparent; color:var(--dark);
            -webkit-font-smoothing:antialiased; font-size:14px; line-height:1.5; }

/* App shell */
.app { min-height:100vh;
       background:linear-gradient(160deg,#EEF3FF 0%,#F2F2F7 40%,#F0EEF7 100%); }

/* Navbar */
.navbar {
    position:sticky; top:0; z-index:100;
    background:rgba(242,242,247,.82);
    backdrop-filter:saturate(180%) blur(24px);
    -webkit-backdrop-filter:saturate(180%) blur(24px);
    border-bottom:1px solid var(--g5);
    padding:0 28px;
    display:flex; align-items:center; height:60px; gap:0;
}
.navbar-brand { display:flex; align-items:center; gap:10px; margin-right:32px; }
.navbar-icon {
    width:36px; height:36px;
    background:linear-gradient(145deg,#007AFF,#5AC8FA 60%,#34C9A0);
    border-radius:10px; display:flex; align-items:center; justify-content:center;
    font-size:18px;
    box-shadow:0 3px 10px rgba(0,122,255,.30), inset 0 1px 0 rgba(255,255,255,.3);
}
.navbar-name { font-size:16px; font-weight:700; letter-spacing:-.3px; }
.navbar-sub  { font-size:11px; color:var(--ter); }

/* Segmented nav */
.nav-tabs { display:flex; gap:2px; background:rgba(118,118,128,.12);
            border-radius:var(--r-sm); padding:3px; margin-left:auto; }
.nav-tab  { padding:7px 16px; border-radius:10px; font-size:13px; font-weight:500;
            color:var(--ter); cursor:pointer; border:none; background:none;
            transition:all .15s var(--ease); white-space:nowrap; font-family:var(--font); }
.nav-tab.active { background:var(--white); color:var(--dark); font-weight:600;
                  box-shadow:0 1px 6px rgba(0,0,0,.10); }
.nav-tab:hover:not(.active) { background:rgba(0,0,0,.05); }

/* Page padding */
.page { padding:28px 28px 48px; }

/* Section label */
.lbl { font-size:11px; font-weight:700; text-transform:uppercase;
       letter-spacing:.7px; color:var(--qua); margin-bottom:12px; margin-left:2px; }

/* Glass card */
.card {
    background:var(--glass-hvy);
    backdrop-filter:saturate(160%) blur(20px);
    -webkit-backdrop-filter:saturate(160%) blur(20px);
    border-radius:var(--r-lg); border:1px solid var(--glass-brd);
    box-shadow:var(--shd); padding:22px 24px;
    position:relative; overflow:hidden;
    transition:box-shadow .22s var(--ease), transform .22s var(--ease);
}
.card::before {
    content:''; position:absolute; top:0; left:0; right:0; height:1px;
    background:linear-gradient(90deg,transparent,rgba(255,255,255,.9) 40%,
        rgba(255,255,255,1) 50%,rgba(255,255,255,.9) 60%,transparent);
    pointer-events:none;
}
.card:hover { box-shadow:var(--shd2); transform:translateY(-1px); }

/* KPIs */
.kpi-grid { display:grid; grid-template-columns:repeat(5,1fr); gap:12px; margin-bottom:24px; }
.kpi {
    background:var(--glass-hvy); backdrop-filter:blur(16px);
    border-radius:var(--r-md); border:1px solid var(--glass-brd);
    box-shadow:var(--shd); padding:18px 16px 14px;
    position:relative; overflow:hidden;
    transition:transform .2s var(--spring);
}
.kpi:hover { transform:translateY(-3px); box-shadow:var(--shd2); }
.kpi::after { content:''; position:absolute; top:0; left:0; right:0;
              height:3px; border-radius:var(--r-md) var(--r-md) 0 0; }
.kpi.blue::after   { background:var(--blue); }
.kpi.green::after  { background:var(--green); }
.kpi.orange::after { background:var(--orange); }
.kpi.red::after    { background:var(--red); }
.kpi.purple::after { background:var(--purple); }
.kpi-val { font-size:30px; font-weight:700; letter-spacing:-.5px; line-height:1.1; margin-top:6px; }
.kpi.blue   .kpi-val { color:var(--blue); }
.kpi.green  .kpi-val { color:var(--green); }
.kpi.orange .kpi-val { color:var(--orange); }
.kpi.red    .kpi-val { color:var(--red); }
.kpi.purple .kpi-val { color:var(--purple); }
.kpi-lbl { font-size:10.5px; font-weight:600; text-transform:uppercase;
           letter-spacing:.5px; color:var(--qua); }
.kpi-sub { font-size:11px; color:var(--ter); margin-top:4px; }

/* Charts */
.charts-row { display:grid; grid-template-columns:1fr 1fr; gap:16px; margin-bottom:20px; }
.chart-card { background:var(--glass-hvy); border-radius:var(--r-lg);
              border:1px solid var(--glass-brd); box-shadow:var(--shd);
              padding:18px 20px; overflow:hidden; position:relative; }
.chart-card::before { content:''; position:absolute; top:0; left:0; right:0; height:1px;
    background:linear-gradient(90deg,transparent,rgba(255,255,255,.9),transparent); }
.chart-card img { width:100%; border-radius:var(--r-sm); display:block; }

/* Table */
.tbl-wrap { background:var(--glass-hvy); border-radius:var(--r-lg);
            border:1px solid var(--glass-brd); box-shadow:var(--shd); overflow:hidden; }
table { width:100%; border-collapse:collapse; font-size:12.5px; }
thead th { background:rgba(0,122,255,.06); color:var(--blue); font-weight:600;
           font-size:11px; text-transform:uppercase; letter-spacing:.5px;
           padding:10px 14px; text-align:left; border-bottom:1px solid var(--g5); }
tbody tr { border-bottom:1px solid rgba(0,0,0,.04); transition:background .1s; }
tbody tr:hover { background:rgba(0,122,255,.03); }
tbody td { padding:10px 14px; color:var(--sec); }
.badge { display:inline-flex; align-items:center; gap:4px; padding:3px 10px;
         border-radius:var(--r-pill); font-size:11px; font-weight:600; }
.badge-red   { background:var(--red-lt);   color:var(--red); }
.badge-green { background:var(--green-lt); color:var(--green); }

/* Alert */
.alert { border-radius:var(--r-md); padding:13px 16px; font-size:13px;
         line-height:1.55; margin:10px 0; border:1px solid transparent;
         display:flex; gap:10px; align-items:flex-start; }
.alert-icon { font-size:15px; flex-shrink:0; margin-top:1px; }
.alert-info  { background:rgba(0,122,255,.07);  border-color:rgba(0,122,255,.20); color:#004AAD; }
.alert-ok    { background:rgba(52,199,89,.07);  border-color:rgba(52,199,89,.25); color:#186D2E; }
.alert-warn  { background:rgba(255,149,0,.07);  border-color:rgba(255,149,0,.25); color:#7A4200; }
.alert-error { background:rgba(255,59,48,.07);  border-color:rgba(255,59,48,.20); color:#A00000; }

/* Code */
.code-lbl { font-size:10px; font-weight:700; text-transform:uppercase;
            letter-spacing:.7px; color:var(--qua); margin-bottom:6px; }
.code-block { background:#1C1C1E; border-radius:var(--r-md); padding:16px 18px;
              font-family:var(--mono); font-size:12px; color:#5AC8FA; line-height:1.7;
              overflow-x:auto; white-space:pre; margin:10px 0;
              border:1px solid rgba(255,255,255,.06); }

/* Blockchain */
.chain { display:flex; flex-direction:column; gap:4px; }
.chain-block { background:var(--glass-hvy); border:1px solid var(--glass-brd);
               border-radius:var(--r-md); padding:12px 16px;
               font-family:var(--mono); font-size:11.5px; line-height:1.6;
               position:relative; overflow:hidden;
               transition:transform .2s var(--ease); }
.chain-block:hover { transform:translateX(4px); }
.chain-block::before { content:''; position:absolute; top:0; left:0; right:0; height:1px;
    background:linear-gradient(90deg,transparent,rgba(255,255,255,.9),transparent); }
.chain-block.genesis { background:rgba(0,122,255,.05); border-color:rgba(0,122,255,.25); }
.chain-idx   { font-size:10px; font-weight:700; color:var(--blue); font-family:var(--font);
               text-transform:uppercase; letter-spacing:.7px; margin-bottom:4px; }
.chain-hash  { color:var(--qua); font-size:10.5px; }
.chain-arrow { text-align:center; color:var(--g3); font-size:14px; line-height:1.8; }

/* Layouts */
.two-col   { display:grid; grid-template-columns:1fr 1fr;     gap:16px; }
.three-col { display:grid; grid-template-columns:1fr 1fr 1fr; gap:12px; }

/* Stat boxes (análisis individual) */
.stats-grid { display:grid; grid-template-columns:repeat(3,1fr); gap:10px; margin-bottom:14px; }
.stat { background:var(--g6); border-radius:var(--r-sm); padding:14px; }
.stat-val { font-size:22px; font-weight:700; }
.stat-lbl { font-size:10px; color:var(--qua); text-transform:uppercase;
            letter-spacing:.5px; font-weight:600; margin-top:2px; }

/* Recs */
.rec { padding:9px 0; font-size:13px; color:var(--sec);
       border-bottom:1px solid rgba(0,0,0,.05); display:flex; gap:8px; }
.rec:last-child { border-bottom:none; }

/* Scrollbar */
::-webkit-scrollbar { width:5px; height:5px; }
::-webkit-scrollbar-track { background:transparent; }
::-webkit-scrollbar-thumb { background:var(--g3); border-radius:10px; }
code { font-family:var(--mono); font-size:.9em;
       background:rgba(0,0,0,.06); border-radius:4px; padding:1px 5px; }
</style>
"""

NAVBAR_HIDE = """
<style>
/* Ocultar botonera de navegación Streamlit (solo usada para lógica) */
div[data-testid="stHorizontalBlock"]:first-of-type {
    height:0 !important; overflow:hidden !important;
    margin:0 !important; padding:0 !important; min-height:0 !important;
}
div[data-testid="stHorizontalBlock"]:first-of-type button { display:none !important; }
</style>
"""

# ── Navegación (botones invisibles = hooks Python) ────────────────────────────
PAGES = [
    ("dashboard",  "📊 Dashboard"),
    ("individual", "🔍 Análisis Individual"),
    ("crypto",     "🔐 Criptografía"),
    ("blockchain", "⛓ Blockchain"),
    ("ml",         "🤖 Predicción ML"),
]

cols_nav = st.columns(len(PAGES))
for i, (pid, lbl) in enumerate(PAGES):
    with cols_nav[i]:
        if st.button(lbl, key=f"nav_{pid}", use_container_width=True):
            st.session_state.pagina = pid
            st.rerun()

st.markdown(NAVBAR_HIDE, unsafe_allow_html=True)

pagina = st.session_state.pagina

# Navbar visual HTML
def make_navbar(active):
    tabs_html = "".join(
        f'<div class="nav-tab {"active" if pid==active else ""}">{lbl}</div>'
        for pid, lbl in PAGES
    )
    return f"""{IOS_CSS}
    <div class="navbar">
        <div class="navbar-brand">
            <div class="navbar-icon">🎓</div>
            <div>
                <div class="navbar-name">EduAnalytics</div>
                <div class="navbar-sub">Learning Analytics · Criptografía · Blockchain</div>
            </div>
        </div>
        <div class="nav-tabs">{tabs_html}</div>
    </div>"""

components.html(make_navbar(pagina), height=68, scrolling=False)


# ═══════════════════════════════════════════════════════════════════════════════
# PÁGINA 1 — DASHBOARD
# ═══════════════════════════════════════════════════════════════════════════════
if pagina == "dashboard":

    chart_notas   = fig_to_b64(fig_distribucion_notas(df))
    chart_scatter = fig_to_b64(fig_asistencia_vs_nota(df))

    filas = ""
    for _, r in df.iterrows():
        badge = ('<span class="badge badge-red">⚠ En riesgo</span>'
                 if r["en_riesgo"] else
                 '<span class="badge badge-green">✓ Ok</span>')
        filas += f"""<tr>
            <td style="font-family:monospace;font-size:11px">{r['id_estudiante']}</td>
            <td><b>{r['nota_media']:.1f}</b></td>
            <td>{r['asistencia_pct']:.1f}%</td>
            <td>{r['participacion_foro']}</td>
            <td>{r['tareas_entregadas']}/{int(r['total_tareas'])}</td>
            <td style="font-family:monospace">{r['indice_riesgo']:.3f}</td>
            <td>{badge}</td>
        </tr>"""

    # Botones de datos
    st.markdown("""
    <style>
    div[data-testid="stHorizontalBlock"].data-controls { margin: 4px 28px 0 !important;
        height:auto !important; overflow:visible !important; }
    </style>""", unsafe_allow_html=True)

    c1, c2, c3 = st.columns([1.5, 1, 3])
    with c1:
        n_est = st.slider("Estudiantes", 10, 50, 20, label_visibility="collapsed")
    with c2:
        if st.button("🔄 Regenerar dataset"):
            st.session_state.df = calcular_riesgo(generar_dataset(n_estudiantes=n_est))
            st.rerun()
    with c3:
        up = st.file_uploader("CSV", type=["csv"], label_visibility="collapsed")
        if up:
            try:
                st.session_state.df = calcular_riesgo(cargar_csv(up))
                st.rerun()
            except Exception as e:
                st.error(str(e))

    html = f"""{IOS_CSS}
    <div class="app"><div class="page">

        <div class="kpi-grid">
            <div class="kpi blue">
                <div class="kpi-lbl">Estudiantes</div>
                <div class="kpi-val">{stats['total_estudiantes']}</div>
            </div>
            <div class="kpi green">
                <div class="kpi-lbl">Nota Media</div>
                <div class="kpi-val">{stats['nota_media_grupo']:.1f}</div>
                <div class="kpi-sub">sobre 10</div>
            </div>
            <div class="kpi blue">
                <div class="kpi-lbl">Asistencia</div>
                <div class="kpi-val">{stats['asistencia_media']:.1f}%</div>
            </div>
            <div class="kpi red">
                <div class="kpi-lbl">En Riesgo</div>
                <div class="kpi-val">{stats['en_riesgo']}</div>
                <div class="kpi-sub">{stats['pct_riesgo']}% del grupo</div>
            </div>
            <div class="kpi orange">
                <div class="kpi-lbl">Entrega Tareas</div>
                <div class="kpi-val">{stats['tasa_entrega_media']}%</div>
            </div>
        </div>

        <div class="charts-row">
            <div class="chart-card">
                <p class="lbl">Distribución de Notas</p>
                <img src="{chart_notas}" alt="Notas">
            </div>
            <div class="chart-card">
                <p class="lbl">Asistencia vs Rendimiento</p>
                <img src="{chart_scatter}" alt="Scatter">
            </div>
        </div>

        <p class="lbl">Listado de Estudiantes</p>
        <div class="tbl-wrap">
            <table>
                <thead><tr>
                    <th>ID</th><th>Nota</th><th>Asistencia</th>
                    <th>Foro</th><th>Tareas</th><th>Índice Riesgo</th><th>Estado</th>
                </tr></thead>
                <tbody>{filas}</tbody>
            </table>
        </div>
    </div></div>"""
    components.html(html, height=1160, scrolling=True)


# ═══════════════════════════════════════════════════════════════════════════════
# PÁGINA 2 — ANÁLISIS INDIVIDUAL
# ═══════════════════════════════════════════════════════════════════════════════
elif pagina == "individual":

    sid = st.selectbox("Seleccionar estudiante", df["id_estudiante"].tolist(),
                       label_visibility="collapsed")
    st.markdown("""<style>
    div[data-testid="stSelectbox"] { max-width:360px; margin:12px 28px 4px; }
    div[data-testid="stSelectbox"] > div > div {
        border-radius:12px !important; border:1px solid rgba(0,0,0,.12) !important;
        font-size:14px !important; background:rgba(255,255,255,.9) !important; }
    </style>""", unsafe_allow_html=True)

    row  = df[df["id_estudiante"] == sid].iloc[0]
    recs_list = recomendaciones(row)
    chart_radar = fig_to_b64(fig_radar_estudiante(row), dpi=130)
    chart_gauge = fig_to_b64(fig_riesgo_gauge(float(row["indice_riesgo"])), dpi=130)

    nota_cols = sorted(
        [c for c in df.columns if c.startswith("nota_") and c != "nota_media"],
        key=lambda x: -row[x]
    )
    notas_rows = "".join(
        f'<tr><td>{c.replace("nota_","").replace("_"," ").title()}</td>'
        f'<td style="font-weight:600;color:{"#34C759" if row[c]>=7 else "#FF9500" if row[c]>=5 else "#FF3B30"}">'
        f'{row[c]:.2f}</td></tr>'
        for c in nota_cols
    )
    recs_html = "".join(f'<div class="rec"><span>{r}</span></div>' for r in recs_list)
    riesgo_c  = "#FF3B30" if row["indice_riesgo"]>.6 else "#FF9500" if row["indice_riesgo"]>.35 else "#34C759"
    nivel     = "ALTO" if row["indice_riesgo"]>.6 else "MEDIO" if row["indice_riesgo"]>.35 else "BAJO"

    html = f"""{IOS_CSS}
    <div class="page" style="padding-top:12px">
        <div class="two-col" style="margin-bottom:16px">

            <div>
                <p class="lbl">Métricas del Estudiante</p>
                <div class="card" style="margin-bottom:12px">
                    <div class="stats-grid">
                        <div class="stat"><div class="stat-val" style="color:#007AFF">{row['nota_media']:.1f}</div><div class="stat-lbl">Nota Media</div></div>
                        <div class="stat"><div class="stat-val" style="color:#34C759">{row['asistencia_pct']:.1f}%</div><div class="stat-lbl">Asistencia</div></div>
                        <div class="stat"><div class="stat-val" style="color:#FF9500">{row['tareas_entregadas']}/{int(row['total_tareas'])}</div><div class="stat-lbl">Tareas</div></div>
                        <div class="stat"><div class="stat-val" style="color:#5856D6">{row['participacion_foro']}</div><div class="stat-lbl">Participación</div></div>
                        <div class="stat"><div class="stat-val" style="color:#AF52DE">{row['tiempo_plataforma_h']:.0f}h</div><div class="stat-lbl">Tiempo Online</div></div>
                        <div class="stat" style="background:{riesgo_c}14;border:1px solid {riesgo_c}30">
                            <div class="stat-val" style="color:{riesgo_c}">{row['indice_riesgo']:.3f}</div>
                            <div class="stat-lbl" style="color:{riesgo_c}">Riesgo {nivel}</div>
                        </div>
                    </div>
                </div>
                <p class="lbl">Indicador de Riesgo</p>
                <div class="card">
                    <img src="{chart_gauge}" style="width:65%;margin:0 auto;display:block">
                </div>
            </div>

            <div>
                <p class="lbl">Perfil Multidimensional</p>
                <div class="card" style="margin-bottom:12px">
                    <img src="{chart_radar}" style="width:100%">
                </div>
                <p class="lbl">Notas por Asignatura</p>
                <div class="tbl-wrap">
                    <table><thead><tr><th>Asignatura</th><th>Nota</th></tr></thead>
                    <tbody>{notas_rows}</tbody></table>
                </div>
            </div>
        </div>

        <p class="lbl">Recomendaciones Personalizadas</p>
        <div class="card">{recs_html}</div>
    </div>"""
    components.html(html, height=1080, scrolling=True)


# ═══════════════════════════════════════════════════════════════════════════════
# PÁGINA 3 — CRIPTOGRAFÍA
# ═══════════════════════════════════════════════════════════════════════════════
elif pagina == "crypto":

    sub = st.radio("", ["🔑 AES-256-GCM", "✍ Firma RSA", "📋 Cifrado Masivo"],
                   horizontal=True, label_visibility="collapsed")
    st.markdown("""<style>
    div[data-testid="stRadio"] { margin: 8px 28px 0; }
    div[data-testid="stRadio"] > div { gap:6px; }
    div[data-testid="stRadio"] label {
        background:rgba(255,255,255,.85); border-radius:10px !important;
        border:1px solid rgba(0,0,0,.1) !important; padding:6px 16px !important;
        font-size:13px !important; font-weight:500 !important;
    }
    div[data-testid="stRadio"] label[data-checked="true"] {
        background:#007AFF !important; color:white !important; border-color:#007AFF !important;
    }
    div[data-testid="stTextArea"]  { margin:8px 28px 8px; }
    div[data-testid="stTextArea"] textarea {
        border-radius:12px !important; font-size:13px !important;
        background:rgba(255,255,255,.9) !important; border:1px solid rgba(0,0,0,.12) !important; }
    div[data-testid="stTextInput"] { margin:8px 28px 8px; }
    div[data-testid="stTextInput"] input {
        border-radius:12px !important; font-size:13px !important;
        background:rgba(255,255,255,.9) !important; border:1px solid rgba(0,0,0,.12) !important; }
    div[data-testid="stMultiSelect"] { margin:8px 28px 8px; }
    div[data-testid="stSelectbox"]   { margin:8px 28px 8px; }
    div[data-testid="stSelectbox"] > div > div {
        border-radius:12px !important; background:rgba(255,255,255,.9) !important; }
    /* Botones acción */
    section[data-testid="stMain"] button:not([data-testid]) {
        border-radius:10px !important; background:#007AFF !important;
        color:white !important; border:none !important; font-weight:600 !important;
        font-size:13px !important; transition:all .15s !important;
    }
    section[data-testid="stMain"] button:not([data-testid]):hover {
        background:#0066DD !important; transform:scale(1.02) !important; }
    div[data-testid="stHorizontalBlock"] { height:auto !important; overflow:visible !important;
        margin:0 28px !important; }
    </style>""", unsafe_allow_html=True)

    # ── AES ──
    if sub == "🔑 AES-256-GCM":
        texto = st.text_area("Texto a cifrar",
                             "Nombre: Ana García | Nota: 8.7 | DNI: 12345678A",
                             height=72, label_visibility="collapsed")
        c1, c2, c3 = st.columns([1,1,2])
        with c1:
            if st.button("🔒 Cifrar", use_container_width=True):
                st.session_state.aes_payload = cipher.encrypt(texto)
                st.session_state.aes_result  = None
        with c2:
            if st.button("🔓 Descifrar", use_container_width=True):
                if st.session_state.aes_payload:
                    try:
                        dec = cipher.decrypt(st.session_state.aes_payload)
                        st.session_state.aes_result = ("ok", dec)
                    except Exception as e:
                        st.session_state.aes_result = ("err", str(e))
        with c3:
            if st.button("🧪 Simular ataque (corromper ciphertext)", use_container_width=True):
                if st.session_state.aes_payload:
                    p = dict(st.session_state.aes_payload)
                    p["ciphertext"] = p["ciphertext"][:-4] + "XXXX"
                    try:
                        cipher.decrypt(p)
                    except ValueError as e:
                        st.session_state.aes_result = ("attack", str(e))

        payload = st.session_state.aes_payload
        aes_res = st.session_state.aes_result

        payload_html = ""
        if payload:
            payload_html = f"""
            <div class="code-lbl">Resultado cifrado AES-256-GCM</div>
            <div class="code-block">nonce:      {payload['nonce']}
ciphertext: {payload['ciphertext'][:72]}…</div>"""

        result_html = ""
        if aes_res:
            kind, msg = aes_res
            if kind == "ok":
                result_html = f'<div class="alert alert-ok"><span class="alert-icon">✓</span><span>Descifrado correcto: <b>{msg}</b></span></div>'
            else:
                result_html = f'<div class="alert alert-error"><span class="alert-icon">✗</span><span>{msg}</span></div>'

        components.html(f"""{IOS_CSS}<div class="page" style="padding-top:10px">
            <div class="alert alert-info"><span class="alert-icon">ℹ</span>
            <span><b>AES-256-GCM</b> — Cifrado autenticado (AEAD). Clave 256 bits,
            nonce aleatorio 96 bits/operación. Confidencialidad + integridad en una sola pasada.
            Estándar NIST SP 800-38D. Cualquier modificación del ciphertext levanta
            <code>InvalidTag</code> de forma automática.</span></div>
            {payload_html}{result_html}
        </div>""", height=340, scrolling=False)

    # ── RSA ──
    elif sub == "✍ Firma RSA":
        msg_input = st.text_input("Mensaje a firmar",
                                  "Registro académico · EST-A1B2C3D4 · Nota: 8.5",
                                  label_visibility="collapsed")
        c1, c2, c3 = st.columns([1,1,1.5])
        with c1:
            if st.button("✍ Firmar", use_container_width=True):
                st.session_state.rsa_firma  = signer.sign(msg_input)
                st.session_state.rsa_msg    = msg_input
                st.session_state.rsa_result = None
        with c2:
            if st.button("✅ Verificar firma", use_container_width=True):
                if st.session_state.rsa_firma:
                    ok = signer.verify(msg_input, st.session_state.rsa_firma)
                    st.session_state.rsa_result = ("ok" if ok else "err")
        with c3:
            if st.button("🧪 Verificar con mensaje alterado", use_container_width=True):
                if st.session_state.rsa_firma:
                    ok = signer.verify("Mensaje ALTERADO 🔴", st.session_state.rsa_firma)
                    st.session_state.rsa_result = "attack"

        firma   = st.session_state.rsa_firma
        rsa_res = st.session_state.rsa_result

        firma_html  = ""
        if firma:
            firma_html = f"""<div class="code-lbl">Firma RSA-2048 + SHA-256 (Base64)</div>
            <div class="code-block">{firma[:88]}…</div>"""

        result_html = ""
        if rsa_res == "ok":
            result_html = '<div class="alert alert-ok"><span class="alert-icon">✓</span><span>Firma válida — autenticidad e integridad confirmadas.</span></div>'
        elif rsa_res == "attack":
            result_html = '<div class="alert alert-error"><span class="alert-icon">✗</span><span>Firma inválida para el mensaje alterado. El sistema detecta la manipulación correctamente.</span></div>'
        elif rsa_res == "err":
            result_html = '<div class="alert alert-error"><span class="alert-icon">✗</span><span>Firma inválida.</span></div>'

        pem = signer.export_public_key_pem()
        pem_html = f'<div class="code-lbl" style="margin-top:16px">Clave pública RSA (PEM)</div><div class="code-block" style="font-size:10px;color:#8E8E93">{pem[:280]}…</div>'

        components.html(f"""{IOS_CSS}<div class="page" style="padding-top:10px">
            <div class="alert alert-info"><span class="alert-icon">ℹ</span>
            <span><b>RSA-2048 + SHA-256 (PKCS#1v15)</b> — La firma digital garantiza autenticidad
            (el mensaje proviene del firmante) y no repudio (no puede negarlo).
            Cada bloque de la blockchain se firma con esta clave.</span></div>
            {firma_html}{result_html}{pem_html}
        </div>""", height=440, scrolling=False)

    # ── Cifrado masivo ──
    else:
        cols_opts = ["nombre_real","nota_media","asistencia_pct","indice_riesgo"]
        sel_cols  = st.multiselect("Columnas a cifrar", cols_opts,
                                   default=["nombre_real","nota_media"],
                                   label_visibility="collapsed")
        c1, c2 = st.columns([1,3])
        with c1:
            if st.button("🔒 Cifrar dataset"):
                with st.spinner("Cifrando…"):
                    st.session_state.registros_cifrados = cifrar_columnas_df(df, sel_cols, cipher)

        cifrado_html = dec_html = ""
        if st.session_state.registros_cifrados:
            ej_id = list(st.session_state.registros_cifrados.keys())[0]
            ej    = st.session_state.registros_cifrados[ej_id]
            cifrado_html = f'<div class="code-lbl">Registro {ej_id} — cifrado AES-256-GCM</div><div class="code-block">{json.dumps(ej, indent=2)[:400]}…</div>'

            id_sel = st.selectbox("Descifrar registro:", list(st.session_state.registros_cifrados.keys()),
                                   label_visibility="collapsed")
            if st.button("🔓 Descifrar registro"):
                desc = descifrar_registro(st.session_state.registros_cifrados[id_sel], cipher)
                dec_html = f'<div class="code-lbl">Resultado descifrado — {id_sel}</div><div class="code-block">{json.dumps(desc, indent=2, ensure_ascii=False)}</div>'

        components.html(f"""{IOS_CSS}<div class="page" style="padding-top:10px">
            <div class="alert alert-info"><span class="alert-icon">ℹ</span>
            <span>Cifrado GDPR: datos sensibles cifrados con AES-256-GCM antes de almacenarse.
            Solo usuarios con la clave pueden descifrarlos. Los IDs son pseudoanonimizados con SHA-256.</span></div>
            {cifrado_html}{dec_html}
        </div>""", height=480, scrolling=True)


# ═══════════════════════════════════════════════════════════════════════════════
# PÁGINA 4 — BLOCKCHAIN
# ═══════════════════════════════════════════════════════════════════════════════
elif pagina == "blockchain":

    st.markdown("""<style>
    div[data-testid="stSelectbox"]  { margin:6px 0; }
    div[data-testid="stTextInput"]  { margin:6px 0; }
    div[data-testid="stCheckbox"]   { margin:6px 0 10px; }
    div[data-testid="stSelectbox"] > div > div {
        border-radius:12px !important; background:rgba(255,255,255,.9) !important;
        border:1px solid rgba(0,0,0,.12) !important; font-size:13px !important; }
    div[data-testid="stTextInput"] input {
        border-radius:12px !important; background:rgba(255,255,255,.9) !important;
        border:1px solid rgba(0,0,0,.12) !important; font-size:13px !important; }
    section[data-testid="stMain"] button:not([data-testid]) {
        border-radius:10px !important; background:#007AFF !important;
        color:white !important; border:none !important; font-weight:600 !important;
        font-size:13px !important; margin-bottom:6px !important; }
    div[data-testid="stHorizontalBlock"] { height:auto !important; overflow:visible !important; margin:0 !important; }
    div[data-testid="stColumn"] { padding:0 6px !important; }
    </style>""", unsafe_allow_html=True)

    c1, c2 = st.columns([1.2, 1])
    with c1:
        st.markdown("**Registrar evento educativo**")
        sid_bc  = st.selectbox("Est.", df["id_estudiante"].tolist(), label_visibility="collapsed")
        evento  = st.selectbox("Tipo", ["CALIFICACIÓN","ASISTENCIA","TAREA_ENTREGADA",
                                         "ACCESO_PLATAFORMA","EXAMEN","FEEDBACK"],
                                label_visibility="collapsed")
        detalle = st.text_input("Detalle", placeholder="ej. Nota: 8.5 · Matemáticas",
                                label_visibility="collapsed")
        firmar  = st.checkbox("✍ Firmar con RSA", value=True)
        if st.button("⛓ Añadir bloque", use_container_width=True):
            with st.spinner("Minando…"):
                blq = blockchain.agregar_registro_estudiante(
                    sid_bc, evento, {"valor": detalle},
                    signer=signer if firmar else None)
            st.session_state.bc_msg = f'<div class="alert alert-ok"><span class="alert-icon">✓</span><span>Bloque #{blq.index} minado · Hash: <code>{blq.hash_propio[:20]}…</code> · Nonce: {blq.nonce}</span></div>'
            st.session_state.integ_msg = ""
            st.rerun()

    with c2:
        st.markdown("**Verificación de integridad**")
        if st.button("🔍 Verificar cadena completa", use_container_width=True):
            r = blockchain.verificar_integridad()
            if r["integra"]:
                st.session_state.integ_msg = f'<div class="alert alert-ok"><span class="alert-icon">✓</span><span>Cadena íntegra · {r["total_bloques"]} bloques verificados correctamente.</span></div>'
            else:
                st.session_state.integ_msg = f'<div class="alert alert-error"><span class="alert-icon">✗</span><span>Integridad comprometida: {", ".join(r["errores"])}</span></div>'
            st.rerun()
        if st.button("🧪 Simular manipulación (demo)", use_container_width=True):
            if len(blockchain.cadena) > 1:
                blockchain.manipular_bloque_demo(1, "DATOS_ALTERADOS")
                st.session_state.integ_msg = '<div class="alert alert-warn"><span class="alert-icon">⚠</span><span>Bloque 1 manipulado. Pulsa verificar para detectarlo.</span></div>'
                st.rerun()

    # Cadena visual
    chain_html = ""
    for i, blq in enumerate(blockchain.cadena[-10:]):
        is_gen    = blq.index == 0
        firma_ln  = f'<div class="chain-hash">✍ firma: {blq.firma[:22]}…</div>' if blq.firma else ""
        arrow     = '<div class="chain-arrow">↕</div>' if i < min(10, len(blockchain.cadena)) - 1 else ""
        ts        = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(blq.timestamp))
        chain_html += f"""
        <div class="chain-block {"genesis" if is_gen else ""}">
            <div class="chain-idx">Bloque #{blq.index}{"  ·  GÉNESIS" if is_gen else ""}</div>
            <div>🕐 {ts} · Nonce: {blq.nonce}</div>
            <div class="chain-hash">↑ prev: {blq.hash_anterior[:22]}…</div>
            <div class="chain-hash">🔑 hash: {blq.hash_propio[:22]}…</div>
            {firma_ln}
        </div>{arrow}"""

    html = f"""{IOS_CSS}
    <div class="page" style="padding-top:10px">
        {st.session_state.bc_msg}
        {st.session_state.integ_msg}
        <p class="lbl" style="margin-top:16px">Cadena — últimos {min(10,len(blockchain.cadena))} bloques</p>
        <div class="card">
            <div class="chain">{chain_html}</div>
        </div>
    </div>"""
    components.html(html, height=720, scrolling=True)


# ═══════════════════════════════════════════════════════════════════════════════
# PÁGINA 5 — PREDICCIÓN ML
# ═══════════════════════════════════════════════════════════════════════════════
elif pagina == "ml":

    st.markdown("""<style>
    div[data-testid="stSlider"] { margin:6px 28px; }
    section[data-testid="stMain"] button:not([data-testid]) {
        border-radius:10px !important; background:#007AFF !important;
        color:white !important; border:none !important; font-weight:600 !important;
        font-size:13px !important; }
    div[data-testid="stHorizontalBlock"] { height:auto !important; overflow:visible !important; margin:0 28px !important; }
    hr { margin:12px 28px !important; border-color:#E5E5EA !important; }
    </style>""", unsafe_allow_html=True)

    if st.button("🚀 Entrenar modelo Random Forest"):
        with st.spinner("Entrenando…"):
            m = ModeloRiesgo()
            metricas = m.entrenar(df)
            st.session_state.modelo     = m
            st.session_state.metricas_ml = metricas
        st.rerun()

    acc_html = feat_html = pred_html = manual_html = ""

    if st.session_state.modelo:
        m        = st.session_state.modelo
        metricas = st.session_state.metricas_ml
        acc      = metricas["accuracy"]
        rep      = metricas["report"]
        prec     = rep.get("1", {}).get("precision", 0)
        rec_val  = rep.get("1", {}).get("recall", 0)

        chart_feat = fig_to_b64(fig_importancia_features(metricas["importancias"]), dpi=130)

        probs   = m.predecir(df)
        df_pred = df[["id_estudiante","nota_media","asistencia_pct","en_riesgo"]].copy()
        df_pred["prob_ml"] = probs.round(3)
        df_pred["pred_ml"] = (probs > 0.5).astype(int)

        filas_pred = ""
        for _, r in df_pred.iterrows():
            match = "✅" if r["en_riesgo"] == r["pred_ml"] else "❌"
            col   = "#FF3B30" if r["pred_ml"] == 1 else "#34C759"
            filas_pred += f"""<tr>
                <td style="font-family:monospace;font-size:11px">{r['id_estudiante']}</td>
                <td>{r['nota_media']:.1f}</td>
                <td>{r['asistencia_pct']:.1f}%</td>
                <td>{"Sí" if r["en_riesgo"] else "No"}</td>
                <td style="color:{col};font-weight:600">{r['prob_ml']:.1%}</td>
                <td>{match}</td>
            </tr>"""

        acc_html = f"""
        <div class="three-col" style="margin-bottom:18px">
            <div class="card" style="text-align:center">
                <div style="font-size:34px;font-weight:700;color:#007AFF">{acc:.1%}</div>
                <div class="lbl" style="margin:4px 0 0">Accuracy</div>
            </div>
            <div class="card" style="text-align:center">
                <div style="font-size:34px;font-weight:700;color:#34C759">{prec:.1%}</div>
                <div class="lbl" style="margin:4px 0 0">Precision (riesgo)</div>
            </div>
            <div class="card" style="text-align:center">
                <div style="font-size:34px;font-weight:700;color:#FF9500">{rec_val:.1%}</div>
                <div class="lbl" style="margin:4px 0 0">Recall (riesgo)</div>
            </div>
        </div>"""

        feat_html = f"""
        <p class="lbl">Importancia de Variables</p>
        <div class="card" style="margin-bottom:16px">
            <img src="{chart_feat}" style="width:100%;border-radius:8px">
        </div>"""

        pred_html = f"""
        <p class="lbl">Predicciones — Dataset Completo</p>
        <div class="tbl-wrap" style="margin-bottom:20px">
            <table>
                <thead><tr><th>ID</th><th>Nota</th><th>Asistencia</th>
                <th>Riesgo Real</th><th>Prob. ML</th><th>Acierto</th></tr></thead>
                <tbody>{filas_pred}</tbody>
            </table>
        </div>"""

    # Predicción manual
    st.markdown("---")
    st.markdown("**Predicción manual — nuevo estudiante**")
    c1, c2, c3 = st.columns(3)
    nota_n   = c1.slider("Nota media",           0.0, 10.0, 6.0, 0.1)
    asist_n  = c2.slider("Asistencia %",         0,   100,  80)
    parti_n  = c3.slider("Participación foro",   0,   30,   10)
    c4, c5   = st.columns(2)
    tareas_n = c4.slider("Tareas entregadas",    0,   20,   15)
    tiempo_n = c5.slider("Tiempo plataforma (h)",0,   120,  40)

    if st.session_state.modelo:
        nuevo  = pd.DataFrame([{
            "nota_media": nota_n, "asistencia_pct": asist_n,
            "participacion_foro": parti_n, "tareas_entregadas": tareas_n,
            "tiempo_plataforma_h": tiempo_n,
        }])
        prob_n  = float(st.session_state.modelo.predecir(nuevo)[0])
        chart_g = fig_to_b64(fig_riesgo_gauge(prob_n), dpi=120)
        manual_html = f"""
        <p class="lbl">Resultado — Predicción Manual</p>
        <div class="card" style="text-align:center">
            <img src="{chart_g}" style="width:280px;margin:0 auto;display:block">
        </div>"""

    html = f"""{IOS_CSS}
    <div class="page" style="padding-top:10px">
        <div class="alert alert-info"><span class="alert-icon">ℹ</span>
        <span><b>Random Forest</b> — 100 árboles, max_depth=5,
        <code>class_weight='balanced'</code> (corrige desequilibrio 20/80).
        Entrenado con nota media, asistencia, participación, tareas y tiempo online.
        Split 75/25 estratificado.</span></div>
        {acc_html}{feat_html}{pred_html}{manual_html}
    </div>"""
    components.html(html, height=1300, scrolling=True)
