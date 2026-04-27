"""
analytics_module.py
-------------------
Módulo de Learning Analytics:
  - Estadísticas descriptivas de rendimiento estudiantil.
  - Predicción de riesgo de abandono (Random Forest).
  - Recomendaciones personalizadas.
  - Generación de figuras Matplotlib/Plotly-ready.

Referencias:
  https://pandas.pydata.org/docs/
  https://scikit-learn.org/stable/documentation.html
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.gridspec import GridSpec
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report, accuracy_score
from typing import Tuple, Dict, Any, Optional
import warnings

warnings.filterwarnings("ignore")

# Paleta iOS 26 — colores sistema Apple
IOS_PALETTE = {
    "bg": "#F2F2F7",
    "card": "#FFFFFF",
    "blue": "#007AFF",
    "green": "#34C759",
    "orange": "#FF9500",
    "red": "#FF3B30",
    "gray": "#8E8E93",
    "dark": "#1C1C1E",
    "text_secondary": "#6C6C70",
}

FEATURES = [
    "nota_media",
    "asistencia_pct",
    "participacion_foro",
    "tareas_entregadas",
    "tiempo_plataforma_h",
]


# ---------------------------------------------------------------------------
# Estadísticas descriptivas
# ---------------------------------------------------------------------------

def estadisticas_generales(df: pd.DataFrame) -> Dict[str, Any]:
    """Resumen ejecutivo del grupo."""
    en_riesgo = df["en_riesgo"].sum() if "en_riesgo" in df.columns else 0
    return {
        "total_estudiantes": len(df),
        "nota_media_grupo": round(df["nota_media"].mean(), 2),
        "asistencia_media": round(df["asistencia_pct"].mean(), 1),
        "en_riesgo": int(en_riesgo),
        "pct_riesgo": round(en_riesgo / len(df) * 100, 1) if len(df) > 0 else 0,
        "participacion_media": round(df["participacion_foro"].mean(), 1),
        "tasa_entrega_media": round(
            (df["tareas_entregadas"] / df["total_tareas"]).mean() * 100, 1
        ),
    }


def recomendaciones(row: pd.Series) -> list:
    """Genera recomendaciones personalizadas para un estudiante."""
    recs = []
    if row["nota_media"] < 5:
        recs.append("📚 Refuerzo urgente: nota media por debajo de 5. Contactar tutor.")
    elif row["nota_media"] < 7:
        recs.append("📖 Revisar material complementario para mejorar calificaciones.")

    if row["asistencia_pct"] < 70:
        recs.append("⚠️  Asistencia crítica (<70%). Intervención recomendada.")
    elif row["asistencia_pct"] < 85:
        recs.append("📅 Mejorar asistencia — impacto directo en rendimiento.")

    tasa = row["tareas_entregadas"] / row["total_tareas"]
    if tasa < 0.6:
        recs.append("📝 Tasa de entrega de tareas muy baja. Seguimiento personalizado.")
    elif tasa < 0.8:
        recs.append("✏️  Intentar completar más tareas para consolidar conocimientos.")

    if row["participacion_foro"] < 5:
        recs.append("💬 Baja participación en foro. Fomentar interacción con compañeros.")

    if row["tiempo_plataforma_h"] < 15:
        recs.append("⏱️  Tiempo en plataforma insuficiente. Dedicar más horas de estudio online.")

    if not recs:
        recs.append("✅ Rendimiento satisfactorio. ¡Continúa así!")

    return recs


# ---------------------------------------------------------------------------
# Modelo ML: predicción de riesgo de abandono
# ---------------------------------------------------------------------------

class ModeloRiesgo:
    """Random Forest para predecir riesgo de abandono estudiantil."""

    def __init__(self):
        self.model = RandomForestClassifier(
            n_estimators=100,
            max_depth=5,
            random_state=42,
            class_weight="balanced",
        )
        self.scaler = StandardScaler()
        self.entrenado = False
        self.metricas: Dict[str, Any] = {}

    def entrenar(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Entrena el modelo con el DataFrame procesado."""
        X = df[FEATURES].values
        y = df["en_riesgo"].values

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.25, random_state=42, stratify=y
        )

        X_train_s = self.scaler.fit_transform(X_train)
        X_test_s = self.scaler.transform(X_test)

        self.model.fit(X_train_s, y_train)
        y_pred = self.model.predict(X_test_s)

        self.entrenado = True
        self.metricas = {
            "accuracy": round(accuracy_score(y_test, y_pred), 3),
            "report": classification_report(y_test, y_pred, output_dict=True),
            "importancias": dict(zip(FEATURES, self.model.feature_importances_.tolist())),
        }
        return self.metricas

    def predecir(self, df: pd.DataFrame) -> np.ndarray:
        """Devuelve probabilidad de riesgo [0..1] para cada estudiante."""
        if not self.entrenado:
            raise RuntimeError("Modelo no entrenado. Llama a entrenar() primero.")
        X = self.scaler.transform(df[FEATURES].values)
        return self.model.predict_proba(X)[:, 1]  # Prob. clase "en riesgo"


# ---------------------------------------------------------------------------
# Visualizaciones (retornan fig de Matplotlib)
# ---------------------------------------------------------------------------

def _ios_style(ax, title: str = "", xlabel: str = "", ylabel: str = "") -> None:
    """Aplica estilo iOS 26 minimalista a un eje."""
    ax.set_facecolor(IOS_PALETTE["card"])
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.spines["bottom"].set_color("#E5E5EA")
    ax.tick_params(colors=IOS_PALETTE["text_secondary"], labelsize=9)
    ax.xaxis.label.set_color(IOS_PALETTE["text_secondary"])
    ax.yaxis.label.set_color(IOS_PALETTE["text_secondary"])
    if title:
        ax.set_title(title, color=IOS_PALETTE["dark"], fontsize=12, fontweight="600", pad=12)
    if xlabel:
        ax.set_xlabel(xlabel, fontsize=9)
    if ylabel:
        ax.set_ylabel(ylabel, fontsize=9)
    ax.yaxis.set_tick_params(left=False)
    ax.set_axisbelow(True)
    ax.yaxis.grid(True, color="#F2F2F7", linewidth=1)


def fig_distribucion_notas(df: pd.DataFrame) -> plt.Figure:
    fig, ax = plt.subplots(figsize=(8, 4), facecolor=IOS_PALETTE["bg"])
    bins = np.arange(0, 11, 1)
    colors = [IOS_PALETTE["red"] if x < 5 else IOS_PALETTE["orange"] if x < 7
              else IOS_PALETTE["green"] for x in df["nota_media"]]
    ax.bar(range(len(df)), sorted(df["nota_media"]), color=sorted(colors), width=0.7,
           edgecolor="white", linewidth=0.5)
    _ios_style(ax, "Distribución de Notas Medias", "Estudiantes (ordenados)", "Nota Media")
    ax.set_ylim(0, 10)
    ax.axhline(5, color=IOS_PALETTE["red"], linestyle="--", linewidth=1, alpha=0.6, label="Aprobado")
    ax.axhline(7, color=IOS_PALETTE["green"], linestyle="--", linewidth=1, alpha=0.6, label="Notable")
    ax.legend(fontsize=8, framealpha=0)
    fig.tight_layout(pad=2)
    return fig


def fig_asistencia_vs_nota(df: pd.DataFrame) -> plt.Figure:
    fig, ax = plt.subplots(figsize=(7, 4.5), facecolor=IOS_PALETTE["bg"])
    colores = [IOS_PALETTE["red"] if r else IOS_PALETTE["blue"]
               for r in df["en_riesgo"]] if "en_riesgo" in df.columns else IOS_PALETTE["blue"]
    sc = ax.scatter(
        df["asistencia_pct"], df["nota_media"],
        c=colores, alpha=0.8, s=80, edgecolors="white", linewidths=0.8
    )
    _ios_style(ax, "Asistencia vs Nota Media", "Asistencia (%)", "Nota Media")
    patch_r = mpatches.Patch(color=IOS_PALETTE["red"], label="En riesgo")
    patch_b = mpatches.Patch(color=IOS_PALETTE["blue"], label="Sin riesgo")
    ax.legend(handles=[patch_r, patch_b], fontsize=8, framealpha=0)
    ax.set_xlim(0, 105)
    ax.set_ylim(0, 10.5)
    fig.tight_layout(pad=2)
    return fig


def fig_importancia_features(importancias: dict) -> plt.Figure:
    fig, ax = plt.subplots(figsize=(7, 3.5), facecolor=IOS_PALETTE["bg"])
    etiquetas = {
        "nota_media": "Nota Media",
        "asistencia_pct": "Asistencia",
        "participacion_foro": "Participación",
        "tareas_entregadas": "Tareas",
        "tiempo_plataforma_h": "Tiempo Online",
    }
    items = sorted(importancias.items(), key=lambda x: x[1], reverse=True)
    labels = [etiquetas.get(k, k) for k, _ in items]
    valores = [v for _, v in items]
    bars = ax.barh(labels, valores, color=IOS_PALETTE["blue"], edgecolor="white",
                   linewidth=0.5, height=0.55)
    for bar, val in zip(bars, valores):
        ax.text(val + 0.005, bar.get_y() + bar.get_height() / 2,
                f"{val:.2f}", va="center", fontsize=8, color=IOS_PALETTE["text_secondary"])
    _ios_style(ax, "Importancia de Variables (ML)", "Importancia", "")
    ax.invert_yaxis()
    fig.tight_layout(pad=2)
    return fig


def fig_radar_estudiante(row: pd.Series) -> plt.Figure:
    """Gráfico de araña para perfil individual de un estudiante."""
    categorias = ["Nota\nMedia", "Asistencia", "Participación", "Tareas", "Tiempo\nOnline"]
    valores_raw = [
        row["nota_media"] / 10,
        row["asistencia_pct"] / 100,
        min(row["participacion_foro"] / 30, 1),
        row["tareas_entregadas"] / row["total_tareas"],
        min(row["tiempo_plataforma_h"] / 120, 1),
    ]
    N = len(categorias)
    angulos = [n / float(N) * 2 * np.pi for n in range(N)]
    valores = valores_raw + [valores_raw[0]]
    angulos += angulos[:1]

    fig, ax = plt.subplots(figsize=(5, 5), subplot_kw=dict(polar=True),
                           facecolor=IOS_PALETTE["bg"])
    ax.set_facecolor(IOS_PALETTE["card"])
    ax.plot(angulos, valores, color=IOS_PALETTE["blue"], linewidth=2)
    ax.fill(angulos, valores, alpha=0.15, color=IOS_PALETTE["blue"])
    ax.set_xticks(angulos[:-1])
    ax.set_xticklabels(categorias, size=9, color=IOS_PALETTE["dark"])
    ax.set_ylim(0, 1)
    ax.set_yticks([0.25, 0.5, 0.75, 1.0])
    ax.set_yticklabels(["25%", "50%", "75%", "100%"], size=7,
                       color=IOS_PALETTE["text_secondary"])
    ax.grid(color="#E5E5EA", linewidth=0.8)
    ax.spines["polar"].set_visible(False)
    fig.tight_layout()
    return fig


def fig_riesgo_gauge(prob: float) -> plt.Figure:
    """Indicador semicircular de riesgo estilo iOS."""
    fig, ax = plt.subplots(figsize=(4, 2.5), facecolor=IOS_PALETTE["bg"])
    ax.set_aspect("equal")
    ax.set_xlim(-1.2, 1.2)
    ax.set_ylim(-0.2, 1.2)
    ax.axis("off")

    # Arco de fondo
    theta = np.linspace(np.pi, 0, 200)
    ax.plot(np.cos(theta), np.sin(theta), color="#E5E5EA", linewidth=18, solid_capstyle="round")

    # Arco de valor
    color = IOS_PALETTE["green"] if prob < 0.35 else IOS_PALETTE["orange"] if prob < 0.65 \
        else IOS_PALETTE["red"]
    theta_val = np.linspace(np.pi, np.pi - prob * np.pi, 200)
    ax.plot(np.cos(theta_val), np.sin(theta_val), color=color,
            linewidth=18, solid_capstyle="round")

    # Texto central
    ax.text(0, 0.15, f"{prob:.0%}", ha="center", va="center",
            fontsize=22, fontweight="700", color=IOS_PALETTE["dark"])
    nivel = "BAJO" if prob < 0.35 else "MEDIO" if prob < 0.65 else "ALTO"
    ax.text(0, -0.05, f"Riesgo {nivel}", ha="center", va="center",
            fontsize=9, color=color, fontweight="600")
    fig.tight_layout(pad=0.5)
    return fig
